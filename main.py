from pprint import pprint
import pickle
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
    all_threads_info = []
    for thread in threads:
        tdata = service.users().threads().get(userId=user_id, id=thread['id']).execute()
        nmsgs = len(tdata['messages'])
        msgs_in_thread = [tdata['messages'][i] for i in range(nmsgs)]

        sender_email = ''
        all_responses = []
        first_run = True
        for msg in msgs_in_thread:
            if first_run: #only want to get responses, not og message
                pass
            else:
                message = show_message(msg['payload']['parts'][0]['body']['data'])

            responder_email = ''
            for header in msg['payload']['headers']:
                if header['name'] == 'From':
                    if first_run:
                        first_run = False
                        sender_email = find_email(header['value'])
                        sender_dict = {'sender': sender_email}
                        all_responses.append(sender_dict)
                    else:
                        responder_email = find_email(header['value'])
                        msg_dict = {'responder': responder_email, 'reponse': message}
                        all_responses.append(msg_dict)
        all_threads_info.append(all_responses)
    return all_threads_info

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
    x = s.split('On')
    y = ''.join(x[0])
    return y

def find_email(s):
    x = s.split('<')
    y = ''.join(x[1])
    return y[0:len(y)-1]

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


print(show_threads(get_service()))

