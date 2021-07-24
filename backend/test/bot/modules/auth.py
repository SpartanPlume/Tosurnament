"""
All tests concerning the Tosurnament auth module.
'link' generates a code to set on the osu profile.
'auth' finalizes the linking process, meaning the discord and osu! account are associated.
"""

import importlib
import pytest

from bot.modules import auth
from common.databases.tosurnament.user import User
import test.resources.mock.tosurnament as tosurnament_mock


MODULE_TO_TEST = "bot.modules.auth"
REQUESTS_MODULE = MODULE_TO_TEST + ".requests"
OS_MODULE = MODULE_TO_TEST + ".os"

CODE_URANDOM = b"\xe8!(r\xbd\xc6\x00\\\x825\x9f\xc9\xdbm>A"
CODE_ASCII = "6CEocr3GAFyCNZ_J220-QQ"


@pytest.fixture(autouse=True)
def reload_tosurnament_mock():
    importlib.reload(tosurnament_mock)


@pytest.mark.asyncio
async def test_link_already_verified():
    """Links the user but they are already verified."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(tosurnament_mock.DEFAULT_USER_STUB)
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    with pytest.raises(auth.UserAlreadyVerified):
        await cog.link(cog, tosurnament_mock.CtxMock(mock_bot))


@pytest.mark.asyncio
async def test_link(mocker):
    """Links the user."""
    mocker.patch(OS_MODULE + ".urandom", mocker.Mock(return_value=CODE_URANDOM))
    mock_author = tosurnament_mock.UserMock()
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    mock_ctx = tosurnament_mock.CtxMock(mock_bot, mock_author)
    await cog.link(cog, mock_ctx)
    mock_bot.session.add.assert_called_once_with(
        tosurnament_mock.Matcher(
            User(discord_id_snowflake=tosurnament_mock.DEFAULT_USER_MOCK.id, verified=False, code=CODE_ASCII)
        )
    )
    assert mock_bot.session.update.call_count == 0
    assert mock_ctx.message.delete.call_count == 1
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", CODE_ASCII, channel=tosurnament_mock.DM_CHANNEL_MOCK)


@pytest.mark.asyncio
async def test_link_regenerate_code(mocker):
    """Links the user, and since they already tried to link, regenerate the linking code."""
    mocker.patch(OS_MODULE + ".urandom", mocker.Mock(return_value=CODE_URANDOM))
    mock_author = tosurnament_mock.UserMock()
    await mock_author.create_dm()
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(User(discord_id=tosurnament_mock.DEFAULT_USER_MOCK.id, verified=False, code="test"))
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    mock_ctx = tosurnament_mock.CtxMock(mock_bot, mock_author)
    await cog.link(cog, mock_ctx)
    assert mock_bot.session.add.call_count == 0
    user_matcher = tosurnament_mock.Matcher(
        User(
            verified=False,
            code=CODE_ASCII,
        )
    )
    mock_bot.session.update.assert_called_once_with(user_matcher)
    assert mock_ctx.message.delete.call_count == 1
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", CODE_ASCII, channel=tosurnament_mock.DM_CHANNEL_MOCK)
