"""
All tests concerning the Tosurnament player module.
"""

import datetime
import dateparser
import pytest

from discord.ext import commands

from bot.modules.tosurnament import module as tosurnament
from bot.modules.tosurnament import player as player_module
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.allowed_reschedule import AllowedReschedule
from common.databases.messages.reschedule_message import RescheduleMessage
from common.databases.user import User
from test.resources.mock.spreadsheet import (
    SpreadsheetMock,
    PlayersSpreadsheetSingleMock,
    SchedulesSpreadsheetSingleMock,
)
from common import exceptions
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.player"
MATCH_ID = "T1-1"
MATCH_IDS = ["sdf", "gre", "ewr", "egfr", "fdew"]


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    tournament = Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID)
    mock_bot.session.add_stub(tournament)
    bracket = Bracket(id=1, tournament_id=1)
    mock_bot.session.add_stub(bracket)
    cog = tosurnament_mock.mock_cog(player_module.get_class(mock_bot))
    return cog, mock_bot, tournament, bracket


def init_reschedule_single_mocks(mocker):
    cog, mock_bot, tournament, bracket = init_mocks()
    mock_bot.session.add_stub(PlayersSpreadsheetSingleMock(id=1))
    bracket.players_spreadsheet_id = 1
    mock_bot.session.add_stub(SchedulesSpreadsheetSingleMock(id=1))
    bracket.schedules_spreadsheet_id = 1
    mocker.patch("common.databases.spreadsheets.base_spreadsheet.Spreadsheet", SpreadsheetMock)
    return cog, mock_bot, tournament, bracket


@pytest.mark.asyncio
async def test_register_registration_ended():
    """Registers the player but the registration phase ended."""
    cog, mock_bot, tournament, bracket = init_mocks()
    date = tournament.parse_date("1 week ago")
    bracket.registration_end_date = date.strftime(tosurnament.DATABASE_DATE_FORMAT)
    with pytest.raises(exceptions.RegistrationEnded):
        await cog.register(cog, tosurnament_mock.CtxMock(mock_bot), "")


@pytest.mark.asyncio
async def test_reschedule_invalid_new_date():
    """Reschedules a match, but the new date in invalid."""
    cog, mock_bot, _, _ = init_mocks()
    with pytest.raises(commands.UserInputError):
        await cog.reschedule(cog, tosurnament_mock.CtxMock(mock_bot), "", date="test new date")


@pytest.mark.asyncio
async def test_reschedule_dateparser_value_error(mocker):
    """Reschedules a match, but dateparser throws a ValueError exception while trying to parse the new date."""
    cog, mock_bot, _, _ = init_mocks()
    mocker.patch("common.databases.tournament.dateparser.parse", mocker.Mock(side_effect=ValueError()))
    with pytest.raises(commands.UserInputError):
        await cog.reschedule(cog, tosurnament_mock.CtxMock(mock_bot), "", date="monday")


def test_reschedule_is_skip_deadline_validation_true():
    """Tests that the given match id is in the AllowedReschedule list."""
    cog, mock_bot, tournament, _ = init_mocks()
    for match_id in [*MATCH_IDS, MATCH_ID.lower()]:
        mock_bot.session.add_stub(AllowedReschedule(tournament_id=tournament.id, match_id=match_id))
    assert cog.is_skip_deadline_validation(tournament, MATCH_ID)


def test_reschedule_is_skip_deadline_validation_false():
    """Tests that the given match id is not in the AllowedReschedule list."""
    cog, mock_bot, tournament, _ = init_mocks()
    for match_id in MATCH_IDS:
        mock_bot.session.add_stub(AllowedReschedule(tournament_id=tournament.id, match_id=match_id))
    assert not cog.is_skip_deadline_validation(tournament, MATCH_ID)


@pytest.mark.asyncio
async def test_reschedule_invalid_match_id(mocker):
    """Reschedules a match, but the match id is invalid."""
    cog, mock_bot, _, _ = init_reschedule_single_mocks(mocker)
    with pytest.raises(exceptions.InvalidMatchId):
        await cog.reschedule(cog, tosurnament_mock.CtxMock(mock_bot), "A1", date="3 days")


@pytest.mark.asyncio
async def test_reschedule_invalid_match(mocker):
    """Reschedules a match, but the author is not a participant in the match."""
    cog, mock_bot, _, _ = init_reschedule_single_mocks(mocker)
    with pytest.raises(exceptions.InvalidMatch):
        await cog.reschedule(cog, tosurnament_mock.CtxMock(mock_bot), "T1-1", date="3 days")


@pytest.mark.asyncio
async def test_reschedule(mocker):
    """Reschedules a match, but the author is not a participant in the match."""
    cog, mock_bot, _, _ = init_reschedule_single_mocks(mocker)
    opponent_discord_id = 3249805
    mock_bot.session.add_stub(User(verified=True, osu_name_hash="team2", discord_id_snowflake=opponent_discord_id))
    match_id = "T1-1"
    author = tosurnament_mock.UserMock(user_tag="Team1#0001")
    await cog.reschedule(cog, tosurnament_mock.CtxMock(mock_bot, author), match_id, date="3 days 18:30")
    mock_bot.session.add.assert_called_once_with(
        tosurnament_mock.Matcher(
            RescheduleMessage(
                tournament_id=1,
                bracket_id=1,
                match_id=match_id,
                ally_user_id=author.id,
                opponent_user_id=opponent_discord_id,
                previous_date=mocker.ANY,
                new_date=mocker.ANY,
            )
        )
    )


def test_validate_new_date_time_is_in_the_past():
    """Date is in the past."""
    cog, mock_bot, tournament, _ = init_mocks()
    new_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    with pytest.raises(exceptions.TimeInThePast):
        cog.validate_new_date(tosurnament_mock.CtxMock(mock_bot), tournament, None, new_date, False)


def test_validate_new_date_invalid_minute():
    """Date has invalid minutes (not % 15 == 0)."""
    cog, mock_bot, tournament, _ = init_mocks()
    new_date = dateparser.parse(
        "1 day 22:13", settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "+00:00", "RETURN_AS_TIMEZONE_AWARE": True}
    )
    with pytest.raises(exceptions.InvalidMinute):
        cog.validate_new_date(tosurnament_mock.CtxMock(mock_bot), tournament, None, new_date, False)


def test_validate_new_date():
    """Date is valid."""
    cog, mock_bot, tournament, _ = init_mocks()
    new_date = dateparser.parse(
        "3 days 22:15", settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "+00:00", "RETURN_AS_TIMEZONE_AWARE": True}
    )
    result_date = cog.validate_new_date(tosurnament_mock.CtxMock(mock_bot), tournament, None, new_date, False)
    assert new_date == result_date


def test_validate_new_date_midnight():
    """Date is valid but at midnight, so one minute is removed."""
    cog, mock_bot, tournament, _ = init_mocks()
    new_date = dateparser.parse(
        "3 days 00:00", settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "+00:00", "RETURN_AS_TIMEZONE_AWARE": True}
    )
    result_date = cog.validate_new_date(tosurnament_mock.CtxMock(mock_bot), tournament, None, new_date, False)
    assert (new_date - datetime.timedelta(minutes=1)) == result_date


def test_validate_new_date_impossible_reschedule(mocker):
    """Date is valid, but the current time is passed the deadline to reschedule."""
    cog, mock_bot, tournament, _ = init_mocks()
    new_date = dateparser.parse(
        "1 hour",
        settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "+00:00", "RETURN_AS_TIMEZONE_AWARE": True},
    )
    new_date = new_date.replace(minute=0)
    cog.get_referees_mentions_of_match = mocker.Mock()
    with pytest.raises(exceptions.ImpossibleReschedule):
        cog.validate_new_date(tosurnament_mock.CtxMock(mock_bot), tournament, mocker.Mock(), new_date, False)


def test_validate_new_date_skip_deadline_validation():
    """Date is valid, the current time is passed the deadline to reschedule, but the deadline validation is skipped."""
    cog, mock_bot, tournament, _ = init_mocks()
    new_date = dateparser.parse(
        "1 hour",
        settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "+00:00", "RETURN_AS_TIMEZONE_AWARE": True},
    )
    new_date = new_date.replace(minute=0)
    result_date = cog.validate_new_date(tosurnament_mock.CtxMock(mock_bot), tournament, None, new_date, True)
    assert new_date == result_date


def test_validate_reschedule_feasibility_same_date(mocker):
    """The new date is the same than the previous date."""
    cog, mock_bot, tournament, _ = init_mocks()
    schedules_spreadsheet = SchedulesSpreadsheetSingleMock(id=1)
    new_date = dateparser.parse(
        "1 hour",
        settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "+00:00", "RETURN_AS_TIMEZONE_AWARE": True},
    )
    new_date = new_date.replace(second=0).replace(microsecond=0)
    match_info = mocker.MagicMock()
    match_info.get_datetime.return_value = new_date.strftime("%d %B %H:%M")
    with pytest.raises(exceptions.SameDate):
        cog.validate_reschedule_feasibility(
            tosurnament_mock.CtxMock(mock_bot), tournament, schedules_spreadsheet, match_info, new_date, True
        )


def test_validate_reschedule_feasibility_no_previous_date(mocker):
    """There is no previous date."""
    cog, mock_bot, tournament, _ = init_mocks()
    schedules_spreadsheet = SchedulesSpreadsheetSingleMock(id=1)
    match_info = mocker.MagicMock()
    match_info.get_datetime.return_value = ""
    previous_date = cog.validate_reschedule_feasibility(
        tosurnament_mock.CtxMock(mock_bot), tournament, schedules_spreadsheet, match_info, None, False
    )
    assert not previous_date


def test_validate_reschedule_feasibility_past_deadline(mocker):
    """Previous date of the match to reschedule is past the reschedule deadline."""
    cog, mock_bot, tournament, _ = init_mocks()
    schedules_spreadsheet = SchedulesSpreadsheetSingleMock(id=1)
    previous_date = dateparser.parse(
        "1 hour",
        settings={"PREFER_DATES_FROM": "past", "TIMEZONE": "+00:00", "RETURN_AS_TIMEZONE_AWARE": True},
    )
    match_info = mocker.MagicMock()
    match_info.get_datetime.return_value = previous_date.strftime("%d %B %H:%M")
    cog.get_referees_mentions_of_match = mocker.Mock()
    with pytest.raises(exceptions.PastDeadline):
        cog.validate_reschedule_feasibility(
            tosurnament_mock.CtxMock(mock_bot),
            tournament,
            schedules_spreadsheet,
            match_info,
            datetime.datetime.utcnow(),
            False,
        )


def test_validate_reschedule_feasibility_past_deadline_end(mocker):
    """Previous date of the match to reschedule is past the reschedule deadline."""
    cog, mock_bot, tournament, _ = init_mocks()
    tournament.reschedule_deadline_end = "monday 12:00"
    schedules_spreadsheet = SchedulesSpreadsheetSingleMock(id=1)
    previous_date = dateparser.parse(
        "monday 01:00",
        settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "+00:00", "RETURN_AS_TIMEZONE_AWARE": True},
    )
    new_date = dateparser.parse(
        "monday 13:00",
        settings={
            "PREFER_DATES_FROM": "future",
            "TIMEZONE": "+00:00",
            "RETURN_AS_TIMEZONE_AWARE": True,
            "RELATIVE_BASE": previous_date,
        },
    )
    match_info = mocker.MagicMock()
    match_info.get_datetime.return_value = previous_date.strftime("%d %B %H:%M")
    with pytest.raises(exceptions.PastDeadlineEnd):
        cog.validate_reschedule_feasibility(
            tosurnament_mock.CtxMock(mock_bot),
            tournament,
            schedules_spreadsheet,
            match_info,
            new_date,
            False,
        )


def test_validate_reschedule_feasibility_invalid_date_or_format(mocker):
    """The date in the match_info is invalid."""
    cog, mock_bot, tournament, _ = init_mocks()
    schedules_spreadsheet = SchedulesSpreadsheetSingleMock(id=1)
    match_info = mocker.MagicMock()
    match_info.get_datetime.return_value = "abc"
    with pytest.raises(exceptions.InvalidDateOrFormat):
        cog.validate_reschedule_feasibility(
            tosurnament_mock.CtxMock(mock_bot),
            tournament,
            schedules_spreadsheet,
            match_info,
            datetime.datetime.utcnow(),
            False,
        )


def test_validate_reschedule_feasibility(mocker):
    """Validates the reschedule feasibility and returns the previous date."""
    cog, mock_bot, tournament, _ = init_mocks()
    tournament.reschedule_deadline_end = "monday 12:00"
    schedules_spreadsheet = SchedulesSpreadsheetSingleMock(id=1)
    previous_date = dateparser.parse(
        "monday 01:00",
        settings={"PREFER_DATES_FROM": "future", "TIMEZONE": "+00:00", "RETURN_AS_TIMEZONE_AWARE": True},
    )
    previous_date = previous_date.replace(second=0).replace(microsecond=0)
    new_date = dateparser.parse(
        "monday 11:00",
        settings={
            "PREFER_DATES_FROM": "future",
            "TIMEZONE": "+00:00",
            "RETURN_AS_TIMEZONE_AWARE": True,
            "RELATIVE_BASE": previous_date,
        },
    )
    match_info = mocker.MagicMock()
    match_info.get_datetime.return_value = previous_date.strftime("%d %B %H:%M")
    result_date = cog.validate_reschedule_feasibility(
        tosurnament_mock.CtxMock(mock_bot),
        tournament,
        schedules_spreadsheet,
        match_info,
        new_date,
        False,
    )
    assert previous_date == result_date


@pytest.mark.asyncio
async def test_agree_to_reschedule(mocker):
    """Agrees to a reschedule by reacting on the reschedule message"""
    cog, mock_bot, tournament, bracket = init_reschedule_single_mocks(mocker)
    new_date = datetime.datetime.utcnow()
    reschedule_message = RescheduleMessage(
        tournament_id=tournament.id,
        bracket_id=bracket.id,
        match_id=MATCH_ID,
        new_date=new_date.strftime(tosurnament.DATABASE_DATE_FORMAT),
        ally_user_id=tosurnament_mock.USER_ID,
        opponent_user_id=tosurnament_mock.NOT_USER_ID,
    )
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name, "reaction_on_reschedule_message")
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, command=mock_command)
    await cog.agree_to_reschedule(mock_ctx, reschedule_message, tournament)
    expected_replies = [
        mocker.call(mocker.ANY, "accepted", tosurnament_mock.USER_NAME, MATCH_ID),
        mocker.call(
            mocker.ANY,
            "staff_notification",
            MATCH_ID,
            "Team1",
            "Team2",
            "**No previous date**",
            "**" + new_date.strftime(tosurnament.PRETTY_DATE_FORMAT) + "**",
            "Referee",
            "Streamer",
            mocker.ANY,  # TODO: should be "Commentator 1 / Commentator 2", but set is not ordered
            channel=tosurnament_mock.ChannelMock(),
        ),
    ]
    assert cog.send_reply.call_args_list == expected_replies
