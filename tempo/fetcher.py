import requests
import datetime
import os

if os.environ.get('local'):
    import constants_local as constants
else:
    import constants


class Fetcher(object):

    def __init__(self):
        self.token = constants.TEMPO_API_TOKEN
        self.project = constants.PROJECT_KEY
        self.days = constants.DAYS

    def start(self):
        date = datetime.datetime.today()

        today = date.strftime('%Y-%m-%d')
        from_date = (date - datetime.timedelta(days=self.days)).strftime('%Y-%m-%d')

        print('TEMPO: Fetching worklogs')
        headers = {'Authorization': 'Bearer ' + self.token}

        res = requests.get('https://api.tempo.io/core/3/worklogs/project/'
                           + self.project
                           + "?from=" + from_date
                           + "&to=" + today
                           + "&limit=1000", headers=headers)

        if res.status_code != 200:
            print(res.status_code, res.reason)
            exit(0)

        res = res.json()

        logs = dict()
        print('TEMPO: Calculating the working time')
        while True:
            results = res["results"]

            for i in results:
                key = i['author']['displayName']

                if key not in logs:
                    logs[key] = {'issues': []}

                issue_key = i['issue']['key']
                logs[key]['issues'].append({
                    'issue_key': issue_key,
                    'time': i['billableSeconds'],
                    'spent_date': datetime.datetime.strptime(i['startDate'], '%Y-%m-%d').strftime('%Y-%m-%d'),
                    'tempo_id': i['tempoWorklogId']
                })

            if 'next' not in res['metadata']:
                break

            res = requests.get(res['metadata']['next'], headers=headers).json()

        return logs
