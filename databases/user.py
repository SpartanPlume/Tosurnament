"""User class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary, Boolean
from sqlalchemy import orm
from databases.base import Base
import helpers.crypt

class User(Base):
    """User class"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    discord_id = Column(Binary)
    osu_id = Column(Binary)
    verified = Column(Boolean)
    code = Column(Binary)
    to_hash = ["discord_id"]
    ignore = []

    @orm.reconstructor
    def init(self):
        """Decrypts the object after being queried"""
        self = helpers.crypt.decrypt_obj(self)
