"""Guild verify message table"""

from encrypted_mysqldb.fields import HashField
from .base_message import BaseMessage


class GuildVerifyMessage(BaseMessage):
    """Guild verify message class"""

    guild_id = HashField()
