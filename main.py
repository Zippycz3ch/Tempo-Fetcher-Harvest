import requests
from requests.auth import HTTPBasicAuth
import sys
import os

import tempo
import harvest

if os.environ.get('local'):
    import constants_local as constants
else:
    import constants

if __name__ == "__main__":

    auth = HTTPBasicAuth(constants.ATLASSIAN_EMAIL, constants.ATLASSIAN_API_TOKEN)
    response = requests.get("https://cleevio.atlassian.net/rest/api/2/project/" + constants.PROJECT_KEY,
                            headers={"Accept": "application/json"}, auth=auth).json()

    if "errorMessages" in response:
        [print(i) for i in response["errorMessages"]]
        sys.exit()

    # fetch the logs
    logs = tempo.Fetcher().start()

    harvest.Fetcher(response["name"], logs).start()
