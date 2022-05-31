"""End tournament message table"""

from encrypted_mysqldb.fields import IdField
from .base_message import BaseAuthorLockMessage


class EndTournamentMessage(BaseAuthorLockMessage):
    """End tournament message class"""

    tournament_id = IdField()
