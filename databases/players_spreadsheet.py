"""Players spreadsheet class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary
from databases.base import Base

class PlayersSpreadsheet(Base):
    """Players spreadsheet class"""
    __tablename__ = 'players_spreadsheet'

    id = Column(Integer, primary_key=True)
    spreadsheet_id = Column(Binary)
    range_team_name = Column(Binary)
    range_team = Column(Binary)
    n_column = Column(Binary)
    n_row = Column(Binary)
    incr_column = Column(Integer)
    incr_row = Column(Integer)
    to_hash = []
    ignore = ["n_column", "n_row", "incr_column", "incr_row"]
