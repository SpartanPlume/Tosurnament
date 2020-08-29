"""
All tests concerning the spreadsheet api module.
"""

import pytest
from unittest import mock
from hypothesis import strategies, given

import socket
import googleapiclient
from common.api import spreadsheet

MODULE_TO_TEST = "common.api.spreadsheet"

row_strategy = strategies.lists(strategies.one_of(strategies.text(), strategies.integers(), strategies.booleans()))
table_strategy = strategies.lists(row_strategy)


def values_to_cells(values):
    cells = []
    for y, row in enumerate(values):
        cells.append([])
        for x, value in enumerate(row):
            cells[y].append(spreadsheet.Cell(x, y, value))
    return cells


@mock.patch(MODULE_TO_TEST + ".get_spreadsheet_with_values")
def test_spreadsheet_retrieve_spreadsheet(mock_spreadsheet_get):
    """Gets a Spreadsheet from a spreadsheet id."""
    mock_spreadsheet_get.return_value = [
        {"name": "sheet1", "cells": values_to_cells([["A1"]])},
        {"name": "sheet2", "cells": values_to_cells([["A1", "B1"]])},
    ]
    sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")
    mock_spreadsheet_get.assert_called_once_with("spreadsheet_id")
    assert len(sp.worksheets) == 2
    assert sp.get_worksheet(0).get_values() == [["A1"]]
    assert sp.get_worksheet("sheet2").get_values() == [["A1", "B1"]]
    with pytest.raises(spreadsheet.InvalidWorksheet):
        sp.get_worksheet("non-existing sheet")

    mock_spreadsheet_get.side_effect = googleapiclient.errors.HttpError({"status": 404}, bytes())
    with pytest.raises(spreadsheet.HttpError) as error:
        sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")
    assert error.value.code == 404
    assert error.value.operation == "read"

    mock_spreadsheet_get.side_effect = googleapiclient.errors.HttpError({}, bytes())
    with pytest.raises(spreadsheet.HttpError) as error:
        sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")
    assert error.value.code == 500

    mock_spreadsheet_get.side_effect = ConnectionResetError()
    with pytest.raises(spreadsheet.HttpError) as error:
        sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")
    assert error.value.code == 499

    mock_spreadsheet_get.side_effect = socket.timeout()
    with pytest.raises(spreadsheet.HttpError) as error:
        sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")
    assert error.value.code == 408


@given(table1=table_strategy, table2=table_strategy)
@mock.patch(MODULE_TO_TEST + ".get_spreadsheet_with_values")
def test_spreadsheet_retrieve_spreadsheet_with_given(mock_spreadsheet_get, table1, table2):
    """Gets a Spreadsheet from a spreadsheet id."""
    mock_spreadsheet_get.return_value = [
        {"name": "sheet1", "cells": values_to_cells(table1)},
        {"name": "sheet2", "cells": values_to_cells(table2)},
    ]
    sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")
    mock_spreadsheet_get.assert_called_once_with("spreadsheet_id")
    assert len(sp.worksheets) == 2
    assert sp.get_worksheet(0).get_values() == table1
    assert sp.get_worksheet("sheet2").get_values() == table2


@mock.patch(MODULE_TO_TEST + ".get_spreadsheet_with_values")
def test_spreadsheet_get_range(mock_spreadsheet_get):
    """Gets a Spreadsheet from a spreadsheet id."""
    TEST_VALUES = [
        ["A1", "B1", "C1", "D1", "E1"],
        ["A2", "B2", "C2", "D2", "E2"],
        ["A3", "B3", "C3", "D3", "E3"],
        ["A4", "B4", "C4", "D4", "E4"],
        ["A5", "B5", "C5", "D5", "E5"],
    ]
    mock_spreadsheet_get.return_value = [
        {"name": "sheet1", "cells": values_to_cells(TEST_VALUES)},
        {"name": "sheet2", "cells": values_to_cells([["data sheet2"]])},
        {"name": "!!!sheet3!!!", "cells": values_to_cells([["data sheet3"]])},
    ]
    sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")

    range_cells = sp.get_range("")
    assert range_cells == []

    range_cells = sp.get_range("B2:D4")
    assert spreadsheet.get_values_from_cells(range_cells) == [
        ["B2", "C2", "D2"],
        ["B3", "C3", "D3"],
        ["B4", "C4", "D4"],
    ]

    range_cells = sp.get_range("B:D")
    assert spreadsheet.get_values_from_cells(range_cells) == [
        ["B1", "C1", "D1"],
        ["B2", "C2", "D2"],
        ["B3", "C3", "D3"],
        ["B4", "C4", "D4"],
        ["B5", "C5", "D5"],
    ]

    range_cells = sp.get_range("B3:D")
    assert spreadsheet.get_values_from_cells(range_cells) == [
        ["B3", "C3", "D3"],
        ["B4", "C4", "D4"],
        ["B5", "C5", "D5"],
    ]

    range_cells = sp.get_range("B:D3")
    assert spreadsheet.get_values_from_cells(range_cells) == [
        ["B3", "C3", "D3"],
        ["B4", "C4", "D4"],
        ["B5", "C5", "D5"],
    ]

    range_cells = sp.get_range("2:4")
    assert spreadsheet.get_values_from_cells(range_cells) == [
        ["A2", "B2", "C2", "D2", "E2"],
        ["A3", "B3", "C3", "D3", "E3"],
        ["A4", "B4", "C4", "D4", "E4"],
    ]

    range_cells = sp.get_range("C2:4")
    assert spreadsheet.get_values_from_cells(range_cells) == [
        ["C2", "D2", "E2"],
        ["C3", "D3", "E3"],
        ["C4", "D4", "E4"],
    ]

    range_cells = sp.get_range("A")
    assert spreadsheet.get_values_from_cells(range_cells) == [["A1"], ["A2"], ["A3"], ["A4"], ["A5"]]

    range_cells = sp.get_range("1")
    assert spreadsheet.get_values_from_cells(range_cells) == [["A1", "B1", "C1", "D1", "E1"]]

    range_cells = sp.get_range("A1:A,C3:C,E1:E3")
    assert spreadsheet.get_values_from_cells(range_cells) == [
        ["A1", "C3", "E1"],
        ["A2", "C4", "E2"],
        ["A3", "C5", "E3"],
        ["A4"],
        ["A5"],
    ]

    range_cells = sp.get_range(",A1:A,C3:C,,E1:E3,")
    assert spreadsheet.get_values_from_cells(range_cells) == [
        ["A1", "C3", "E1"],
        ["A2", "C4", "E2"],
        ["A3", "C5", "E3"],
        ["A4"],
        ["A5"],
    ]

    range_cells = sp.get_range("E5:F6")
    assert spreadsheet.get_values_from_cells(range_cells) == [["E5", ""], ["", ""]]

    range_cells = sp.get_range("E5:7")
    assert spreadsheet.get_values_from_cells(range_cells) == [["E5", ""], ["", ""], ["", ""]]

    range_cells = sp.get_range("'sheet2'!A1")
    assert spreadsheet.get_values_from_cells(range_cells) == [["data sheet2"]]

    range_cells = sp.get_range("!!!sheet3!!!!A1")
    assert spreadsheet.get_values_from_cells(range_cells) == [["data sheet3"]]


@mock.patch(MODULE_TO_TEST + ".get_spreadsheet_with_values")
def test_spreadsheet_get_cells_with_value_in_range(mock_spreadsheet_get):
    """Gets a Spreadsheet from a spreadsheet id."""
    TEST_VALUES = [
        ["A1", "B1", "C1", "", "E1"],
        ["A2", "", "C2", "D2", "E2"],
        ["", "B3", "C3", "D3", ""],
        ["A4", "", "", "D4", "E4"],
        ["", "B5", "C5", "D5", "E5"],
    ]
    mock_spreadsheet_get.return_value = [
        {"name": "sheet1", "cells": values_to_cells(TEST_VALUES)},
    ]
    sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")
    test_values_as_row = [value for test_values_row in TEST_VALUES for value in test_values_row if value]

    range_cells = sp.get_cells_with_value_in_range("A:E")
    range_values = [cell.value for cell in range_cells]
    assert range_values == test_values_as_row


@mock.patch(MODULE_TO_TEST + ".get_spreadsheet_with_values")
def test_spreadsheet_find_cells(mock_spreadsheet_get):
    """Gets a Spreadsheet from a spreadsheet id."""
    TEST_VALUES = [
        ["A", "B", "C", "D1", "E1"],
        ["A", "B", "C", "D:E", "D:E"],
        ["A", "B", "C", "D:e", "E3"],
        ["A", "B", "C", "d:E", "D:E"],
        ["A", "B", "C", "d:E", "E5"],
    ]
    mock_spreadsheet_get.return_value = [
        {"name": "sheet1", "cells": values_to_cells(TEST_VALUES)},
    ]
    sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")
    test_values_as_row = [value for test_values_row in TEST_VALUES for value in test_values_row if value == "D:E"]
    test_values_as_row_insensitive = [
        value for test_values_row in TEST_VALUES for value in test_values_row if value.lower() == "d:e"
    ]

    range_cells = sp.find_cells("A:E", "D:E")
    range_values = [cell.value for cell in range_cells]
    assert range_values == test_values_as_row_insensitive

    range_cells = sp.find_cells("A:E", "D:E", True)
    range_values = [cell.value for cell in range_cells]
    assert range_values == test_values_as_row

    range_cells = sp.find_cells(sp.get_range("A:E"), "D:E")
    range_values = [cell.value for cell in range_cells]
    assert range_values == test_values_as_row_insensitive

    assert sp.find_cells(None, "D:E") == []


@mock.patch(MODULE_TO_TEST + ".get_spreadsheet_with_values")
def test_spreadsheet_change_value_in_range(mock_spreadsheet_get):
    """Gets a Spreadsheet from a spreadsheet id."""
    TEST_VALUES = [
        ["A", "B", "C", "D1", "E1"],
        ["A", "B", "C", "D:E", "D:E"],
        ["A", "B", "C", "D:E", "E3"],
        ["A", "B", "C", "D:E", "D:E"],
        ["A", "B", "C", "D:E", "E5"],
    ]
    mock_spreadsheet_get.return_value = [
        {"name": "sheet1", "cells": values_to_cells(TEST_VALUES)},
    ]
    sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")

    assert not sp.change_value_in_range("A:E", "A1", "First cell")
    assert sp.get_worksheet(0).get_values() == TEST_VALUES

    assert sp.change_value_in_range("A:E", "A", "Column A")
    range_cells = sp.get_cells_with_value_in_range("A1:A")
    range_values = [cell.value for cell in range_cells]
    assert range_values == ["Column A"] * 5


@mock.patch(MODULE_TO_TEST + ".get_spreadsheet_with_values")
def test_worksheet_get_cell(mock_spreadsheet_get):
    """Gets the corresponding Cell. If it does not exist, it creates it."""
    TEST_VALUES = [
        ["A1", "B1", "C1", "D1", "E1"],
        ["A2", "B2", "C2", "D2", "E2"],
        ["A3", "B3", "C3", "D3", "E3"],
        ["A4", "B4", "C4", "D4", "E4"],
        ["A5", "B5", "C5", "D5", "E5"],
    ]
    mock_spreadsheet_get.return_value = [
        {"name": "sheet1", "cells": values_to_cells(TEST_VALUES)},
        {"name": "sheet2", "cells": values_to_cells([["A1"]])},
    ]
    sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")

    assert sp.get_worksheet(0).get_cell(1, 2).value == "B3"
    assert sp.get_worksheet(1).get_cell(1, 1).value == ""
    assert sp.get_worksheet(1).get_values() == [["A1"], ["", ""]]


@mock.patch(MODULE_TO_TEST + ".write_ranges")
@mock.patch(MODULE_TO_TEST + ".get_spreadsheet_with_values")
def test_spreadsheet_update(mock_spreadsheet_get, mock_spreadsheet_write):
    """Gets a Spreadsheet from a spreadsheet id."""
    TEST_VALUES = [
        ["A1", "B1", "C1", "D1", "E1"],
        ["A2", "B2", "C2", "D2", "E2"],
        ["A3", "B3", "C3", "D3", "E3"],
        ["A4", "B4", "C4", "D4", "E4"],
        ["A5", "B5", "C5", "D5", "E5"],
    ]
    mock_spreadsheet_get.return_value = [
        {"name": "sheet1", "cells": values_to_cells(TEST_VALUES)},
        {"name": "sheet2", "cells": values_to_cells([["data sheet2"]])},
        {"name": "!!!sheet3!!!", "cells": values_to_cells([["data sheet3"]])},
    ]
    sp = spreadsheet.Spreadsheet.retrieve_spreadsheet("spreadsheet_id")

    new_cell_value = "First cell"
    sp.get_worksheet().get_range("A1")[0][0].value = new_cell_value
    sp.update()
    mock_spreadsheet_write.assert_called_once_with("spreadsheet_id", ["sheet1!A1:A1"], [[[new_cell_value]]])

    new_cell_value = "Second sheet"
    sp.get_worksheet("sheet2").get_range("A1")[0][0].value = new_cell_value
    sp.update()
    mock_spreadsheet_write.assert_called_with("spreadsheet_id", ["sheet2!A1:A1"], [[[new_cell_value]]])
