"""Reaction for role message table"""

from .base_message import BaseMessage


class ReactionForRoleMessage(BaseMessage):
    """Reaction for role message class"""

    __tablename__ = "reaction_for_role_message"

    guild_id = bytes()
    author_id = bytes()
    setup_channel_id = int()
    setup_message_id = int()
    preview_message_id = int()
    channel_id = int()
    text = str()
    emojis = str()
    roles = str()
