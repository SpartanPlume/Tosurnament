"""
All tests concerning the Tosurnament guild module.
"""

import importlib
import pytest

import discord

from bot.modules import reaction_for_role_message as reaction_for_role_message_module
from common.databases.messages.reaction_for_role_message import ReactionForRoleMessage
from common import exceptions
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.reaction_for_role_message"


@pytest.fixture(autouse=True)
def reload_tosurnament_mock():
    importlib.reload(tosurnament_mock)


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    reaction_for_role_message = ReactionForRoleMessage(
        guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id,
        author_id=tosurnament_mock.DEFAULT_USER_MOCK.id,
        setup_channel_id=tosurnament_mock.SETUP_CHANNEL_MOCK.id,
        setup_message_id=tosurnament_mock.SETUP_MESSAGE_MOCK.id,
        preview_message_id=tosurnament_mock.PREVIEW_MESSAGE_MOCK.id,
        channel_id=tosurnament_mock.DEFAULT_CHANNEL_MOCK.id,
        text="Some text",
    )
    mock_bot.session.add_stub(reaction_for_role_message)
    cog = tosurnament_mock.mock_cog(reaction_for_role_message_module.get_class(mock_bot))
    return cog, mock_bot, reaction_for_role_message


@pytest.mark.asyncio
async def test_delete_setup_messages():
    """Deletes the setup messages."""
    cog, _, reaction_for_role_message = init_mocks()
    await cog.delete_setup_messages(reaction_for_role_message)
    assert tosurnament_mock.SETUP_MESSAGE_MOCK.delete.call_count == 1
    assert tosurnament_mock.PREVIEW_MESSAGE_MOCK.delete.call_count == 1


@pytest.mark.asyncio
async def test_delete_setup_messages_fail():
    """Deletes the setup messages but an error occurs."""
    cog, _, _ = init_mocks()
    await cog.delete_setup_messages(None)
    assert tosurnament_mock.SETUP_MESSAGE_MOCK.delete.call_count == 0
    assert tosurnament_mock.PREVIEW_MESSAGE_MOCK.delete.call_count == 0


@pytest.mark.asyncio
async def test_create_reaction_for_role_message(mocker):
    """Creates a reaction for role message."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(reaction_for_role_message_module.get_class(mock_bot))
    cog.send_reply = mocker.AsyncMock(return_value=tosurnament_mock.SETUP_MESSAGE_MOCK)
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, channel=tosurnament_mock.SETUP_CHANNEL_MOCK)
    mock_ctx.send = mocker.AsyncMock(return_value=tosurnament_mock.PREVIEW_MESSAGE_MOCK)
    message_text = "Some text"
    await cog.create_reaction_for_role_message(
        cog, mock_ctx, tosurnament_mock.DEFAULT_CHANNEL_MOCK, message_text=message_text
    )
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", "None\n")
    mock_ctx.send.assert_called_once_with(message_text)
    mock_bot.session.add.assert_called_once_with(
        tosurnament_mock.Matcher(
            ReactionForRoleMessage(
                guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id,
                author_id=tosurnament_mock.DEFAULT_USER_MOCK.id,
                setup_channel_id=tosurnament_mock.SETUP_CHANNEL_MOCK.id,
                setup_message_id=tosurnament_mock.SETUP_MESSAGE_MOCK.id,
                preview_message_id=tosurnament_mock.PREVIEW_MESSAGE_MOCK.id,
                channel_id=tosurnament_mock.DEFAULT_CHANNEL_MOCK.id,
                text=message_text,
            )
        )
    )


@pytest.mark.asyncio
async def test_create_reaction_for_role_message_with_message_already_existing(mocker):
    """Creates a reaction for role message, one is already existing so it will be deleted."""
    cog, mock_bot, reaction_for_role_message = init_mocks()
    cog.send_reply = mocker.AsyncMock(return_value=tosurnament_mock.SETUP_MESSAGE_MOCK)
    cog.delete_setup_messages = mocker.AsyncMock()
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, channel=tosurnament_mock.SETUP_CHANNEL_MOCK)
    mock_ctx.send = mocker.AsyncMock(return_value=tosurnament_mock.PREVIEW_MESSAGE_MOCK)
    message_text = "Some text"
    await cog.create_reaction_for_role_message(
        cog, mock_ctx, tosurnament_mock.DEFAULT_CHANNEL_MOCK, message_text=message_text
    )
    cog.delete_setup_messages.assert_called_once_with(tosurnament_mock.Matcher(reaction_for_role_message))
    mock_bot.session.delete.assert_called_once_with(tosurnament_mock.Matcher(reaction_for_role_message))
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", "None\n")
    mock_ctx.send.assert_called_once_with(message_text)
    mock_bot.session.add.assert_called_once_with(
        tosurnament_mock.Matcher(
            ReactionForRoleMessage(
                guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id,
                author_id=tosurnament_mock.DEFAULT_USER_MOCK.id,
                setup_channel_id=tosurnament_mock.SETUP_CHANNEL_MOCK.id,
                setup_message_id=tosurnament_mock.SETUP_MESSAGE_MOCK.id,
                preview_message_id=tosurnament_mock.PREVIEW_MESSAGE_MOCK.id,
                channel_id=tosurnament_mock.DEFAULT_CHANNEL_MOCK.id,
                text=message_text,
            )
        )
    )


@pytest.mark.asyncio
async def test_add_emoji_role_pair_no_message_in_creation(mocker):
    """Adds a emoji/role pair to the role message creation, but no message is in creation."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(reaction_for_role_message_module.get_class(mock_bot))
    await cog.add_emoji_role_pair(cog, tosurnament_mock.CtxMock(mock_bot), None, None)
    cog.send_reply.assert_called_once_with(mocker.ANY, "error")


@pytest.mark.asyncio
async def test_add_emoji_role_pair_emoji_already_on_message(mocker):
    """Adds a emoji/role pair to the role message creation, but the emoji is already on the message."""
    cog, mock_bot, reaction_for_role_message = init_mocks()
    reaction_for_role_message.emojis = "🛎️"
    await cog.add_emoji_role_pair(cog, tosurnament_mock.CtxMock(mock_bot), "🛎️", None)
    cog.send_reply.assert_called_once_with(mocker.ANY, "emoji_duplicate")


@pytest.mark.asyncio
async def test_add_emoji_role_pair_invalid_argument(mocker):
    """Adds a emoji/role pair to the role message creation, but the emoji is an InvalidArgument."""
    cog, mock_bot, _ = init_mocks()
    mock_message = tosurnament_mock.DEFAULT_MESSAGE_MOCK
    mock_message.add_reaction = mocker.AsyncMock(side_effect=discord.InvalidArgument())
    await cog.add_emoji_role_pair(cog, tosurnament_mock.CtxMock(mock_bot, message=mock_message), "🛎️", None)
    cog.send_reply.assert_called_once_with(mocker.ANY, "invalid_emoji", "🛎️")


@pytest.mark.asyncio
async def test_add_emoji_role_pair_emoji_not_found(mocker):
    """Adds a emoji/role pair to the role message creation, but the emoji is NotFound."""
    cog, mock_bot, _ = init_mocks()
    mock_message = tosurnament_mock.DEFAULT_MESSAGE_MOCK
    mock_not_found_response = mocker.Mock()
    mock_not_found_response.status = 0
    mock_message.add_reaction = mocker.AsyncMock(side_effect=discord.NotFound(mock_not_found_response, ""))
    await cog.add_emoji_role_pair(cog, tosurnament_mock.CtxMock(mock_bot, message=mock_message), "🛎️", None)
    cog.send_reply.assert_called_once_with(mocker.ANY, "emoji_not_found", "🛎️")


@pytest.mark.asyncio
async def test_add_emoji_role_pair_emoji_http_exception_400(mocker):
    """Adds a emoji/role pair to the role message creation, but there is an HTTPException 400."""
    cog, mock_bot, _ = init_mocks()
    mock_message = tosurnament_mock.DEFAULT_MESSAGE_MOCK
    mock_not_found_response = mocker.Mock()
    mock_not_found_response.status = 400
    mock_message.add_reaction = mocker.AsyncMock(side_effect=discord.HTTPException(mock_not_found_response, ""))
    await cog.add_emoji_role_pair(cog, tosurnament_mock.CtxMock(mock_bot, message=mock_message), "🛎️", None)
    cog.send_reply.assert_called_once_with(mocker.ANY, "emoji_not_found", "🛎️")


@pytest.mark.asyncio
async def test_add_emoji_role_pair_emoji_http_exception_other(mocker):
    """Adds a emoji/role pair to the role message creation, but there is an HTTPException other than 400."""
    cog, mock_bot, _ = init_mocks()
    mock_message = tosurnament_mock.DEFAULT_MESSAGE_MOCK
    mock_not_found_response = mocker.Mock()
    mock_not_found_response.status = 500
    mock_message.add_reaction = mocker.AsyncMock(side_effect=discord.HTTPException(mock_not_found_response, ""))
    with pytest.raises(discord.HTTPException):
        await cog.add_emoji_role_pair(cog, tosurnament_mock.CtxMock(mock_bot, message=mock_message), "🛎️", None)


@pytest.mark.asyncio
async def test_add_emoji_role_pair_emoji(mocker):
    """Adds a emoji/role pair to the role message creation."""
    cog, mock_bot, reaction_for_role_message = init_mocks()
    cog.delete_setup_messages = mocker.AsyncMock()
    cog.send_reply.return_value = tosurnament_mock.MessageMock(tosurnament_mock.SETUP_MESSAGE_MOCK.id + 1)
    mock_channel = tosurnament_mock.ChannelMock(tosurnament_mock.SETUP_CHANNEL_MOCK.id + 1)
    mock_ctx = tosurnament_mock.CtxMock(mock_bot, channel=mock_channel)
    mock_preview_message = tosurnament_mock.MessageMock(tosurnament_mock.PREVIEW_MESSAGE_MOCK.id + 1)
    mock_ctx.send.return_value = mock_preview_message
    await cog.add_emoji_role_pair(cog, mock_ctx, "🛎️", tosurnament_mock.VERIFIED_ROLE_MOCK)
    cog.delete_setup_messages.assert_called_once_with(reaction_for_role_message)
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", "🛎️ | Verified\n")
    mock_ctx.send.assert_called_once_with("Some text")
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(
            ReactionForRoleMessage(
                guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id,
                author_id=tosurnament_mock.DEFAULT_USER_MOCK.id,
                setup_channel_id=tosurnament_mock.SETUP_CHANNEL_MOCK.id + 1,
                setup_message_id=tosurnament_mock.SETUP_MESSAGE_MOCK.id + 1,
                preview_message_id=tosurnament_mock.PREVIEW_MESSAGE_MOCK.id + 1,
                channel_id=tosurnament_mock.DEFAULT_CHANNEL_MOCK.id,
                text="Some text",
                emojis="🛎️",
                roles=str(tosurnament_mock.VERIFIED_ROLE_MOCK.id),
            )
        )
    )
    mock_preview_message.add_reaction.assert_called_once_with("🛎️")


@pytest.mark.asyncio
async def test_cancel_reaction_for_role_message_creation_no_message_in_creation(mocker):
    """Cancels a reaction for role message creation, but no message is in creation."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(reaction_for_role_message_module.get_class(mock_bot))
    await cog.cancel_reaction_for_role_message_creation(cog, tosurnament_mock.CtxMock(mock_bot))
    cog.send_reply.assert_called_once_with(mocker.ANY, "error")


@pytest.mark.asyncio
async def test_cancel_reaction_for_role_message_creation(mocker):
    """Cancels a reaction for role message creation."""
    cog, mock_bot, reaction_for_role_message = init_mocks()
    cog.delete_setup_messages = mocker.AsyncMock()
    await cog.cancel_reaction_for_role_message_creation(cog, tosurnament_mock.CtxMock(mock_bot))
    cog.delete_setup_messages.assert_called_once_with(tosurnament_mock.Matcher(reaction_for_role_message))
    mock_bot.session.delete.assert_called_once_with(tosurnament_mock.Matcher(reaction_for_role_message))
    cog.send_reply.assert_called_once_with(mocker.ANY, "success")
