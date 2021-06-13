"""
All tests concerning the Tosurnament guild module.
"""

import importlib
import pytest

from bot.modules import guild as guild_module
from common.databases.guild import Guild
from common.databases.messages.guild_verify_message import GuildVerifyMessage
from common import exceptions
import test.resources.mock.tosurnament as tosurnament_mock


MODULE_TO_TEST = "bot.modules.guild"


@pytest.fixture(autouse=True)
def reload_tosurnament_mock():
    importlib.reload(tosurnament_mock)


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    guild = Guild(guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id)
    mock_bot.session.add_stub(guild)
    cog = tosurnament_mock.mock_cog(guild_module.get_class(mock_bot))
    return cog, mock_bot, guild


@pytest.mark.asyncio
async def test_set_guild_values():
    """Sets guild values."""
    cog, mock_bot, guild = init_mocks()
    admin_role = tosurnament_mock.RoleMock("role", 324987)
    assert guild.admin_role_id != admin_role.id
    verified_role = tosurnament_mock.RoleMock("role", 324987)
    assert guild.verified_role_id != verified_role.id
    await cog.set_guild_values(
        tosurnament_mock.CtxMock(mock_bot), {"admin_role_id": admin_role.id, "verified_role_id": verified_role.id}
    )
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Guild(admin_role_id=admin_role.id, verified_role_id=verified_role.id))
    )


@pytest.mark.asyncio
async def test_set_guild_values_and_create_guild():
    """Sets guild values and create Guild object as it does not exist."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(guild_module.get_class(mock_bot))
    role = tosurnament_mock.RoleMock("role", 324987)
    await cog.set_guild_values(tosurnament_mock.CtxMock(mock_bot), {"admin_role_id": role.id})
    mock_bot.session.add.assert_called_once_with(tosurnament_mock.Matcher(Guild(admin_role_id=role.id)))


@pytest.mark.asyncio
async def test_set_admin_role():
    """Sets the admin role."""
    cog, mock_bot, guild = init_mocks()
    role = tosurnament_mock.RoleMock("role", 324987)
    assert guild.admin_role_id != role.id
    await cog.set_admin_role(cog, tosurnament_mock.CtxMock(mock_bot), role=role)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Guild(admin_role_id=role.id)))


@pytest.mark.asyncio
async def test_set_verified_role():
    """Sets the verified role."""
    cog, mock_bot, guild = init_mocks()
    role = tosurnament_mock.RoleMock("role", 324987)
    assert guild.verified_role_id != role.id
    await cog.set_verified_role(cog, tosurnament_mock.CtxMock(mock_bot), role=role)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Guild(verified_role_id=role.id)))


@pytest.mark.asyncio
async def test_set_language_default(mocker):
    """Sets the language, but no language is specified so instead show the list of languages."""
    cog, mock_bot, _ = init_mocks()
    await cog.set_language(cog, tosurnament_mock.CtxMock(mock_bot), language=None)
    cog.send_reply.assert_called_once_with(mocker.ANY, "default", "en")


@pytest.mark.asyncio
async def test_set_language_invalid_language(mocker):
    """Sets the language, but the language is not in the list of languages."""
    cog, mock_bot, _ = init_mocks()
    await cog.set_language(cog, tosurnament_mock.CtxMock(mock_bot), language="fr")
    cog.send_reply.assert_called_once_with(mocker.ANY, "invalid_language")


@pytest.mark.asyncio
async def test_set_language():
    """Sets the language."""
    cog, mock_bot, guild = init_mocks()
    assert not guild.language
    await cog.set_language(cog, tosurnament_mock.CtxMock(mock_bot), language="en")
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Guild(language="en")))


@pytest.mark.asyncio
async def test_setup_verification_channel_no_verified_role(mocker):
    """Setups the verification channel, but the verified role does not exist."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(guild_module.get_class(mock_bot))
    mock_guild = tosurnament_mock.DEFAULT_GUILD_MOCK
    mock_guild.roles = []
    mock_channel = tosurnament_mock.DEFAULT_CHANNEL_MOCK
    with pytest.raises(exceptions.RoleDoesNotExist):
        await cog.setup_verification_channel(cog, tosurnament_mock.CtxMock(mock_bot, guild=mock_guild), mock_channel)


@pytest.mark.asyncio
async def test_setup_verification_channel(mocker):
    """Setups the verification channel."""
    cog, mock_bot, guild = init_mocks()
    verified_role = tosurnament_mock.VERIFIED_ROLE_MOCK
    guild.verified_role_id = verified_role.id
    mock_guild = tosurnament_mock.DEFAULT_GUILD_MOCK
    mock_guild.roles = [verified_role]
    mock_channel = tosurnament_mock.DEFAULT_CHANNEL_MOCK
    await cog.setup_verification_channel(cog, tosurnament_mock.CtxMock(mock_bot, guild=mock_guild), mock_channel)
    cog.send_reply.assert_called_once_with(mocker.ANY, "setup", channel=mock_channel)
    mock_bot.session.add.assert_called_once_with(tosurnament_mock.Matcher(GuildVerifyMessage()))


@pytest.mark.asyncio
async def test_setup_verification_channel_update_message_id(mocker):
    """Setups the verification channel, a message already exists so only the message_id is updated."""
    cog, mock_bot, guild = init_mocks()
    mock_bot.session.add(GuildVerifyMessage(guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    verified_role = tosurnament_mock.VERIFIED_ROLE_MOCK
    guild.verified_role_id = verified_role.id
    mock_guild = tosurnament_mock.DEFAULT_GUILD_MOCK
    mock_guild.roles = [verified_role]
    mock_channel = tosurnament_mock.DEFAULT_CHANNEL_MOCK
    await cog.setup_verification_channel(cog, tosurnament_mock.CtxMock(mock_bot, guild=mock_guild), mock_channel)
    cog.send_reply.assert_called_once_with(mocker.ANY, "setup", channel=mock_channel)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(GuildVerifyMessage()))


@pytest.mark.asyncio
async def test_reaction_on_verify_message_not_verified_user(mocker):
    """Calls on_verified_user, but the user is not verified."""
    cog, mock_bot, _ = init_mocks()
    mock_user = tosurnament_mock.DEFAULT_USER_STUB
    mock_user.verified = False
    mock_bot.session.add(mock_user)
    await cog.reaction_on_verify_message.__wrapped__.__wrapped__(
        self=cog, ctx=tosurnament_mock.CtxMock(mock_bot), emoji=None, guild_verify_message=None
    )
    cog.on_cog_command_error.assert_called_once_with(
        mocker.ANY, tosurnament_mock.Matcher(exceptions.UserNotVerified()), channel=mocker.ANY
    )


@pytest.mark.asyncio
async def test_reaction_on_verify_message():
    """Calls on_verified_user"""
    cog, mock_bot, _ = init_mocks()
    mock_bot.session.add(tosurnament_mock.DEFAULT_USER_STUB)
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)
    await cog.reaction_on_verify_message.__wrapped__.__wrapped__(
        self=cog, ctx=mock_ctx, emoji=None, guild_verify_message=None
    )
    mock_bot.on_verified_user.assert_called_once_with(mock_ctx.guild, mock_ctx.author)


@pytest.mark.asyncio
async def test_on_verified_user_no_verified_role(mocker):
    """Adds the verified role to the user, but the role does not exist"""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(guild_module.get_class(mock_bot))
    mock_guild = tosurnament_mock.DEFAULT_GUILD_MOCK
    mock_guild.roles = []
    mock_user = tosurnament_mock.DEFAULT_USER_MOCK
    mock_user.add_roles = mocker.AsyncMock()
    await cog.on_verified_user(mock_guild, mock_user)
    assert mock_user.add_roles.call_count == 0


@pytest.mark.asyncio
async def test_on_verified_user():
    """Adds the verified role to the user"""
    cog, _, guild = init_mocks()
    verified_role = tosurnament_mock.VERIFIED_ROLE_MOCK
    guild.verified_role_id = verified_role.id
    mock_guild = tosurnament_mock.DEFAULT_GUILD_MOCK
    mock_guild.roles = [verified_role]
    mock_user = tosurnament_mock.DEFAULT_USER_MOCK
    await cog.on_verified_user(mock_guild, mock_user)
    assert mock_user.roles == [verified_role]


@pytest.mark.asyncio
async def test_show_guild_settings():
    """Shows the guild settings of the current bracket."""
    cog, mock_bot, _ = init_mocks()
    expected_output = "**__Guild settings:__**\n\n"
    expected_output += "__id__: `1`\n"
    expected_output += "__guild_id__: `" + str(tosurnament_mock.DEFAULT_GUILD_MOCK.id) + "`\n"
    expected_output += "__verified_role_id__: `0`\n"
    expected_output += "__admin_role_id__: `0`\n"
    expected_output += "__last_notification_date__: `Undefined`\n"
    expected_output += "__language__: `Undefined`\n"
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name, "show_guild_settings")
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, command=mock_command)
    await cog.show_guild_settings(cog, mock_ctx)
    mock_ctx.send.assert_called_once_with(expected_output)
