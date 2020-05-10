"""User table"""

from mysqldb_wrapper import Base, Id


class User(Base):
    """User class"""

    __tablename__ = "user"

    id = Id()
    discord_id = bytes()
    osu_id = str()
    verified = bool()
    code = str()
    osu_name = str()
    osu_previous_name = str()
