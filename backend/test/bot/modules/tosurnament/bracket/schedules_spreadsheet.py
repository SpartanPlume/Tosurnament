"""
All tests concerning the Tosurnament schedules spreadsheet module.
"""

import pytest

from discord.ext import commands

from bot.modules import module as base
from bot.modules.tosurnament.bracket import schedules_spreadsheet as module_to_test
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.spreadsheets.schedules_spreadsheet import SchedulesSpreadsheet
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.bracket.schedules_spreadsheet"


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, schedules_spreadsheet_id=1))
    schedules_spreadsheet = SchedulesSpreadsheet(id=1)
    mock_bot.session.add_stub(schedules_spreadsheet)
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    return cog, mock_bot, schedules_spreadsheet


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet(mocker):
    """Sets bracket spreadsheets."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1))
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    spreadsheet_id = "abcd1234"
    sheet_name = "a sheet name"

    await cog.set_schedules_spreadsheet(cog, mock_ctx, spreadsheet_id, sheet_name=sheet_name)
    update_expected = [
        mocker.call(tosurnament_mock.Matcher(Bracket(tournament_id=1, schedules_spreadsheet_id=1))),
        mocker.call(
            tosurnament_mock.Matcher(SchedulesSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name))
        ),
    ]
    assert mock_bot.session.update.call_args_list == update_expected

    await cog.set_schedules_spreadsheet(cog, mock_ctx, spreadsheet_id, sheet_name="")
    update_expected = [
        mocker.call(
            tosurnament_mock.Matcher(SchedulesSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name))
        ),
    ]
    assert mock_bot.session.update.call_args_list[2:] == update_expected


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_values(mocker):
    """Sets schedules spreadsheet values."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, schedules_spreadsheet_id=1))
    cog = tosurnament_mock.mock_cog(module_to_test.get_class(mock_bot))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    sheet_name = "a sheet name"
    with pytest.raises(base.NoSpreadsheet):
        await cog.set_schedules_spreadsheet_values(mock_ctx, {"sheet_name": sheet_name})

    schedules_spreadsheet = SchedulesSpreadsheet(id=1)
    mock_bot.session.add_stub(schedules_spreadsheet)
    assert schedules_spreadsheet.sheet_name != sheet_name
    await cog.set_schedules_spreadsheet_values(mock_ctx, {"sheet_name": sheet_name})
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(sheet_name=sheet_name))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_value(mocker):
    """Sets schedules spreadsheet range value."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    range_name = "range_match_id"
    range_value = "A"
    mocker.patch(MODULE_TO_TEST + ".spreadsheet.check_range", mocker.Mock(return_value=False))
    with pytest.raises(commands.UserInputError):
        await cog.set_schedules_spreadsheet_range_value(mock_ctx, range_name, range_value)

    mocker.patch(MODULE_TO_TEST + ".spreadsheet.check_range", mocker.Mock(return_value=True))
    assert schedules_spreadsheet.range_match_id != range_value
    await cog.set_schedules_spreadsheet_range_value(mock_ctx, range_name, range_value)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_match_id=range_value))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_sheet_name(mocker):
    """Sets the schedules spreasheet's sheet name."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    sheet_name = "a sheet name"
    assert schedules_spreadsheet.sheet_name != sheet_name
    await cog.set_schedules_spreadsheet_sheet_name(cog, tosurnament_mock.CtxMock(mock_bot), sheet_name=sheet_name)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(sheet_name=sheet_name))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_date_format(mocker):
    """Sets the schedules spreasheet's date format."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    date_format = "%d %m"
    assert schedules_spreadsheet.date_format != date_format
    await cog.set_schedules_spreadsheet_date_format(cog, tosurnament_mock.CtxMock(mock_bot), date_format=date_format)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(date_format=date_format))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_staff_is_range(mocker):
    """Sets the schedules spreasheet's staff can be in multiple cells."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    use_range = True
    assert schedules_spreadsheet.use_range != use_range
    await cog.set_schedules_spreadsheet_staff_is_range(cog, tosurnament_mock.CtxMock(mock_bot), use_range=use_range)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(SchedulesSpreadsheet(use_range=use_range)))


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_match_id(mocker):
    """Sets the schedules spreasheet's range match id."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    range_match_id = "A"
    assert schedules_spreadsheet.range_match_id != range_match_id
    await cog.set_schedules_spreadsheet_range_match_id(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_match_id
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_match_id=range_match_id))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_team1(mocker):
    """Sets the schedules spreasheet's range team1."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    range_team1 = "A"
    assert schedules_spreadsheet.range_team1 != range_team1
    await cog.set_schedules_spreadsheet_range_team1(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_team1)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_team1=range_team1))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_team2(mocker):
    """Sets the schedules spreasheet's range team2."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    range_team2 = "A"
    assert schedules_spreadsheet.range_team2 != range_team2
    await cog.set_schedules_spreadsheet_range_team2(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_team2)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_team2=range_team2))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_score_team1(mocker):
    """Sets the schedules spreasheet's range score_team1."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    range_score_team1 = "A"
    assert schedules_spreadsheet.range_score_team1 != range_score_team1
    await cog.set_schedules_spreadsheet_range_score_team1(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_score_team1
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_score_team1=range_score_team1))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_score_team2(mocker):
    """Sets the schedules spreasheet's range score_team2."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    range_score_team2 = "A"
    assert schedules_spreadsheet.range_score_team2 != range_score_team2
    await cog.set_schedules_spreadsheet_range_score_team2(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_score_team2
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_score_team2=range_score_team2))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_date(mocker):
    """Sets the schedules spreasheet's range date."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    range_date = "A"
    assert schedules_spreadsheet.range_date != range_date
    await cog.set_schedules_spreadsheet_range_date(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_date)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_date=range_date))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_time(mocker):
    """Sets the schedules spreasheet's range time."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    range_time = "A"
    assert schedules_spreadsheet.range_time != range_time
    await cog.set_schedules_spreadsheet_range_time(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_time)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_time=range_time))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_referee(mocker):
    """Sets the schedules spreasheet's range referee."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    range_referee = "A"
    assert schedules_spreadsheet.range_referee != range_referee
    await cog.set_schedules_spreadsheet_range_referee(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_referee)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_referee=range_referee))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_streamer(mocker):
    """Sets the schedules spreasheet's range streamer."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    range_streamer = "A"
    assert schedules_spreadsheet.range_streamer != range_streamer
    await cog.set_schedules_spreadsheet_range_streamer(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_streamer
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_streamer=range_streamer))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_commentator(mocker):
    """Sets the schedules spreasheet's range commentator."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    range_commentator = "A"
    assert schedules_spreadsheet.range_commentator != range_commentator
    await cog.set_schedules_spreadsheet_range_commentator(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_commentator
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_commentator=range_commentator))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_mp_links(mocker):
    """Sets the schedules spreasheet's range mp_links."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    range_mp_links = "A"
    assert schedules_spreadsheet.range_mp_links != range_mp_links
    await cog.set_schedules_spreadsheet_range_mp_links(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_mp_links
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_mp_links=range_mp_links))
    )


@pytest.mark.asyncio
async def test_show_schedules_spreadsheet_settings():
    """Shows the schedules spreadsheet settings of the current bracket."""
    cog, mock_bot, schedules_spreadsheet = init_mocks()
    schedules_spreadsheet.range_match_id = "A2:A"
    expected_output = "**__Schedules spreadsheet settings:__**\n\n"
    expected_output += "__range_match_id__: `A2:A`\n"
    expected_output += "__range_team1__: `Undefined`\n"
    expected_output += "__range_score_team1__: `Undefined`\n"
    expected_output += "__range_score_team2__: `Undefined`\n"
    expected_output += "__range_team2__: `Undefined`\n"
    expected_output += "__range_date__: `Undefined`\n"
    expected_output += "__range_time__: `Undefined`\n"
    expected_output += "__range_referee__: `Undefined`\n"
    expected_output += "__range_streamer__: `Undefined`\n"
    expected_output += "__range_commentator__: `Undefined`\n"
    expected_output += "__range_mp_links__: `Undefined`\n"
    expected_output += "__date_format__: `Undefined`\n"
    expected_output += "__use_range__: `False`\n"
    expected_output += "__max_referee__: `1`\n"
    expected_output += "__max_streamer__: `1`\n"
    expected_output += "__max_commentator__: `2`\n"
    expected_output += "__id__: `1`\n"
    expected_output += "__spreadsheet_id__: `Undefined`\n"
    expected_output += "__sheet_name__: `Undefined`\n"
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name, "show_schedules_spreadsheet_settings")
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, command=mock_command)
    await cog.show_schedules_spreadsheet_settings(cog, mock_ctx)
    mock_ctx.send.assert_called_once_with(expected_output)
