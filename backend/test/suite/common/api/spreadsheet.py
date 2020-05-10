"""
All tests concerning the spreadsheet api module.
"""

import unittest
from unittest import mock

from common.api import spreadsheet

MODULE_TO_TEST = "common.api.spreadsheet"
TEST_VALUES = [
    ["A1", "B1", "C1", "D1", "E1"],
    ["A2", "B2", "C2", "D2", "E2"],
    ["A3", "B3", "C3", "D3", "E3"],
    ["A4", "B4", "C4", "D4", "E4"],
    ["A5", "B5", "C5", "D5", "E5"],
]


def cells_to_values(cells):
    values = []
    for y, row in enumerate(cells):
        values.append([])
        for cell in row:
            values[y].append(cell.value)
    return values


def values_to_cells(values):
    cells = []
    for y, row in enumerate(values):
        cells.append([])
        for x, value in enumerate(row):
            cells[y].append(spreadsheet.Cell(x, y, value))
    return cells


class SpreadsheetTestCase(unittest.TestCase):
    @mock.patch(MODULE_TO_TEST + ".write_ranges")
    @mock.patch(MODULE_TO_TEST + ".get_spreadsheet_with_values")
    def test_spreadsheet(self, mock_get, mock_write):
        """Gets a Spreadsheet from a spreadsheet id."""
        mock_get.return_value = [
            {"name": "sheet1", "cells": values_to_cells(TEST_VALUES)},
            {"name": "sheet2", "cells": values_to_cells([["A1"]])},
        ]
        sp = spreadsheet.Spreadsheet.get_from_id("spreadsheet_id")
        mock_get.assert_called_once_with("spreadsheet_id")
        self.assertEqual(len(sp.worksheets), 2)
        self.assertEqual(sp.get_worksheet(0).get_values(), TEST_VALUES)
        self.assertEqual(sp.get_worksheet("sheet2").get_values(), [["A1"]])

        sp.update()
        mock_write.assert_called_once_with("spreadsheet_id", ["sheet1!A1:E5", "sheet2!A1:A1"], [TEST_VALUES, [["A1"]]])

    @mock.patch(MODULE_TO_TEST + ".get_spreadsheet_with_values")
    def test_worksheet_get_cell(self, mock_get):
        """Gets the corresponding Cell. If it does not exist, it creates it."""
        mock_get.return_value = [
            {"name": "sheet1", "cells": values_to_cells(TEST_VALUES)},
            {"name": "sheet2", "cells": values_to_cells([["A1"]])},
        ]
        sp = spreadsheet.Spreadsheet.get_from_id("spreadsheet_id")

        self.assertEqual(sp.get_worksheet(0).get_cell(1, 2).value, "B3")
        self.assertEqual(sp.get_worksheet(1).get_cell(1, 1).value, "")
        self.assertEqual(sp.get_worksheet(1).get_values(), [["A1"], ["", ""]])

    @mock.patch(MODULE_TO_TEST + ".get_spreadsheet_with_values")
    def test_worksheet_get_range(self, mock_get):
        """Gets an array of Cell. If a Cell does not exist in the range, it creates it."""
        mock_get.return_value = [
            {"name": "sheet1", "cells": values_to_cells(TEST_VALUES)},
            {"name": "sheet2", "cells": values_to_cells([["A1"]])},
        ]
        sp = spreadsheet.Spreadsheet.get_from_id("spreadsheet_id")

        range_cells = sp.get_worksheet(0).get_range("B2:D4")
        self.assertEqual(
            cells_to_values(range_cells), [["B2", "C2", "D2"], ["B3", "C3", "D3"], ["B4", "C4", "D4"]],
        )

        range_cells = sp.get_worksheet(0).get_range("B:D")
        self.assertEqual(
            cells_to_values(range_cells),
            [["B1", "C1", "D1"], ["B2", "C2", "D2"], ["B3", "C3", "D3"], ["B4", "C4", "D4"], ["B5", "C5", "D5"]],
        )

        range_cells = sp.get_worksheet(0).get_range("B3:D")
        self.assertEqual(
            cells_to_values(range_cells), [["B3", "C3", "D3"], ["B4", "C4", "D4"], ["B5", "C5", "D5"]],
        )

        range_cells = sp.get_worksheet(0).get_range("B:D3")
        self.assertEqual(
            cells_to_values(range_cells), [["B3", "C3", "D3"], ["B4", "C4", "D4"], ["B5", "C5", "D5"]],
        )

        range_cells = sp.get_worksheet(0).get_range("2:4")
        self.assertEqual(
            cells_to_values(range_cells),
            [["A2", "B2", "C2", "D2", "E2"], ["A3", "B3", "C3", "D3", "E3"], ["A4", "B4", "C4", "D4", "E4"]],
        )

        range_cells = sp.get_worksheet(0).get_range("C2:4")
        self.assertEqual(
            cells_to_values(range_cells), [["C2", "D2", "E2"], ["C3", "D3", "E3"], ["C4", "D4", "E4"]],
        )

        range_cells = sp.get_worksheet(0).get_range("E5:F6")
        self.assertEqual(
            cells_to_values(range_cells), [["E5", ""], ["", ""]],
        )


def suite():
    suite = unittest.TestSuite()
    suite.addTest(SpreadsheetTestCase("test_spreadsheet"))
    suite.addTest(SpreadsheetTestCase("test_worksheet_get_cell"))
    suite.addTest(SpreadsheetTestCase("test_worksheet_get_range"))
    return suite
