"""
All tests concerning the Tosurnament tournament module.
"""

import pytest

import discord

from bot.modules.tosurnament import tournament
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.tournament"
BRACKET_NAME = "Bracket name"
BRACKET_NAME_2 = "Bracket name 2"


@pytest.mark.asyncio
async def test_create_bracket(mocker):
    """Creates a bracket."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, current_bracket_id=2))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    await cog.create_bracket(cog, tosurnament_mock.CtxMock(mock_bot), name=BRACKET_NAME)
    mock_bot.session.add.assert_called_once_with(tosurnament_mock.Matcher(Bracket(tournament_id=1, name=BRACKET_NAME)))
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(current_bracket_id=1)))
    cog.send_reply.assert_called_once_with(mocker.ANY, mocker.ANY, "success", BRACKET_NAME)


@pytest.mark.asyncio
async def test_set_tournament_values(mocker):
    """Puts the input values into the corresponding tournament."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.GUILD_ID))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    await cog.set_tournament_values(tosurnament_mock.CtxMock(mock_bot), {"current_bracket_id": 1})
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(current_bracket_id=1)))
    cog.send_reply.assert_called_once_with(mocker.ANY, mocker.ANY, "success", 1)


@pytest.mark.asyncio
async def test_set_team_captain_role():
    """Sets the team captain role."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.GUILD_ID))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))
    mock_role = tosurnament_mock.RoleMock("Team Captain Role")

    await cog.set_team_captain_role(cog, tosurnament_mock.CtxMock(mock_bot), role=mock_role)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(team_captain_role_id=1)))


@pytest.mark.asyncio
async def test_set_team_captain_role_remove():
    """Removes the team captain role."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.GUILD_ID, team_captain_role_id=1))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    await cog.set_team_captain_role(cog, tosurnament_mock.CtxMock(mock_bot))
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(team_captain_role_id=0)))


@pytest.mark.asyncio
async def test_get_bracket(mocker):
    """Shows all brackets."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, current_bracket_id=1))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, name=BRACKET_NAME))
    mock_bot.session.add_stub(Bracket(id=2, tournament_id=1, name=BRACKET_NAME_2))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    expected_output = "1: `" + BRACKET_NAME + "` (current bracket)\n"
    expected_output += "2: `" + BRACKET_NAME_2 + "`\n"

    await cog.get_bracket(cog, tosurnament_mock.CtxMock(mock_bot))
    cog.send_reply.assert_called_once_with(mocker.ANY, mocker.ANY, "default", expected_output)


@pytest.mark.asyncio
async def test_get_a_bracket(mocker):
    """Sets a bracket as current bracket."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, current_bracket_id=1))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, name=BRACKET_NAME))
    mock_bot.session.add_stub(Bracket(id=2, tournament_id=1, name=BRACKET_NAME_2))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    await cog.get_bracket(cog, tosurnament_mock.CtxMock(mock_bot), number=2)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(current_bracket_id=2)))
    cog.send_reply.assert_called_once_with(mocker.ANY, mocker.ANY, "success", BRACKET_NAME_2)


@pytest.mark.asyncio
async def test_get_a_bracket_that_does_not_exist():
    """Sets a bracket as current bracket but it does not exist."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(tournament_id=1, name=BRACKET_NAME))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    with pytest.raises(discord.ext.commands.UserInputError):
        await cog.get_bracket(cog, tosurnament_mock.CtxMock(mock_bot), number=0)
