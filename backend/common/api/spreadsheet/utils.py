import re

from . import Cell


def from_letter_base(letters):
    """Tranforms a letter base number into an integer."""
    n = 0
    for i, letter in enumerate(letters):
        n += (ord(letter) - 64) * pow(26, len(letters) - (i + 1))
    return n - 1


def find_corresponding_cell_best_effort(cells, base_cell, max_difference_with_base=0):
    default_cell = Cell(-1, -1, "")
    for y in base_cell.y_merge_range:
        for row in cells:
            for cell in row:
                if cell.x <= base_cell.x:
                    continue
                if max_difference_with_base > 0 and cell.x > base_cell.x + max_difference_with_base:
                    continue
                if cell.y == y and cell:
                    return cell
                elif cell.y == base_cell.y and default_cell.x == -1:
                    default_cell = cell
    return default_cell


def find_corresponding_cell_best_effort_from_range(spreadsheet, range_name, base_cell, max_difference_with_base=0):
    range_cells = spreadsheet.get_range(range_name)
    corresponding_cell = find_corresponding_cell_best_effort(range_cells, base_cell, max_difference_with_base)
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


def find_corresponding_cells_best_effort(cells, ys, base_cell, max_difference_with_base=0, filled_only=True):
    default_cells = []
    corresponding_cells = []
    for y in ys:
        for row in cells:
            for cell in row:
                if cell.x <= base_cell.x:
                    continue
                if max_difference_with_base > 0 and cell.x > base_cell.x + max_difference_with_base:
                    continue
                if cell.y == y:
                    if not filled_only or cell:
                        corresponding_cells.append(cell)
                if cell.y == base_cell.y:
                    default_cells.append(cell)
    if not corresponding_cells:
        return default_cells
    return corresponding_cells


def find_corresponding_qualifier_cells_best_effort(
    spreadsheet, cells, base_cell, max_difference_with_base=0, filled_only=True
):
    default_cells = []
    corresponding_cells = []
    last_y = -1
    all_x = set()
    for row in cells:
        for cell in row:
            last_y = cell.y
            if cell.x <= base_cell.x:
                continue
            if max_difference_with_base > 0 and cell.x > base_cell.x + max_difference_with_base:
                continue
            if cell.y in base_cell.y_merge_range and (not filled_only or cell):
                corresponding_cells.append(cell)
                all_x.add(cell.x)
            if cell.y == base_cell.y:
                default_cells.append(cell)
    if not filled_only:
        y = last_y + 1
        all_x = sorted(all_x)
        worksheet = spreadsheet.get_worksheet()
        while y <= max(base_cell.y_merge_range):
            new_row = []
            for x in all_x:
                new_row.append(Cell(x, y, ""))
            worksheet.cells.append(new_row)
            corresponding_cells = [*corresponding_cells, *new_row]
            y += 1
    if not corresponding_cells:
        return default_cells
    return corresponding_cells


def find_corresponding_cells_best_effort_from_range(
    spreadsheet, range_name, base_cell, max_difference_with_base=0, filled_only=True
):
    range_cells = spreadsheet.get_range(range_name)
    corresponding_cells = find_corresponding_cells_best_effort(
        range_cells, base_cell.y_merge_range, base_cell, max_difference_with_base, filled_only
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
            spreadsheet.get_range(range_name),
            base_cell.y_merge_range,
            base_cell,
            max_difference_with_base,
            filled_only,
        )
    return corresponding_cells


def check_range(cell_range):
    """Checks if the range is valid."""
    # TODO
    return True


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
