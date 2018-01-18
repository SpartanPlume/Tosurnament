"""Reschedule message class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary
from sqlalchemy import orm
from databases.base import Base
import helpers.crypt

class RescheduleMessage(Base):
    """Reschedule message class"""
    __tablename__ = 'rechesule_message'

    id = Column(Integer, primary_key=True)
    message_id = Column(Binary)
    new_date = Column(Binary)
    ally_mention = Column(Binary)
    enemy_mention = Column(Binary)
    to_hash = []
    ignore = []

    @orm.reconstructor
    def init(self):
        """Decrypts the object after being queried"""
        self = helpers.crypt.decrypt_obj(self)
