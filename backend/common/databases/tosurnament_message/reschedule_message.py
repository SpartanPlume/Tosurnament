"""Reschedule message table"""

from mysqldb_wrapper import Id
from .base_message import BaseLockMessage


class RescheduleMessage(BaseLockMessage):
    """Reschedule message class"""

    __tablename__ = "reschedule_message"

    tournament_id = Id()
    bracket_id = Id()
    previous_date = str()
    new_date = str()
    match_id = str()
    match_id_hash = bytes()
    ally_user_id = str()
    ally_user_id_str = str()
    ally_team_role_id = str()
    ally_team_role_id_str = str()
    opponent_user_id = str()
    opponent_user_id_str = str()
