"""Tournament table"""

import datetime
from mysqldb_wrapper import Base, Id
from common.databases.bracket import Bracket
from common.exceptions import UnknownError


class Tournament(Base):
    """Tournament class"""

    __tablename__ = "tournament"

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._current_bracket = None
        self._brackets = None

    id = Id()
    guild_id = bytes()
    acronym = str()
    name = str()
    staff_channel_id = int()
    match_notification_channel_id = int()
    referee_role_id = int()
    streamer_role_id = int()
    commentator_role_id = int()
    player_role_id = int()
    team_captain_role_id = int()
    post_result_message = str()
    post_result_message_rolls = str()
    post_result_message_bans = str()
    post_result_message_tb_bans = str()
    reschedule_deadline_hours = int(24)
    reschedule_deadline_begin = str()
    reschedule_deadline_end = str()
    reschedule_allowed_begin = str()
    reschedule_allowed_end = str()
    reschedule_ping_team = bool(True)
    current_bracket_id = Id()
    created_at = int()
    matches_to_ignore = str()

    @property
    def current_bracket(self):
        if self._current_bracket is None:
            for bracket in self.brackets:
                if bracket.id == self.current_bracket_id:
                    self._current_bracket = bracket
                    break
        return self._current_bracket

    @property
    def brackets(self):
        if self._brackets is None:
            self._brackets = self._session.query(Bracket).where(Bracket.tournament_id == self.id).all()
            if not self._brackets:
                raise UnknownError("No brackets found")
        return self._brackets

    def get_role_id(self, role_name):
        field = role_name.lower().replace(" ", "_") + "_role_id"
        try:
            return vars(self)[field]
        except KeyError:
            return None

    def create_date_from_week_times(self, week_time_begin, week_time_end, date):
        if not week_time_begin or not week_time_end:
            return date, date
        day_name, time = week_time_begin.split(" ")
        hours, minutes = time.split(":")
        weekday = self.get_weekday_from_day_name(day_name)
        date_week_begin = date - datetime.timedelta(days=(date.weekday() - weekday) % 7)
        date_week_begin = date_week_begin.replace(hour=int(hours), minute=int(minutes))
        day_name, time = week_time_end.split(" ")
        hours, minutes = time.split(":")
        weekday = self.get_weekday_from_day_name(day_name)
        date_week_end = date + datetime.timedelta(days=(date_week_begin.weekday() - weekday) % 7)
        date_week_end = date_week_end.replace(hour=int(hours), minute=int(minutes))
        return date_week_begin, date_week_end

    def get_weekday_from_day_name(self, day_name):
        days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        return days.index(day_name)
