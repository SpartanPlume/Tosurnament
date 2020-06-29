"""Allowed reschedule table"""

from mysqldb_wrapper import Base, Id


class AllowedReschedule(Base):
    """AllowedReschedule class"""

    __tablename__ = "allowed_reschedule"

    id = Id()
    tournament_id = Id()
    match_id = str()
    allowed_hours = int(24)
    created_at = int()
