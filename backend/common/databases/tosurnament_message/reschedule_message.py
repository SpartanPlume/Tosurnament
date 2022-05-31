"""Reschedule message table"""

from encrypted_mysqldb.fields import IdField, StrField, HashField
from .base_message import BaseLockMessage


class RescheduleMessage(BaseLockMessage):
    """Reschedule message class"""

    tournament_id = IdField()
    bracket_id = IdField()
    previous_date = StrField()
    new_date = StrField()
    match_id = StrField()
    match_id_hash = HashField()
    ally_user_id = StrField()
    ally_team_role_id = StrField()
    opponent_user_id = StrField()
