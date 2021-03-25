"""Bracket table"""

from mysqldb_wrapper import Base, Id
from common.databases.players_spreadsheet import PlayersSpreadsheet
from common.databases.schedules_spreadsheet import SchedulesSpreadsheet
from common.databases.qualifiers_spreadsheet import QualifiersSpreadsheet
from common.databases.qualifiers_results_spreadsheet import QualifiersResultsSpreadsheet
from common.api import challonge
from common.api import spreadsheet


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
    role_id = int()
    challonge = str()
    players_spreadsheet_id = Id(-1)
    schedules_spreadsheet_id = Id(-1)
    qualifiers_spreadsheet_id = Id(-1)
    qualifiers_results_spreadsheet_id = Id(-1)
    post_result_channel_id = int()
    current_round = str()
    registration_end_date = str()
    # TODO set_all_post_result_channel

    def get_spreadsheet_from_type(self, spreadsheet_type):
        return getattr(self, spreadsheet_type + "_spreadsheet")

    def create_spreadsheet_from_type(self, bot, spreadsheet_type):
        spreadsheet_types = Bracket.get_spreadsheet_types()
        if spreadsheet_type in spreadsheet_types:
            spreadsheet = spreadsheet_types[spreadsheet_type]()
            bot.session.add(spreadsheet)
            setattr(self, spreadsheet_type + "_spreadsheet_id", spreadsheet.id)
            bot.session.update(self)
            return spreadsheet
        return None

    def update_spreadsheet_of_type(self, bot, spreadsheet_type, spreadsheet_id, sheet_name):
        any_spreadsheet = self.get_spreadsheet_from_type(spreadsheet_type)
        if not any_spreadsheet:
            any_spreadsheet = self.create_spreadsheet_from_type(bot, spreadsheet_type)
        spreadsheet_id = spreadsheet.extract_spreadsheet_id(spreadsheet_id)
        any_spreadsheet.spreadsheet_id = spreadsheet_id
        if sheet_name:
            any_spreadsheet.sheet_name = sheet_name
        bot.session.update(any_spreadsheet)
        return spreadsheet_id

    @classmethod
    def get_spreadsheet_types(cls):
        return {
            "players": PlayersSpreadsheet,
            "schedules": SchedulesSpreadsheet,
            "qualifiers": QualifiersSpreadsheet,
            "qualifiers_results": QualifiersResultsSpreadsheet,
        }

    async def get_players_spreadsheet(self, retry=False, force_sync=False):
        if self._players_spreadsheet is None:
            self._players_spreadsheet = (
                self._session.query(PlayersSpreadsheet)
                .where(PlayersSpreadsheet.id == self.players_spreadsheet_id)
                .first()
            )
            if self._players_spreadsheet:
                await self._players_spreadsheet.get_spreadsheet(retry, force_sync)
        return self._players_spreadsheet

    async def get_schedules_spreadsheet(self, retry=False, force_sync=False):
        if self._schedules_spreadsheet is None:
            self._schedules_spreadsheet = (
                self._session.query(SchedulesSpreadsheet)
                .where(SchedulesSpreadsheet.id == self.schedules_spreadsheet_id)
                .first()
            )
            if self._schedules_spreadsheet:
                await self._schedules_spreadsheet.get_spreadsheet(retry, force_sync)
        return self._schedules_spreadsheet

    async def get_qualifiers_spreadsheet(self, retry=False, force_sync=False):
        if self._qualifiers_spreadsheet is None:
            self._qualifiers_spreadsheet = (
                self._session.query(QualifiersSpreadsheet)
                .where(QualifiersSpreadsheet.id == self.qualifiers_spreadsheet_id)
                .first()
            )
            if self._qualifiers_spreadsheet:
                await self._qualifiers_spreadsheet.get_spreadsheet(retry, force_sync)
        return self._qualifiers_spreadsheet

    async def qualifiers_results_spreadsheet(self, retry=False, force_sync=False):
        if self._qualifiers_results_spreadsheet is None:
            self._qualifiers_results_spreadsheet = (
                self._session.query(QualifiersResultsSpreadsheet)
                .where(QualifiersResultsSpreadsheet.id == self.qualifiers_results_spreadsheet_id)
                .first()
            )
            if self._qualifiers_results_spreadsheet:
                await self._qualifiers_results_spreadsheet.get_spreadsheet(retry, force_sync)
        return self._qualifiers_results_spreadsheet

    @property
    def challonge_tournament(self):
        if self._challonge_tournament is None:
            self._challonge_tournament = challonge.get_tournament(self.challonge)
        return self._challonge_tournament
