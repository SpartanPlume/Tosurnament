"""
All tests concerning the Tosurnament bracket module.
"""

import pytest

from discord.ext import commands
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
CHALLONGE_ID = "challonge_id"
CHALLONGE_ID_URL = "https://www.challonge.com/" + CHALLONGE_ID + "/"


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
async def test_set_challonge(mocker):
    """Sets the challonge."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1))
    cog = tosurnament_mock.mock_cog(bracket.get_class(mock_bot))

    await cog.set_challonge(cog, tosurnament_mock.CtxMock(mock_bot), challonge_tournament=CHALLONGE_ID_URL)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Bracket(tournament_id=1, challonge=CHALLONGE_ID))
    )
    cog.send_reply.assert_called_once_with(mocker.ANY, mocker.ANY, "success", CHALLONGE_ID)


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
async def test_clear_player_role(mocker):
    """Removes the player roles of all players not present in the challonge."""
    # TODO


@pytest.mark.asyncio
async def test_copy_bracket_not_enough_bracket(mocker):
    """Copies a bracket settings to another one, but there is only one bracket."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1))
    cog = tosurnament_mock.mock_cog(bracket.get_class(mock_bot))

    with pytest.raises(commands.UserInputError):
        await cog.copy_bracket(cog, tosurnament_mock.CtxMock(mock_bot), 1, 2)


@pytest.mark.asyncio
async def test_copy_bracket_wrong_index(mocker):
    """Copies a bracket settings to another one, but input indexes are wrong."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1))
    mock_bot.session.add_stub(Bracket(id=2, tournament_id=1))
    cog = tosurnament_mock.mock_cog(bracket.get_class(mock_bot))

    with pytest.raises(commands.UserInputError):
        await cog.copy_bracket(cog, tosurnament_mock.CtxMock(mock_bot), 1, 3)

    with pytest.raises(commands.UserInputError):
        await cog.copy_bracket(cog, tosurnament_mock.CtxMock(mock_bot), 0, 2)


@pytest.mark.asyncio
async def test_copy_bracket(mocker):
    """Copies a bracket settings to another one."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))

    mock_bot.session.add_stub(
        Bracket(id=1, tournament_id=1, schedules_spreadsheet_id=1, players_spreadsheet_id=1, post_result_channel_id=1)
    )
    schedules_spreadsheet = SchedulesSpreadsheet(
        id=1, sheet_name=SHEET_NAME + " s", range_match_id="B2:B", range_team1="C2:C"
    )
    mock_bot.session.add_stub(schedules_spreadsheet)

    mock_bot.session.add_stub(Bracket(id=2, tournament_id=1, schedules_spreadsheet_id=2))
    mock_bot.session.add_stub(
        SchedulesSpreadsheet(id=2, sheet_name=SHEET_NAME, range_match_id="A1:A", range_score_team1="B1:B")
    )

    cog = tosurnament_mock.mock_cog(bracket.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    await cog.copy_bracket(cog, mock_ctx, 1, 2)
    assert len(mock_bot.session.tables[Bracket.__tablename__]) == 2
    assert mock_bot.session.tables[Bracket.__tablename__][1].post_result_channel_id == 1
    assert len(mock_bot.session.tables[SchedulesSpreadsheet.__tablename__]) == 2
    assert mock_bot.session.tables[SchedulesSpreadsheet.__tablename__][1] != tosurnament_mock.Matcher(
        schedules_spreadsheet
    )
    schedules_spreadsheet.sheet_name = SHEET_NAME
    assert mock_bot.session.tables[SchedulesSpreadsheet.__tablename__][1] == tosurnament_mock.Matcher(
        schedules_spreadsheet
    )
    assert PlayersSpreadsheet.__tablename__ not in mock_bot.session.tables

    players_spreadsheet = PlayersSpreadsheet(id=1, range_team="A1:A")
    mock_bot.session.add_stub(players_spreadsheet)

    await cog.copy_bracket(cog, mock_ctx, 1, 2)
    assert len(mock_bot.session.tables[PlayersSpreadsheet.__tablename__]) == 2
    assert mock_bot.session.tables[PlayersSpreadsheet.__tablename__][1] == tosurnament_mock.Matcher(players_spreadsheet)
