"""Reschedule message table"""

from mysqldb_wrapper import Base, Id


class RescheduleMessage(Base):
    """Reschedule message class"""

    __tablename__ = "reschedule_message"

    id = Id()
    tournament_id = Id()
    bracket_id = Id()
    message_id = bytes()
    previous_date = str()
    new_date = str()
    match_id = str()
    ally_user_id = int()
    ally_team_role_id = int()
    opponent_user_id = int()
    in_use = bool()
    created_at = int()
