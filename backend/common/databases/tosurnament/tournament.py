"""Tournament table"""

import datetime
import dateparser
from mysqldb_wrapper import Base, Id
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
    guild_id_snowflake = int()
    guild_id_snowflake_str = str()
    acronym = str()
    name = str()
    staff_channel_id = int()
    staff_channel_id_str = str()
    match_notification_channel_id = int()
    match_notification_channel_id_str = str()
    referee_role_id = int()
    referee_role_id_str = str()
    streamer_role_id = int()
    streamer_role_id_str = str()
    commentator_role_id = int()
    commentator_role_id_str = str()
    player_role_id = int()
    player_role_id_str = str()
    team_captain_role_id = int()
    team_captain_role_id_str = str()
    post_result_message = str()
    post_result_message_team1_with_score = str()
    post_result_message_team2_with_score = str()
    post_result_message_mp_link = str()
    post_result_message_rolls = str()
    post_result_message_bans = str()
    post_result_message_tb_bans = str()
    reschedule_deadline_hours_before_current_time = int(6)
    reschedule_deadline_hours_before_new_time = int(24)
    reschedule_deadline_end = str()
    reschedule_before_date = str()
    reschedule_ping_team = bool(True)
    current_bracket_id = Id()
    matches_to_ignore = str()
    notify_no_staff_reschedule = bool(True)
    utc = str()
    template_code = str()
    registration_phase = bool(False)
    game_mode = int(0)
    registration_background_update = bool(False)
    created_at = int()
    updated_at = int()
    date_format = str()

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
    ):
        if self.date_format:
            date_formats.append(self.date_format)
        elif not date_formats:
            date_formats.append("%d %B")
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
