"""Staff reschedule message table"""

from encrypted_mysqldb.fields import IdField, StrField
from .base_message import BaseLockMessage


class StaffRescheduleMessage(BaseLockMessage):
    """Staff reschedule message class"""

    tournament_id = IdField()
    bracket_id = IdField()
    match_id = StrField()
    team1 = StrField()
    team2 = StrField()
    previous_date = StrField()
    new_date = StrField()
    referees_id = StrField()
    streamers_id = StrField()
    commentators_id = StrField()
