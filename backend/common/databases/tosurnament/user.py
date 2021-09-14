"""User table"""

from mysqldb_wrapper import Base, Id


class User(Base):
    """User class"""

    __tablename__ = "user"

    id = Id()
    discord_id = bytes()
    discord_id_snowflake = str()
    osu_id = str()
    verified = bool()
    code = bytes()
    osu_name = str()
    osu_name_hash = bytes()
    osu_previous_name = str()
