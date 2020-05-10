"""End tournament message table"""

from mysqldb_wrapper import Base, Id


class EndTournamentMessage(Base):
    """End tournament message class"""

    __tablename__ = "end_tournament_message"

    id = Id()
    message_id = bytes()
    created_at = int()
