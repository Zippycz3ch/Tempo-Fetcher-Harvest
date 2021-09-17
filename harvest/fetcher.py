import requests
import os
import sqlite3
import json

if os.environ.get('local'):
    import constants_local as constants
else:
    import constants

import sys

API_URL = "https://api.harvestapp.com/api/v2"


class Fetcher(object):

    def __init__(self, project_name, jira_logs):
        self.token = constants.HARVEST_API_TOKEN
        self.account_id = constants.HARVEST_ACCOUNT_ID
        self.project_key = constants.PROJECT_KEY

        self.project_name = project_name
        self.jira_logs = jira_logs

        self.headers = {'Authorization': 'Bearer ' + self.token, 'Harvest-Account-Id': self.account_id}

        self.tasks = {}
        self.users = {}

        self.db = sqlite3.connect('harvest.db')
        self.init_db()
        self.index()

    def start(self):
        project_id = self.find_project()
        c = self.db.cursor()

        for user_name, val in self.jira_logs.items():
            print('Starting to convert for user:', user_name)

            user_id = self.get_user_id(user_name)

            if user_id is None:
                continue

            for issue in val['issues']:
                issue_key = issue['issue_key']

                time = issue['time'] / float(3600)
                tempo_id = issue['tempo_id']

                exist = c.execute(f"SELECT * FROM `entry` WHERE `tempo_id` = {tempo_id}").fetchone()

                if exist is not None:
                    if round(time, 2) != exist[4]:
                        print(f"Updating the entry {exist[0]} with time {time}")
                        requests.patch(f"{API_URL}/time_entries/{exist[0]}", headers=self.headers, json={'hours': time})

                else:
                    task_id = self.get_task_id(issue_key)
                    res = requests.post(f"{API_URL}/projects/{project_id}/task_assignments", json={'task_id': task_id},
                                        headers=self.headers)

                    print("Binding with the project :", res.status_code, res.reason)

                    res = requests.post(f'{API_URL}/time_entries', json=
                    {
                        'user_id': user_id,
                        'project_id': project_id,
                        'task_id': task_id,
                        'spent_date': issue['spent_date'],
                        'hours': time
                    }, headers=self.headers)

                    print(issue_key, '-', res.status_code, res.reason)

                    if res.status_code == 422:
                        print(res.json())

                    harvest_id = res.json()['id']
                    spent = issue['spent_date']
                    c.execute(
                        f"INSERT INTO `entry` (`harvest_id`, `tempo_id`, `user`, `date`, `hours`) VALUES "
                        f"('{harvest_id}', '{tempo_id}', '{user_name}', '{spent}', '{round(time, 2)}')")

            self.db.commit()

            print('Finished for user:', user_name)

    def get_user_id(self, user_name):
        if user_name in self.users:
            return self.users[user_name]

        print('Cannot find user', user_name)
        return None

    def get_task_id(self, task_name):
        if task_name in self.tasks:
            return self.tasks[task_name]

        task_response = requests.post(f'{API_URL}/tasks', json={'name': task_name}, headers=self.headers).json()

        if 'id' not in task_response:
            print(f'Error during creating task {task_name}. Response:', task_response)
            sys.exit()

        task_id = task_response['id']

        self.tasks[task_name] = task_id

        c = self.db.cursor()
        c.execute(f'INSERT INTO `task` (`id`, `name`) VALUES (\'{task_id}\', \'{task_name}\')')
        self.db.commit()

        return task_id

    def find_project(self):
        response = requests.get(f'{API_URL}/projects', headers=self.headers).json()

        if 'error' in response:
            print(response['error_description'])
            return

        for i in response['projects']:
            if i['code'] == self.project_key:
                return i['id']

        print(f'Project {self.project_key} not found on Harvest.')
        sys.exit()

    def index_users(self):
        c = self.db.cursor()

        print('Harvest: creating index file for users')
        res = requests.get(f'{API_URL}/users?is_active=true', headers=self.headers).json()

        while True:
            for i in res['users']:
                name = f"{i['first_name']} {i['last_name']}"
                c.execute(f'INSERT OR IGNORE INTO `user` (`id`, `name`) VALUES (\'{i["id"]}\', \'{name}\')')
                self.users[name] = i['id']

            if not res['links']['next']:
                break

            res = requests.get(res['links']['next'], headers=self.headers).json()

        self.db.commit()

        results = c.execute('SELECT * FROM `user`').fetchall()
        self.users = {name: key for key, name in results}

    def index_tasks(self):
        c = self.db.cursor()
        results = c.execute('SELECT * FROM `task`').fetchall()

        if len(results) > 0:
            self.tasks = {name: key for key, name in results}
        else:
            print('Harvest: creating index file for tasks')
            res = requests.get(f'{API_URL}/tasks?is_active=true', headers=self.headers).json()

            while True:
                for i in res['tasks']:
                    c.execute(f'INSERT INTO `task` (`id`, `name`) VALUES (\'{i["id"]}\', \'{i["name"]}\')')
                    self.tasks[i['name']] = i['id']

                if not res['links']['next']:
                    break

                res = requests.get(res['links']['next'], headers=self.headers).json()

            self.db.commit()

    def index(self):
        self.index_tasks()
        self.index_users()

    def init_db(self):
        c = self.db.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS `user` (
            `id` VARCHAR(255) PRIMARY KEY UNIQUE,
            `name` VARCHAR(255) NOT NULL)
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS `task` (
            `id` VARCHAR(255) PRIMARY KEY UNIQUE,
            `name` VARCHAR(255) NOT NULL)
                ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS `entry` (
            `harvest_id` VARCHAR(255) PRIMARY KEY UNIQUE,
            `tempo_id` VARCHAR(255) NOT NULL,
            `user` VARCHAR(255) NOT NULL,
            `date` datetime(6) NOT NULL,
            `hours` decimal(19,2) NOT NULL)
                ''')

        self.db.commit()
