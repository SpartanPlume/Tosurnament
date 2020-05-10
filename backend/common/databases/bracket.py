"""Bracket table"""

from mysqldb_wrapper import Base, Id


class Bracket(Base):
    """Bracket class"""

    __tablename__ = "bracket"

    id = Id()
    tournament_id = Id()
    name = str()
    role_id = int()
    challonge = str()
    players_spreadsheet_id = Id(-1)
    schedules_spreadsheet_id = Id(-1)
    post_result_channel_id = int()
    # TODO set_all_post_result_channel
