"""Token class"""

from mysqldb_wrapper import Base, Id


class Token(Base):
    """Token class"""

    __tablename__ = "token"

    id = Id()
    session_token = bytes()
    discord_user_id = str()
    access_token = str()
    token_type = str()
    access_token_expiry_date = int()
    refresh_token = str()
    scope = str()
    expiry_date = int()
