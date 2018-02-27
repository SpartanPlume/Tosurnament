"""Reschedule message class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary, Boolean
from sqlalchemy import orm
from databases.base import Base
import helpers.crypt

class RescheduleMessage(Base):
    """Reschedule message class"""
    __tablename__ = 'rechesule_message'

    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer)
    message_id = Column(Binary)
    previous_date = Column(Binary)
    new_date = Column(Binary)
    match_id = Column(Binary)
    ally_user_id = Column(Binary)
    ally_role_id = Column(Binary)
    enemy_user_id = Column(Binary)
    enemy_role_id = Column(Binary)
    to_hash = ["message_id"]
    ignore = ["tournament_id"]

    @orm.reconstructor
    def init(self):
        """Decrypts the object after being queried"""
        self = helpers.crypt.decrypt_obj(self)
