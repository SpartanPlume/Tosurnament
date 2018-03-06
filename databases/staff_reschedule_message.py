"""Staff reschedule message class"""

from mysql_wrapper import Base

class StaffRescheduleMessage(Base):
    """Staff reschedule message class"""
    __tablename__ = 'staff_reschedule_message'

    id = int()
    tournament_id = bytes()
    message_id = bytes()
    match_id = bytes()
    new_date = bytes()
    staff_id = bytes()
    to_hash = ["message_id"]
    ignore = ["staff_type", "tournament_id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
