"""
All tests concerning the Tosurnament bracket module.
"""

import pytest

from bot.modules import module as base
from bot.modules.tosurnament import bracket
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.players_spreadsheet import PlayersSpreadsheet
from common.databases.schedules_spreadsheet import SchedulesSpreadsheet
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.bracket"
BRACKET_NAME = "Bracket name"
BRACKET_NAME_2 = "Bracket name 2"
SPREADSHEET_ID = "abcd1234"
SHEET_NAME = "a sheet name"


@pytest.mark.asyncio
async def test_set_bracket_values(mocker):
    """Puts the input values into the corresponding bracket."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, name=BRACKET_NAME))
    cog = tosurnament_mock.mock_cog(bracket.get_class(mock_bot))

    await cog.set_bracket_values(tosurnament_mock.CtxMock(mock_bot), {"name": BRACKET_NAME_2})
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Bracket(tournament_id=1, name=BRACKET_NAME_2))
    )
    cog.send_reply.assert_called_once_with(mocker.ANY, mocker.ANY, "success", BRACKET_NAME_2)


@pytest.mark.asyncio
async def test_set_bracket_spreadsheet(mocker):
    """Sets bracket spreadsheets."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1))
    cog = tosurnament_mock.mock_cog(bracket.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    await cog.set_bracket_spreadsheet(mock_ctx, "players", SPREADSHEET_ID, "")
    update_expected = [
        mocker.call(tosurnament_mock.Matcher(Bracket(tournament_id=1, players_spreadsheet_id=1))),
        mocker.call(tosurnament_mock.Matcher(PlayersSpreadsheet(spreadsheet_id=SPREADSHEET_ID))),
    ]
    assert mock_bot.session.update.call_args_list == update_expected
    await cog.set_bracket_spreadsheet(mock_ctx, "players", SPREADSHEET_ID, SHEET_NAME)
    update_expected = [
        mocker.call(tosurnament_mock.Matcher(PlayersSpreadsheet(spreadsheet_id=SPREADSHEET_ID, sheet_name=SHEET_NAME))),
    ]
    assert mock_bot.session.update.call_args_list[2:] == update_expected

    await cog.set_bracket_spreadsheet(mock_ctx, "schedules", SPREADSHEET_ID, "")
    update_expected = [
        mocker.call(
            tosurnament_mock.Matcher(Bracket(tournament_id=1, players_spreadsheet_id=1, schedules_spreadsheet_id=1))
        ),
        mocker.call(tosurnament_mock.Matcher(SchedulesSpreadsheet(spreadsheet_id=SPREADSHEET_ID))),
    ]
    assert mock_bot.session.update.call_args_list[3:] == update_expected


@pytest.mark.asyncio
async def test_set_spreadsheet_values(mocker):
    """Sets spreadsheet values."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, schedules_spreadsheet_id=1, players_spreadsheet_id=1))
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=1))
    cog = tosurnament_mock.mock_cog(bracket.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    await cog.set_schedules_spreadsheet_values(mock_ctx, {"sheet_name": SHEET_NAME})
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(sheet_name=SHEET_NAME))
    )

    with pytest.raises(base.NoSpreadsheet):
        await cog.set_players_spreadsheet_values(mock_ctx, {"sheet_name": SHEET_NAME})

    mock_bot.session.add_stub(PlayersSpreadsheet(id=1))
    await cog.set_players_spreadsheet_values(mock_ctx, {"sheet_name": SHEET_NAME})


@pytest.mark.asyncio
async def test_copy_bracket(mocker):
    """Copies a bracket settings to another one."""
    # TODO
