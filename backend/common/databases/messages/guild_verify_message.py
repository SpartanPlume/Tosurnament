"""Guild verify message table"""

from .base_message import BaseMessage


class GuildVerifyMessage(BaseMessage):
    """Guild verify message class"""

    __tablename__ = "guild_verify_message"

    guild_id = bytes()
