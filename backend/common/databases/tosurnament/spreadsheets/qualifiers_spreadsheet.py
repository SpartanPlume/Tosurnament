"""Qualifiers spreadsheet table"""

import math
import datetime

from discord.ext import commands
from encrypted_mysqldb.fields import StrField, IntField

from .base_spreadsheet import BaseSpreadsheet
from common.api.spreadsheet import (
    find_corresponding_cell_best_effort,
    find_corresponding_qualifier_cells_best_effort,
    Cell,
)


class QualifiersSpreadsheet(BaseSpreadsheet):
    """Qualifiers spreadsheet class"""

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._type = "qualifiers"

    range_lobby_id = StrField()
    range_teams = StrField()
    range_referee = StrField()
    range_date = StrField()
    range_time = StrField()
    max_teams_in_row = IntField(8)


class LobbyIdNotFound(commands.CommandError):
    """Thrown when a match id is not found."""

    def __init__(self, lobby_id):
        self.lobby_id = lobby_id


class DuplicateLobbyId(commands.CommandError):
    """Thrown when a match id is found multiple times."""

    def __init__(self, lobby_id):
        self.lobby_id = lobby_id


class DateIsNotString(commands.CommandError):
    """Thrown when the date or time is not a string."""

    def __init__(self, range_type):
        self.type = range_type


class LobbyInfo:
    """Contains all info about a lobby."""

    def __init__(self, lobby_id_cell):
        self.lobby_id = lobby_id_cell
        self.lobby_id.value_type = str
        self.teams = []
        self.referee = Cell(-1, -1, "")
        self.date = Cell(-1, -1, "")
        self.time = Cell(-1, -1, "")

    def set_teams(self, team_cells):
        self.teams = team_cells
        for team in self.teams:
            team.value_type = str

    def set_referee(self, referee_cell):
        self.referee = referee_cell
        self.referee.value_type = str

    def set_date(self, date_cell):
        self.date = date_cell
        if self.date.value_type == int or self.date.value_type == float:
            self.date.value_type = int
            return
        if self.date.value_type != str:
            raise DateIsNotString("date")

    def set_time(self, time_cell):
        self.time = time_cell
        if self.time.value_type == float or self.time.value_type == int:
            self.time.value_type = float
            return
        if self.time.value_type != str:
            raise DateIsNotString("time")

    def get_datetime(self):
        if self.date.value_type == int:
            date = (datetime.datetime(1970, 1, 1) + datetime.timedelta(days=self.date.get() - 25569)).strftime("%d %B")
        else:
            date = self.date.get()
        if self.time.value_type == float:
            time_value = self.time.get()
            time_hour_floor = math.floor(time_value * 24)
            time = str(time_hour_floor) + ":" + str(round((time_value * 24 - time_hour_floor) * 60))
        else:
            time = self.time.get()
        return " ".join(filter(None, [date, time]))

    @staticmethod
    def from_id(qualifiers_spreadsheet, lobby_id, filled_only=True):
        lobby_id_cells = qualifiers_spreadsheet.spreadsheet.get_range(qualifiers_spreadsheet.range_lobby_id)
        corresponding_lobby_id_cells = qualifiers_spreadsheet.spreadsheet.find_cells(lobby_id_cells, lobby_id, False)
        if not corresponding_lobby_id_cells:
            raise LobbyIdNotFound(lobby_id)
        if len(corresponding_lobby_id_cells) > 1:
            raise DuplicateLobbyId(lobby_id)
        lobby_id_cell = corresponding_lobby_id_cells[0]
        return LobbyInfo.from_lobby_id_cell(qualifiers_spreadsheet, lobby_id_cell, filled_only)

    @staticmethod
    def from_lobby_id_cell(qualifiers_spreadsheet, lobby_id_cell, filled_only=True):
        lobby_info = LobbyInfo(lobby_id_cell)
        spreadsheet = qualifiers_spreadsheet.spreadsheet
        lobby_info.set_teams(
            find_corresponding_qualifier_cells_best_effort(
                spreadsheet,
                spreadsheet.get_range(qualifiers_spreadsheet.range_teams),
                lobby_id_cell,
                qualifiers_spreadsheet.max_teams_in_row,
                filled_only,
            )
        )
        lobby_info.set_referee(
            find_corresponding_cell_best_effort(
                spreadsheet.get_range(qualifiers_spreadsheet.range_referee),
                lobby_id_cell,
                qualifiers_spreadsheet.max_teams_in_row,
            )
        )
        lobby_info.set_date(
            find_corresponding_cell_best_effort(
                spreadsheet.get_range(qualifiers_spreadsheet.range_date),
                lobby_id_cell,
                qualifiers_spreadsheet.max_teams_in_row,
            )
        )
        lobby_info.set_time(
            find_corresponding_cell_best_effort(
                spreadsheet.get_range(qualifiers_spreadsheet.range_time),
                lobby_id_cell,
                qualifiers_spreadsheet.max_teams_in_row,
            )
        )
        return lobby_info
