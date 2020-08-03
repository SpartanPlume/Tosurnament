"""
All tests concerning the Tosurnament bracket module.
"""

import unittest

from bot.modules.tosurnament import module as tosurnament
from common.databases.tournament import Tournament
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.staff"


class StaffTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_is_staff(self):
        """Checks if the user is part of the tournament staff."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(Tournament())
        ctx_mock = tosurnament_mock.CtxMock(bot_mock)

        user_roles = tosurnament.UserDetails.get_from_ctx(ctx_mock)
        self.assertFalse(user_roles.is_staff())

        ctx_mock.author.roles.append(tosurnament_mock.RoleMock(0, "Random"))
        user_roles = tosurnament.UserDetails.get_from_ctx(ctx_mock)
        self.assertFalse(user_roles.is_staff())

        ctx_mock.author.roles.append(tosurnament_mock.RoleMock(0, "Referee"))
        user_roles = tosurnament.UserDetails.get_from_ctx(ctx_mock)
        self.assertTrue(user_roles.is_staff())
        self.assertIsNotNone(user_roles.referee)
        self.assertIsNone(user_roles.streamer)
        self.assertIsNone(user_roles.commentator)

        ctx_mock.author.roles.append(tosurnament_mock.RoleMock(0, "Commentator"))
        user_roles = tosurnament.UserDetails.get_from_ctx(ctx_mock)
        self.assertTrue(user_roles.is_staff())
        self.assertIsNotNone(user_roles.referee)
        self.assertIsNone(user_roles.streamer)
        self.assertIsNotNone(user_roles.commentator)

        ctx_mock.author.roles.append(tosurnament_mock.RoleMock(0, "Streamer"))
        user_roles = tosurnament.UserDetails.get_from_ctx(ctx_mock)
        self.assertTrue(user_roles.is_staff())
        self.assertIsNotNone(user_roles.referee)
        self.assertIsNotNone(user_roles.streamer)
        self.assertIsNotNone(user_roles.commentator)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(StaffTestCase("test_is_staff"))
    return suite
