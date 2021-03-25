"""
All tests concerning the Tosurnament qualifiers results spreadsheet module.
"""

import pytest

from discord.ext import commands

from bot.modules import module as base
from bot.modules.tosurnament.bracket import qualifiers_results_spreadsheet as module_to_test
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.spreadsheets.qualifiers_results_spreadsheet import QualifiersResultsSpreadsheet
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.bracket.qualifiers_results_spreadsheet"


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, qualifiers_results_spreadsheet_id=1))
    qualifiers_results_spreadsheet = QualifiersResultsSpreadsheet(id=1)
    mock_bot.session.add_stub(qualifiers_results_spreadsheet)
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    return cog, mock_bot, qualifiers_results_spreadsheet


@pytest.mark.asyncio
async def test_set_qualifiers_results_spreadsheet(mocker):
    """Sets bracket spreadsheets."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1))
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    spreadsheet_id = "abcd1234"
    sheet_name = "a sheet name"

    await cog.set_qualifiers_results_spreadsheet(cog, mock_ctx, spreadsheet_id, sheet_name=sheet_name)
    update_expected = [
        mocker.call(tosurnament_mock.Matcher(Bracket(tournament_id=1, qualifiers_results_spreadsheet_id=1))),
        mocker.call(
            tosurnament_mock.Matcher(QualifiersResultsSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name))
        ),
    ]
    assert mock_bot.session.update.call_args_list == update_expected

    await cog.set_qualifiers_results_spreadsheet(cog, mock_ctx, spreadsheet_id, sheet_name="")
    update_expected = [
        mocker.call(
            tosurnament_mock.Matcher(QualifiersResultsSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name))
        ),
    ]
    assert mock_bot.session.update.call_args_list[2:] == update_expected


@pytest.mark.asyncio
async def test_set_qualifiers_results_spreadsheet_values(mocker):
    """Sets qualifiers results spreadsheet values."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, qualifiers_results_spreadsheet_id=1))
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    sheet_name = "a sheet name"
    with pytest.raises(base.NoSpreadsheet):
        await cog.set_qualifiers_results_spreadsheet_values(mock_ctx, {"sheet_name": sheet_name})

    qualifiers_results_spreadsheet = QualifiersResultsSpreadsheet(id=1)
    mock_bot.session.add_stub(qualifiers_results_spreadsheet)
    assert qualifiers_results_spreadsheet.sheet_name != sheet_name
    await cog.set_qualifiers_results_spreadsheet_values(mock_ctx, {"sheet_name": sheet_name})
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersResultsSpreadsheet(sheet_name=sheet_name))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_results_spreadsheet_range_value(mocker):
    """Sets qualifiers results spreadsheet range value."""
    cog, mock_bot, qualifiers_results_spreadsheet = init_mocks()
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    range_name = "range_score"
    range_value = "A"
    mocker.patch(MODULE_TO_TEST + ".spreadsheet.check_range", mocker.Mock(return_value=False))
    with pytest.raises(commands.UserInputError):
        await cog.set_qualifiers_results_spreadsheet_range_value(mock_ctx, range_name, range_value)

    mocker.patch(MODULE_TO_TEST + ".spreadsheet.check_range", mocker.Mock(return_value=True))
    assert qualifiers_results_spreadsheet.range_score != range_value
    await cog.set_qualifiers_results_spreadsheet_range_value(mock_ctx, range_name, range_value)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersResultsSpreadsheet(range_score=range_value))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_results_spreadsheet_sheet_name(mocker):
    """Sets the qualifiers results spreasheet's sheet name."""
    cog, mock_bot, qualifiers_results_spreadsheet = init_mocks()
    sheet_name = "a sheet name"
    assert qualifiers_results_spreadsheet.sheet_name != sheet_name
    await cog.set_qualifiers_results_spreadsheet_sheet_name(
        cog, tosurnament_mock.CtxMock(mock_bot), sheet_name=sheet_name
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersResultsSpreadsheet(sheet_name=sheet_name))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_results_spreadsheet_range_osu_id(mocker):
    """Sets the qualifiers_results spreasheet's range osu_id."""
    cog, mock_bot, qualifiers_results_spreadsheet = init_mocks()
    range_osu_id = "A"
    assert qualifiers_results_spreadsheet.range_osu_id != range_osu_id
    await cog.set_qualifiers_results_spreadsheet_range_osu_id(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_osu_id
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersResultsSpreadsheet(range_osu_id=range_osu_id))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_results_spreadsheet_range_score(mocker):
    """Sets the qualifiers_results spreasheet's range score."""
    cog, mock_bot, qualifiers_results_spreadsheet = init_mocks()
    range_score = "A"
    assert qualifiers_results_spreadsheet.range_score != range_score
    await cog.set_qualifiers_results_spreadsheet_range_score(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_score
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersResultsSpreadsheet(range_score=range_score))
    )
