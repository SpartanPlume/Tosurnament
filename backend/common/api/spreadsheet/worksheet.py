import re

from .cell import Cell
from . import utils

LETTER_BASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


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
            x_range.append(utils.from_letter_base(range_name_splitted[0]))
        else:
            x_min = utils.from_letter_base(range_name_splitted[0])
            x_max = utils.from_letter_base(range_name_splitted[1])
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
            x_range.append(utils.from_letter_base(column))
            y_range.append(int(row) - 1)
        else:
            column, row, _ = separate_regex.split(range_name_splitted[0])
            x_min = utils.from_letter_base(column)
            y_min = int(row) - 1
            column, row, _ = separate_regex.split(range_name_splitted[1])
            x_max = utils.from_letter_base(column)
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
        x_min = utils.from_letter_base(column)
        x_max = utils.from_letter_base(column2)
        y_min = int(row) - 1
        y_max = len(self.cells)
        return range(x_min, x_max + 1), range(y_min, y_max)

    def _from_partial_row_range(self, range_name):
        """Gets the range from a range name when the range is row only."""
        range_part1, row2 = range_name.split(":")
        separate_regex = re.compile(r"(\d+)")
        column, row, _ = separate_regex.split(range_part1)
        x_min = utils.from_letter_base(column)
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
        for range_name in re.split(r",| |, |;|; |\|", range_names):
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
                if cell:
                    cells_with_value.append(cell)
        return cells_with_value

    def change_value_in_range(self, range_name, previous_value, new_value, case_sensitive=False):
        """Changes the value of all cells that are equal to previous_value to new_value in a range."""
        correponding_cells = self.find_cells(range_name, previous_value, case_sensitive)
        value_changed = False
        for cell in correponding_cells:
            cell.set(new_value)
            value_changed = True
        return value_changed

    def find_cells(self, range_name, value_to_find, case_sensitive=False):
        """Returns an array of Cell matching the value_to_find."""
        value_to_find = str(value_to_find)
        if not case_sensitive:
            value_to_find = value_to_find.casefold()
        if isinstance(range_name, str):
            range_cells = self.get_range(range_name)
        elif isinstance(range_name, list):
            range_cells = range_name
        else:
            return []
        matching_cells = []
        for row in range_cells:
            for cell in row:
                cell_value = cell if case_sensitive else cell.casefold()
                if cell_value == value_to_find:
                    matching_cells.append(cell)
        return matching_cells

    def get_range_name(self):
        """Gets the entire range of the cells array."""
        range_name = ""
        if self.name:
            range_name += self.name + "!"
        range_name += _get_range_name_from_cells(self.cells)
        return range_name

    def get_values(self):
        """Returns an array of all values. (Not Cells)"""
        return _get_values_from_cells(self.cells)

    def get_updated_values_with_ranges(self):
        """Returns an array of array of updated values (Not Cells) and an array of corresponding ranges."""
        ranges, values = [], []
        tmp_cells = []
        for row in self.cells:
            for cell in row:
                if cell._updated:
                    tmp_cells.append(cell)
                elif tmp_cells:
                    values.append(_get_values_from_cells([tmp_cells]))
                    range_name = ""
                    if self.name:
                        range_name += self.name + "!"
                    range_name += _get_range_name_from_cells([tmp_cells])
                    ranges.append(range_name)
                    tmp_cells = []
            if tmp_cells:
                values.append(_get_values_from_cells([tmp_cells]))
                range_name = ""
                if self.name:
                    range_name += self.name + "!"
                range_name += _get_range_name_from_cells([tmp_cells])
                ranges.append(range_name)
                tmp_cells = []
        return ranges, values

    def reset_updated_state(self):
        for row in self.cells:
            for cell in row:
                cell._updated = False


def _get_values_from_cells(cells):
    values = []
    for y, row in enumerate(cells):
        values.append([])
        for cell in row:
            values[y].append(cell.get())
    return values


def _get_range_name_from_cells(cells):
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
    return _to_base(min_x, LETTER_BASE) + str(min_y + 1) + ":" + _to_base(max_x, LETTER_BASE) + str(max_y + 1)


def _to_base(n, base):
    """Transforms an integer to another defined base."""
    len_base = len(base)
    if n < len_base:
        return base[n]
    else:
        return _to_base(n // len_base, base) + base[n % len_base]
