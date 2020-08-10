"""Bracket table"""

from mysqldb_wrapper import Base, Id
from common.databases.players_spreadsheet import PlayersSpreadsheet
from common.databases.schedules_spreadsheet import SchedulesSpreadsheet
from common.api import challonge


class Bracket(Base):
    """Bracket class"""

    __tablename__ = "bracket"

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._players_spreadsheet = None
        self._schedules_spreadsheet = None
        self._challonge_tournament = None

    id = Id()
    tournament_id = Id()
    name = str()
    role_id = int()
    challonge = str()
    players_spreadsheet_id = Id(-1)
    schedules_spreadsheet_id = Id(-1)
    post_result_channel_id = int()
    current_round = str()
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

    @classmethod
    def get_spreadsheet_types(cls):
        return {"players": PlayersSpreadsheet, "schedules": SchedulesSpreadsheet}

    @property
    def players_spreadsheet(self):
        if self._players_spreadsheet is None:
            self._players_spreadsheet = (
                self._session.query(PlayersSpreadsheet)
                .where(PlayersSpreadsheet.id == self.players_spreadsheet_id)
                .first()
            )
        return self._players_spreadsheet

    @property
    def schedules_spreadsheet(self):
        if self._schedules_spreadsheet is None:
            self._schedules_spreadsheet = (
                self._session.query(SchedulesSpreadsheet)
                .where(SchedulesSpreadsheet.id == self.schedules_spreadsheet_id)
                .first()
            )
        return self._schedules_spreadsheet

    @property
    def challonge_tournament(self):
        if self._challonge_tournament is None:
            self._challonge_tournament = challonge.get_tournament(self.challonge)
        return self._challonge_tournament
