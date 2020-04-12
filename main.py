from pprint import pprint
import pickle
import requests
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def show_threads(service, user_id='me'):
    threads = service.users().threads().list(userId=user_id).execute().get('threads', [])
    for thread in threads:
        tdata = service.users().threads().get(userId=user_id, id=thread['id']).execute()
        nmsgs = len(tdata['messages'])
        
        #pprint(tdata)
        for k in msgs.keys():
            if k == 'payload':
                print(msgs[k]['body'])#.keys())
                #print(msgs[k]['parts'])
# id
# threadId
# labelIds
# snippet
# historyId
# internalDate
# payload
# sizeEstimate
        msgs = tdata['messages'][0]['snippet']

        # subject = ''
        # for header in msg['headers']:
        #     if header['name'] == 'Subject':
        #         subject = header['value']
        #         break


def get_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    return service


show_threads(get_service())
def threads(service, user_id = "me"):
    threads = service.users().threads()
