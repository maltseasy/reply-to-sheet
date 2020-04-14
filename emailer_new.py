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
from time import sleep
spreadsheet_body = {
    'properties': {
        'title': 'Your Email Chain'
    }}

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
SCOPES_EMAIL = ['https://www.googleapis.com/auth/gmail.readonly']
SCOPES_SHEET = ['https://www.googleapis.com/auth/drive']

def get_sheet_service():
    global sheetservice
    global drive_service
    global emailservice
    creds_email = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token_email.pickle'):
        with open('token_email.pickle', 'rb') as token:
            creds_email = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds_email or not creds_email.valid:
        if creds_email and creds_email.expired and creds_email.refresh_token:
            creds_email.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials_email.json', SCOPES_EMAIL)
            creds_email = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token_email.pickle', 'wb') as token:
            pickle.dump(creds_email, token)

    emailservice = googleapiclient.discovery.build('gmail', 'v1', credentials=creds_email)
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
    return sheetservice, drive_service, emailservice

def main(service, user_id='me'):
    threads = service.users().threads().list(userId=user_id).execute().get('threads', [])
    cc_thread = []
    for thread in threads:
        iscc = False

        tdata = service.users().threads().get(userId=user_id, id=thread['id']).execute()
        nmsgs = len(tdata['messages'])
        
        
        for header in tdata['messages'][0]['payload']['headers']:
            if header['name'] == 'Cc':
                iscc = True
               
        if iscc:

            thread_id = tdata['id']
            pprint(tdata['messages'][0]['payload']['headers'])
            print('\n\n\n\n')
            thread_client = re.search("\<(.*?)\>",tdata['messages'][0]['payload']['headers'][6]['value']).group(1)
            thread_origin = re.search("\<(.*?)\>",tdata['messages'][0]['payload']['headers'][22]['value']).group(1)
            print(thread_client)
            print(thread_origin)
            if thread_client not in sheetslink:
                temp = {thread_client:{
                            "sheetid": 0,
                            "idlist": []
                            }}
                sheetslink.update(temp)
            msg_body = tdata['messages'][0]['payload']['parts'][0]['body']['data']
            msg_raw = base64.urlsafe_b64decode(msg_body.encode('ASCII'))
            msg_str = email.message_from_bytes(msg_raw)
            content_type = msg_str.get_content_maintype()
            if content_type == 'multipart':
                #part 1 is plain text, part 2 is html
                part1, part2 = msg_str.get_payload()
                thread_response = find_message(part1.get_payload())
                pprint(thread_response)
            else:
                thread_response = find_message(msg_str.get_payload())
                pprint(thread_response)
            
            if thread_id not in sheetslink[thread_client]["idlist"]:
                sheetslink[thread_client]["idlist"].append(thread_id)
                if sheetslink[thread_client]["sheetid"] == 0:
                    spreadsheet = sheetservice.spreadsheets().create(body=spreadsheet_body,fields='spreadsheetId').execute()
                    sheetslink[thread_client]["sheetid"] = spreadsheet.get('spreadsheetId')
                request = sheetservice.spreadsheets().values().get(spreadsheetId=sheetslink[thread_client]["sheetid"], range='A:Z', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='SERIAL_NUMBER')
                response = request.execute()
                
                values = response['values']
                val_toadd = [thread_id,thread_origin,thread_client,thread_response]
                values.append(val_toadd)
                pprint(values)
                body = {
                'values': values
                }
                result = sheetservice.spreadsheets().values().update(spreadsheetId=sheetslink[thread_client]["sheetid"],body=body, range='A:Z',valueInputOption='USER_ENTERED').execute()
                share(drive_service, thread_client,sheetslink[thread_client]["sheetid"])

def share(drive_service,email,id):
    batch = drive_service.new_batch_http_request(callback=callback)
    user_permission = {
    'type': 'user',
    'role': 'writer',
    'emailAddress': email
    }
    batch.add(drive_service.permissions().create(
        fileId=id,
        body=user_permission,
        fields='id',
    ))
    batch.execute()      
        
def find_message(s):
    x = s.split('On')
    y = ''.join(x[0])
    return y.replace('\n','').replace('\r','')
if __name__ == "__main__":
    try:
        sheetservice, drive_service, emailservice = get_sheet_service()
        while 1:
            sleep(1)
            main(emailservice)
            break
        write_json(sheetslink)
    except KeyboardInterrupt:
        write_json(sheetslink)  
        print("Program Ended.")
