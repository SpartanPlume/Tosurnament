"""User class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from databases.base import Base

class User(Base):
    """User class"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    discord_id = Column(String)
    osu_id = Column(String)
    verified = Column(Boolean)
    code = Column(String)

    def __repr__(self):
        return "<User(discord_id='%s', osu_id='%s', verified='%i', code='%s')>" % (self.discord_id, self.osu_id, self.verified, self.code)
