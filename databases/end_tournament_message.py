"""End tournament message class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary
from sqlalchemy import orm
from databases.base import Base
import helpers.crypt

class EndTournamentMessage(Base):
    """End tournament message class"""
    __tablename__ = 'end_tournament_message'

    id = Column(Integer, primary_key=True)
    message_id = Column(Binary)
    to_hash = ["message_id"]
    ignore = []

    @orm.reconstructor
    def init(self):
        """Decrypts the object after being queried"""
        self = helpers.crypt.decrypt_obj(self)
