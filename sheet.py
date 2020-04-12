import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
def callback(request_id, response, exception):
    if exception:
        # Handle error
        print (exception)
    else:
        print ("Permission Id: %s" % response.get('id'))
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
SAMPLE_RANGE_NAME = 'Class Data!A2:E'

def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
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

    service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    spreadsheet = {
    'properties': {
        'title': 'title'
    }
    }
    spreadsheet = service.spreadsheets().create(body=spreadsheet,
                                        fields='spreadsheetId').execute()
    print('Spreadsheet ID: {0}'.format(spreadsheet.get('spreadsheetId')))

    batch = drive_service.new_batch_http_request(callback=callback)
    user_permission = {
    'type': 'user',
    'role': 'writer',
    'emailAddress': 'aryanmisra4@gmail.com'
    }
    batch.add(drive_service.permissions().create(
        fileId=spreadsheet.get('spreadsheetId'),
        body=user_permission,
        fields='id',
    ))
    batch.execute()


    # request = service.spreadsheets().values().get(spreadsheetId='1a-j_1JRJZFahjp6ES8GTRQ0p7UbLTuMCh49H258Avs4', range='A:B', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='SERIAL_NUMBER')
    # response = request.execute()
    # values = [
    # [response['values'][0][0], response['values'][0][1]],
    # ['hi3','hi8']]
    # # print(response['values'][0][0])
    # body = {
    # 'values': values
    # }

    # result = service.spreadsheets().values().update(
    # spreadsheetId='1a-j_1JRJZFahjp6ES8GTRQ0p7UbLTuMCh49H258Avs4',body=body, range='A:B',valueInputOption='USER_ENTERED').execute()
    # print('{0} cells updated.'.format(result.get('updatedCells')))
if __name__ == '__main__':
    main()