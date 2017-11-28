"""Players spreadsheet class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary
from databases.base import Base

class PlayersSpreadsheet(Base):
    """Players spreadsheet class"""
    __tablename__ = 'players_spreadsheet'

    id = Column(Integer, primary_key=True)
    #ezrlkezrlkkzl_id = Column(Binary)
    acronym = Column(Binary)
    name = Column(Binary)
    staff_channel_id = Column(Binary)
    admin_role_id = Column(Binary)
    referee_role_id = Column(Binary)
    player_role_id = Column(Binary)
    players_spreadsheet_id = Column(Integer)
    to_hash = ["server_id"]
    ignore = ["players_spreadsheet_id"]
