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
from common.databases.qualifiers_spreadsheet import QualifiersSpreadsheet
from common.databases.qualifiers_results_spreadsheet import QualifiersResultsSpreadsheet
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.bracket"


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    bracket = Bracket(id=1, tournament_id=1)
    mock_bot.session.add_stub(bracket)
    cog = tosurnament_mock.mock_cog(bracket_module.get_class(mock_bot))
    return cog, mock_bot, bracket


def init_schedules_spreadsheet_mocks():
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, schedules_spreadsheet_id=1))
    schedules_spreadsheet = SchedulesSpreadsheet(id=1)
    mock_bot.session.add_stub(schedules_spreadsheet)
    cog = tosurnament_mock.mock_cog(bracket_module.get_class(mock_bot))
    return cog, mock_bot, schedules_spreadsheet


def init_players_spreadsheet_mocks():
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, players_spreadsheet_id=1))
    players_spreadsheet = PlayersSpreadsheet(id=1)
    mock_bot.session.add_stub(players_spreadsheet)
    cog = tosurnament_mock.mock_cog(bracket_module.get_class(mock_bot))
    return cog, mock_bot, players_spreadsheet


def init_qualifiers_spreadsheet_mocks():
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, qualifiers_spreadsheet_id=1))
    qualifiers_spreadsheet = QualifiersSpreadsheet(id=1)
    mock_bot.session.add_stub(qualifiers_spreadsheet)
    cog = tosurnament_mock.mock_cog(bracket_module.get_class(mock_bot))
    return cog, mock_bot, qualifiers_spreadsheet


def init_qualifiers_results_spreadsheet_mocks():
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, qualifiers_results_spreadsheet_id=1))
    qualifiers_results_spreadsheet = QualifiersResultsSpreadsheet(id=1)
    mock_bot.session.add_stub(qualifiers_results_spreadsheet)
    cog = tosurnament_mock.mock_cog(bracket_module.get_class(mock_bot))
    return cog, mock_bot, qualifiers_results_spreadsheet


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
async def test_set_bracket_name(mocker):
    """Sets the bracket name."""
    cog, mock_bot, bracket = init_mocks()
    bracket_name = "Bracket name"
    assert bracket.name != bracket_name
    await cog.set_bracket_name(cog, tosurnament_mock.CtxMock(mock_bot), name=bracket_name)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Bracket(tournament_id=1, name=bracket_name))
    )


@pytest.mark.asyncio
async def test_set_bracket_role(mocker):
    """Sets the bracket role."""
    cog, mock_bot, bracket = init_mocks()
    role = tosurnament_mock.RoleMock("role", 324987)
    assert bracket.role_id != role.id
    await cog.set_bracket_role(cog, tosurnament_mock.CtxMock(mock_bot), role=role)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Bracket(tournament_id=1, role_id=role.id)))


@pytest.mark.asyncio
async def test_set_current_bracket_round(mocker):
    """Sets the round of the current bracket."""
    cog, mock_bot, bracket = init_mocks()
    current_round = "RO64"
    assert bracket.current_round != current_round
    await cog.set_current_bracket_round(cog, tosurnament_mock.CtxMock(mock_bot), current_round=current_round)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Bracket(tournament_id=1, current_round=current_round))
    )


@pytest.mark.asyncio
async def test_set_post_result_channel(mocker):
    """Sets the post result channel."""
    cog, mock_bot, bracket = init_mocks()
    channel = tosurnament_mock.ChannelMock(324769)
    assert bracket.post_result_channel_id != channel.id
    await cog.set_post_result_channel(cog, tosurnament_mock.CtxMock(mock_bot), channel=channel)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Bracket(tournament_id=1, post_result_channel_id=channel.id))
    )


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
async def test_set_registration_end_date_value_error(mocker):
    """Sets the registration end date."""
    cog, mock_bot, bracket = init_mocks()
    mocker.patch("common.databases.tournament.dateparser.parse", mocker.Mock(side_effect=ValueError()))
    date = "1 week"
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
async def test_clear_player_role(mocker):
    """Removes the player roles of all players not present in the challonge."""
    # TODO


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
async def test_set_schedules_spreadsheet_sheet_name(mocker):
    """Sets the schedules spreasheet's sheet name."""
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
    sheet_name = "a sheet name"
    assert schedules_spreadsheet.sheet_name != sheet_name
    await cog.set_schedules_spreadsheet_sheet_name(cog, tosurnament_mock.CtxMock(mock_bot), sheet_name=sheet_name)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(sheet_name=sheet_name))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_date_format(mocker):
    """Sets the schedules spreasheet's date format."""
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
    date_format = "%d %m"
    assert schedules_spreadsheet.date_format != date_format
    await cog.set_schedules_spreadsheet_date_format(cog, tosurnament_mock.CtxMock(mock_bot), date_format=date_format)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(date_format=date_format))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_staff_is_range(mocker):
    """Sets the schedules spreasheet's staff can be in multiple cells."""
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
    use_range = True
    assert schedules_spreadsheet.use_range != use_range
    await cog.set_schedules_spreadsheet_staff_is_range(cog, tosurnament_mock.CtxMock(mock_bot), use_range=use_range)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(SchedulesSpreadsheet(use_range=use_range)))


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_match_id(mocker):
    """Sets the schedules spreasheet's range match id."""
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
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
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
    range_team1 = "A"
    assert schedules_spreadsheet.range_team1 != range_team1
    await cog.set_schedules_spreadsheet_range_team1(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_team1)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_team1=range_team1))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_team2(mocker):
    """Sets the schedules spreasheet's range team2."""
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
    range_team2 = "A"
    assert schedules_spreadsheet.range_team2 != range_team2
    await cog.set_schedules_spreadsheet_range_team2(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_team2)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_team2=range_team2))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_score_team1(mocker):
    """Sets the schedules spreasheet's range score_team1."""
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
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
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
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
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
    range_date = "A"
    assert schedules_spreadsheet.range_date != range_date
    await cog.set_schedules_spreadsheet_range_date(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_date)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_date=range_date))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_time(mocker):
    """Sets the schedules spreasheet's range time."""
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
    range_time = "A"
    assert schedules_spreadsheet.range_time != range_time
    await cog.set_schedules_spreadsheet_range_time(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_time)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_time=range_time))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_referee(mocker):
    """Sets the schedules spreasheet's range referee."""
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
    range_referee = "A"
    assert schedules_spreadsheet.range_referee != range_referee
    await cog.set_schedules_spreadsheet_range_referee(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_referee)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_referee=range_referee))
    )


@pytest.mark.asyncio
async def test_set_schedules_spreadsheet_range_streamer(mocker):
    """Sets the schedules spreasheet's range streamer."""
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
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
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
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
    cog, mock_bot, schedules_spreadsheet = init_schedules_spreadsheet_mocks()
    range_mp_links = "A"
    assert schedules_spreadsheet.range_mp_links != range_mp_links
    await cog.set_schedules_spreadsheet_range_mp_links(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_mp_links
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(SchedulesSpreadsheet(range_mp_links=range_mp_links))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_sheet_name(mocker):
    """Sets the players spreasheet's sheet name."""
    cog, mock_bot, players_spreadsheet = init_players_spreadsheet_mocks()
    sheet_name = "a sheet name"
    assert players_spreadsheet.sheet_name != sheet_name
    await cog.set_players_spreadsheet_sheet_name(cog, tosurnament_mock.CtxMock(mock_bot), sheet_name=sheet_name)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(PlayersSpreadsheet(sheet_name=sheet_name)))


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_team_name(mocker):
    """Sets the players spreasheet's range team_name."""
    cog, mock_bot, players_spreadsheet = init_players_spreadsheet_mocks()
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
    cog, mock_bot, players_spreadsheet = init_players_spreadsheet_mocks()
    range_team = "A"
    assert players_spreadsheet.range_team != range_team
    await cog.set_players_spreadsheet_range_team(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_team)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(PlayersSpreadsheet(range_team=range_team)))


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_discord(mocker):
    """Sets the players spreasheet's range discord."""
    cog, mock_bot, players_spreadsheet = init_players_spreadsheet_mocks()
    range_discord = "A"
    assert players_spreadsheet.range_discord != range_discord
    await cog.set_players_spreadsheet_range_discord(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_discord)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_discord=range_discord))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_discord_id(mocker):
    """Sets the players spreasheet's range discord_id."""
    cog, mock_bot, players_spreadsheet = init_players_spreadsheet_mocks()
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
    cog, mock_bot, players_spreadsheet = init_players_spreadsheet_mocks()
    range_rank = "A"
    assert players_spreadsheet.range_rank != range_rank
    await cog.set_players_spreadsheet_range_rank(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_rank)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(PlayersSpreadsheet(range_rank=range_rank)))


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_bws_rank(mocker):
    """Sets the players spreasheet's range bws_rank."""
    cog, mock_bot, players_spreadsheet = init_players_spreadsheet_mocks()
    range_bws_rank = "A"
    assert players_spreadsheet.range_bws_rank != range_bws_rank
    await cog.set_players_spreadsheet_range_bws_rank(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_bws_rank)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_bws_rank=range_bws_rank))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_osu_id(mocker):
    """Sets the players spreasheet's range osu_id."""
    cog, mock_bot, players_spreadsheet = init_players_spreadsheet_mocks()
    range_osu_id = "A"
    assert players_spreadsheet.range_osu_id != range_osu_id
    await cog.set_players_spreadsheet_range_osu_id(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_osu_id)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_osu_id=range_osu_id))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_pp(mocker):
    """Sets the players spreasheet's range pp."""
    cog, mock_bot, players_spreadsheet = init_players_spreadsheet_mocks()
    range_pp = "A"
    assert players_spreadsheet.range_pp != range_pp
    await cog.set_players_spreadsheet_range_pp(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_pp)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(PlayersSpreadsheet(range_pp=range_pp)))


@pytest.mark.asyncio
async def test_set_players_spreadsheet_range_timezone(mocker):
    """Sets the players spreasheet's range timezone."""
    cog, mock_bot, players_spreadsheet = init_players_spreadsheet_mocks()
    range_timezone = "A"
    assert players_spreadsheet.range_timezone != range_timezone
    await cog.set_players_spreadsheet_range_timezone(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_timezone)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(range_timezone=range_timezone))
    )


@pytest.mark.asyncio
async def test_set_players_spreadsheet_max_range_for_teams(mocker):
    """Sets the players spreasheet's max range for teams."""
    cog, mock_bot, players_spreadsheet = init_players_spreadsheet_mocks()
    max_range_for_teams = 1
    assert players_spreadsheet.max_range_for_teams != max_range_for_teams
    await cog.set_players_spreadsheet_max_range_for_teams(
        cog, tosurnament_mock.CtxMock(mock_bot), length=max_range_for_teams
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(PlayersSpreadsheet(max_range_for_teams=max_range_for_teams))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_sheet_name(mocker):
    """Sets the qualifiers spreasheet's sheet name."""
    cog, mock_bot, qualifiers_spreadsheet = init_qualifiers_spreadsheet_mocks()
    sheet_name = "a sheet name"
    assert qualifiers_spreadsheet.sheet_name != sheet_name
    await cog.set_qualifiers_spreadsheet_sheet_name(cog, tosurnament_mock.CtxMock(mock_bot), sheet_name=sheet_name)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(sheet_name=sheet_name))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_range_lobby_id(mocker):
    """Sets the qualifiers spreasheet's range lobby_id."""
    cog, mock_bot, qualifiers_spreadsheet = init_qualifiers_spreadsheet_mocks()
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
    cog, mock_bot, qualifiers_spreadsheet = init_qualifiers_spreadsheet_mocks()
    range_teams = "A"
    assert qualifiers_spreadsheet.range_teams != range_teams
    await cog.set_qualifiers_spreadsheet_range_teams(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_teams)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(range_teams=range_teams))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_range_referee(mocker):
    """Sets the qualifiers spreasheet's range referee."""
    cog, mock_bot, qualifiers_spreadsheet = init_qualifiers_spreadsheet_mocks()
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
    cog, mock_bot, qualifiers_spreadsheet = init_qualifiers_spreadsheet_mocks()
    range_date = "A"
    assert qualifiers_spreadsheet.range_date != range_date
    await cog.set_qualifiers_spreadsheet_range_date(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_date)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(range_date=range_date))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_spreadsheet_range_time(mocker):
    """Sets the qualifiers spreasheet's range time."""
    cog, mock_bot, qualifiers_spreadsheet = init_qualifiers_spreadsheet_mocks()
    range_time = "A"
    assert qualifiers_spreadsheet.range_time != range_time
    await cog.set_qualifiers_spreadsheet_range_time(cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_time)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersSpreadsheet(range_time=range_time))
    )


@pytest.mark.asyncio
async def test_set_qualifiers_results_spreadsheet_range_osu_id(mocker):
    """Sets the qualifiers_results spreasheet's range osu_id."""
    cog, mock_bot, qualifiers_results_spreadsheet = init_qualifiers_results_spreadsheet_mocks()
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
    cog, mock_bot, qualifiers_results_spreadsheet = init_qualifiers_results_spreadsheet_mocks()
    range_score = "A"
    assert qualifiers_results_spreadsheet.range_score != range_score
    await cog.set_qualifiers_results_spreadsheet_range_score(
        cog, tosurnament_mock.CtxMock(mock_bot), cell_range=range_score
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(QualifiersResultsSpreadsheet(range_score=range_score))
    )


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
