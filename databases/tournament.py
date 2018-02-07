"""Tournament class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary, String
from sqlalchemy import orm
from databases.base import Base
import helpers.crypt

class Tournament(Base):
    """Tournament class"""
    __tablename__ = 'tournaments'

    id = Column(Integer, primary_key=True)
    server_id = Column(Binary)
    acronym = Column(String)
    name = Column(Binary)
    staff_channel_id = Column(Binary)
    admin_role_id = Column(Binary)
    referee_role_id = Column(Binary)
    player_role_id = Column(Binary)
    players_spreadsheet_id = Column(Integer)
    schedules_spreadsheet_id = Column(Integer)
    challonge = Column(Binary)
    to_hash = ["server_id"]
    ignore = ["acronym", "players_spreadsheet_id", "schedules_spreadsheet_id"]

    @orm.reconstructor
    def init(self):
        """Decrypts the object after being queried"""
        self = helpers.crypt.decrypt_obj(self)
