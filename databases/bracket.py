"""Bracket class"""

from mysql_wrapper import Base

class Bracket(Base):
    """Bracket class"""
    __tablename__ = 'brackets'

    id = int()
    tournament_id = int()
    name = bytes()
    name_hash = bytes()
    bracket_role_id = bytes()
    players_spreadsheet_id = int()
    schedules_spreadsheet_id = int()
    challonge = bytes()
    to_hash = ["name_hash"]
    ignore = ["tournament_id", "players_spreadsheet_id", "schedules_spreadsheet_id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
