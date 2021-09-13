"""Qualifiers results message table"""

from mysqldb_wrapper import Base, Id


class QualifiersResultsMessage(Base):
    """Qualifiers results message class"""

    __tablename__ = "qualifiers_results_message"

    id = Id()
    tournament_id = Id()
    bracket_id = Id()
    message_id = int()
    channel_id = int()
    channel_id_str = str()
