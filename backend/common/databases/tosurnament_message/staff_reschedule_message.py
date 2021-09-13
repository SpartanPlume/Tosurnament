"""Staff reschedule message table"""

from mysqldb_wrapper import Id
from .base_message import BaseLockMessage


class StaffRescheduleMessage(BaseLockMessage):
    """Staff reschedule message class"""

    __tablename__ = "staff_reschedule_message"

    tournament_id = Id()
    bracket_id = Id()
    match_id = str()
    team1 = str()
    team2 = str()
    previous_date = str()
    new_date = str()
    referees_id = str()
    streamers_id = str()
    commentators_id = str()
