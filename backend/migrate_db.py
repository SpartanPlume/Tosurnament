import gc
import logging
import datetime
from logging.handlers import TimedRotatingFileHandler
from encrypted_mysqldb.database import Database
from encrypted_mysqldb.table import Table
from encrypted_mysqldb.fields import IdField, StrField, IntField, DatetimeField, HashField, BoolField
from cryptography.fernet import Fernet
from common.config import constants

logging_handler = TimedRotatingFileHandler(
    filename="log/migrate_db.log",
    when="W1",
    utc=True,
    backupCount=4,
    atTime=datetime.time(hour=12),
)
logging_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(name)s <%(filename)s:%(lineno)d>: %(message)s")
)
db_logger = logging.getLogger("encrypted_mysqldb")
db_logger.addHandler(logging_handler)
db_logger.setLevel(logging.DEBUG)


class AllowedReschedule(Table):
    tournament_id = IdField()
    match_id = StrField()
    allowed_hours = IntField(24)
    created_at = IntField()


class Bracket(Table):
    tournament_id = IdField()
    name = StrField()
    role_id = StrField()
    challonge = StrField()
    players_spreadsheet_id = IdField(-1)
    schedules_spreadsheet_id = IdField(-1)
    qualifiers_spreadsheet_id = IdField(-1)
    qualifiers_results_spreadsheet_id = IdField(-1)
    post_result_channel_id = StrField()
    current_round = StrField()
    minimum_rank = IntField()
    maximum_rank = IntField()
    registration_end_date = StrField()
    created_at = IntField()
    updated_at = IntField()


class Guild(Table):
    guild_id = HashField()
    guild_id_snowflake = StrField()
    verified_role_id = StrField()
    admin_role_id = StrField()
    last_notification_date = IntField()
    language = StrField()
    created_at = IntField()
    updated_at = IntField()


class Tournament(Table):
    guild_id = HashField()
    guild_id_snowflake = StrField()
    acronym = StrField()
    name = StrField()
    staff_channel_id = StrField()
    match_notification_channel_id = StrField()
    referee_role_id = StrField()
    streamer_role_id = StrField()
    commentator_role_id = StrField()
    player_role_id = StrField()
    team_captain_role_id = StrField()
    post_result_message = StrField()
    post_result_message_team1_with_score = StrField()
    post_result_message_team2_with_score = StrField()
    post_result_message_mp_link = StrField()
    post_result_message_rolls = StrField()
    post_result_message_bans = StrField()
    post_result_message_tb_bans = StrField()
    reschedule_deadline_hours_before_current_time = IntField(6)
    reschedule_deadline_hours_before_new_time = IntField(24)
    reschedule_deadline_end = StrField()
    reschedule_before_date = StrField()
    reschedule_ping_team = BoolField(True)
    current_bracket_id = IdField()
    matches_to_ignore = StrField()
    notify_no_staff_reschedule = BoolField(True)
    utc = StrField()
    template_code = StrField()
    registration_phase = BoolField(False)
    game_mode = IntField(0)
    registration_background_update = BoolField(False)
    created_at = IntField()
    updated_at = IntField()
    date_format = StrField()


class PlayersSpreadsheet(Table):
    spreadsheet_id = StrField()
    sheet_name = StrField()
    range_team_name = StrField()
    range_team = StrField()
    range_discord = StrField()
    range_discord_id = StrField()
    range_rank = StrField()
    range_bws_rank = StrField()
    range_osu_id = StrField()
    range_pp = StrField()
    range_country = StrField()
    range_timezone = StrField()
    max_range_for_teams = IntField()


class QualifiersResultsSpreadsheet(Table):
    spreadsheet_id = StrField()
    sheet_name = StrField()
    range_osu_id = StrField()
    range_score = StrField()


class QualifiersSpreadsheet(Table):
    spreadsheet_id = StrField()
    sheet_name = StrField()
    range_lobby_id = StrField()
    range_teams = StrField()
    range_referee = StrField()
    range_date = StrField()
    range_time = StrField()
    max_teams_in_row = IntField(8)


class SchedulesSpreadsheet(Table):
    spreadsheet_id = StrField()
    sheet_name = StrField()
    range_match_id = StrField()
    range_team1 = StrField()
    range_score_team1 = StrField()
    range_score_team2 = StrField()
    range_team2 = StrField()
    range_date = StrField()
    range_time = StrField()
    range_referee = StrField()
    range_streamer = StrField()
    range_commentator = StrField()
    range_mp_links = StrField()
    date_format = StrField()
    use_range = BoolField(False)
    max_referee = IntField(1)
    max_streamer = IntField(1)
    max_commentator = IntField(2)


db = Database(constants.DB_USERNAME, constants.DB_PASSWORD, constants.DB_NAME, Fernet(constants.ENCRYPTION_KEY))

tournaments = [tournament.get_table_dict() for tournament in db.query(Tournament).all()]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(Tournament.__tablename__))

brackets = [bracket.get_table_dict() for bracket in db.query(Bracket).all()]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(Bracket.__tablename__))

allowed_reschedules = [allowed_reschedule.get_table_dict() for allowed_reschedule in db.query(AllowedReschedule).all()]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(AllowedReschedule.__tablename__))

guilds = [guild.get_table_dict() for guild in db.query(Guild).all()]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(Guild.__tablename__))

players_spreadsheets = [
    players_spreadsheet.get_table_dict() for players_spreadsheet in db.query(PlayersSpreadsheet).all()
]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(PlayersSpreadsheet.__tablename__))

qualifiers_spreadsheets = [
    qualifiers_spreadsheet.get_table_dict() for qualifiers_spreadsheet in db.query(QualifiersSpreadsheet).all()
]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(QualifiersSpreadsheet.__tablename__))

qualifiers_results_spreadsheets = [
    qualifiers_results_spreadsheet.get_table_dict()
    for qualifiers_results_spreadsheet in db.query(QualifiersResultsSpreadsheet).all()
]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(QualifiersResultsSpreadsheet.__tablename__))

schedules_spreadsheets = [
    schedules_spreadsheet.get_table_dict() for schedules_spreadsheet in db.query(SchedulesSpreadsheet).all()
]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(SchedulesSpreadsheet.__tablename__))

with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format("token"))

db.close()
del AllowedReschedule
del Tournament
del Guild
del Bracket
del PlayersSpreadsheet
del QualifiersResultsSpreadsheet
del QualifiersSpreadsheet
del SchedulesSpreadsheet
gc.collect()


class EndTournamentMessage(Table):
    message_id = HashField()
    created_at = IntField()
    updated_at = IntField()
    locked = BoolField()
    author_id = HashField()
    tournament_id = IdField()


class GuildVerifyMessage(Table):
    message_id = HashField()
    created_at = IntField()
    updated_at = IntField()
    guild_id = HashField()


class MatchNotification(Table):
    message_id = HashField()
    created_at = IntField()
    updated_at = IntField()
    locked = BoolField()
    tournament_id = IdField()
    bracket_id = IdField()
    message_id_int = IntField()
    match_id = StrField()
    teams_mentions = StrField()
    team1_mention = StrField()
    team2_mention = StrField()
    date_info = StrField()
    notification_type = IntField()


class PostResultMessage(Table):
    message_id = HashField()
    created_at = IntField()
    updated_at = IntField()
    locked = BoolField()
    author_id = HashField()
    tournament_id = IdField()
    bracket_id = IdField()
    preview_message_id = IntField()
    setup_message_id = IntField()
    step = IntField(1)
    match_id = StrField()
    score_team1 = IntField()
    score_team2 = IntField()
    best_of = IntField()
    roll_team1 = IntField()
    roll_team2 = IntField()
    n_warmup = IntField()
    mp_links = StrField()
    bans_team1 = StrField()
    bans_team2 = StrField()
    tb_bans_team1 = StrField()
    tb_bans_team2 = StrField()


class QualifiersResultsMessage(Table):
    tournament_id = IdField()
    bracket_id = IdField()
    message_id = IntField()
    channel_id = StrField()


class ReactionForRoleMessage(Table):
    message_id = HashField()
    created_at = IntField()
    updated_at = IntField()
    guild_id = HashField()
    author_id = HashField()
    setup_channel_id = StrField()
    setup_message_id = IntField()
    preview_message_id = IntField()
    channel_id = StrField()
    text = StrField()
    emojis = StrField()
    roles = StrField()


class RescheduleMessage(Table):
    message_id = HashField()
    created_at = IntField()
    updated_at = IntField()
    locked = BoolField()
    tournament_id = IdField()
    bracket_id = IdField()
    previous_date = StrField()
    new_date = StrField()
    match_id = StrField()
    match_id_hash = HashField()
    ally_user_id = StrField()
    ally_team_role_id = StrField()
    opponent_user_id = StrField()


class StaffRescheduleMessage(Table):
    message_id = HashField()
    created_at = IntField()
    updated_at = IntField()
    locked = BoolField()
    tournament_id = IdField()
    bracket_id = IdField()
    match_id = StrField()
    team1 = StrField()
    team2 = StrField()
    previous_date = StrField()
    new_date = StrField()
    referees_id = StrField()
    streamers_id = StrField()
    commentators_id = StrField()


db = Database(constants.DB_USERNAME, constants.DB_PASSWORD, constants.DB_MESSAGE_NAME, Fernet(constants.ENCRYPTION_KEY))

end_tournament_messages = [
    end_tournament_message.get_table_dict() for end_tournament_message in db.query(EndTournamentMessage).all()
]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(EndTournamentMessage.__tablename__))

guild_verify_messages = [
    guild_verify_message.get_table_dict() for guild_verify_message in db.query(GuildVerifyMessage).all()
]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(GuildVerifyMessage.__tablename__))

match_notifications = [match_notification.get_table_dict() for match_notification in db.query(MatchNotification).all()]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(MatchNotification.__tablename__))

post_result_messages = [
    post_result_message.get_table_dict() for post_result_message in db.query(PostResultMessage).all()
]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(PostResultMessage.__tablename__))

qualifiers_results_messages = [
    qualifiers_results_message.get_table_dict()
    for qualifiers_results_message in db.query(QualifiersResultsMessage).all()
]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(QualifiersResultsMessage.__tablename__))

reaction_for_role_messages = [
    reaction_for_role_message.get_table_dict() for reaction_for_role_message in db.query(ReactionForRoleMessage).all()
]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(ReactionForRoleMessage.__tablename__))

reschedule_messages = [reschedule_message.get_table_dict() for reschedule_message in db.query(RescheduleMessage).all()]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(RescheduleMessage.__tablename__))

staff_reschedule_messages = [
    staff_reschedule_message.get_table_dict() for staff_reschedule_message in db.query(StaffRescheduleMessage).all()
]
with db.connection_pool.create_cursor() as cursor:
    cursor.execute("DROP TABLE {0}".format(StaffRescheduleMessage.__tablename__))


db.close()
del EndTournamentMessage
del GuildVerifyMessage
del MatchNotification
del PostResultMessage
del QualifiersResultsMessage
del ReactionForRoleMessage
del RescheduleMessage
del StaffRescheduleMessage
gc.collect()

import datetime


class AllowedReschedule(Table):
    tournament_id = IdField()
    match_id = StrField()
    allowed_hours = IntField(24)
    created_at = DatetimeField()


class Bracket(Table):
    tournament_id = IdField()
    name = StrField()
    role_id = StrField()
    challonge = StrField()
    players_spreadsheet_id = IdField(-1)
    schedules_spreadsheet_id = IdField(-1)
    qualifiers_spreadsheet_id = IdField(-1)
    qualifiers_results_spreadsheet_id = IdField(-1)
    post_result_channel_id = StrField()
    current_round = StrField()
    minimum_rank = IntField()
    maximum_rank = IntField()
    registration_end_date = StrField()
    created_at = DatetimeField()
    updated_at = DatetimeField()


class Guild(Table):
    guild_id = HashField()
    guild_id_snowflake = StrField()
    verified_role_id = StrField()
    admin_role_id = StrField()
    last_notification_date = DatetimeField()
    language = StrField()
    created_at = DatetimeField()
    updated_at = DatetimeField()


class Tournament(Table):
    guild_id = HashField()
    guild_id_snowflake = StrField()
    acronym = StrField()
    name = StrField()
    staff_channel_id = StrField()
    match_notification_channel_id = StrField()
    referee_role_id = StrField()
    streamer_role_id = StrField()
    commentator_role_id = StrField()
    player_role_id = StrField()
    team_captain_role_id = StrField()
    post_result_message = StrField()
    post_result_message_team1_with_score = StrField()
    post_result_message_team2_with_score = StrField()
    post_result_message_mp_link = StrField()
    post_result_message_rolls = StrField()
    post_result_message_bans = StrField()
    post_result_message_tb_bans = StrField()
    reschedule_deadline_hours_before_current_time = IntField(6)
    reschedule_deadline_hours_before_new_time = IntField(24)
    reschedule_deadline_end = StrField()
    reschedule_before_date = StrField()
    reschedule_ping_team = BoolField(True)
    current_bracket_id = IdField()
    matches_to_ignore = StrField()
    notify_no_staff_reschedule = BoolField(True)
    utc = StrField()
    template_code = StrField()
    registration_phase = BoolField(False)
    game_mode = IntField(0)
    registration_background_update = BoolField(False)
    created_at = DatetimeField()
    updated_at = DatetimeField()
    date_format = StrField()


class PlayersSpreadsheet(Table):
    spreadsheet_id = StrField()
    sheet_name = StrField()
    range_team_name = StrField()
    range_team = StrField()
    range_discord = StrField()
    range_discord_id = StrField()
    range_rank = StrField()
    range_bws_rank = StrField()
    range_osu_id = StrField()
    range_pp = StrField()
    range_country = StrField()
    range_timezone = StrField()
    max_range_for_teams = IntField()


class QualifiersResultsSpreadsheet(Table):
    spreadsheet_id = StrField()
    sheet_name = StrField()
    range_osu_id = StrField()
    range_score = StrField()


class QualifiersSpreadsheet(Table):
    spreadsheet_id = StrField()
    sheet_name = StrField()
    range_lobby_id = StrField()
    range_teams = StrField()
    range_referee = StrField()
    range_date = StrField()
    range_time = StrField()
    max_teams_in_row = IntField(8)


class SchedulesSpreadsheet(Table):
    spreadsheet_id = StrField()
    sheet_name = StrField()
    range_match_id = StrField()
    range_team1 = StrField()
    range_score_team1 = StrField()
    range_score_team2 = StrField()
    range_team2 = StrField()
    range_date = StrField()
    range_time = StrField()
    range_referee = StrField()
    range_streamer = StrField()
    range_commentator = StrField()
    range_mp_links = StrField()
    date_format = StrField()
    use_range = BoolField(False)
    max_referee = IntField(1)
    max_streamer = IntField(1)
    max_commentator = IntField(2)


db = Database(constants.DB_USERNAME, constants.DB_PASSWORD, constants.DB_NAME, Fernet(constants.ENCRYPTION_KEY))

tournament_ids_map = {}
players_spreadsheets_ids_map = {}
qualifiers_spreadsheets_ids_map = {}
qualifiers_results_spreadsheets_ids_map = {}
schedules_spreadsheets_ids_map = {}
bracket_ids_map = {}
guild_ids = []

for guild in guilds:
    if guild["guild_id_snowflake"] in guild_ids:
        continue
    guild_ids.append(guild["guild_id_snowflake"])
    guild["created_at"] = datetime.datetime.utcnow()
    guild["updated_at"] = datetime.datetime.utcnow()
    guild["last_notification_date"] = datetime.datetime.utcnow()
    guild = db.add(Guild(**guild))


for tournament in tournaments:
    previous_id = int(tournament["id"])
    tournament["created_at"] = datetime.datetime.utcnow()
    tournament["updated_at"] = datetime.datetime.utcnow()
    tournament = db.add(Tournament(**tournament))
    tournament_ids_map[previous_id] = int(tournament.id)

for allowed_reschedule in allowed_reschedules:
    if allowed_reschedule["tournament_id"] in tournament_ids_map:
        allowed_reschedule["created_at"] = datetime.datetime.utcnow()
        allowed_reschedule["tournament_id"] = tournament_ids_map[allowed_reschedule["tournament_id"]]
        allowed_reschedule = db.add(AllowedReschedule(**allowed_reschedule))

for players_spreadsheet in players_spreadsheets:
    previous_id = int(players_spreadsheet["id"])
    players_spreadsheet = db.add(PlayersSpreadsheet(**players_spreadsheet))
    players_spreadsheets_ids_map[previous_id] = int(players_spreadsheet.id)

for qualifiers_spreadsheet in qualifiers_spreadsheets:
    previous_id = int(qualifiers_spreadsheet["id"])
    qualifiers_spreadsheet = db.add(QualifiersSpreadsheet(**qualifiers_spreadsheet))
    qualifiers_spreadsheets_ids_map[previous_id] = int(qualifiers_spreadsheet.id)

for qualifiers_results_spreadsheet in qualifiers_results_spreadsheets:
    previous_id = int(qualifiers_results_spreadsheet["id"])
    qualifiers_results_spreadsheet = db.add(QualifiersResultsSpreadsheet(**qualifiers_results_spreadsheet))
    qualifiers_results_spreadsheets_ids_map[previous_id] = int(qualifiers_results_spreadsheet.id)

for schedules_spreadsheet in schedules_spreadsheets:
    previous_id = int(schedules_spreadsheet["id"])
    schedules_spreadsheet = db.add(SchedulesSpreadsheet(**schedules_spreadsheet))
    schedules_spreadsheets_ids_map[previous_id] = int(schedules_spreadsheet.id)

for bracket in brackets:
    previous_id = int(bracket["id"])
    bracket["created_at"] = datetime.datetime.utcnow()
    bracket["updated_at"] = datetime.datetime.utcnow()
    bracket["tournament_id"] = tournament_ids_map[bracket["tournament_id"]]
    if bracket["players_spreadsheet_id"] > 0:
        bracket["players_spreadsheet_id"] = players_spreadsheets_ids_map[bracket["players_spreadsheet_id"]]
    if bracket["qualifiers_spreadsheet_id"] > 0:
        bracket["qualifiers_spreadsheet_id"] = qualifiers_spreadsheets_ids_map[bracket["qualifiers_spreadsheet_id"]]
    if bracket["qualifiers_results_spreadsheet_id"] > 0:
        bracket["qualifiers_results_spreadsheet_id"] = qualifiers_results_spreadsheets_ids_map[
            bracket["qualifiers_results_spreadsheet_id"]
        ]
    if bracket["schedules_spreadsheet_id"] > 0:
        bracket["schedules_spreadsheet_id"] = schedules_spreadsheets_ids_map[bracket["schedules_spreadsheet_id"]]
    bracket = db.add(Bracket(**bracket))
    bracket_ids_map[previous_id] = int(bracket.id)

db.close()
del allowed_reschedule
del tournament
del guild
del bracket
del players_spreadsheet
del qualifiers_results_spreadsheet
del qualifiers_spreadsheet
del schedules_spreadsheet
del AllowedReschedule
del Tournament
del Guild
del Bracket
del PlayersSpreadsheet
del QualifiersResultsSpreadsheet
del QualifiersSpreadsheet
del SchedulesSpreadsheet
gc.collect()


class EndTournamentMessage(Table):
    message_id = HashField()
    created_at = DatetimeField()
    updated_at = DatetimeField()
    locked = BoolField()
    author_id = HashField()
    tournament_id = IdField()


class GuildVerifyMessage(Table):
    message_id = HashField()
    created_at = DatetimeField()
    updated_at = DatetimeField()
    guild_id = HashField()


class MatchNotification(Table):
    message_id = HashField()
    created_at = DatetimeField()
    updated_at = DatetimeField()
    locked = BoolField()
    tournament_id = IdField()
    bracket_id = IdField()
    message_id_int = IntField()
    match_id = StrField()
    teams_mentions = StrField()
    team1_mention = StrField()
    team2_mention = StrField()
    date_info = StrField()
    notification_type = IntField()


class PostResultMessage(Table):
    message_id = HashField()
    created_at = DatetimeField()
    updated_at = DatetimeField()
    locked = BoolField()
    author_id = HashField()
    tournament_id = IdField()
    bracket_id = IdField()
    preview_message_id = IntField()
    setup_message_id = IntField()
    step = IntField(1)
    match_id = StrField()
    score_team1 = IntField()
    score_team2 = IntField()
    best_of = IntField()
    roll_team1 = IntField()
    roll_team2 = IntField()
    n_warmup = IntField()
    mp_links = StrField()
    bans_team1 = StrField()
    bans_team2 = StrField()
    tb_bans_team1 = StrField()
    tb_bans_team2 = StrField()


class QualifiersResultsMessage(Table):
    tournament_id = IdField()
    bracket_id = IdField()
    message_id = IntField()
    channel_id = StrField()


class ReactionForRoleMessage(Table):
    message_id = HashField()
    created_at = DatetimeField()
    updated_at = DatetimeField()
    guild_id = HashField()
    author_id = HashField()
    setup_channel_id = StrField()
    setup_message_id = IntField()
    preview_message_id = IntField()
    channel_id = StrField()
    text = StrField()
    emojis = StrField()
    roles = StrField()


class RescheduleMessage(Table):
    message_id = HashField()
    created_at = DatetimeField()
    updated_at = DatetimeField()
    locked = BoolField()
    tournament_id = IdField()
    bracket_id = IdField()
    previous_date = StrField()
    new_date = StrField()
    match_id = StrField()
    match_id_hash = HashField()
    ally_user_id = StrField()
    ally_team_role_id = StrField()
    opponent_user_id = StrField()


class StaffRescheduleMessage(Table):
    message_id = HashField()
    created_at = DatetimeField()
    updated_at = DatetimeField()
    locked = BoolField()
    tournament_id = IdField()
    bracket_id = IdField()
    match_id = StrField()
    team1 = StrField()
    team2 = StrField()
    previous_date = StrField()
    new_date = StrField()
    referees_id = StrField()
    streamers_id = StrField()
    commentators_id = StrField()


db = Database(constants.DB_USERNAME, constants.DB_PASSWORD, constants.DB_MESSAGE_NAME, Fernet(constants.ENCRYPTION_KEY))

for end_tournament_message in end_tournament_messages:
    if end_tournament_message["tournament_id"] in tournament_ids_map:
        end_tournament_message["created_at"] = datetime.datetime.utcnow()
        end_tournament_message["updated_at"] = datetime.datetime.utcnow()
        end_tournament_message["tournament_id"] = tournament_ids_map[end_tournament_message["tournament_id"]]
        end_tournament_message = db.add(EndTournamentMessage(**end_tournament_message))

for guild_verify_message in guild_verify_messages:
    guild_verify_message["created_at"] = datetime.datetime.utcnow()
    guild_verify_message["updated_at"] = datetime.datetime.utcnow()
    guild_verify_message = db.add(GuildVerifyMessage(**guild_verify_message))

for match_notification in match_notifications:
    if (
        match_notification["tournament_id"] in tournament_ids_map
        and match_notification["bracket_id"] in bracket_ids_map
    ):
        match_notification["created_at"] = datetime.datetime.utcnow()
        match_notification["updated_at"] = datetime.datetime.utcnow()
        match_notification["tournament_id"] = tournament_ids_map[match_notification["tournament_id"]]
        match_notification["bracket_id"] = bracket_ids_map[match_notification["bracket_id"]]
        match_notification = db.add(MatchNotification(**match_notification))

for post_result_message in post_result_messages:
    if (
        post_result_message["tournament_id"] in tournament_ids_map
        and post_result_message["bracket_id"] in bracket_ids_map
    ):
        post_result_message["created_at"] = datetime.datetime.utcnow()
        post_result_message["updated_at"] = datetime.datetime.utcnow()
        post_result_message["tournament_id"] = tournament_ids_map[post_result_message["tournament_id"]]
        post_result_message["bracket_id"] = bracket_ids_map[post_result_message["bracket_id"]]
        post_result_message = db.add(PostResultMessage(**post_result_message))

for qualifiers_results_message in qualifiers_results_messages:
    if (
        qualifiers_results_message["tournament_id"] in tournament_ids_map
        and qualifiers_results_message["bracket_id"] in bracket_ids_map
    ):
        qualifiers_results_message["tournament_id"] = tournament_ids_map[qualifiers_results_message["tournament_id"]]
        qualifiers_results_message["bracket_id"] = bracket_ids_map[qualifiers_results_message["bracket_id"]]
        qualifiers_results_message = db.add(QualifiersResultsMessage(**qualifiers_results_message))

for reaction_for_role_message in reaction_for_role_messages:
    reaction_for_role_message["created_at"] = datetime.datetime.utcnow()
    reaction_for_role_message["updated_at"] = datetime.datetime.utcnow()
    reaction_for_role_message = db.add(ReactionForRoleMessage(**reaction_for_role_message))

for reschedule_message in reschedule_messages:
    if (
        reschedule_message["tournament_id"] in tournament_ids_map
        and reschedule_message["bracket_id"] in bracket_ids_map
    ):
        reschedule_message["created_at"] = datetime.datetime.utcnow()
        reschedule_message["updated_at"] = datetime.datetime.utcnow()
        reschedule_message["tournament_id"] = tournament_ids_map[reschedule_message["tournament_id"]]
        reschedule_message["bracket_id"] = bracket_ids_map[reschedule_message["bracket_id"]]
        reschedule_message = db.add(RescheduleMessage(**reschedule_message))

for staff_reschedule_message in staff_reschedule_messages:
    if (
        staff_reschedule_message["tournament_id"] in tournament_ids_map
        and staff_reschedule_message["bracket_id"] in bracket_ids_map
    ):
        staff_reschedule_message["created_at"] = datetime.datetime.utcnow()
        staff_reschedule_message["updated_at"] = datetime.datetime.utcnow()
        staff_reschedule_message["tournament_id"] = tournament_ids_map[staff_reschedule_message["tournament_id"]]
        staff_reschedule_message["bracket_id"] = bracket_ids_map[staff_reschedule_message["bracket_id"]]
        staff_reschedule_message = db.add(StaffRescheduleMessage(**staff_reschedule_message))
