"""Reschedule message class"""

from mysql_wrapper import Base

class RescheduleMessage(Base):
    """Reschedule message class"""
    __tablename__ = 'reschedule_message'

    id = int()
    tournament_id = int()
    message_id = bytes()
    previous_date = bytes()
    new_date = bytes()
    match_id = bytes()
    ally_user_id = bytes()
    ally_role_id = bytes()
    enemy_user_id = bytes()
    enemy_role_id = bytes()
    in_use = bool()
    to_hash = ["message_id"]
    ignore = ["tournament_id", "in_use"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
