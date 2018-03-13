"""User class"""

from mysql_wrapper import Base

class User(Base):
    """User class"""
    __tablename__ = 'users'

    id = int()
    discord_id = bytes()
    osu_id = bytes()
    verified = bool()
    code = bytes()
    to_hash = ["discord_id"]
    ignore = ["verified"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
