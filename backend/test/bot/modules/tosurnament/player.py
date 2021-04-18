"""
All tests concerning the Tosurnament player module.
"""

import pytest

from discord.ext import commands

from bot.modules import module as base
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
MATCH_ID = "A1"
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
    cog, mock_bot, _, bracket = init_mocks()
    mock_bot.session.add_stub(PlayersSpreadsheetSingleMock(id=1))
    bracket.players_spreadsheet_id = 1
    mock_bot.session.add_stub(SchedulesSpreadsheetSingleMock(id=1))
    bracket.schedules_spreadsheet_id = 1
    mocker.patch("common.databases.spreadsheets.base_spreadsheet.Spreadsheet", SpreadsheetMock)
    return cog, mock_bot


@pytest.mark.asyncio
async def test_register_registration_ended():
    """Registers the player but the registration phase ended."""
    cog, mock_bot, tournament, bracket = init_mocks()
    date = tournament.parse_date("1 week ago")
    bracket.registration_end_date = date.strftime(tosurnament.DATABASE_DATE_FORMAT)
    with pytest.raises(base.RegistrationEnded):
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
    cog, mock_bot = init_reschedule_single_mocks(mocker)
    with pytest.raises(exceptions.InvalidMatchId):
        await cog.reschedule(cog, tosurnament_mock.CtxMock(mock_bot), "A1", date="3 days")


@pytest.mark.asyncio
async def test_reschedule_invalid_match(mocker):
    """Reschedules a match, but the author is not a participant in the match."""
    cog, mock_bot = init_reschedule_single_mocks(mocker)
    with pytest.raises(exceptions.InvalidMatch):
        await cog.reschedule(cog, tosurnament_mock.CtxMock(mock_bot), "T1-1", date="3 days")


@pytest.mark.asyncio
async def test_reschedule(mocker):
    """Reschedules a match, but the author is not a participant in the match."""
    cog, mock_bot = init_reschedule_single_mocks(mocker)
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
