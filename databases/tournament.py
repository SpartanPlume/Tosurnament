"""Tournament class"""

from mysql_wrapper import Base

class Tournament(Base):
    """Tournament class"""
    __tablename__ = 'tournaments'

    id = int()
    server_id = bytes()
    acronym = bytes()
    name = bytes()
    name_change_enabled = bool()
    staff_channel_id = bytes()
    admin_role_id = bytes()
    referee_role_id = bytes()
    streamer_role_id = bytes()
    commentator_role_id = bytes()
    player_role_id = bytes()
    team_captain_role_id = bytes()
    post_result_message = bytes()
    reschedule_hours_deadline = int()
    reschedule_range_begin = bytes()
    reschedule_range_end = bytes()
    current_bracket_id = int()
    ping_team = bool()
    to_hash = ["server_id"]
    ignore = ["current_bracket_id", "name_change_enabled", "ping_team", "reschedule_hours_deadline"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
