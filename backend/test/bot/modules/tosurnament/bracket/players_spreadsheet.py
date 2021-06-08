"""
All tests concerning the Tosurnament players spreadsheet module.
"""

import pytest

from discord.ext import commands

from bot.modules import module as base
from bot.modules.tosurnament.bracket import players_spreadsheet as module_to_test
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.spreadsheets.players_spreadsheet import PlayersSpreadsheet
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.bracket.players_spreadsheet"


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, players_spreadsheet_id=1))
    players_spreadsheet = PlayersSpreadsheet(id=1)
    mock_bot.session.add_stub(players_spreadsheet)
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    return cog, mock_bot, players_spreadsheet


@pytest.mark.asyncio
async def test_set_players_spreadsheet(mocker):
    """Sets bracket spreadsheets."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1))
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    spreadsheet_id = "abcd1234"
    sheet_name = "a sheet name"

    await cog.set_players_spreadsheet(cog, mock_ctx, spreadsheet_id, sheet_name=sheet_name)
    update_expected = [
        mocker.call(tosurnament_mock.Matcher(Bracket(tournament_id=1, players_spreadsheet_id=1))),
        mocker.call(tosurnament_mock.Matcher(PlayersSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name))),
    ]
    assert mock_bot.session.update.call_args_list == update_expected

    await cog.set_players_spreadsheet(cog, mock_ctx, spreadsheet_id, sheet_name="")
    update_expected = [
        mocker.call(tosurnament_mock.Matcher(PlayersSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name))),
    ]
    assert mock_bot.session.update.call_args_list[2:] == update_expected


@pytest.mark.asyncio
async def test_set_players_spreadsheet_values(mocker):
    """Sets players spreadsheet values."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, players_spreadsheet_id=1))
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    sheet_name = "a sheet name"
    with pytest.raises(base.NoSpreadsheet):
        await cog.set_players_spreadsheet_values(mock_ctx, {"sheet_name": sheet_name})

    players_spreadsheet = PlayersSpreadsheet(id=1)
    mock_bot.session.add_stub(players_spreadsheet)
    assert players_spreadsheet.sheet_name != sheet_name
    await cog.set_players_spreadsheet_values(mock_ctx, {"sheet_name": sheet_name})
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(PlayersSpreadsheet(sheet_name=sheet_name)))


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_value(mocker):
    """Sets players spreadsheet range value."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    range_name = "range_team_name"
    range_value = "A"
    mocker.patch(MODULE_TO_TEST + ".spreadsheet.check_range", mocker.Mock(return_value=False))
    with pytest.raises(commands.UserInputError):
        await cog.set_players_spreadsheet_range_value(mock_ctx, range_name, range_value)

    mocker.patch(MODULE_TO_TEST + ".spreadsheet.check_range", mocker.Mock(return_value=True))
    assert players_spreadsheet.range_team_name != range_value
    await cog.set_players_spreadsheet_range_value(mock_ctx, range_name, range_value)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_team_name=range_value))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_sheet_name(mocker):
    """Sets the players spreasheet's sheet name."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    sheet_name = "a sheet name"
    assert players_spreadsheet.sheet_name != sheet_name
    await cog.set_players_spreadsheet_sheet_name(cog, tosurnament_mock.CtxMock(mock_bot), sheet_name=sheet_name)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(PlayersSpreadsheet(sheet_name=sheet_name)))


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_team_name(mocker):
    """Sets the players spreasheet's range team_name."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    range_team_name = "A"
    assert players_spreadsheet.range_team_name != range_team_name
    await cog.set_players_spreadsheet_range_team_name(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_team_name
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_team_name=range_team_name))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_team(mocker):
    """Sets the players spreasheet's range team."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    range_team = "A"
    assert players_spreadsheet.range_team != range_team
    await cog.set_players_spreadsheet_range_team(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_team)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(PlayersSpreadsheet(range_team=range_team)))


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_discord(mocker):
    """Sets the players spreasheet's range discord."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    range_discord = "A"
    assert players_spreadsheet.range_discord != range_discord
    await cog.set_players_spreadsheet_range_discord(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_discord)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_discord=range_discord))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_discord_id(mocker):
    """Sets the players spreasheet's range discord_id."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    range_discord_id = "A"
    assert players_spreadsheet.range_discord_id != range_discord_id
    await cog.set_players_spreadsheet_range_discord_id(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_discord_id
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_discord_id=range_discord_id))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_rank(mocker):
    """Sets the players spreasheet's range rank."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    range_rank = "A"
    assert players_spreadsheet.range_rank != range_rank
    await cog.set_players_spreadsheet_range_rank(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_rank)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(PlayersSpreadsheet(range_rank=range_rank)))


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_bws_rank(mocker):
    """Sets the players spreasheet's range bws_rank."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    range_bws_rank = "A"
    assert players_spreadsheet.range_bws_rank != range_bws_rank
    await cog.set_players_spreadsheet_range_bws_rank(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_bws_rank)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_bws_rank=range_bws_rank))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_osu_id(mocker):
    """Sets the players spreasheet's range osu_id."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    range_osu_id = "A"
    assert players_spreadsheet.range_osu_id != range_osu_id
    await cog.set_players_spreadsheet_range_osu_id(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_osu_id)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_osu_id=range_osu_id))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_pp(mocker):
    """Sets the players spreasheet's range pp."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    range_pp = "A"
    assert players_spreadsheet.range_pp != range_pp
    await cog.set_players_spreadsheet_range_pp(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_pp)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(PlayersSpreadsheet(range_pp=range_pp)))


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_country(mocker):
    """Sets the players spreasheet's range country."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    range_country = "A"
    assert players_spreadsheet.range_country != range_country
    await cog.set_players_spreadsheet_range_country(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_country)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_country=range_country))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_timezone(mocker):
    """Sets the players spreasheet's range timezone."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    range_timezone = "A"
    assert players_spreadsheet.range_timezone != range_timezone
    await cog.set_players_spreadsheet_range_timezone(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_timezone)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_timezone=range_timezone))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_max_range_for_teams(mocker):
    """Sets the players spreasheet's max range for teams."""
    cog, mock_bot, players_spreadsheet = init_mocks()
    max_range_for_teams = 1
    assert players_spreadsheet.max_range_for_teams != max_range_for_teams
    await cog.set_players_spreadsheet_max_range_for_teams(
        cog, tosurnament_mock.CtxMock(mock_bot), length=max_range_for_teams
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(max_range_for_teams=max_range_for_teams))
    )
