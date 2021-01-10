"""
All tests concerning the Tosurnament player module.
"""

import pytest

from bot.modules import module as base
from bot.modules.tosurnament import module as tosurnament
from bot.modules.tosurnament import player as player_module
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.player"


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    tournament = Tournament(id=1, current_bracket_id=1, guild_id=tosurnament_mock.GUILD_ID)
    mock_bot.session.add_stub(tournament)
    bracket = Bracket(id=1, tournament_id=1)
    mock_bot.session.add_stub(bracket)
    cog = tosurnament_mock.mock_cog(player_module.get_class(mock_bot))
    return cog, mock_bot, tournament, bracket


@pytest.mark.asyncio
async def test_register_registration_ended(mocker):
    """Registers the player but the registration phase ended."""
    cog, mock_bot, tournament, bracket = init_mocks()
    date = tournament.parse_date("1 week ago")
    bracket.registration_end_date = date.strftime(tosurnament.DATABASE_DATE_FORMAT)
    with pytest.raises(base.RegistrationEnded):
        await cog.register(cog, tosurnament_mock.CtxMock(mock_bot), "")
