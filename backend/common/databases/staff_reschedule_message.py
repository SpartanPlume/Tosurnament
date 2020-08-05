"""Staff reschedule message table"""

from mysqldb_wrapper import Base, Id


class StaffRescheduleMessage(Base):
    """Staff reschedule message class"""

    __tablename__ = "staff_reschedule_message"

    id = Id()
    tournament_id = Id()
    bracket_id = Id()
    message_id = bytes()
    match_id = str()
    team1 = str()
    team2 = str()
    previous_date = str()
    new_date = str()
    staff_id = int()
    referees_id = str()
    streamers_id = str()
    commentators_id = str()
    in_use = bool()
    created_at = int()
