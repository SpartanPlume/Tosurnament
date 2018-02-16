"""Bracket class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary, String, Boolean
from sqlalchemy import orm
from databases.base import Base
import helpers.crypt

class Bracket(Base):
    """Bracket class"""
    __tablename__ = 'brackets'

    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer)
    name = Column(Binary)
    name_hash = Column(Binary)
    bracket_role_id = Column(Binary)
    players_spreadsheet_id = Column(Integer)
    schedules_spreadsheet_id = Column(Integer)
    challonge = Column(Binary)
    to_hash = ["name_hash"]
    ignore = ["tournament_id", "players_spreadsheet_id", "schedules_spreadsheet_id"]

    @orm.reconstructor
    def init(self):
        """Decrypts the object after being queried"""
        self = helpers.crypt.decrypt_obj(self)
