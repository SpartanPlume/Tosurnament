"""Tournament class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary, String
from databases.base import Base

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
    to_hash = ["server_id"]
    ignore = ["acronym", "players_spreadsheet_id"]
