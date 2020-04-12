from pprint import pprint
import pickle
import os.path
import googleapiclient.discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import email
import base64
import re
import json
def callback(request_id, response, exception):
    if exception:
        # Handle error
        print (exception)
    else:
        print ("Permission Id: %s" % response.get('id'))
def write_json(data, filename='sheetslink.json'): 
    with open(filename,'w') as f: 
        json.dump(data, f, indent=4)

with open('sheetslink.json') as json_file: 
    sheetslink = json.load(json_file) 

pprint(sheetslink)
SCOPES_EMAIL = ['https://www.googleapis.com/auth/gmail.readonly']
SCOPES_SHEET = ['https://www.googleapis.com/auth/drive']

def show_threads(service, user_id='me'):
    spreadsheet_body = {
    'properties': {
        'title': 'Your Email Chain'
    }}
    global spreadsheetid
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
    pprint(all_threads_info[1])
    if all_threads_info[1]['responder'] in sheetslink:
        spreadsheetid = sheetslink[all_threads_info[0][0]['sender']]
        request = sheetservice.spreadsheets().values().get(spreadsheetId=spreadsheetid, range='A:B', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='SERIAL_NUMBER')
        response = request.execute()
        share(drive_service,all_threads_info[0][1]['responder'])
    else:
        
        spreadsheet = sheetservice.spreadsheets().create(body=spreadsheet_body,
                                        fields='spreadsheetId').execute()
        spreadsheetid = spreadsheet.get('spreadsheetId')
        temp = {all_threads_info[0][0]['sender']:spreadsheetid}
        sheetslink.update(temp)
        request = sheetservice.spreadsheets().values().get(spreadsheetId=spreadsheetid, range='A:B', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='SERIAL_NUMBER')
        response = request.execute()
        values = [
        [str(response)],
        [all_threads_info[0][0]['sender'],'all_threads_info[0][1][]']]
        # print(response['values'][0][0])
        body = {
        'values': values
        }
        result = sheetservice.spreadsheets().values().update(spreadsheetId=spreadsheetid,body=body, range='A:B',valueInputOption='USER_ENTERED').execute()
        share(drive_service, all_threads_info[0][0]['sender'])
    return all_threads_info[0]
def share(drive_service,email):
    batch = drive_service.new_batch_http_request(callback=callback)
    user_permission = {
    'type': 'user',
    'role': 'writer',
    'emailAddress': email
    }
    batch.add(drive_service.permissions().create(
        fileId=spreadsheetid,
        body=user_permission,
        fields='id',
    ))
    batch.execute()
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
    if os.path.exists('token_email.pickle'):
        with open('token_email.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials_email.json', SCOPES_EMAIL)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token_email.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)

    return service
def get_sheet_service():
    global sheetservice
    global drive_service
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token_sheet.pickle'):
        with open('token_sheet.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials_sheet.json', SCOPES_SHEET)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token_sheet.pickle', 'wb') as token:
            pickle.dump(creds, token)

    sheetservice = googleapiclient.discovery.build('sheets', 'v4', credentials=creds)
    drive_service = googleapiclient.discovery.build('drive', 'v3', credentials=creds)
    return sheetservice, drive_service

if __name__ == "__main__":
    try:
        sheetservice, drive_service = get_sheet_service()

        pprint(show_threads(get_service()))
        write_json(sheetslink)  
    except KeyboardInterrupt:
        write_json(sheetslink)  
        print("yea")
