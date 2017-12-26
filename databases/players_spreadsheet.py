"""Players spreadsheet class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary
from sqlalchemy import orm
from databases.base import Base
import helpers.crypt

class PlayersSpreadsheet(Base):
    """Players spreadsheet class"""
    __tablename__ = 'players_spreadsheet'

    id = Column(Integer, primary_key=True)
    spreadsheet_id = Column(Binary)
    range_team_name = Column(Binary)
    range_team = Column(Binary)
    incr_column = Column(Binary)
    incr_row = Column(Binary)
    n_team = Column(Integer)
    to_hash = []
    ignore = ["n_team"]

    @orm.reconstructor
    def init(self):
        """Decrypts the object after being queried"""
        self = helpers.crypt.decrypt_obj(self)
