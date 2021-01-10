"""
All tests concerning the Tosurnament bracket module.
"""

import pytest

import datetime

from discord.ext import commands
from bot.modules import module as base
from bot.modules.tosurnament import module as tosurnament
from bot.modules.tosurnament import bracket as bracket_module
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.players_spreadsheet import PlayersSpreadsheet
from common.databases.schedules_spreadsheet import SchedulesSpreadsheet
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.bracket"


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    bracket = Bracket(id=1, tournament_id=1)
    mock_bot.session.add_stub(bracket)
    cog = tosurnament_mock.mock_cog(bracket_module.get_class(mock_bot))
    return cog, mock_bot, bracket


@pytest.mark.asyncio
async def test_set_bracket_values(mocker):
    """Puts the input values into the corresponding bracket."""
    cog, mock_bot, bracket = init_mocks()
    bracket_name = "Bracket name"
    assert bracket.name != bracket_name
    await cog.set_bracket_values(tosurnament_mock.CtxMock(mock_bot), {"name": bracket_name})
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Bracket(tournament_id=1, name=bracket_name))
    )
    cog.send_reply.assert_called_once_with(mocker.ANY, mocker.ANY, "success", bracket_name)


@pytest.mark.asyncio
async def test_set_challonge(mocker):
    """Sets the challonge."""
    cog, mock_bot, bracket = init_mocks()
    challonge_id = "challonge_id"
    challonge_id_url = "https://www.challonge.com/" + challonge_id + "/"
    assert bracket.challonge != challonge_id
    await cog.set_challonge(cog, tosurnament_mock.CtxMock(mock_bot), challonge_tournament=challonge_id_url)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Bracket(tournament_id=1, challonge=challonge_id))
    )


@pytest.mark.asyncio
async def test_set_registration_end_date_invalid_date(mocker):
    """Sets the registration end date."""
    cog, mock_bot, bracket = init_mocks()
    date = "abcdef"
    with pytest.raises(commands.UserInputError):
        await cog.set_registration_end(cog, tosurnament_mock.CtxMock(mock_bot), date=date)


@pytest.mark.asyncio
async def test_set_registration_end_date(mocker):
    """Sets the registration end date."""
    cog, mock_bot, bracket = init_mocks()
    date = "1 week"
    assert bracket.registration_end_date != date
    await cog.set_registration_end(cog, tosurnament_mock.CtxMock(mock_bot), date=date)
    new_date = datetime.datetime.now() + datetime.timedelta(days=7)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(
            Bracket(tournament_id=1, registration_end_date=new_date.strftime(tosurnament.DATABASE_DATE_FORMAT))
        )
    )


@pytest.mark.asyncio
async def test_set_bracket_spreadsheet(mocker):
    """Sets bracket spreadsheets."""
    cog, mock_bot, bracket = init_mocks()
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)
    spreadsheet_id = "abcd1234"
    sheet_name = "a sheet name"
    assert bracket.players_spreadsheet_id <= 0
    assert bracket.schedules_spreadsheet_id <= 0

    await cog.set_bracket_spreadsheet(mock_ctx, "players", spreadsheet_id, "")
    update_expected = [
        mocker.call(tosurnament_mock.Matcher(Bracket(tournament_id=1, players_spreadsheet_id=1))),
        mocker.call(tosurnament_mock.Matcher(PlayersSpreadsheet(spreadsheet_id=spreadsheet_id))),
    ]
    assert mock_bot.session.update.call_args_list == update_expected
    await cog.set_bracket_spreadsheet(mock_ctx, "players", spreadsheet_id, sheet_name)
    update_expected = [
        mocker.call(tosurnament_mock.Matcher(PlayersSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name))),
    ]
    assert mock_bot.session.update.call_args_list[2:] == update_expected

    await cog.set_bracket_spreadsheet(mock_ctx, "schedules", spreadsheet_id, "")
    update_expected = [
        mocker.call(
            tosurnament_mock.Matcher(Bracket(tournament_id=1, players_spreadsheet_id=1, schedules_spreadsheet_id=1))
        ),
        mocker.call(tosurnament_mock.Matcher(SchedulesSpreadsheet(spreadsheet_id=spreadsheet_id))),
    ]
    assert mock_bot.session.update.call_args_list[3:] == update_expected


@pytest.mark.asyncio
async def test_set_spreadsheet_values(mocker):
    """Sets spreadsheet values."""
    cog, mock_bot, bracket = init_mocks()
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)
    bracket.players_spreadsheet_id = 1
    bracket.schedules_spreadsheet_id = 1
    schedules_spreadsheet = SchedulesSpreadsheet(id=1)
    mock_bot.session.add_stub(schedules_spreadsheet)
    spreadsheet_id = "abcd1234"
    sheet_name = "a sheet name"

    assert schedules_spreadsheet.spreadsheet_id != spreadsheet_id
    await cog.set_spreadsheet_values(mock_ctx, "schedules", {"spreadsheet_id": spreadsheet_id})
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(spreadsheet_id=spreadsheet_id))
    )

    assert schedules_spreadsheet.sheet_name != sheet_name
    await cog.set_schedules_spreadsheet_values(mock_ctx, {"sheet_name": sheet_name})
    update_expected = [
        mocker.call(
            tosurnament_mock.Matcher(SchedulesSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name))
        )
    ]
    assert mock_bot.session.update.call_args_list[1:] == update_expected

    with pytest.raises(base.NoSpreadsheet):
        await cog.set_players_spreadsheet_values(mock_ctx, {"sheet_name": sheet_name})

    players_spreadsheet = PlayersSpreadsheet(id=1)
    mock_bot.session.add_stub(players_spreadsheet)
    assert players_spreadsheet.sheet_name != sheet_name
    await cog.set_players_spreadsheet_values(mock_ctx, {"sheet_name": sheet_name})
    update_expected = [mocker.call(tosurnament_mock.Matcher(PlayersSpreadsheet(sheet_name=sheet_name)))]
    assert mock_bot.session.update.call_args_list[2:] == update_expected


@pytest.mark.asyncio
async def test_clear_player_role(mocker):
    """Removes the player roles of all players not present in the challonge."""
    # TODO


@pytest.mark.asyncio
async def test_copy_bracket_not_enough_bracket(mocker):
    """Copies a bracket settings to another one, but there is only one bracket."""
    cog, mock_bot, _ = init_mocks()
    with pytest.raises(commands.UserInputError):
        await cog.copy_bracket(cog, tosurnament_mock.CtxMock(mock_bot), 1, 2)


@pytest.mark.asyncio
async def test_copy_bracket_wrong_index(mocker):
    """Copies a bracket settings to another one, but input indexes are wrong."""
    cog, mock_bot, _ = init_mocks()
    mock_bot.session.add_stub(Bracket(id=2, tournament_id=1))

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
    sheet_name = "a sheet name"
    schedules_spreadsheet = SchedulesSpreadsheet(
        id=1, sheet_name=sheet_name + " s", range_match_id="B2:B", range_team1="C2:C"
    )
    mock_bot.session.add_stub(schedules_spreadsheet)

    mock_bot.session.add_stub(Bracket(id=2, tournament_id=1, schedules_spreadsheet_id=2))
    mock_bot.session.add_stub(
        SchedulesSpreadsheet(id=2, sheet_name=sheet_name, range_match_id="A1:A", range_score_team1="B1:B")
    )

    cog = tosurnament_mock.mock_cog(bracket_module.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    await cog.copy_bracket(cog, mock_ctx, 1, 2)
    assert len(mock_bot.session.tables[Bracket.__tablename__]) == 2
    assert mock_bot.session.tables[Bracket.__tablename__][1].post_result_channel_id == 1
    assert len(mock_bot.session.tables[SchedulesSpreadsheet.__tablename__]) == 2
    assert mock_bot.session.tables[SchedulesSpreadsheet.__tablename__][1] != tosurnament_mock.Matcher(
        schedules_spreadsheet
    )
    schedules_spreadsheet.sheet_name = sheet_name
    assert mock_bot.session.tables[SchedulesSpreadsheet.__tablename__][1] == tosurnament_mock.Matcher(
        schedules_spreadsheet
    )
    assert PlayersSpreadsheet.__tablename__ not in mock_bot.session.tables

    players_spreadsheet = PlayersSpreadsheet(id=1, range_team="A1:A")
    mock_bot.session.add_stub(players_spreadsheet)

    await cog.copy_bracket(cog, mock_ctx, 1, 2)
    assert len(mock_bot.session.tables[PlayersSpreadsheet.__tablename__]) == 2
    assert mock_bot.session.tables[PlayersSpreadsheet.__tablename__][1] == tosurnament_mock.Matcher(players_spreadsheet)
