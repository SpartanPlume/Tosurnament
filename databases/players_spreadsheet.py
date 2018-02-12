"""Players spreadsheet class"""

import re
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary
from sqlalchemy import orm
from databases.base import Base
import helpers.crypt
import api.spreadsheet

class PlayersSpreadsheet(Base):
    """Players spreadsheet class"""
    __tablename__ = 'players_spreadsheet'

    id = Column(Integer, primary_key=True)
    spreadsheet_id = Column(Binary)
    range_team_name = Column(Binary)
    range_team = Column(Binary)
    incr_column = Column(Binary)
    incr_row = Column(Binary)
    n_team = Column(Integer)
    to_hash = []
    ignore = ["n_team"]

    @orm.reconstructor
    def init(self):
        """Decrypts the object after being queried"""
        self = helpers.crypt.decrypt_obj(self)

    def get_ranges(self):
        """Gets all ranges to use to get all datas"""
        if "!" in self.range_team_name:
            range_team_name = self.range_team_name.split("!")[1]
        else:
            range_team_name = self.range_team_name            
        if "!" in self.range_team:
            sheet_name = self.range_team.split("!")[0]
            range_team = self.range_team.split("!")[1]
        else:
            sheet_name = ""
            range_team = self.range_team
        range_names = []
        cells_team_name = range_team_name.split(":")
        cells_team = range_team.split(":")
        regex = re.compile(re.escape("n"), re.IGNORECASE)
        for i in range(0, self.n_team):
            incr_column = int(eval(regex.sub(str(i), self.incr_column)))
            incr_row = int(eval(regex.sub(str(i), self.incr_row)))
            if range_team_name.lower() != "none":
                range_names.append(self.get_incremented_range(cells_team_name, sheet_name, incr_column, incr_row))
            range_names.append(self.get_incremented_range(cells_team, sheet_name, incr_column, incr_row))
        return range_names

    def get_incremented_range(self, cells, sheet_name, incr_column, incr_row):
        """Returns a range from the incremented list of cells"""
        incremented_cells = self.increment_cells(cells, incr_column, incr_row)
        range_name = incremented_cells[0]
        if len(incremented_cells) > 1:
            range_name += ":" + incremented_cells[1]
        if sheet_name:
            range_name = sheet_name + "!" + range_name
        return range_name

    def increment_cells(self, cells, incr_column, incr_row):
        """Returns the incremented cells"""
        incremented_cells = []
        for cell in cells:
            x, y = api.spreadsheet.from_cell(cell)
            x += incr_column
            y += incr_row
            incremented_cells.append(api.spreadsheet.to_cell((x, y)))
        return incremented_cells
