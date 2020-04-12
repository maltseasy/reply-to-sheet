from pprint import pprint
import pickle
import requests
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import email
import base64
import re
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def show_threads(service, user_id='me'):
    threads = service.users().threads().list(userId=user_id).execute().get('threads', [])
    for thread in threads:
        tdata = service.users().threads().get(userId=user_id, id=thread['id']).execute()
        nmsgs = len(tdata['messages'])
        entire_thread = tdata['messages'][nmsgs-1]
        msg1 = entire_thread['payload']['parts'][0]['body']['data']
        msg2 = entire_thread['payload']['parts'][1]['body']['data']
        print("yuh")
        pprint(show_message(msg1))
        print("eh")
        pprint(show_message(msg2))
        # for i in range(0, nmsgs):
        #     msg = entire_thread['payload']['parts'][i]['body']['data']
        #     pprint(msg)
        #     print("-------------------------------")
            #['payload']['parts'][1]['body']['data']

def show_message(encoded_message):
    msg_raw = base64.urlsafe_b64decode(encoded_message.encode('ASCII'))
    msg_str = email.message_from_bytes(msg_raw)
    content_type = msg_str.get_content_maintype()

    if content_type == 'multipart':
        #part 1 is plain text, part 2 is html
        part1, part2 = msg_str.get_payload()
        thread_response = find_message(part1.get_payload())
        return thread_response
    else:
        thread_response = find_message(msg_str.get_payload())
        return thread_response

def find_message(s):
    msg = re.search(r'<div dir="ltr">(.*?)<div><br></div>', s)
    if msg != None:
        return msg.group(1)
    else:
        return "Error"


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
