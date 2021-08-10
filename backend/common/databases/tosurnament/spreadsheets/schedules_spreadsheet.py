"""Schedules spreadsheet table"""

from discord.ext import commands
from .base_spreadsheet import BaseSpreadsheet
from common.api.spreadsheet import (
    Cell,
    find_corresponding_cell_best_effort_from_range,
    find_corresponding_cells_best_effort_from_range,
)


class SchedulesSpreadsheet(BaseSpreadsheet):
    """Schedules spreadsheet class"""

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._type = "schedules"

    __tablename__ = "schedules_spreadsheet"

    range_match_id = str()
    range_team1 = str()
    range_score_team1 = str()
    range_score_team2 = str()
    range_team2 = str()
    range_date = str()
    range_time = str()
    range_referee = str()
    range_streamer = str()
    range_commentator = str()
    range_mp_links = str()
    date_format = str()
    use_range = bool(False)
    max_referee = int(1)
    max_streamer = int(1)
    max_commentator = int(2)


class MatchIdNotFound(commands.CommandError):
    """Thrown when a match id is not found."""

    def __init__(self, match_id):
        self.match_id = match_id


class DuplicateMatchId(commands.CommandError):
    """Thrown when a match id is found multiple times."""

    def __init__(self, match_id):
        self.match_id = match_id


class DateIsNotString(commands.CommandError):
    """Thrown when the date or time is not a string."""

    def __init__(self, range_type):
        self.type = range_type


class MatchInfo:
    """Contains all info about a match."""

    def __init__(self, match_id_cell):
        self.match_id = match_id_cell
        self.match_id.value_type = str
        self.team1 = Cell(-1, -1, "")
        self.team2 = Cell(-1, -1, "")
        self.score_team1 = Cell(-1, -1, "")
        self.score_team2 = Cell(-1, -1, "")
        self.date = Cell(-1, -1, "")
        self.time = Cell(-1, -1, "")
        self.referees = []
        self.streamers = []
        self.commentators = []
        self.mp_links = []

    def set_team1(self, team1_cell):
        self.team1 = team1_cell
        self.team1.value_type = str

    def set_team2(self, team2_cell):
        self.team2 = team2_cell
        self.team2.value_type = str

    def set_score_team1(self, score_team1_cell):
        self.score_team1 = score_team1_cell
        self.score_team1.value_type = str

    def set_score_team2(self, score_team2_cell):
        self.score_team2 = score_team2_cell
        self.score_team2.value_type = str

    def set_date(self, date_cell):
        self.date = date_cell
        if self.date.value_type != str:
            raise DateIsNotString("date")

    def set_time(self, time_cell):
        self.time = time_cell
        if self.time.value_type != str:
            raise DateIsNotString("time")

    def set_referees(self, referee_cells):
        self.referees = referee_cells
        for referee_cell in self.referees:
            referee_cell.value_type = str

    def set_streamers(self, streamer_cells):
        self.streamers = streamer_cells
        for streamer_cell in self.streamers:
            streamer_cell.value_type = str

    def set_commentators(self, commentator_cells):
        self.commentators = commentator_cells
        for commentator_cell in self.commentators:
            commentator_cell.value_type = str

    def set_mp_links(self, mp_link_cells):
        self.mp_links = mp_link_cells
        for mp_link_cell in self.mp_links:
            mp_link_cell.value_type = str

    def get_datetime(self):
        return " ".join(filter(None, [self.date.get(), self.time.get()]))

    @staticmethod
    def from_id(schedules_spreadsheet, match_id, filled_only=True):
        match_id_cells = schedules_spreadsheet.spreadsheet.get_range(schedules_spreadsheet.range_match_id)
        corresponding_match_id_cells = schedules_spreadsheet.spreadsheet.find_cells(match_id_cells, match_id, False)
        if not corresponding_match_id_cells:
            raise MatchIdNotFound(match_id)
        if len(corresponding_match_id_cells) > 1:
            raise DuplicateMatchId(match_id)
        match_id_cell = corresponding_match_id_cells[0]
        return MatchInfo.from_match_id_cell(schedules_spreadsheet, match_id_cell, filled_only)

    @staticmethod
    def from_match_id_cell(schedules_spreadsheet, match_id_cell, filled_only=True):
        match_info = MatchInfo(match_id_cell)
        spreadsheet = schedules_spreadsheet.spreadsheet
        match_info.set_team1(
            find_corresponding_cell_best_effort_from_range(
                spreadsheet,
                schedules_spreadsheet.range_team1,
                match_id_cell,
            )
        )
        match_info.set_team2(
            find_corresponding_cell_best_effort_from_range(
                spreadsheet,
                schedules_spreadsheet.range_team2,
                match_id_cell,
            )
        )
        match_info.set_score_team1(
            find_corresponding_cell_best_effort_from_range(
                spreadsheet,
                schedules_spreadsheet.range_score_team1,
                match_id_cell,
            )
        )
        match_info.set_score_team2(
            find_corresponding_cell_best_effort_from_range(
                spreadsheet,
                schedules_spreadsheet.range_score_team2,
                match_id_cell,
            )
        )
        match_info.set_date(
            find_corresponding_cell_best_effort_from_range(
                spreadsheet,
                schedules_spreadsheet.range_date,
                match_id_cell,
            )
        )
        match_info.set_time(
            find_corresponding_cell_best_effort_from_range(
                spreadsheet,
                schedules_spreadsheet.range_time,
                match_id_cell,
            )
        )
        if schedules_spreadsheet.use_range:
            match_info.set_referees(
                find_corresponding_cells_best_effort_from_range(
                    spreadsheet,
                    schedules_spreadsheet.range_referee,
                    match_id_cell,
                    filled_only=filled_only,
                )
            )
            match_info.set_streamers(
                find_corresponding_cells_best_effort_from_range(
                    spreadsheet,
                    schedules_spreadsheet.range_streamer,
                    match_id_cell,
                    filled_only=filled_only,
                )
            )
            match_info.set_commentators(
                find_corresponding_cells_best_effort_from_range(
                    spreadsheet,
                    schedules_spreadsheet.range_commentator,
                    match_id_cell,
                    filled_only=filled_only,
                )
            )
            match_info.set_mp_links(
                find_corresponding_cells_best_effort_from_range(
                    spreadsheet,
                    schedules_spreadsheet.range_mp_links,
                    match_id_cell,
                    filled_only=filled_only,
                )
            )
        else:
            match_info.set_referees(
                [
                    find_corresponding_cell_best_effort_from_range(
                        spreadsheet,
                        schedules_spreadsheet.range_referee,
                        match_id_cell,
                    )
                ]
            )
            match_info.set_streamers(
                [
                    find_corresponding_cell_best_effort_from_range(
                        spreadsheet,
                        schedules_spreadsheet.range_streamer,
                        match_id_cell,
                    )
                ]
            )
            match_info.set_commentators(
                [
                    find_corresponding_cell_best_effort_from_range(
                        spreadsheet,
                        schedules_spreadsheet.range_commentator,
                        match_id_cell,
                    )
                ]
            )
            match_info.set_mp_links(
                [
                    find_corresponding_cell_best_effort_from_range(
                        spreadsheet,
                        schedules_spreadsheet.range_mp_links,
                        match_id_cell,
                    )
                ]
            )
        return match_info
