"""Google Spreadsheet API wrapper"""

import os
import httplib2

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Tosurnament Bot'
service = None

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('.')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'tosurnament.bot.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def start_service():
    """Starts Google Spreadsheet API service"""
    global service
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

def get_range(spreadsheet_id, range_name):
    """Gets values of a range"""
    if not service:
        return []
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name).execute()
    return result.get('values', [])

def get_ranges(spreadsheet_id, ranges_name):
    """Gets values of multiple ranges"""
    if not service:
        return []
    return []

def write_range(spreadsheet_id, range_name, values, value_input_option="RAW"):
    """Writes values in a range"""
    return write_ranges(spreadsheet_id, [range_name], [values], value_input_option)

def write_ranges(spreadsheet_id, range_name_array, values_array, value_input_option="RAW"):
    """Writes values in multiple ranges"""
    if not service:
        return 1
    data = []
    if len(range_name_array) != len(values_array):
        return 1
    for i in range(0, len(range_name_array)):
        tmp = {
            'range': range_name_array[i],
            'values': values_array[i]
        }
        data.append(tmp)
    body = {
        'valueInputOption': value_input_option,
        'data': data
    }
    result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body).execute()
    return 0
