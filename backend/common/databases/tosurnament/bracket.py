"""Bracket table"""

from encrypted_mysqldb.table import Table
from encrypted_mysqldb.fields import IdField, StrField, IntField, DatetimeField
from common.databases.tosurnament.spreadsheets.players_spreadsheet import PlayersSpreadsheet
from common.databases.tosurnament.spreadsheets.schedules_spreadsheet import SchedulesSpreadsheet
from common.databases.tosurnament.spreadsheets.qualifiers_spreadsheet import QualifiersSpreadsheet
from common.databases.tosurnament.spreadsheets.qualifiers_results_spreadsheet import QualifiersResultsSpreadsheet
from common.api import challonge


class Bracket(Table):
    """Bracket class"""

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._players_spreadsheet = None
        self._schedules_spreadsheet = None
        self._qualifiers_spreadsheet = None
        self._qualifiers_results_spreadsheet = None
        self._challonge_tournament = None

    tournament_id = IdField()
    name = StrField()
    role_id = StrField()
    challonge = StrField()
    players_spreadsheet_id = IdField(-1)
    schedules_spreadsheet_id = IdField(-1)
    qualifiers_spreadsheet_id = IdField(-1)
    qualifiers_results_spreadsheet_id = IdField(-1)
    post_result_channel_id = StrField()
    current_round = StrField()
    minimum_rank = IntField()
    maximum_rank = IntField()
    registration_end_date = StrField()
    created_at = DatetimeField()
    updated_at = DatetimeField()
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
