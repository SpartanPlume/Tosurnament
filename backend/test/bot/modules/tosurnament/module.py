"""
All tests concerning the Tosurnament main module.
"""

from bot.modules.tosurnament import module as tosurnament
from common.databases.tournament import Tournament
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament"


def test_is_staff():
    """Checks if the user is part of the tournament staff."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    mock_ctx = tosurnament_mock.CtxMock(mock_bot)

    user_roles = tosurnament.UserDetails.get_from_ctx(mock_ctx)
    assert not user_roles.is_staff()

    mock_ctx.author.roles.append(tosurnament_mock.RoleMock("Random"))
    user_roles = tosurnament.UserDetails.get_from_ctx(mock_ctx)
    assert not user_roles.is_staff()

    mock_ctx.author.roles.append(tosurnament_mock.RoleMock("Referee"))
    user_roles = tosurnament.UserDetails.get_from_ctx(mock_ctx)
    assert user_roles.is_staff()
    assert user_roles.referee
    assert not user_roles.streamer
    assert not user_roles.commentator

    mock_ctx.author.roles.append(tosurnament_mock.RoleMock("Commentator"))
    user_roles = tosurnament.UserDetails.get_from_ctx(mock_ctx)
    assert user_roles.is_staff()
    assert user_roles.referee
    assert not user_roles.streamer
    assert user_roles.commentator

    mock_ctx.author.roles.append(tosurnament_mock.RoleMock("Streamer"))
    user_roles = tosurnament.UserDetails.get_from_ctx(mock_ctx)
    assert user_roles.is_staff()
    assert user_roles.referee
    assert user_roles.streamer
    assert user_roles.commentator
