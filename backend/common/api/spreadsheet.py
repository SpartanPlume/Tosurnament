"""Google Spreadsheet API wrapper"""

import hashlib
import os
import pickle
import ssl
from discord.ext import commands
import re
import socket
import googleapiclient
from googleapiclient import discovery
from google.oauth2 import service_account
from functools import lru_cache

LETTER_BASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
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


class Cell:
    """Contains coordinates and a value."""

    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
        self.x_merge_range = [x]
        self.y_merge_range = [y]
        self._updated = False

    def __setattr__(self, name, value):
        if name == "value":
            self._updated = True
        return super().__setattr__(name, value)

    def __repr__(self):
        return "(%i, %i, %s)" % (self.x, self.y, str(self.value))

    def set_merge_range(self, x_merge_range, y_merge_range):
        """Sets the x_range and y_range of the merge containing this cell."""
        self.x_merge_range = x_merge_range
        self.y_merge_range = y_merge_range

    def has_value(self, value_to_compare, case_sensitive=False):
        """Checks if the cell contains a value. To use in case of multi values like: value1/value2."""
        cell_value = self.value
        if not case_sensitive:
            value_to_compare = value_to_compare.lower()
            cell_value = cell_value.lower()
        if cell_value == value_to_compare:
            return True
        values = str(self.value).split("/")
        for value in values:
            if value.strip() == value_to_compare:
                return True
        return False

    def change_value_to_string(self):
        """Changes internal value to string type without setting the _updated variable to True."""
        object.__setattr__(self, "value", str(self.value))


class Worksheet:
    """Sheet of a spreasheet. Contains the index, name, cells and utility functions."""

    def __init__(self, index, sheet_name, cells):
        self.index = index
        self.name = sheet_name
        self.cells = cells

    def get_cell(self, x, y):
        """Returns the corresponding Cell. If it does not exist, it creates it."""
        while y >= len(self.cells):
            self.cells.append([])
        while x >= (current_x := len(self.cells[y])):
            self.cells[y].append(Cell(current_x, y, ""))
        return self.cells[y][x]

    def _from_column_range(self, range_name):
        """Gets the range from a range name when the range is column only."""
        x_range = []
        range_name_splitted = range_name.split(":")
        if len(range_name_splitted) == 1:
            x_range.append(from_letter_base(range_name_splitted[0]))
        else:
            x_min = from_letter_base(range_name_splitted[0])
            x_max = from_letter_base(range_name_splitted[1])
            x_range = range(x_min, x_max + 1)
        return x_range, []

    def _from_row_range(self, range_name):
        """Gets the range from a range name when the range is row only."""
        y_range = []
        range_name_splitted = range_name.split(":")
        if len(range_name_splitted) == 1:
            y_range.append(int(range_name_splitted[0]) - 1)
        else:
            y_min = int(range_name_splitted[0]) - 1
            y_max = int(range_name_splitted[1]) - 1
            y_range = range(y_min, y_max + 1)
        return [], y_range

    def _from_square_range(self, range_name):
        """Gets the range from a range name when the range is a square."""
        x_range, y_range = [], []
        range_name_splitted = range_name.split(":")
        separate_regex = re.compile(r"(\d+)")
        if len(range_name_splitted) == 1:
            column, row, _ = separate_regex.split(range_name_splitted[0])
            x_range.append(from_letter_base(column))
            y_range.append(int(row) - 1)
        else:
            column, row, _ = separate_regex.split(range_name_splitted[0])
            x_min = from_letter_base(column)
            y_min = int(row) - 1
            column, row, _ = separate_regex.split(range_name_splitted[1])
            x_max = from_letter_base(column)
            y_max = int(row) - 1
            x_range = range(x_min, x_max + 1)
            y_range = range(y_min, y_max + 1)
        return x_range, y_range

    def _from_partial_column_range(self, range_name):
        """Gets the range from a range name when the range is column only."""
        range_part1, range_part2 = range_name.split(":")
        separate_regex = re.compile(r"(\d+)")
        if len((splitted_range_part1 := separate_regex.split(range_part1))) == 3:
            column, row, _ = splitted_range_part1
            column2 = range_part2
        else:
            column = range_part1
            column2, row, _ = separate_regex.split(range_part2)
        x_min = from_letter_base(column)
        x_max = from_letter_base(column2)
        y_min = int(row) - 1
        y_max = len(self.cells)
        return range(x_min, x_max + 1), range(y_min, y_max)

    def _from_partial_row_range(self, range_name):
        """Gets the range from a range name when the range is row only."""
        range_part1, row2 = range_name.split(":")
        separate_regex = re.compile(r"(\d+)")
        column, row, _ = separate_regex.split(range_part1)
        x_min = from_letter_base(column)
        y_min = int(row) - 1
        y_max = int(row2) - 1
        x_max = 0
        while y_max >= len(self.cells):
            self.cells.append([])
        for y in range(y_min, y_max + 1):
            if x_max < (row_length := len(self.cells[y])):
                x_max = row_length
        return range(x_min, x_max), range(y_min, y_max + 1)

    def get_range(self, range_names):
        """Returns an array of Cell. If a Cell does not exist in the range, it creates it."""
        if not range_names:
            return []
        x_ranges, y_ranges = [], []
        for range_name in range_names.split(","):
            range_name = range_name.strip()
            if re.match(r"^[A-Z]+(:[A-Z]+)?$", range_name):
                x_range, y_range = self._from_column_range(range_name)
            elif re.match(r"^[0-9]+(:[0-9]+)?$", range_name):
                x_range, y_range = self._from_row_range(range_name)
            elif re.match(r"^[A-Z]+[0-9]+(:[A-Z]+[0-9]+)?$", range_name):
                x_range, y_range = self._from_square_range(range_name)
            elif re.match(r"^[A-Z]+[0-9]*:[A-Z]+[0-9]*$", range_name):
                x_range, y_range = self._from_partial_column_range(range_name)
            elif re.match(r"^[A-Z]+[0-9]+:[0-9]+$", range_name):
                x_range, y_range = self._from_partial_row_range(range_name)
            else:
                continue
            x_ranges.append(x_range)
            y_ranges.append(y_range)
        range_cells = []
        for x_range, y_range in zip(x_ranges, y_ranges):
            if not y_range:
                y_range = range(0, len(self.cells))
            if not x_range:
                max_x = 0
                for row in self.cells:
                    if max_x < (row_length := len(row)):
                        max_x = row_length
                x_range = range(0, max_x)
            for new_y, y in enumerate(y_range):
                if new_y >= len(range_cells):
                    range_cells.append([])
                for x in x_range:
                    range_cells[new_y].append(self.get_cell(x, y))
        return range_cells

    def get_cells_with_value_in_range(self, range_name):
        range_cells = self.get_range(range_name)
        cells_with_value = []
        for row in range_cells:
            for cell in row:
                if cell.value:
                    cells_with_value.append(cell)
        return cells_with_value

    def change_value_in_range(self, range_name, previous_value, new_value, case_sensitive=False):
        """Changes the value of all cells that are equal to previous_value to new_value in a range."""
        correponding_cells = self.find_cells(range_name, previous_value, case_sensitive)
        value_changed = False
        for cell in correponding_cells:
            cell.value = new_value
            value_changed = True
        return value_changed

    def find_cells(self, range_name, value_to_find, case_sensitive=False):
        """Returns an array of Cell matching the value_to_find."""
        value_to_find_with_case = value_to_find
        if not case_sensitive:
            value_to_find_with_case = value_to_find_with_case.lower()
        if isinstance(range_name, str):
            range_cells = self.get_range(range_name)
        elif isinstance(range_name, list):
            range_cells = range_name
        else:
            return []
        matching_cells = []
        for row in range_cells:
            for cell in row:
                cell_value_with_case = cell.value
                if not case_sensitive:
                    cell_value_with_case = str(cell_value_with_case).lower()
                if cell_value_with_case == value_to_find_with_case:
                    matching_cells.append(cell)
        return matching_cells

    def get_range_name(self):
        """Gets the entire range of the cells array."""
        range_name = ""
        if self.name:
            range_name += self.name + "!"
        range_name += get_range_name_from_cells(self.cells)
        return range_name

    def get_values(self):
        """Returns an array of all values. (Not Cells)"""
        return get_values_from_cells(self.cells)

    def get_updated_values_with_ranges(self):
        """Returns an array of array of updated values (Not Cells) and an array of corresponding ranges."""
        ranges, values = [], []
        tmp_cells = []
        for row in self.cells:
            for cell in row:
                if cell._updated:
                    tmp_cells.append(cell)
                elif tmp_cells:
                    values.append(get_values_from_cells([tmp_cells]))
                    range_name = ""
                    if self.name:
                        range_name += self.name + "!"
                    range_name += get_range_name_from_cells([tmp_cells])
                    ranges.append(range_name)
                    tmp_cells = []
            if tmp_cells:
                values.append(get_values_from_cells([tmp_cells]))
                range_name = ""
                if self.name:
                    range_name += self.name + "!"
                range_name += get_range_name_from_cells([tmp_cells])
                ranges.append(range_name)
                tmp_cells = []
        return ranges, values

    def reset_updated_state(self):
        for row in self.cells:
            for cell in row:
                cell._updated = False


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
            sheets = get_spreadsheet_with_values(spreadsheet_id)
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
            write_ranges(self.id, ranges_name, ranges_values)
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


def from_letter_base(letters):
    """Tranforms a letter base number into an integer."""
    n = 0
    for i, letter in enumerate(letters):
        n += (ord(letter) - 64) * pow(26, len(letters) - (i + 1))
    return n - 1


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


def get_spreadsheet_with_values(spreadsheet_id):
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
    return sheets


def write_range(spreadsheet_id, range_name, values, value_input_option="USER_ENTERED"):
    """Writes values in a range in the real spreadsheet."""
    return write_ranges(spreadsheet_id, [range_name], [values], value_input_option)


def write_ranges(spreadsheet_id, range_name_array, values_array, value_input_option="USER_ENTERED"):
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


def to_base(n, base):
    """Transforms an integer to another defined base."""
    len_base = len(base)
    if n < len_base:
        return base[n]
    else:
        return to_base(n // len_base, base) + base[n % len_base]


def extract_spreadsheet_id(string):
    """Extracts the sprreadsheet id from an url."""
    if "/edit" in string:
        string = string.split("/edit")[0]
    if "/" in string:
        string = string.rstrip("/")
        string = string.split("/")[-1]
        string = string.split("&")[0]
        string = string.split("#")[0]
    return string


def find_corresponding_cell_best_effort(cells, ys, default_y, max_difference_with_base=0, to_string=False):
    default_cell = Cell(-1, -1, "")
    for y in ys:
        for row in cells:
            for cell in row:
                if max_difference_with_base > 0 and cell.x > base_cell.x + max_difference_with_base:
                    continue
                if to_string:
                    cell.change_value_to_string()
                if cell.y == y and cell.value:
                    return cell
                elif cell.y == default_y and default_cell.x == -1:
                    default_cell = cell
    return default_cell


def find_corresponding_qualifier_cell_best_effort(cells, base_cell, max_difference_with_base=0, to_string=False):
    default_cell = Cell(-1, -1, "")
    for y in base_cell.y_merge_range:
        for row in cells:
            for cell in row:
                if cell.x <= base_cell.x:
                    continue
                if max_difference_with_base > 0 and cell.x > base_cell.x + max_difference_with_base:
                    continue
                if to_string:
                    cell.change_value_to_string()
                if cell.y == y and cell.value:
                    return cell
                elif cell.y == base_cell.y and default_cell.x == -1:
                    default_cell = cell
    return default_cell


def find_corresponding_cell_best_effort_from_range(
    spreadsheet, range_name, base_cell, max_difference_with_base=0, to_string=False
):
    range_cells = spreadsheet.get_range(range_name)
    corresponding_cell = find_corresponding_cell_best_effort(
        range_cells, base_cell.y_merge_range, base_cell.y, to_string
    )
    if corresponding_cell.x == -1 and range_name:
        worksheet, range_name = spreadsheet.get_worksheet_and_range(range_name)
        cells = worksheet.cells
        splitted_range = range_name.split(":")[0]
        column = re.split(r"(\d+)", splitted_range)[0]  # TODO: handle all kind of ranges
        column = from_letter_base(column)
        while len(cells) <= base_cell.y:  # TODO: handle different y from base_cell
            cells.append([])
        while len(cells[base_cell.y]) <= column:
            cells[base_cell.y].append(Cell(len(cells[base_cell.y]), base_cell.y, ""))
        corresponding_cell = cells[base_cell.y][column]
    return corresponding_cell


def find_corresponding_cells_best_effort(
    cells, ys, base_cell, max_difference_with_base=0, filled_only=True, to_string=False
):
    default_cells = []
    corresponding_cells = []
    for y in ys:
        for row in cells:
            for cell in row:
                if max_difference_with_base > 0 and cell.x > base_cell.x + max_difference_with_base:
                    continue
                if to_string:
                    cell.change_value_to_string()
                if cell.y == y:
                    if not filled_only or cell.value:
                        corresponding_cells.append(cell)
                if cell.y == base_cell.y:
                    default_cells.append(cell)
    if not corresponding_cells:
        return default_cells
    return corresponding_cells


def find_corresponding_qualifier_cells_best_effort(
    cells, base_cell, max_difference_with_base=0, filled_only=True, to_string=False
):
    default_cells = []
    corresponding_cells = []
    for y in base_cell.y_merge_range:
        for row in cells:
            for cell in row:
                if cell.x <= base_cell.x:
                    continue
                if max_difference_with_base > 0 and cell.x > base_cell.x + max_difference_with_base:
                    continue
                if to_string:
                    cell.change_value_to_string()
                if cell.y == y:
                    if not filled_only or cell.value:
                        corresponding_cells.append(cell)
                if cell.y == base_cell.y:
                    default_cells.append(cell)
    if not corresponding_cells:
        return default_cells
    return corresponding_cells


def find_corresponding_cells_best_effort_from_range(
    spreadsheet, range_name, base_cell, max_difference_with_base=0, filled_only=True, to_string=False
):
    range_cells = spreadsheet.get_range(range_name)
    corresponding_cells = find_corresponding_cells_best_effort(
        range_cells, base_cell.y_merge_range, base_cell, filled_only, to_string
    )
    if not filled_only and not corresponding_cells and range_name:
        worksheet, range_name = spreadsheet.get_worksheet_and_range(range_name)
        cells = worksheet.cells
        splitted_range = range_name.split(":")[0]
        column, _, _ = re.split(r"(\d+)", splitted_range)  # TODO: handle all kind of ranges
        column = from_letter_base(column)
        max_y = base_cell.y_merge_range[-1]
        while len(cells) <= max_y:  # TODO: handle different y from base_cell
            cells.append([])
        while len(cells[max_y]) <= column:
            cells[max_y].append(Cell(len(cells[max_y]), max_y, ""))
        return find_corresponding_cells_best_effort(
            spreadsheet.get_range(range_name), base_cell.y_merge_range, base_cell, filled_only, to_string
        )
    return corresponding_cells


def get_values_from_cells(cells):
    values = []
    for y, row in enumerate(cells):
        values.append([])
        for cell in row:
            values[y].append(cell.value)
    return values


def get_range_name_from_cells(cells):
    if not cells:
        return ""
    min_y = cells[0][0].y
    max_y = cells[-1][0].y
    min_x, max_x = -1, -1
    for row in cells:
        if min_x < 0 or min_x > row[0].x:
            min_x = row[0].x
        if max_x < row[-1].x:
            max_x = row[-1].x
    return to_base(min_x, LETTER_BASE) + str(min_y + 1) + ":" + to_base(max_x, LETTER_BASE) + str(max_y + 1)


def check_range(cell_range):
    """Checks if the range is valid."""
    # TODO
    return True
