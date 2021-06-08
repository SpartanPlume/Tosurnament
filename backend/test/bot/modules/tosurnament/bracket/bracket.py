"""
All tests concerning the Tosurnament bracket module.
"""

import pytest
from unittest import mock

import datetime

from discord.ext import commands
from bot.modules import module as base
from bot.modules.tosurnament import module as tosurnament
from bot.modules.tosurnament.bracket import bracket as bracket_module
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.spreadsheets.players_spreadsheet import PlayersSpreadsheet
from common.databases.spreadsheets.schedules_spreadsheet import SchedulesSpreadsheet
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.bracket.bracket"
BRACKET1_NAME = "Bracket 1"
PARTICIPANT_LIST = [
    "Participant 1",
    "ParTiCIpanT 2",
    "participant 3",
    "PARTICIPANT 4",
    tosurnament_mock.DEFAULT_USER_STUB.osu_name,
]


def init_mocks(n_of_brackets=1):
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    for i in range(n_of_brackets):
        bracket = Bracket(id=i + 1, tournament_id=1, name=("Bracket " + str(i + 1)))
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
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", bracket_name)


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
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Bracket(tournament_id=1, role_id=role.id, name=BRACKET1_NAME))
    )


@pytest.mark.asyncio
async def test_set_current_bracket_round(mocker):
    """Sets the round of the current bracket."""
    cog, mock_bot, bracket = init_mocks()
    current_round = "RO64"
    assert bracket.current_round != current_round
    await cog.set_current_bracket_round(cog, tosurnament_mock.CtxMock(mock_bot), current_round=current_round)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Bracket(tournament_id=1, current_round=current_round, name=BRACKET1_NAME))
    )


@pytest.mark.asyncio
async def test_set_post_result_channel(mocker):
    """Sets the post result channel."""
    cog, mock_bot, bracket = init_mocks()
    channel = tosurnament_mock.ChannelMock(324769)
    assert bracket.post_result_channel_id != channel.id
    await cog.set_post_result_channel(cog, tosurnament_mock.CtxMock(mock_bot), channel=channel)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Bracket(tournament_id=1, post_result_channel_id=channel.id, name=BRACKET1_NAME))
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
        tosurnament_mock.Matcher(Bracket(tournament_id=1, challonge=challonge_id, name=BRACKET1_NAME))
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
    new_date = datetime.datetime.now() + datetime.timedelta(days=7)
    assert bracket.registration_end_date != new_date.strftime(tosurnament.DATABASE_DATE_FORMAT)
    parse_date_mock = mocker.Mock(return_value=new_date)
    with mock.patch.object(Tournament, "parse_date", new=parse_date_mock):
        await cog.set_registration_end(cog, tosurnament_mock.CtxMock(mock_bot), date=date)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(
            Bracket(
                tournament_id=1,
                registration_end_date=new_date.strftime(tosurnament.DATABASE_DATE_FORMAT),
                name=BRACKET1_NAME,
            )
        )
    )


def test_is_player_in_challonge_not_a_participant(mocker):
    """ "Gets the team_info (if applicable) and the player name of the player if they are a running participant."""
    cog = tosurnament_mock.mock_cog(bracket_module.get_class(tosurnament_mock.BotMock()))
    member_name = "abvdsrjgfkh"
    member = tosurnament_mock.UserMock(user_name=member_name)
    team_info, player_name = cog.is_player_in_challonge(member, [], PARTICIPANT_LIST)
    assert not team_info
    assert not player_name


def test_is_player_in_challonge_no_teams_info(mocker):
    """ "Gets the team_info (if applicable) and the player name of the player if they are a running participant."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(bracket_module.get_class(mock_bot))
    mock_bot.session.add_stub(tosurnament_mock.DEFAULT_USER_STUB)
    team_info, player_name = cog.is_player_in_challonge(tosurnament_mock.DEFAULT_USER_MOCK, [], PARTICIPANT_LIST)
    assert not team_info
    assert player_name == tosurnament_mock.DEFAULT_USER_STUB.osu_name


@pytest.mark.asyncio
async def test_is_player_in_challonge(mocker):
    """Gets the team_info (if applicable) and the player name of the player if they are a running participant."""
    # TODO
    cog = tosurnament_mock.mock_cog(bracket_module.get_class(tosurnament_mock.BotMock()))
    member = tosurnament_mock.UserMock()
    teams_info = []
    participants = []
    cog.is_player_in_challonge(member, teams_info, participants)


@pytest.mark.asyncio
async def test_clear_player_role(mocker):
    """Removes the player roles of all players not present in the challonge."""
    # TODO


@pytest.mark.asyncio
async def test_clear_player_role_multi_brackets_no_specified_bracket(mocker):
    """Removes the player roles of all players not present in the challonge."""
    cog, mock_bot, _ = init_mocks(2)
    await cog.clear_player_role(cog, tosurnament_mock.CtxMock(mock_bot))
    cog.send_reply.assert_called_once_with(mocker.ANY, "default", "1: `Bracket 1`\n2: `Bracket 2`\n")


@pytest.mark.asyncio
async def test_clear_player_role_no_challonge(mocker):
    """Removes the player roles of all players not present in the challonge."""
    cog, mock_bot, _ = init_mocks()
    with pytest.raises(base.NoChallonge):
        await cog.clear_player_role(cog, tosurnament_mock.CtxMock(mock_bot))


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
    mock_bot.session.add_stub(Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))

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
