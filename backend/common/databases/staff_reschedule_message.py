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
    new_date = str()
    staff_id = int()
    in_use = bool()
    created_at = int()
