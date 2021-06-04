"""
All tests concerning the Tosurnament staff module.
"""

import pytest

from bot.modules.tosurnament import module as tosurnament
from bot.modules.tosurnament import staff as staff_module
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from test.resources.mock.spreadsheet import (
    SpreadsheetMock,
    PlayersSpreadsheetSingleMock,
    SchedulesSpreadsheetSingleMock,
)
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.staff"


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    tournament = Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID)
    mock_bot.session.add_stub(tournament)
    bracket = Bracket(id=1, tournament_id=1)
    mock_bot.session.add_stub(bracket)
    cog = tosurnament_mock.mock_cog(staff_module.get_class(mock_bot))
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
async def test_drop_match_as_referee(mocker):
    """Drops a match as referee."""
    cog, mock_bot, _, bracket = init_reschedule_single_mocks(mocker)
    schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
    mock_role = tosurnament_mock.RoleMock("Referee", tosurnament_mock.REFEREE_ROLE_ID)
    mock_user = tosurnament_mock.UserMock(user_name="Referee", roles=[mock_role])
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name, "drop_match_as_referee")
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, mock_user, command=mock_command)
    await cog.drop_match_as_referee(cog, mock_ctx, "T1-1")
    mock_ctx.send.assert_called_once_with(
        "As a __" + mock_role.name + "__, " + mock_user.display_name + " **succesfully dropped** the matches: T1-1\n"
    )
    assert schedules_spreadsheet.spreadsheet.get_updated_values_with_ranges() == (["Tier 1!H2:H2"], [[[""]]])


@pytest.mark.asyncio
async def test_drop_match_as_streamer(mocker):
    """Drops a match as streamer."""
    cog, mock_bot, _, bracket = init_reschedule_single_mocks(mocker)
    schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
    mock_role = tosurnament_mock.RoleMock("Streamer", tosurnament_mock.STREAMER_ROLE_ID)
    mock_user = tosurnament_mock.UserMock(user_name="Streamer", roles=[mock_role])
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name, "drop_match_as_streamer")
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, mock_user, command=mock_command)
    await cog.drop_match_as_streamer(cog, mock_ctx, "T1-1")
    mock_ctx.send.assert_called_once_with(
        "As a __" + mock_role.name + "__, " + mock_user.display_name + " **succesfully dropped** the matches: T1-1\n"
    )
    assert schedules_spreadsheet.spreadsheet.get_updated_values_with_ranges() == (["Tier 1!I2:I2"], [[[""]]])


@pytest.mark.asyncio
async def test_drop_match_as_commentator(mocker):
    """Drops a match as commentator."""
    cog, mock_bot, _, bracket = init_reschedule_single_mocks(mocker)
    schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
    mock_role = tosurnament_mock.RoleMock("Commentator", tosurnament_mock.COMMENTATOR_ROLE_ID)
    mock_user = tosurnament_mock.UserMock(
        user_name="Commentator 1",
        roles=[mock_role],
    )
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name, "drop_match_as_commentator")
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, mock_user, command=mock_command)
    await cog.drop_match_as_commentator(cog, mock_ctx, "T1-1")
    mock_ctx.send.assert_called_once_with(
        "As a __" + mock_role.name + "__, " + mock_user.display_name + " **succesfully dropped** the matches: T1-1\n"
    )
    assert schedules_spreadsheet.spreadsheet.get_updated_values_with_ranges() == (
        ["Tier 1!J2:J2"],
        [[["Commentator 2"]]],
    )


@pytest.mark.asyncio
async def test_take_match_as_referee(mocker):
    """Takes a match as referee."""
    cog, mock_bot, _, bracket = init_reschedule_single_mocks(mocker)
    schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
    mock_role = tosurnament_mock.RoleMock("Referee", tosurnament_mock.REFEREE_ROLE_ID)
    mock_user = tosurnament_mock.UserMock(user_name="Referee", roles=[mock_role])
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name, "take_match_as_referee")
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, mock_user, command=mock_command)
    await cog.take_match_as_referee(cog, mock_ctx, "T1-12")
    mock_ctx.send.assert_called_once_with(
        "As a __" + mock_role.name + "__, " + mock_user.display_name + " **succesfully took** the matches: T1-12\n"
    )
    assert schedules_spreadsheet.spreadsheet.get_updated_values_with_ranges() == (
        ["Tier 1!H13:H13"],
        [[[mock_user.display_name]]],
    )


@pytest.mark.asyncio
async def test_take_match_as_streamer(mocker):
    """Takes a match as streamer."""
    cog, mock_bot, _, bracket = init_reschedule_single_mocks(mocker)
    schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
    mock_role = tosurnament_mock.RoleMock("Streamer", tosurnament_mock.STREAMER_ROLE_ID)
    mock_user = tosurnament_mock.UserMock(user_name="Streamer", roles=[mock_role])
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name, "take_match_as_streamer")
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, mock_user, command=mock_command)
    await cog.take_match_as_streamer(cog, mock_ctx, "T1-12")
    mock_ctx.send.assert_called_once_with(
        "As a __" + mock_role.name + "__, " + mock_user.display_name + " **succesfully took** the matches: T1-12\n"
    )
    assert schedules_spreadsheet.spreadsheet.get_updated_values_with_ranges() == (
        ["Tier 1!I13:I13"],
        [[[mock_user.display_name]]],
    )


@pytest.mark.asyncio
async def test_take_match_as_commentator(mocker):
    """Takes a match as commentator."""
    cog, mock_bot, _, bracket = init_reschedule_single_mocks(mocker)
    schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
    mock_role = tosurnament_mock.RoleMock("Commentator", tosurnament_mock.COMMENTATOR_ROLE_ID)
    mock_user = tosurnament_mock.UserMock(
        user_name="Commentator 2",
        roles=[mock_role],
    )
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name, "take_match_as_commentator")
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, mock_user, command=mock_command)
    await cog.take_match_as_commentator(cog, mock_ctx, "T1-12")
    mock_ctx.send.assert_called_once_with(
        "As a __" + mock_role.name + "__, " + mock_user.display_name + " **succesfully took** the matches: T1-12\n"
    )
    assert schedules_spreadsheet.spreadsheet.get_updated_values_with_ranges() == (
        ["Tier 1!J13:J13"],
        [[["Commentator 1 / " + mock_user.display_name]]],
    )
