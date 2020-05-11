"""
All tests concerning the Tosurnament tournament module.
"""

import unittest
from unittest import mock

import discord

from bot.modules.tosurnament import tournament
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.tournament"
BRACKET_NAME = "Bracket name"
BRACKET_NAME_2 = "Bracket name 2"


class TournamentTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_create_bracket(self):
        """Creates a bracket."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament(id=1, current_bracket_id=2))
        cog = tosurnament_mock.mock_cog(tournament.get_class(bot_mock))

        await cog.create_bracket(cog, tosurnament_mock.CtxMock(bot_mock), name=BRACKET_NAME)
        bot_mock.session.add.assert_called_once_with(
            tosurnament_mock.Matcher(Bracket(tournament_id=1, name=BRACKET_NAME))
        )
        bot_mock.session.update.assert_called_once_with(
            tosurnament_mock.Matcher(Tournament(id=1, current_bracket_id=1))
        )
        cog.send_reply.assert_called_once_with(mock.ANY, mock.ANY, "success", BRACKET_NAME)

    async def test_set_tournament_values(self):
        """Puts the input values into the corresponding tournament."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament())
        cog = tosurnament_mock.mock_cog(tournament.get_class(bot_mock))

        await cog.set_tournament_values(tosurnament_mock.CtxMock(bot_mock), {"current_bracket_id": 1})
        bot_mock.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(current_bracket_id=1)))
        cog.send_reply.assert_called_once_with(mock.ANY, mock.ANY, "success", 1)

    async def test_set_team_captain_role(self):
        """Sets the team captain role."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament())
        cog = tosurnament_mock.mock_cog(tournament.get_class(bot_mock))
        role_mock = mock.Mock()
        role_mock.id = 1

        await cog.set_team_captain_role(cog, tosurnament_mock.CtxMock(bot_mock), role=role_mock)
        bot_mock.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(team_captain_role_id=1)))

    async def test_set_team_captain_role_remove(self):
        """Removes the team captain role."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament(team_captain_role_id=1))
        cog = tosurnament_mock.mock_cog(tournament.get_class(bot_mock))

        await cog.set_team_captain_role(cog, tosurnament_mock.CtxMock(bot_mock))
        bot_mock.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(team_captain_role_id=0)))

    async def test_get_bracket(self):
        """Shows all brackets."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament(current_bracket_id=1))
        bot_mock.session.add_stub(Bracket(id=1, name=BRACKET_NAME))
        bot_mock.session.add_stub(Bracket(id=2, name=BRACKET_NAME_2))
        cog = tosurnament_mock.mock_cog(tournament.get_class(bot_mock))

        expected_output = "1: `" + BRACKET_NAME + "` (current bracket)\n"
        expected_output += "2: `" + BRACKET_NAME_2 + "`\n"

        await cog.get_bracket(cog, tosurnament_mock.CtxMock(bot_mock))
        cog.send_reply.assert_called_once_with(mock.ANY, mock.ANY, "default", expected_output)

    async def test_get_a_bracket(self):
        """Sets a bracket as current bracket."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament(current_bracket_id=1))
        bot_mock.session.add_stub(Bracket(id=1, name=BRACKET_NAME))
        bot_mock.session.add_stub(Bracket(id=2, name=BRACKET_NAME_2))
        cog = tosurnament_mock.mock_cog(tournament.get_class(bot_mock))

        await cog.get_bracket(cog, tosurnament_mock.CtxMock(bot_mock), number=2)
        bot_mock.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(current_bracket_id=2)))
        cog.send_reply.assert_called_once_with(mock.ANY, mock.ANY, "success", BRACKET_NAME_2)

    async def test_get_a_bracket_that_does_not_exist(self):
        """Sets a bracket as current bracket but it does not exist."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament())
        bot_mock.session.add_stub(Bracket(name=BRACKET_NAME))
        cog = tosurnament_mock.mock_cog(tournament.get_class(bot_mock))

        with self.assertRaises(discord.ext.commands.UserInputError):
            await cog.get_bracket(cog, tosurnament_mock.CtxMock(bot_mock), number=0)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TournamentTestCase("test_create_bracket"))
    suite.addTest(TournamentTestCase("test_set_tournament_values"))
    suite.addTest(TournamentTestCase("test_set_team_captain_role"))
    suite.addTest(TournamentTestCase("test_set_team_captain_role_remove"))
    suite.addTest(TournamentTestCase("test_get_bracket"))
    suite.addTest(TournamentTestCase("test_get_a_bracket"))
    suite.addTest(TournamentTestCase("test_get_a_bracket_that_does_not_exist"))
    return suite
