"""Reaction for role message table"""

from encrypted_mysqldb.fields import StrField, IntField, HashField
from .base_message import BaseMessage


class ReactionForRoleMessage(BaseMessage):
    """Reaction for role message class"""

    guild_id = HashField()
    author_id = HashField()
    setup_channel_id = StrField()
    setup_message_id = IntField()
    preview_message_id = IntField()
    channel_id = StrField()
    text = StrField()
    emojis = StrField()
    roles = StrField()
