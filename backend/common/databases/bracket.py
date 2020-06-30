"""Bracket table"""

from mysqldb_wrapper import Base, Id
from common.databases.players_spreadsheet import PlayersSpreadsheet
from common.databases.schedules_spreadsheet import SchedulesSpreadsheet


class Bracket(Base):
    """Bracket class"""

    __tablename__ = "bracket"

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._players_spreadsheet = None
        self._schedules_spreadsheet = None

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
