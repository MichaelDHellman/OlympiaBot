import os.path
import client
import json
import logging 

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

creds = "./credentials/credentials.json"
fpath = "./credentials/token.json"

def main():
    outFile = logging.FileHandler(filename="log.txt", encoding="utf-8", mode='w')
    tokens = {}
    oClient = client.olympiaClient(fpath)
    print(oClient.tokens)
    oClient.run(oClient.tokens["TOKEN"], log_handler=outFile, log_level=logging.WARNING)
    
if __name__ == "__main__":
    main()


"""
def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials\credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=,
                                    range="Master!").execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        print('Name, Major:')
        for row in values:
            if (len(row) > 0):
                print('%s, %s' % (row[1], row[4]))
    except HttpError as err:
        print(err)


if __name__ == '__main__':
    main()
"""