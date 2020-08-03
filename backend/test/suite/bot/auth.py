"""
All tests concerning the Tosurnament auth module.
'link' generates a code to set on the osu profile.
'auth' finalizes the linking process, meaning the discord and osu! account are associated.
"""

import unittest
from unittest import mock

from bot.modules import auth
from bot.modules import module as base
from common.databases.user import User
import test.resources.mock.tosurnament as tosurnament_mock


MODULE_TO_TEST = "bot.modules.auth"
OSU_MODULE = MODULE_TO_TEST + ".osu"
REQUESTS_MODULE = MODULE_TO_TEST + ".requests"
OS_MODULE = MODULE_TO_TEST + ".os"

CODE_URANDOM = b"\xe8!(r\xbd\xc6\x00\\\x825\x9f\xc9\xdbm>A"
CODE_ASCII = "6CEocr3GAFyCNZ_J220-QQ"


class AuthTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_link_already_verified(self):
        """Links the user but they are already verified."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(User(verified=True))
        cog = tosurnament_mock.mock_cog(auth.get_class(bot_mock))

        with self.assertRaises(auth.UserAlreadyVerified):
            await cog.link(
                cog, tosurnament_mock.CtxMock(bot_mock), osu_name=tosurnament_mock.USER_NAME,
            )

    @mock.patch(OSU_MODULE)
    async def test_link_user_not_found(self, mock_osu):
        """Links the user but the osu name/id is not found."""
        mock_osu.get_user.return_value = None

        bot_mock = tosurnament_mock.BotMock()
        cog = tosurnament_mock.mock_cog(auth.get_class(bot_mock))

        with self.assertRaises(base.UserNotFound):
            await cog.link(
                cog, tosurnament_mock.CtxMock(bot_mock), osu_name=tosurnament_mock.USER_NAME,
            )

    @mock.patch(OSU_MODULE, tosurnament_mock.OsuMock())
    @mock.patch(OS_MODULE + ".urandom", mock.Mock(return_value=CODE_URANDOM))
    async def test_link(self):
        """Links the user."""
        bot_mock = tosurnament_mock.BotMock()
        cog = tosurnament_mock.mock_cog(auth.get_class(bot_mock))

        await cog.link(cog, tosurnament_mock.CtxMock(bot_mock), osu_name=tosurnament_mock.USER_NAME)
        bot_mock.session.add.assert_called_once_with(
            tosurnament_mock.Matcher(
                User(
                    osu_id=tosurnament_mock.USER_ID,
                    code=CODE_ASCII,
                    osu_name=tosurnament_mock.USER_NAME,
                    discord_id_snowflake=1,
                )
            )
        )
        assert bot_mock.session.update.call_count == 0
        cog.send_reply.assert_called_once_with(mock.ANY, mock.ANY, "success", CODE_ASCII)

    @mock.patch(OSU_MODULE, tosurnament_mock.OsuMock())
    @mock.patch(OS_MODULE + ".urandom", mock.Mock(return_value=CODE_URANDOM))
    async def test_link_regenerate_code(self):
        """Links the user, and since they already tried to link, regenerate the linking code."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(User(osu_id=tosurnament_mock.USER_ID, verified=False, code="test", osu_name=""))
        cog = tosurnament_mock.mock_cog(auth.get_class(bot_mock))

        await cog.link(cog, tosurnament_mock.CtxMock(bot_mock), osu_name=tosurnament_mock.USER_NAME)
        assert bot_mock.session.add.call_count == 0
        user_matcher = tosurnament_mock.Matcher(
            User(osu_id=tosurnament_mock.USER_ID, verified=False, code=CODE_ASCII, osu_name=tosurnament_mock.USER_NAME)
        )
        bot_mock.session.update.assert_called_once_with(user_matcher)
        cog.send_reply.assert_called_once_with(mock.ANY, mock.ANY, "success", CODE_ASCII)

    async def test_auth_not_linked(self):
        """Tries to authenticate the user but they didn't link their osu! account yet."""
        bot_mock = tosurnament_mock.BotMock()
        cog = tosurnament_mock.mock_cog(auth.get_class(bot_mock))

        with self.assertRaises(base.UserNotLinked):
            await cog.auth(cog, tosurnament_mock.CtxMock(bot_mock))

    async def test_auth_already_verified(self):
        """Tries to authenticate the user but they are already verified."""
        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(User(verified=True))
        cog = tosurnament_mock.mock_cog(auth.get_class(bot_mock))

        with self.assertRaises(auth.UserAlreadyVerified):
            await cog.auth(cog, tosurnament_mock.CtxMock(bot_mock))

    @mock.patch(REQUESTS_MODULE)
    async def test_auth_osu_find_user_web_page(self, requests_mock):
        """Tries to authenticate the user but the osu! website is down (or another error)."""
        requests_get_mock = mock.Mock()
        requests_get_mock.status_code = 404
        requests_mock.get.return_value = requests_get_mock

        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(User(verified=False))
        cog = tosurnament_mock.mock_cog(auth.get_class(bot_mock))

        with self.assertRaises(base.OsuError):
            await cog.auth(cog, tosurnament_mock.CtxMock(bot_mock))

    @mock.patch(REQUESTS_MODULE)
    async def test_auth_osu_location_not_found(self, requests_mock):
        """Tries to authenticate the user but the location of the user on the osu! website is not found."""
        requests_get_mock = mock.Mock()
        requests_get_mock.status_code = 200
        requests_get_mock.text = "random text"
        requests_mock.get.return_value = requests_get_mock

        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(User(verified=False))
        cog = tosurnament_mock.mock_cog(auth.get_class(bot_mock))

        with self.assertRaises(base.OsuError):
            await cog.auth(cog, tosurnament_mock.CtxMock(bot_mock))

    @mock.patch(REQUESTS_MODULE)
    async def test_auth_wrong_code(self, requests_mock):
        """Tries to authenticate the user but the code in location is wrong."""
        requests_get_mock = mock.Mock()
        requests_get_mock.status_code = 200
        requests_get_mock.text = 'location":"'
        requests_mock.get.return_value = requests_get_mock

        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(User(verified=False, code="1234"))
        cog = tosurnament_mock.mock_cog(auth.get_class(bot_mock))

        with self.assertRaises(auth.WrongCodeError):
            await cog.auth(cog, tosurnament_mock.CtxMock(bot_mock))

    @mock.patch(REQUESTS_MODULE)
    async def test_auth(self, requests_mock):
        """Authenticates the user."""
        requests_get_mock = mock.Mock()
        requests_get_mock.status_code = 200
        requests_get_mock.text = 'location":"1234'
        requests_mock.get.return_value = requests_get_mock

        bot_mock = tosurnament_mock.BotMock()
        bot_mock.session.add_stub(User(verified=False, code="1234"))
        cog = tosurnament_mock.mock_cog(auth.get_class(bot_mock))

        await cog.auth(cog, tosurnament_mock.CtxMock(bot_mock))
        bot_mock.session.update.assert_called_once_with(tosurnament_mock.Matcher(User(verified=True, code="1234")))
        cog.send_reply.assert_called_with(mock.ANY, mock.ANY, "success")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(AuthTestCase("test_link_already_verified"))
    suite.addTest(AuthTestCase("test_link_user_not_found"))
    suite.addTest(AuthTestCase("test_link"))
    suite.addTest(AuthTestCase("test_link_regenerate_code"))
    suite.addTest(AuthTestCase("test_auth_not_linked"))
    suite.addTest(AuthTestCase("test_auth_already_verified"))
    suite.addTest(AuthTestCase("test_auth_osu_find_user_web_page"))
    suite.addTest(AuthTestCase("test_auth_osu_location_not_found"))
    suite.addTest(AuthTestCase("test_auth_wrong_code"))
    suite.addTest(AuthTestCase("test_auth"))

    return suite
