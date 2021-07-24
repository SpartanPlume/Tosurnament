"""
All tests concerning the Tosurnament guild_owner module.
'create_tournament' creates a tournament. A tournament always contains at least one bracket.
'end_tournament' sends a message to react on in order to end the tournament.
'set_admin_role' sets an admin role for the bot. Anyone with this role has access to more bot commands.
"""

import pytest

from bot.modules.tosurnament import guild_owner
from bot.modules.tosurnament import module as tosurnament
from common.databases.tosurnament.tournament import Tournament
from common.databases.tosurnament.bracket import Bracket
from common.databases.tosurnament.spreadsheets.schedules_spreadsheet import SchedulesSpreadsheet
from common.databases.tosurnament.spreadsheets.players_spreadsheet import PlayersSpreadsheet
from common.databases.tosurnament_message.reschedule_message import RescheduleMessage
from common.databases.tosurnament_message.staff_reschedule_message import StaffRescheduleMessage
from common.databases.tosurnament_message.end_tournament_message import EndTournamentMessage
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.guild_owner"
TOURNAMENT_ACRONYM = "TT"
TOURNAMENT_NAME = "Tosurnament Tourney"
BRACKET_NAME = "Bracket name"


@pytest.mark.asyncio
async def test_create_tournament_already_created():
    """Creates a tournament but one has already been created."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    cog = tosurnament_mock.mock_cog(guild_owner.get_class(mock_bot))

    with pytest.raises(tosurnament.TournamentAlreadyCreated):
        await cog.create_tournament(
            cog,
            tosurnament_mock.CtxMock(mock_bot),
            TOURNAMENT_ACRONYM,
            TOURNAMENT_NAME,
        )


@pytest.mark.asyncio
async def test_create_tournament(mocker):
    """Creates a tournament."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(guild_owner.get_class(mock_bot))

    await cog.create_tournament(cog, tosurnament_mock.CtxMock(mock_bot), TOURNAMENT_ACRONYM, TOURNAMENT_NAME)
    assert mock_bot.session.update.call_count == 1
    tournament_matcher = tosurnament_mock.Matcher(
        Tournament(acronym=TOURNAMENT_ACRONYM, name=TOURNAMENT_NAME, current_bracket_id=1),
    )
    bracket_matcher = tosurnament_mock.Matcher(Bracket(tournament_id=1, name=TOURNAMENT_NAME))
    expected = [mocker.call(tournament_matcher), mocker.call(bracket_matcher)]
    assert mock_bot.session.add.call_args_list == expected
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", TOURNAMENT_ACRONYM, TOURNAMENT_NAME, TOURNAMENT_NAME)


@pytest.mark.asyncio
async def test_create_tournament_with_bracket_name(mocker):
    """Creates a tournament with a specified bracket name."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(guild_owner.get_class(mock_bot))

    await cog.create_tournament(
        cog,
        tosurnament_mock.CtxMock(mock_bot),
        TOURNAMENT_ACRONYM,
        TOURNAMENT_NAME,
        BRACKET_NAME,
    )
    assert mock_bot.session.update.call_count == 1
    tournament_matcher = tosurnament_mock.Matcher(
        Tournament(acronym=TOURNAMENT_ACRONYM, name=TOURNAMENT_NAME, current_bracket_id=1),
    )
    bracket_matcher = tosurnament_mock.Matcher(Bracket(tournament_id=1, name=BRACKET_NAME))
    expected = [mocker.call(tournament_matcher), mocker.call(bracket_matcher)]
    assert mock_bot.session.add.call_args_list == expected
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", TOURNAMENT_ACRONYM, TOURNAMENT_NAME, BRACKET_NAME)


@pytest.mark.asyncio
async def test_end_tournament(mocker):
    """Sends a message to react on in order to end the tournament."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    cog = tosurnament_mock.mock_cog(guild_owner.get_class(mock_bot))

    await cog.end_tournament(cog, tosurnament_mock.CtxMock(mock_bot))
    cog.send_reply.assert_called_once_with(mocker.ANY, "are_you_sure")
    mock_bot.session.add.assert_called_once_with(tosurnament_mock.Matcher(EndTournamentMessage()))


@pytest.mark.asyncio
async def test_reaction_on_end_tournament_not_guild_owner():
    """Sends a message to react on in order to end the tournament, but the reaction is not from the guild owner."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(guild_owner.get_class(mock_bot))

    mock_message = tosurnament_mock.ANOTHER_MESSAGE_MOCK
    mock_bot.session.add_stub(EndTournamentMessage(message_id=mock_message.id))
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name)
    await cog.reaction_on_end_tournament_message.__wrapped__(
        cog,
        tosurnament_mock.CtxMock(mock_bot, command=mock_command, message=mock_message),
        tosurnament_mock.EmojiMock("✅"),
    )
    assert mock_bot.session.delete.call_count == 0


@pytest.mark.asyncio
async def test_reaction_on_end_tournament_message_no_tournament():
    """Sends a message to react on in order to end the tournament."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(guild_owner.get_class(mock_bot))

    message_obj = EndTournamentMessage(message_id=tosurnament_mock.DEFAULT_MESSAGE_MOCK.id)
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name)
    await cog.reaction_on_end_tournament_message.__wrapped__.__wrapped__(
        self=cog,
        ctx=tosurnament_mock.CtxMock(mock_bot, author=tosurnament_mock.GUILD_OWNER_USER_MOCK, command=mock_command),
        emoji=tosurnament_mock.EmojiMock("✅"),
        end_tournament_message=message_obj,
    )
    assert mock_bot.session.delete.call_count == 1


@pytest.mark.asyncio
async def test_reaction_on_end_tournament_message_refuse(mocker):
    """Sends a message to react on in order to end the tournament."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(guild_owner.get_class(mock_bot))

    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    mock_bot.session.add_stub(Bracket())
    message_obj = EndTournamentMessage(message_id=tosurnament_mock.DEFAULT_MESSAGE_MOCK.id)
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name)
    await cog.reaction_on_end_tournament_message.__wrapped__.__wrapped__(
        self=cog,
        ctx=tosurnament_mock.CtxMock(mock_bot, author=tosurnament_mock.GUILD_OWNER_USER_MOCK, command=mock_command),
        emoji=tosurnament_mock.EmojiMock("❎"),
        end_tournament_message=message_obj,
    )
    cog.send_reply.assert_called_once_with(mocker.ANY, "refused")


@pytest.mark.asyncio
async def test_reaction_on_end_tournament_message(mocker):
    """Sends a message to react on in order to end the tournament."""
    mock_bot = tosurnament_mock.BotMock()
    cog = tosurnament_mock.mock_cog(guild_owner.get_class(mock_bot))

    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.DEFAULT_GUILD_MOCK.id))
    mock_bot.session.add_stub(Bracket(tournament_id=1, schedules_spreadsheet_id=1, players_spreadsheet_id=1))
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=1))
    mock_bot.session.add_stub(PlayersSpreadsheet(id=1))
    mock_bot.session.add_stub(Bracket(tournament_id=1))
    mock_bot.session.add_stub(Bracket(tournament_id=1, schedules_spreadsheet_id=42, players_spreadsheet_id=42))
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=42))
    mock_bot.session.add_stub(PlayersSpreadsheet(id=42))
    mock_bot.session.add_stub(Bracket(tournament_id=1, schedules_spreadsheet_id=43))
    mock_bot.session.add_stub(RescheduleMessage(tournament_id=1))
    mock_bot.session.add_stub(RescheduleMessage(tournament_id=1))
    mock_bot.session.add_stub(StaffRescheduleMessage(tournament_id=1))
    mock_bot.session.add_stub(StaffRescheduleMessage(tournament_id=1))

    mock_bot.session.add_stub(Tournament(id=2))
    mock_bot.session.add_stub(Bracket(tournament_id=2, schedules_spreadsheet_id=2, players_spreadsheet_id=2))
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=2))
    mock_bot.session.add_stub(PlayersSpreadsheet(id=2))
    mock_bot.session.add_stub(RescheduleMessage(tournament_id=2))

    message_obj = EndTournamentMessage(message_id=tosurnament_mock.DEFAULT_MESSAGE_MOCK.id)
    mock_bot.session.add_stub(message_obj)
    mock_command = tosurnament_mock.CommandMock(cog.qualified_name)
    await cog.reaction_on_end_tournament_message.__wrapped__.__wrapped__(
        self=cog,
        ctx=tosurnament_mock.CtxMock(mock_bot, author=tosurnament_mock.GUILD_OWNER_USER_MOCK, command=mock_command),
        emoji=tosurnament_mock.EmojiMock("✅"),
        end_tournament_message=message_obj,
    )
    cog.send_reply.assert_called_once_with(mocker.ANY, "success")

    assert len(mock_bot.session.tables[Tournament.__tablename__]) == 1
    assert len(mock_bot.session.tables[Bracket.__tablename__]) == 1
    assert len(mock_bot.session.tables[SchedulesSpreadsheet.__tablename__]) == 1
    assert len(mock_bot.session.tables[PlayersSpreadsheet.__tablename__]) == 1
    assert len(mock_bot.session.tables[RescheduleMessage.__tablename__]) == 1
    assert len(mock_bot.session.tables[StaffRescheduleMessage.__tablename__]) == 0
    assert len(mock_bot.session.tables[EndTournamentMessage.__tablename__]) == 0
