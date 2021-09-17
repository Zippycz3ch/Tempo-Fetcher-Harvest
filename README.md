# Tempo Fetcher & Harvest

MVP solution to fetch worklogs from the Tempo connected to the JIRA and create a time entries in the Harvest.

## Requirements
* Python3

## Setup
Before running the program, set-up the API keys in the `constants.py` file.

### Required keys
* `TEMPO_API_TOKEN` - API token from Tempo. Can be created [here](https://cleevio.atlassian.net/plugins/servlet/ac/io.tempo.jira/tempo-app#!/configuration/api-integration)
* `ATLASSIAN_API_TOKEN` - API token from Atlassian. Can be created [here](https://id.atlassian.com/manage-profile/security/api-tokens)
* `ATLASSIAN_EMAIL` - E-mail associated with the `ATLASSIAN_API_TOKEN`
* `HARVEST_API_TOKEN` - API token from Harvest. Can be created [here](https://id.getharvest.com/developers)
* `HARVEST_ACCOUNT_ID` - Account ID associated with the Harvest API token
* `PROJECT_KEY` - Project key to find in the Tempo and in Harvest. For example `GT` (`GoodTrust`)
* `DAYS` - How many days back to fetch the entries

For the creating time entries, the account associated with the Harvest API token should be able to create, delete, fetch and update the project.


# Running
Run the application from the command line with `python3 main.py`