"""
All tests concerning the Tosurnament qualifiers spreadsheet module.
"""

import pytest

from discord.ext import commands

from bot.modules import module as base
from bot.modules.tosurnament.bracket import qualifiers_spreadsheet as module_to_test
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.spreadsheets.qualifiers_spreadsheet import QualifiersSpreadsheet
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.bracket.qualifiers_spreadsheet"


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, qualifiers_spreadsheet_id=1))
    qualifiers_spreadsheet = QualifiersSpreadsheet(id=1)
    mock_bot.session.add_stub(qualifiers_spreadsheet)
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    return cog, mock_bot, qualifiers_spreadsheet


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet(mocker):
    """Sets bracket spreadsheets."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1))
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    spreadsheet_id = "abcd1234"
    sheet_name = "a sheet name"

    await cog.set_qualifiers_spreadsheet(cog, mock_ctx, spreadsheet_id, sheet_name=sheet_name)
    update_expected = [
        mocker.call(tosurnament_mock.Matcher(Bracket(tournament_id=1, qualifiers_spreadsheet_id=1))),
        mocker.call(
            tosurnament_mock.Matcher(QualifiersSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name))
        ),
    ]
    assert mock_bot.session.update.call_args_list == update_expected

    await cog.set_qualifiers_spreadsheet(cog, mock_ctx, spreadsheet_id, sheet_name="")
    update_expected = [
        mocker.call(
            tosurnament_mock.Matcher(QualifiersSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name))
        ),
    ]
    assert mock_bot.session.update.call_args_list[2:] == update_expected


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_values(mocker):
    """Sets qualifiers spreadsheet values."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, qualifiers_spreadsheet_id=1))
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    sheet_name = "a sheet name"
    with pytest.raises(base.NoSpreadsheet):
        await cog.set_qualifiers_spreadsheet_values(mock_ctx, {"sheet_name": sheet_name})

    qualifiers_spreadsheet = QualifiersSpreadsheet(id=1)
    mock_bot.session.add_stub(qualifiers_spreadsheet)
    assert qualifiers_spreadsheet.sheet_name != sheet_name
    await cog.set_qualifiers_spreadsheet_values(mock_ctx, {"sheet_name": sheet_name})
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(sheet_name=sheet_name))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_range_value(mocker):
    """Sets qualifiers spreadsheet range value."""
    cog, mock_bot, qualifiers_spreadsheet = init_mocks()
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    range_name = "range_lobby_id"
    range_value = "A"
    mocker.patch(MODULE_TO_TEST + ".spreadsheet.check_range", mocker.Mock(return_value=False))
    with pytest.raises(commands.UserInputError):
        await cog.set_qualifiers_spreadsheet_range_value(mock_ctx, range_name, range_value)

    mocker.patch(MODULE_TO_TEST + ".spreadsheet.check_range", mocker.Mock(return_value=True))
    assert qualifiers_spreadsheet.range_lobby_id != range_value
    await cog.set_qualifiers_spreadsheet_range_value(mock_ctx, range_name, range_value)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(range_lobby_id=range_value))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_sheet_name(mocker):
    """Sets the qualifiers spreasheet's sheet name."""
    cog, mock_bot, qualifiers_spreadsheet = init_mocks()
    sheet_name = "a sheet name"
    assert qualifiers_spreadsheet.sheet_name != sheet_name
    await cog.set_qualifiers_spreadsheet_sheet_name(cog, tosurnament_mock.CtxMock(mock_bot), sheet_name=sheet_name)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(sheet_name=sheet_name))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_range_lobby_id(mocker):
    """Sets the qualifiers spreasheet's range lobby_id."""
    cog, mock_bot, qualifiers_spreadsheet = init_mocks()
    range_lobby_id = "A"
    assert qualifiers_spreadsheet.range_lobby_id != range_lobby_id
    await cog.set_qualifiers_spreadsheet_range_lobby_id(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_lobby_id
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(range_lobby_id=range_lobby_id))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_range_teams(mocker):
    """Sets the qualifiers spreasheet's range teams."""
    cog, mock_bot, qualifiers_spreadsheet = init_mocks()
    range_teams = "A"
    assert qualifiers_spreadsheet.range_teams != range_teams
    await cog.set_qualifiers_spreadsheet_range_teams(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_teams)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(range_teams=range_teams))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_range_referee(mocker):
    """Sets the qualifiers spreasheet's range referee."""
    cog, mock_bot, qualifiers_spreadsheet = init_mocks()
    range_referee = "A"
    assert qualifiers_spreadsheet.range_referee != range_referee
    await cog.set_qualifiers_spreadsheet_range_referee(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_referee
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(range_referee=range_referee))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_range_date(mocker):
    """Sets the qualifiers spreasheet's range date."""
    cog, mock_bot, qualifiers_spreadsheet = init_mocks()
    range_date = "A"
    assert qualifiers_spreadsheet.range_date != range_date
    await cog.set_qualifiers_spreadsheet_range_date(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_date)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(range_date=range_date))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_range_time(mocker):
    """Sets the qualifiers spreasheet's range time."""
    cog, mock_bot, qualifiers_spreadsheet = init_mocks()
    range_time = "A"
    assert qualifiers_spreadsheet.range_time != range_time
    await cog.set_qualifiers_spreadsheet_range_time(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_time)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(range_time=range_time))
    )
