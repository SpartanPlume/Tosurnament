"""
All tests concerning the Tosurnament tournament module.
"""

import pytest

import discord
from hypothesis import strategies, given

from bot.modules.tosurnament import tournament
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.schedules_spreadsheet import SchedulesSpreadsheet
import test.resources.mock.tosurnament as tosurnament_mock

MODULE_TO_TEST = "bot.modules.tosurnament.tournament"
BRACKET_NAME = "Bracket name"
BRACKET_NAME_2 = "Bracket name 2"

day_name_strategy = strategies.sampled_from(
    ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
)
day_time_strategy = strategies.times()


def setup_module(module):
    tosurnament_mock.setup_spreadsheets()


@pytest.mark.asyncio
async def test_create_bracket(mocker):
    """Creates a bracket."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, current_bracket_id=2))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    await cog.create_bracket(cog, tosurnament_mock.CtxMock(mock_bot), name=BRACKET_NAME)
    mock_bot.session.add.assert_called_once_with(tosurnament_mock.Matcher(Bracket(tournament_id=1, name=BRACKET_NAME)))
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(current_bracket_id=1)))
    cog.send_reply.assert_called_once_with(mocker.ANY, mocker.ANY, "success", BRACKET_NAME)


@pytest.mark.asyncio
async def test_set_tournament_values(mocker):
    """Puts the input values into the corresponding tournament."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.GUILD_ID))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    await cog.set_tournament_values(tosurnament_mock.CtxMock(mock_bot), {"current_bracket_id": 1})
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(current_bracket_id=1)))
    cog.send_reply.assert_called_once_with(mocker.ANY, mocker.ANY, "success", 1)


@pytest.mark.asyncio
async def test_set_team_captain_role():
    """Sets the team captain role."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.GUILD_ID))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))
    mock_role = tosurnament_mock.RoleMock("Team Captain Role")

    await cog.set_team_captain_role(cog, tosurnament_mock.CtxMock(mock_bot), role=mock_role)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(team_captain_role_id=1)))


@pytest.mark.asyncio
async def test_set_team_captain_role_remove():
    """Removes the team captain role."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.GUILD_ID, team_captain_role_id=1))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    await cog.set_team_captain_role(cog, tosurnament_mock.CtxMock(mock_bot))
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(team_captain_role_id=0)))


@pytest.mark.asyncio
async def test_get_bracket(mocker):
    """Shows all brackets."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, current_bracket_id=1))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, name=BRACKET_NAME))
    mock_bot.session.add_stub(Bracket(id=2, tournament_id=1, name=BRACKET_NAME_2))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    expected_output = "1: `" + BRACKET_NAME + "` (current bracket)\n"
    expected_output += "2: `" + BRACKET_NAME_2 + "`\n"

    await cog.get_bracket(cog, tosurnament_mock.CtxMock(mock_bot))
    cog.send_reply.assert_called_once_with(mocker.ANY, mocker.ANY, "default", expected_output)


@pytest.mark.asyncio
async def test_get_a_bracket(mocker):
    """Sets a bracket as current bracket."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, current_bracket_id=1))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, name=BRACKET_NAME))
    mock_bot.session.add_stub(Bracket(id=2, tournament_id=1, name=BRACKET_NAME_2))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    await cog.get_bracket(cog, tosurnament_mock.CtxMock(mock_bot), number=2)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(current_bracket_id=2)))
    cog.send_reply.assert_called_once_with(mocker.ANY, mocker.ANY, "success", BRACKET_NAME_2)


@pytest.mark.asyncio
async def test_get_a_bracket_that_does_not_exist():
    """Sets a bracket as current bracket but it does not exist."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(tournament_id=1, name=BRACKET_NAME))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    with pytest.raises(discord.ext.commands.UserInputError):
        await cog.get_bracket(cog, tosurnament_mock.CtxMock(mock_bot), number=0)


@pytest.mark.asyncio
async def test_set_reschedule_deadline_end_invalid_date():
    """Sets a reschedule deadline end but date is invalid."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    with pytest.raises(discord.ext.commands.UserInputError):
        await cog.set_reschedule_deadline_end(cog, tosurnament_mock.CtxMock(mock_bot), date="some date")


@pytest.mark.asyncio
async def test_set_reschedule_deadline_end_empty():
    """Unsets a reschedule deadline end."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(
        Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, reschedule_deadline_end="tuesday 12:00")
    )
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    await cog.set_reschedule_deadline_end(cog, tosurnament_mock.CtxMock(mock_bot), date="")
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(reschedule_deadline_end="")))


@given(day_name=day_name_strategy, day_time=day_time_strategy)
@pytest.mark.asyncio
async def test_set_reschedule_deadline_end(day_name, day_time):
    """Sets a reschedule deadline end."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID))
    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    date = day_name + day_time.strftime(" %H:%M")

    await cog.set_reschedule_deadline_end(cog, tosurnament_mock.CtxMock(mock_bot), date=date)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(reschedule_deadline_end=date)))


@pytest.mark.asyncio
async def test_add_match_to_ignore(mocker):
    """Adds a match to ignore."""
    MATCH_ID_1 = "T1-1"
    MATCH_ID_2 = "t1-2"
    MATCH_ID_3 = "T1-3"
    INVALID_MATCH_ID = "Invalid"

    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(
        Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, matches_to_ignore=MATCH_ID_3, current_bracket_id=1)
    )
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, schedules_spreadsheet_id=1))
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=1, spreadsheet_id="single", sheet_name="Tier 1"))

    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    await cog.add_match_to_ignore(cog, tosurnament_mock.CtxMock(mock_bot), MATCH_ID_1, MATCH_ID_2, INVALID_MATCH_ID)
    assert mock_bot.session.tables[Tournament.__tablename__][0].matches_to_ignore == "\n".join(
        [MATCH_ID_1, MATCH_ID_2.upper(), MATCH_ID_3]
    )
    expected_replies = [
        mocker.call(mocker.ANY, mocker.ANY, "success", " ".join([MATCH_ID_1, MATCH_ID_2.upper(), MATCH_ID_3])),
        mocker.call(mocker.ANY, mocker.ANY, "not_found", INVALID_MATCH_ID.lower()),
        mocker.call(mocker.ANY, mocker.ANY, "to_ignore", mocker.ANY, MATCH_ID_1),
        mocker.call(mocker.ANY, mocker.ANY, "to_ignore", mocker.ANY, MATCH_ID_2.upper()),
    ]
    assert cog.send_reply.call_args_list == expected_replies


@pytest.mark.asyncio
async def test_remove_match_to_ignore(mocker):
    """Removes a match to ignore."""
    MATCH_ID_1 = "T1-1"
    MATCH_ID_2 = "t1-2"
    MATCH_ID_3 = "T1-3"

    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(
        Tournament(
            id=1,
            guild_id=tosurnament_mock.GUILD_ID,
            matches_to_ignore=MATCH_ID_1 + "\n" + MATCH_ID_3,
            current_bracket_id=1,
            staff_channel_id=tosurnament_mock.ChannelMock.STAFF_CHANNEL_ID,
        )
    )
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, schedules_spreadsheet_id=1))
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=1, spreadsheet_id="single", sheet_name="Tier 1"))

    cog = tosurnament_mock.mock_cog(tournament.get_class(mock_bot))

    await cog.remove_match_to_ignore(cog, tosurnament_mock.CtxMock(mock_bot), MATCH_ID_2, MATCH_ID_3)
    assert mock_bot.session.tables[Tournament.__tablename__][0].matches_to_ignore == MATCH_ID_1
    expected_replies = [
        mocker.call(mocker.ANY, mocker.ANY, "success", MATCH_ID_1),
        mocker.call(
            tosurnament_mock.ChannelMock(tosurnament_mock.ChannelMock.STAFF_CHANNEL_ID),
            mocker.ANY,
            "to_not_ignore",
            mocker.ANY,
            MATCH_ID_3,
        ),
    ]
    assert cog.send_reply.call_args_list == expected_replies
