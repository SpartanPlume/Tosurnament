"""End tournament message class"""

from mysql_wrapper import Base

class EndTournamentMessage(Base):
    """End tournament message class"""
    __tablename__ = 'end_tournament_message'

    id = int()
    message_id = bytes()
    to_hash = ["message_id"]
    ignore = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
