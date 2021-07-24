"""End tournament message table"""

from mysqldb_wrapper import Id
from .base_message import BaseAuthorLockMessage


class EndTournamentMessage(BaseAuthorLockMessage):
    """End tournament message class"""

    __tablename__ = "end_tournament_message"

    tournament_id = Id()
