"""Tournament table"""

import datetime
import dateparser
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
    post_result_message_team1_with_score = str()
    post_result_message_team2_with_score = str()
    post_result_message_mp_link = str()
    post_result_message_rolls = str()
    post_result_message_bans = str()
    post_result_message_tb_bans = str()
    reschedule_deadline_hours_before_current_time = int(6)
    reschedule_deadline_hours_before_new_time = int(24)
    reschedule_deadline_begin = str()
    reschedule_deadline_end = str()
    reschedule_allowed_begin = str()
    reschedule_allowed_end = str()
    reschedule_ping_team = bool(True)
    current_bracket_id = Id()
    created_at = int()
    matches_to_ignore = str()
    notify_no_staff_reschedule = bool(True)
    utc = str()
    template_code = str()
    registration_phase = bool(False)

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

    def get_bracket_from_id(self, bracket_id):
        return next((bracket for bracket in self.brackets if bracket.id == bracket_id), None)

    def get_role_id(self, role_name):
        field = role_name.lower().replace(" ", "_") + "_role_id"
        try:
            return vars(self)[field]
        except KeyError:
            return None

    def parse_date(
        self,
        date,
        date_formats=[],
        prefer_dates_from="current_period",
        relative_base=datetime.datetime.now(),
        to_timezone="+00:00",
    ):
        if self.utc:
            return dateparser.parse(
                date,
                date_formats=date_formats,
                settings={
                    "PREFER_DATES_FROM": prefer_dates_from,
                    "RELATIVE_BASE": relative_base,
                    "TIMEZONE": self.utc,
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "DATE_ORDER": "DMY",
                },
            )
        else:
            return dateparser.parse(
                date,
                date_formats=date_formats,
                settings={
                    "PREFER_DATES_FROM": prefer_dates_from,
                    "RELATIVE_BASE": relative_base,
                    "TIMEZONE": "+00:00",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "DATE_ORDER": "DMY",
                },
            )

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
