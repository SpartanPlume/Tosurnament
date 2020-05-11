"""
All tests concerning the Tosurnament guild_owner module.
'create_tournament' creates a tournament. A tournament always contains at least one bracket.
'end_tournament' sends a message to react on in order to end the tournament.
'set_admin_role' sets an admin role for the bot. Anyone with this role has access to more bot commands.
"""

import unittest
from unittest import mock

from bot.modules.tosurnament import guild_owner
from bot.modules.tosurnament import module as tosurnament
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.guild_owner"
TOURNAMENT_ACRONYM = "TT"
TOURNAMENT_NAME = "Tosurnament Tourney"
BRACKET_NAME = "Bracket name"


class GuildOwnerTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_create_tournament_already_created(self):
        """Creates a tournament but one has already been created."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament())
        cog = tosurnament_mock.mock_cog(guild_owner.get_class(bot_mock))

        with self.assertRaises(tosurnament.TournamentAlreadyCreated):
            await cog.create_tournament(
                cog, tosurnament_mock.CtxMock(bot_mock), TOURNAMENT_ACRONYM, TOURNAMENT_NAME,
            )

    async def test_create_tournament(self):
        """Creates a tournament."""
        bot_mock = tosurnament_mock.BotMock()
        cog = tosurnament_mock.mock_cog(guild_owner.get_class(bot_mock))

        await cog.create_tournament(cog, tosurnament_mock.CtxMock(bot_mock), TOURNAMENT_ACRONYM, TOURNAMENT_NAME)
        assert bot_mock.session.update.call_count == 1
        tournament_matcher = tosurnament_mock.Matcher(
            Tournament(acronym=TOURNAMENT_ACRONYM, name=TOURNAMENT_NAME, current_bracket_id=1),
        )
        bracket_matcher = tosurnament_mock.Matcher(Bracket(tournament_id=1, name=TOURNAMENT_NAME))
        expected = [mock.call(tournament_matcher), mock.call(bracket_matcher)]
        assert bot_mock.session.add.call_args_list == expected
        cog.send_reply.assert_called_with(
            mock.ANY, mock.ANY, "success", TOURNAMENT_ACRONYM, TOURNAMENT_NAME, TOURNAMENT_NAME
        )

    async def test_create_tournament_with_bracket_name(self):
        """Creates a tournament with a specified bracket name."""
        bot_mock = tosurnament_mock.BotMock()
        cog = tosurnament_mock.mock_cog(guild_owner.get_class(bot_mock))

        await cog.create_tournament(
            cog, tosurnament_mock.CtxMock(bot_mock), TOURNAMENT_ACRONYM, TOURNAMENT_NAME, BRACKET_NAME,
        )
        assert bot_mock.session.update.call_count == 1
        tournament_matcher = tosurnament_mock.Matcher(
            Tournament(acronym=TOURNAMENT_ACRONYM, name=TOURNAMENT_NAME, current_bracket_id=1),
        )
        bracket_matcher = tosurnament_mock.Matcher(Bracket(tournament_id=1, name=BRACKET_NAME))
        expected = [mock.call(tournament_matcher), mock.call(bracket_matcher)]
        assert bot_mock.session.add.call_args_list == expected
        cog.send_reply.assert_called_with(
            mock.ANY, mock.ANY, "success", TOURNAMENT_ACRONYM, TOURNAMENT_NAME, BRACKET_NAME
        )

    async def test_end_tournament(self):
        """Sends a message to react on in order to end the tournament."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament())
        cog = tosurnament_mock.mock_cog(guild_owner.get_class(bot_mock))

        await cog.end_tournament(cog, tosurnament_mock.CtxMock(bot_mock))
        cog.send_reply.assert_called_with(mock.ANY, mock.ANY, "are_you_sure")
        assert bot_mock.session.add.call_count == 1


def suite():
    suite = unittest.TestSuite()
    suite.addTest(GuildOwnerTestCase("test_create_tournament_already_created"))
    suite.addTest(GuildOwnerTestCase("test_create_tournament"))
    suite.addTest(GuildOwnerTestCase("test_create_tournament_with_bracket_name"))
    suite.addTest(GuildOwnerTestCase("test_end_tournament"))
    return suite
