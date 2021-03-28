"""Google Spreadsheet API wrapper"""

from .cell import Cell
from .worksheet import Worksheet

import hashlib
import os
import pickle
import ssl
from discord.ext import commands
import socket
import googleapiclient
from googleapiclient import discovery
from google.oauth2 import service_account
from functools import lru_cache

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
FIELDS = (
    "sheets.merges,"
    "sheets.properties.title,"
    "sheets.properties.gridProperties,"
    "sheets.data.rowData.values.userEnteredValue,"
    "sheets.data.rowData.values.effectiveValue"
)
SERVICE_ACCOUNT_FILE = "service_account.json"
service = None


def start_service():
    """Starts Google Spreadsheet API service."""
    global service
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = discovery.build("sheets", "v4", credentials=credentials)


class Spreadsheet:
    """A spreadsheet. Contains every worksheet, a return_code when trying to get a Spreadsheet and utility functions."""

    def __init__(self, spreadsheet_id):
        self.id = spreadsheet_id
        self.main_worksheet_index = 0
        self.worksheets = []

    def __copy__(self):
        newobj = type(self)(self.id)
        newdict = dict(self.__dict__)
        del newdict["main_worksheet_index"]
        newobj.__dict__.update(newdict)
        return newobj

    @staticmethod
    def retrieve_spreadsheet(spreadsheet_id):
        spreadsheet = Spreadsheet(spreadsheet_id)
        try:
            sheets = _get_spreadsheet_with_values(spreadsheet_id)
        except googleapiclient.errors.HttpError as error:
            try:
                raise HttpError(error.resp["status"], "read", error)
            except KeyError:
                raise HttpError(500, "read", error)
        except (ConnectionResetError, ssl.SSLError, AttributeError) as error:
            raise HttpError(499, "read", error)
        except socket.timeout as error:
            raise HttpError(408, "read", error)
        for index, sheet in enumerate(sheets):
            spreadsheet.worksheets.append(Worksheet(index, sheet["name"], sheet["cells"]))
        return spreadsheet

    @staticmethod
    def retrieve_spreadsheet_and_update_pickle(spreadsheet_id):
        spreadsheet = Spreadsheet.retrieve_spreadsheet(spreadsheet_id)
        spreadsheet.update_pickle()
        return spreadsheet

    @staticmethod
    @lru_cache(maxsize=8)
    def pickle_from_id(spreadsheet_id):
        if not os.path.exists("pickles"):
            os.mkdir("pickles")
            return None
        try:
            with open("pickles/" + hashlib.blake2s(bytes(spreadsheet_id, "utf-8")).hexdigest(), "rb") as pfile:
                return pickle.load(pfile)
        except IOError:
            return None

    @staticmethod
    def get_from_id(spreadsheet_id):
        """Returns a Spreadsheet."""
        spreadsheet = Spreadsheet.pickle_from_id(spreadsheet_id)
        if not spreadsheet:
            spreadsheet = Spreadsheet.retrieve_spreadsheet_and_update_pickle(spreadsheet_id)
        return spreadsheet

    def update_pickle(self):
        if not os.path.exists("pickles"):
            os.mkdir("pickles")
        with open("pickles/" + hashlib.blake2s(bytes(self.id, "utf-8")).hexdigest(), "w+b") as pfile:
            pickle.dump(self, pfile)

    def get_worksheet(self, option=None):
        """Returns a Worksheet by index or name."""
        if not option and self.worksheets:
            return self.worksheets[self.main_worksheet_index]
        elif isinstance(option, str):
            option = option.strip("'")
            for worksheet in self.worksheets:
                if worksheet.name == option:
                    return worksheet
        elif isinstance(option, int):
            if option < len(self.worksheets):
                return self.worksheets[option]
        raise InvalidWorksheet(str(option))

    def update(self):
        """Sends an update request to the real spreadsheet."""
        ranges_name, ranges_values = [], []
        for worksheet in self.worksheets:
            ranges, values = worksheet.get_updated_values_with_ranges()
            ranges_name = [*ranges_name, *ranges]
            ranges_values = [*ranges_values, *values]
        if not ranges_name or not ranges_values:
            return
        try:
            _write_ranges(self.id, ranges_name, ranges_values)
        except googleapiclient.errors.HttpError as e:
            try:
                raise HttpError(e.resp["status"], "write", e)
            except KeyError:
                raise HttpError(500, "write", e)
        except (ConnectionResetError, ssl.SSLError) as e:
            raise HttpError(499, "write", e)
        except socket.timeout as e:
            raise HttpError(408, "write", e)
        for worksheet in self.worksheets:
            worksheet.reset_updated_state()

    def get_worksheet_and_range(self, range_name):
        """Returns the worksheet specified in the range, or the main worksheet."""
        if "!" not in range_name:
            return self.get_worksheet(), range_name
        worksheet_name, range_name = range_name.rsplit("!", 1)
        return self.get_worksheet(worksheet_name), range_name

    def get_range(self, range_name):
        """Returns an array of Cell. If a Cell does not exist in the range, it creates it."""
        worksheet, range_name = self.get_worksheet_and_range(range_name)
        return worksheet.get_range(range_name)

    def get_cells_with_value_in_range(self, range_name):
        worksheet, range_name = self.get_worksheet_and_range(range_name)
        return worksheet.get_cells_with_value_in_range(range_name)

    def change_value_in_range(self, range_name, previous_value, new_value, case_sensitive=False):
        """Changes the value of all cells that are equal to previous_value to new_value in a range."""
        worksheet, range_name = self.get_worksheet_and_range(range_name)
        return worksheet.change_value_in_range(range_name, previous_value, new_value, case_sensitive)

    def find_cells(self, range_name, value_to_find, case_sensitive=False):
        """Returns an array of Cell matching the value_to_find."""
        if isinstance(range_name, str):
            worksheet, range_name = self.get_worksheet_and_range(range_name)
        else:
            worksheet = self.get_worksheet()
        return worksheet.find_cells(range_name, value_to_find, case_sensitive)


class HttpError(Exception):
    """Special exception raised when the execute functions of the API fails."""

    def __init__(self, error_code, operation, error):
        self.code = error_code
        self.operation = operation
        self.error = error


class InvalidWorksheet(commands.CommandError):
    """Special exception raised when the specified worksheet is invalid."""

    def __init__(self, worksheet):
        self.worksheet = worksheet


def _get_cell_value(value):
    if "userEnteredValue" in value and "formulaValue" in value["userEnteredValue"]:
        return value["userEnteredValue"]["formulaValue"]
    elif "userEnteredValue" in value and "stringValue" in value["userEnteredValue"]:
        return value["userEnteredValue"]["stringValue"].strip()
    elif "userEnteredValue" in value and "numberValue" in value["userEnteredValue"]:
        return value["userEnteredValue"]["numberValue"]
    elif "userEnteredValue" in value and "boolValue" in value["userEnteredValue"]:
        return value["userEnteredValue"]["boolValue"]
    # ? Not used for the main use case, might be needed for other use cases ?
    # elif "effectiveValue" in value and "formattedValue" in value["effectiveValue"]:
    #    return value["effectiveValue"]["formattedValue"]
    # elif "effectiveValue" in value and "stringValue" in value["effectiveValue"]:
    #    return value["effectiveValue"]["stringValue"]
    return ""


def _get_spreadsheet_with_values(spreadsheet_id):
    """Gets all sheets and their cells."""
    sheets = []
    if not service:
        return sheets
    result = service.spreadsheets().get(spreadsheetId=spreadsheet_id, fields=FIELDS).execute()
    for sheet in result["sheets"]:
        if "merges" in sheet:
            merges_info = sheet["merges"]
        else:
            merges_info = []
        values = sheet["data"][0]
        cells = []
        if "rowData" in values:
            for y, row in enumerate(values["rowData"]):
                cells.append([])
                if "values" in row:
                    for x, value in enumerate(row["values"]):
                        cell = Cell(x, y, _get_cell_value(value))
                        for merge_info in merges_info:
                            x_merge_range = range(merge_info["startColumnIndex"], merge_info["endColumnIndex"])
                            y_merge_range = range(merge_info["startRowIndex"], merge_info["endRowIndex"])
                            if x in x_merge_range and y in y_merge_range:
                                cell.set_merge_range(x_merge_range, y_merge_range)
                        cells[y].append(cell)
        sheets.append({"name": sheet["properties"]["title"], "cells": cells})
        # TODO: store sheet["properties"]["gridProperties"]["rowCount"/"columnCount"] too
    return sheets


def _write_ranges(spreadsheet_id, range_name_array, values_array, value_input_option="USER_ENTERED"):
    """Writes values in multiple ranges in the real spreadsheet."""
    if not service or len(range_name_array) != len(values_array):
        return 1
    data = []
    for i in range(0, len(range_name_array)):
        tmp = {"range": range_name_array[i], "values": values_array[i]}
        data.append(tmp)
    body = {"valueInputOption": value_input_option, "data": data}
    service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    return 0
