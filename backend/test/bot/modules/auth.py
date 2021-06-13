"""
All tests concerning the Tosurnament auth module.
'link' generates a code to set on the osu profile.
'auth' finalizes the linking process, meaning the discord and osu! account are associated.
"""

import importlib
import pytest

from bot.modules import module as base
from bot.modules import auth
from common.databases.user import User
import test.resources.mock.tosurnament as tosurnament_mock


MODULE_TO_TEST = "bot.modules.auth"
OSU_MODULE = MODULE_TO_TEST + ".osu"
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
        await cog.link(
            cog,
            tosurnament_mock.CtxMock(mock_bot),
            osu_name=tosurnament_mock.OSU_USER_NAME,
        )


@pytest.mark.asyncio
async def test_link_user_not_found(mocker):
    """Links the user but the osu name/id is not found."""
    mock_osu = mocker.patch(OSU_MODULE)
    mock_osu.get_user.return_value = None
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    with pytest.raises(base.UserNotFound):
        await cog.link(
            cog,
            tosurnament_mock.CtxMock(mock_bot),
            osu_name=tosurnament_mock.OSU_USER_NAME,
        )


@pytest.mark.asyncio
async def test_link(mocker):
    """Links the user."""
    mocker.patch(OSU_MODULE, tosurnament_mock.OsuMock())
    mocker.patch(OS_MODULE + ".urandom", mocker.Mock(return_value=CODE_URANDOM))
    mock_author = tosurnament_mock.UserMock()
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    await cog.link(cog, tosurnament_mock.CtxMock(mock_bot, mock_author), osu_name=tosurnament_mock.OSU_USER_NAME)
    mock_bot.session.add.assert_called_once_with(
        tosurnament_mock.Matcher(
            User(
                osu_id=tosurnament_mock.OSU_USER_ID,
                code=CODE_ASCII,
                osu_name=tosurnament_mock.OSU_USER_NAME,
                discord_id_snowflake=tosurnament_mock.DEFAULT_USER_MOCK.id,
            )
        )
    )
    assert mock_bot.session.update.call_count == 0
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", CODE_ASCII, channel=tosurnament_mock.DM_CHANNEL_MOCK)


@pytest.mark.asyncio
async def test_link_regenerate_code(mocker):
    """Links the user, and since they already tried to link, regenerate the linking code."""
    mocker.patch(OSU_MODULE, tosurnament_mock.OsuMock())
    mocker.patch(OS_MODULE + ".urandom", mocker.Mock(return_value=CODE_URANDOM))
    mock_author = tosurnament_mock.UserMock()
    await mock_author.create_dm()
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(
        User(
            discord_id=tosurnament_mock.DEFAULT_USER_MOCK.id,
            osu_id=tosurnament_mock.OSU_USER_ID,
            verified=False,
            code="test",
            osu_name="",
        )
    )
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    await cog.link(cog, tosurnament_mock.CtxMock(mock_bot, mock_author), osu_name=tosurnament_mock.OSU_USER_NAME)
    assert mock_bot.session.add.call_count == 0
    user_matcher = tosurnament_mock.Matcher(
        User(
            osu_id=tosurnament_mock.OSU_USER_ID,
            verified=False,
            code=CODE_ASCII,
            osu_name=tosurnament_mock.OSU_USER_NAME,
        )
    )
    mock_bot.session.update.assert_called_once_with(user_matcher)
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", CODE_ASCII, channel=tosurnament_mock.DM_CHANNEL_MOCK)


@pytest.mark.asyncio
async def test_auth_not_linked():
    """Tries to authenticate the user but they didn't link their osu! account yet."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    with pytest.raises(base.UserNotLinked):
        await cog.auth(cog, tosurnament_mock.CtxMock(mock_bot))


@pytest.mark.asyncio
async def test_auth_already_verified():
    """Tries to authenticate the user but they are already verified."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(tosurnament_mock.DEFAULT_USER_STUB)
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    with pytest.raises(auth.UserAlreadyVerified):
        await cog.auth(cog, tosurnament_mock.CtxMock(mock_bot))


@pytest.mark.asyncio
async def test_auth_osu_find_user_web_page(mocker):
    """Tries to authenticate the user but the osu! website is down (or another error)."""
    mock_requests_get = mocker.Mock()
    mock_requests_get.status_code = 404
    mock_requests = mocker.patch(REQUESTS_MODULE)
    mock_requests.get.return_value = mock_requests_get
    mock_bot = tosurnament_mock.BotMock()
    user_stub = tosurnament_mock.DEFAULT_USER_STUB
    user_stub.verified = False
    mock_bot.session.add_stub(user_stub)
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    with pytest.raises(base.OsuError):
        await cog.auth(cog, tosurnament_mock.CtxMock(mock_bot))


@pytest.mark.asyncio
async def test_auth_osu_location_not_found(mocker):
    """Tries to authenticate the user but the location of the user on the osu! website is not found."""
    mock_requests_get = mocker.Mock()
    mock_requests_get.status_code = 200
    mock_requests_get.text = "random text"
    mock_requests = mocker.patch(REQUESTS_MODULE)
    mock_requests.get.return_value = mock_requests_get
    mock_bot = tosurnament_mock.BotMock()
    user_stub = tosurnament_mock.DEFAULT_USER_STUB
    user_stub.verified = False
    mock_bot.session.add_stub(user_stub)
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    with pytest.raises(base.OsuError):
        await cog.auth(cog, tosurnament_mock.CtxMock(mock_bot))


@pytest.mark.asyncio
async def test_auth_wrong_code(mocker):
    """Tries to authenticate the user but the code in location is wrong."""
    mock_requests_get = mocker.Mock()
    mock_requests_get.status_code = 200
    mock_requests_get.text = 'location":"'
    mock_requests = mocker.patch(REQUESTS_MODULE)
    mock_requests.get.return_value = mock_requests_get
    mock_bot = tosurnament_mock.BotMock()
    user_stub = tosurnament_mock.DEFAULT_USER_STUB
    user_stub.verified = False
    user_stub.code = CODE_ASCII
    mock_bot.session.add_stub(user_stub)
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    with pytest.raises(auth.WrongCodeError):
        await cog.auth(cog, tosurnament_mock.CtxMock(mock_bot))


@pytest.mark.asyncio
async def test_auth(mocker):
    """Authenticates the user."""
    mock_requests_get = mocker.Mock()
    mock_requests_get.status_code = 200
    mock_requests_get.text = 'location":"' + CODE_ASCII
    mock_requests = mocker.patch(REQUESTS_MODULE)
    mock_requests.get.return_value = mock_requests_get
    mock_author = tosurnament_mock.DEFAULT_USER_MOCK
    mock_bot = tosurnament_mock.BotMock()
    user_stub = tosurnament_mock.DEFAULT_USER_STUB
    user_stub.verified = False
    user_stub.code = CODE_ASCII
    mock_bot.session.add_stub(user_stub)
    cog = tosurnament_mock.mock_cog(auth.get_class(mock_bot))

    await cog.auth(cog, tosurnament_mock.CtxMock(mock_bot, mock_author))
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(
            User(
                discord_id_snowflake=tosurnament_mock.DEFAULT_USER_MOCK.id,
                osu_id=tosurnament_mock.DEFAULT_USER_STUB.osu_id,
                osu_name=tosurnament_mock.DEFAULT_USER_STUB.osu_name,
                verified=True,
                code=CODE_ASCII,
            )
        )
    )
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", channel=tosurnament_mock.DM_CHANNEL_MOCK)
