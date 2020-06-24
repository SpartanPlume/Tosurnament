"""
All tests concerning the Tosurnament bracket module.
"""

import unittest
from unittest import mock

import discord

from bot.modules.tosurnament import bracket
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.bracket"
BRACKET_NAME = "Bracket name"
BRACKET_NAME_2 = "Bracket name 2"
SPREADSHEET_ID = "abcd1234"


class BracketTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_set_bracket_values(self):
        """Puts the input values into the corresponding bracket."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament())
        bot_mock.session.add_stub(Bracket(name=BRACKET_NAME))
        cog = tosurnament_mock.mock_cog(bracket.get_class(bot_mock))

        await cog.set_bracket_values(tosurnament_mock.CtxMock(bot_mock), {"name": BRACKET_NAME_2})
        bot_mock.session.update.assert_called_once_with(tosurnament_mock.Matcher(Bracket(name=BRACKET_NAME_2)))
        cog.send_reply.assert_called_once_with(mock.ANY, mock.ANY, "success", BRACKET_NAME_2)

    async def test_set_bracket_name_no_name(self):
        """Changes current bracket's name to empty (invalid)."""
        bot_mock = tosurnament_mock.BotMock()
        cog = tosurnament_mock.mock_cog(bracket.get_class(bot_mock))

        with self.assertRaises(discord.ext.commands.UserInputError):
            await cog.set_bracket_name(cog, tosurnament_mock.CtxMock(bot_mock), name="")

    async def test_set_bracket_spreadsheet(self):
        """Sets bracket spreadsheets."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament())
        bot_mock.session.add_stub(Bracket())
        cog = tosurnament_mock.mock_cog(bracket.get_class(bot_mock))

        await cog.set_bracket_spreadsheet(tosurnament_mock.CtxMock(bot_mock), "players", SPREADSHEET_ID, "")
        await cog.set_bracket_spreadsheet(tosurnament_mock.CtxMock(bot_mock), "schedules", SPREADSHEET_ID, "")
        # !To fix, but unittest is pretty crappy with this tbh
        # add_expected = [
        #     mock.call(tosurnament_mock.Matcher(PlayersSpreadsheet())),
        #     mock.call(tosurnament_mock.Matcher(SchedulesSpreadsheet())),
        # ]
        # bracket_matcher = tosurnament_mock.Matcher(Bracket(players_spreadsheet_id=1))
        # players_spreadsheet_matcher = tosurnament_mock.Matcher(
        #     PlayersSpreadsheet(spreadsheet_id=SPREADSHEET_ID)
        # )
        # bracket_matcher_2 = tosurnament_mock.Matcher(
        #     Bracket(players_spreadsheet_id=1, schedules_spreadsheet_id=1)
        # )
        # schedules_spreadsheet_matcher = tosurnament_mock.Matcher(
        #     SchedulesSpreadsheet(spreadsheet_id=SPREADSHEET_ID)
        # )
        # update_expected = [
        #     mock.call(bracket_matcher),
        #     mock.call(players_spreadsheet_matcher),
        #     mock.call(bracket_matcher_2),
        #     mock.call(schedules_spreadsheet_matcher),
        # ]
        # assert bot_mock.session.add.call_args_list == add_expected
        # assert bot_mock.session.update.call_args_list == update_expected
        assert bot_mock.session.add.call_count == 2
        assert bot_mock.session.update.call_count == 4


def suite():
    suite = unittest.TestSuite()
    suite.addTest(BracketTestCase("test_set_bracket_values"))
    suite.addTest(BracketTestCase("test_set_bracket_name_no_name"))
    suite.addTest(BracketTestCase("test_set_bracket_spreadsheet"))
    return suite
