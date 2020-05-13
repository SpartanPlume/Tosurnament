"""Reaction for role message table"""

from mysqldb_wrapper import Base, Id


class ReactionForRoleMessage(Base):
    """Reaction for role message class"""

    __tablename__ = "reaction_for_role_message"

    id = Id()
    guild_id = bytes()
    author_id = bytes()
    setup_channel_id = int()
    setup_message_id = int()
    preview_message_id = int()
    message_id = bytes()
    channel_id = int()
    text = str()
    emojis = str()
    roles = str()
