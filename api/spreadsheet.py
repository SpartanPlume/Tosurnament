"""Google Spreadsheet API wrapper"""

import os
import re
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

def get_spreadsheet_with_values(spreadsheet_id):
    """Gets all sheets and their cells"""
    sheets = []
    if not service:
        return sheets
    result = service.spreadsheets().get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title,sheets.properties.gridProperties,sheets.data.rowData.values.userEnteredValue,sheets.data.rowData.values.effectiveValue").execute()
    for sheet in result["sheets"]:
        values = []
        tmp_values = sheet["data"][0]
        if "rowData" in tmp_values:
            tmp_values = tmp_values["rowData"]
            for i, row in enumerate(tmp_values):
                values.append([])
                if "values" in row:
                    for value in row["values"]:
                        if "userEnteredValue" in value and "formulaValue" in value["userEnteredValue"]:
                            values[i].append(value["userEnteredValue"]["formulaValue"])
                        elif "effectiveValue" in value and "formattedValue" in value["effectiveValue"]:
                            values[i].append(value["effectiveValue"]["formattedValue"])
                        elif "effectiveValue" in value and "stringValue" in value["effectiveValue"]:
                            values[i].append(value["effectiveValue"]["stringValue"])
                        elif "userEnteredValue" in value and "stringValue" in value["userEnteredValue"]:
                            values[i].append(value["userEnteredValue"]["stringValue"])
                        else:
                            values[i].append("")
        sheet_range = "A1:" + to_cell((sheet["properties"]["gridProperties"]["columnCount"], sheet["properties"]["gridProperties"]["rowCount"]))
        sheets.append({"name": sheet["properties"]["title"], "range": sheet_range, "values": values})
    return sheets

def get_range(spreadsheet_id, range_name, major_dimension="ROWS", value_render_option="FORMATTED_VALUE", date_time_render_option="SERIAL_NUMBER"):
    """Gets values of a range"""
    if not service:
        return []
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name, majorDimension=major_dimension, valueRenderOption=value_render_option, dateTimeRenderOption=date_time_render_option).execute()
    return result.get('values', [])

def get_ranges(spreadsheet_id, range_names, major_dimension="ROWS", value_render_option="FORMATTED_VALUE", date_time_render_option="SERIAL_NUMBER"):
    """Gets values of multiple ranges"""
    if not service:
        return []
    result = service.spreadsheets().values().batchGet(
        spreadsheetId=spreadsheet_id, ranges=range_names, majorDimension=major_dimension, valueRenderOption=value_render_option, dateTimeRenderOption=date_time_render_option).execute()
    value_ranges = result.get('valueRanges', [])
    if value_ranges:
        tmp = []
        for value_range in value_ranges:
            tmp.append(value_range.get('values', []))
        value_ranges = tmp
    return value_ranges

def write_range(spreadsheet_id, range_name, values, value_input_option="USER_ENTERED"):
    """Writes values in a range"""
    return write_ranges(spreadsheet_id, [range_name], [values], value_input_option)

def write_ranges(spreadsheet_id, range_name_array, values_array, value_input_option="USER_ENTERED"):
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

def from_cell(cell):
    coordinates = re.split('(\d+)', cell)
    x = int(coordinates[0], 36) - 10
    if len(coordinates) == 1:
        y = -1
    else:
        y = int(coordinates[1]) - 1
    return (x, y)

def to_cell(coordinates):
    x, y = coordinates
    cell = to_base(x, "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if y >= 0:
        cell += str(y + 1)
    return (cell)

def to_base(n, base):
    len_base = len(base)
    if n < len_base:
        return base[n]
    else:
        return to_base(n // len_base, base) + base[n % len_base]
