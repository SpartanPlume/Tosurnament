"""End tournament message table"""

from .base_message import BaseAuthorLockMessage


class EndTournamentMessage(BaseAuthorLockMessage):
    """End tournament message class"""

    __tablename__ = "end_tournament_message"
