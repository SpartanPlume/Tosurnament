"""Guild verify message table"""

from mysqldb_wrapper import Base, Id


class GuildVerifyMessage(Base):
    """Guild verify message class"""

    __tablename__ = "guild_verify_message"

    id = Id()
    message_id = bytes()
    guild_id = bytes()
    created_at = int()
