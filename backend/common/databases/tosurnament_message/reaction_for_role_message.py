"""Reaction for role message table"""

from .base_message import BaseMessage


class ReactionForRoleMessage(BaseMessage):
    """Reaction for role message class"""

    __tablename__ = "reaction_for_role_message"

    guild_id = bytes()
    author_id = bytes()
    setup_channel_id = str()
    setup_channel_id_str = str()
    setup_message_id = int()
    preview_message_id = int()
    channel_id = str()
    channel_id_str = str()
    text = str()
    emojis = str()
    roles = str()
