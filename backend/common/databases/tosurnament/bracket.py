"""Bracket table"""

from mysqldb_wrapper import Base, Id
from common.databases.tosurnament.spreadsheets.players_spreadsheet import PlayersSpreadsheet
from common.databases.tosurnament.spreadsheets.schedules_spreadsheet import SchedulesSpreadsheet
from common.databases.tosurnament.spreadsheets.qualifiers_spreadsheet import QualifiersSpreadsheet
from common.databases.tosurnament.spreadsheets.qualifiers_results_spreadsheet import QualifiersResultsSpreadsheet
from common.api import challonge


class Bracket(Base):
    """Bracket class"""

    __tablename__ = "bracket"

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._players_spreadsheet = None
        self._schedules_spreadsheet = None
        self._qualifiers_spreadsheet = None
        self._qualifiers_results_spreadsheet = None
        self._challonge_tournament = None

    id = Id()
    tournament_id = Id()
    name = str()
    role_id = str()
    challonge = str()
    players_spreadsheet_id = Id(-1)
    schedules_spreadsheet_id = Id(-1)
    qualifiers_spreadsheet_id = Id(-1)
    qualifiers_results_spreadsheet_id = Id(-1)
    post_result_channel_id = str()
    current_round = str()
    registration_end_date = str()
    created_at = int()
    updated_at = int()
    # TODO set_all_post_result_channel

    def get_spreadsheet_from_type(self, spreadsheet_type):
        return getattr(self, "_" + spreadsheet_type + "_spreadsheet")

    @classmethod
    def get_spreadsheet_types(cls):
        return {
            "players": PlayersSpreadsheet,
            "schedules": SchedulesSpreadsheet,
            "qualifiers": QualifiersSpreadsheet,
            "qualifiers_results": QualifiersResultsSpreadsheet,
        }

    async def get_players_spreadsheet(self, retry=False, force_sync=False):
        if self._players_spreadsheet:
            await self._players_spreadsheet.get_spreadsheet(retry, force_sync)
        return self._players_spreadsheet

    async def get_schedules_spreadsheet(self, retry=False, force_sync=False):
        if self._schedules_spreadsheet:
            await self._schedules_spreadsheet.get_spreadsheet(retry, force_sync)
        return self._schedules_spreadsheet

    async def get_qualifiers_spreadsheet(self, retry=False, force_sync=False):
        if self._qualifiers_spreadsheet:
            await self._qualifiers_spreadsheet.get_spreadsheet(retry, force_sync)
        return self._qualifiers_spreadsheet

    async def qualifiers_results_spreadsheet(self, retry=False, force_sync=False):
        if self._qualifiers_results_spreadsheet:
            await self._qualifiers_results_spreadsheet.get_spreadsheet(retry, force_sync)
        return self._qualifiers_results_spreadsheet

    # TODO: getter + async too
    @property
    def challonge_tournament(self):
        if not self.challonge:
            return None
        if self._challonge_tournament is None:
            self._challonge_tournament = challonge.get_tournament(self.challonge)
        return self._challonge_tournament
