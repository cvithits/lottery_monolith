import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow,Flow
from google.auth.transport.requests import Request
import os
import pickle

#https://medium.com/analytics-vidhya/how-to-read-and-write-data-to-google-spreadsheet-using-python-ebf54d51a72c

#change this by your sheet ID
SPREADSHEET_ID = '1SQPloXlYzjY4DgjBnIRgVIY6Y4026rUE9puEQQmXenU'

#change the range if needed
SAMPLE_RANGE_NAME = 'A1:D200'

def Create_Service(client_secret_file, api_service_name, api_version, *scopes):
    global service
    SCOPES = [scope for scope in scopes[0]]
    #print(SCOPES)
    
    cred = None

    if os.path.exists('token_write.pickle'):
        with open('token_write.pickle', 'rb') as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            cred = flow.run_local_server()

        with open('token_write.pickle', 'wb') as token:
            pickle.dump(cred, token)

    try:
        service = build(api_service_name, api_version, credentials=cred)
        print(api_service_name, 'service created successfully')
        #return service
    except Exception as e:
        print(e)
        #return None
        
Create_Service('credentials.json', 'sheets', 'v4',['https://www.googleapis.com/auth/spreadsheets'])

def add_sheets(gsheet_id, sheet_name):
    try:
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }]
        }

        response = service.spreadsheets().batchUpdate(
            spreadsheetId=gsheet_id,
            body=request_body
        ).execute()

        #return response
    except Exception as e:
        print(e)


def Export_Data_To_Sheets(df, sheetName):

    add_sheets(SPREADSHEET_ID, sheetName)
    response = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        valueInputOption='RAW',
        range="'"+sheetName+"'!"+SAMPLE_RANGE_NAME,
        body=dict(
            majorDimension='ROWS',
            values=df.T.reset_index().T.values.tolist())
    ).execute()
    print('Sheet successfully Updated')