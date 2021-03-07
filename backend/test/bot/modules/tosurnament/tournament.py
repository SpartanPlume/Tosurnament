"""
All tests concerning the Tosurnament tournament module.
"""

import pytest
from unittest import mock

import asyncio
import discord
from hypothesis import strategies, given

from bot.modules.tosurnament import tournament as tournament_module
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.base_spreadsheet import BaseSpreadsheet
from common.databases.players_spreadsheet import PlayersSpreadsheet
from common.databases.schedules_spreadsheet import SchedulesSpreadsheet, MatchInfo
from common.api.spreadsheet import Cell
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


def init_mocks():
    mock_bot = tosurnament_mock.BotMock()
    tournament = Tournament(guild_id=tosurnament_mock.GUILD_ID)
    mock_bot.session.add_stub(tournament)
    cog = tosurnament_mock.mock_cog(tournament_module.get_class(mock_bot))
    return cog, mock_bot, tournament


@pytest.mark.asyncio
async def test_set_tournament_values(mocker):
    """Puts the input values into the corresponding tournament."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.GUILD_ID))
    cog = tosurnament_mock.mock_cog(tournament_module.get_class(mock_bot))

    await cog.set_tournament_values(tosurnament_mock.CtxMock(mock_bot), {"current_bracket_id": 1})
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(current_bracket_id=1)))
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", 1)


@pytest.mark.asyncio
async def test_create_bracket(mocker):
    """Creates a bracket."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, current_bracket_id=2))
    cog = tosurnament_mock.mock_cog(tournament_module.get_class(mock_bot))

    await cog.create_bracket(cog, tosurnament_mock.CtxMock(mock_bot), name=BRACKET_NAME)
    mock_bot.session.add.assert_called_once_with(tosurnament_mock.Matcher(Bracket(tournament_id=1, name=BRACKET_NAME)))
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(current_bracket_id=1)))
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", BRACKET_NAME)


@pytest.mark.asyncio
async def test_get_bracket(mocker):
    """Shows all brackets."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, current_bracket_id=1))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, name=BRACKET_NAME))
    mock_bot.session.add_stub(Bracket(id=2, tournament_id=1, name=BRACKET_NAME_2))
    cog = tosurnament_mock.mock_cog(tournament_module.get_class(mock_bot))

    expected_output = "1: `" + BRACKET_NAME + "` (current bracket)\n"
    expected_output += "2: `" + BRACKET_NAME_2 + "`\n"

    await cog.get_bracket(cog, tosurnament_mock.CtxMock(mock_bot))
    cog.send_reply.assert_called_once_with(mocker.ANY, "default", expected_output)


@pytest.mark.asyncio
async def test_get_a_bracket(mocker):
    """Sets a bracket as current bracket."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, current_bracket_id=1))
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, name=BRACKET_NAME))
    mock_bot.session.add_stub(Bracket(id=2, tournament_id=1, name=BRACKET_NAME_2))
    cog = tosurnament_mock.mock_cog(tournament_module.get_class(mock_bot))

    await cog.get_bracket(cog, tosurnament_mock.CtxMock(mock_bot), number=2)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(current_bracket_id=2)))
    cog.send_reply.assert_called_once_with(mocker.ANY, "success", BRACKET_NAME_2)


@pytest.mark.asyncio
async def test_get_a_bracket_that_does_not_exist():
    """Sets a bracket as current bracket but it does not exist."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID))
    mock_bot.session.add_stub(Bracket(tournament_id=1, name=BRACKET_NAME))
    mock_bot.session.add_stub(Bracket(tournament_id=1, name=BRACKET_NAME_2))
    cog = tosurnament_mock.mock_cog(tournament_module.get_class(mock_bot))

    with pytest.raises(discord.ext.commands.UserInputError):
        await cog.get_bracket(cog, tosurnament_mock.CtxMock(mock_bot), number=0)


@pytest.mark.asyncio
async def test_set_tournament_name():
    """Sets the tournament name."""
    cog, mock_bot, tournament = init_mocks()
    new_name = "New Name"
    assert tournament.name != new_name
    await cog.set_tournament_name(cog, tosurnament_mock.CtxMock(mock_bot), name=new_name)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(name=new_name)))


@pytest.mark.asyncio
async def test_set_tournament_acronym():
    """Sets the tournament acronym."""
    cog, mock_bot, tournament = init_mocks()
    new_acronym = "NA"
    assert tournament.acronym != new_acronym
    await cog.set_tournament_acronym(cog, tosurnament_mock.CtxMock(mock_bot), acronym=new_acronym)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(acronym=new_acronym)))


@pytest.mark.asyncio
async def test_set_staff_channel():
    """Sets the tournament staff channel."""
    cog, mock_bot, tournament = init_mocks()
    new_channel = tosurnament_mock.ChannelMock(123456)
    assert tournament.staff_channel_id != new_channel.id
    await cog.set_staff_channel(cog, tosurnament_mock.CtxMock(mock_bot), channel=new_channel)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(staff_channel_id=new_channel.id))
    )


@pytest.mark.asyncio
async def test_set_match_notification_channel():
    """Sets the tournament match notification channel."""
    cog, mock_bot, tournament = init_mocks()
    new_channel = tosurnament_mock.ChannelMock(123456)
    assert tournament.match_notification_channel_id != new_channel.id
    await cog.set_match_notification_channel(cog, tosurnament_mock.CtxMock(mock_bot), channel=new_channel)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(match_notification_channel_id=new_channel.id))
    )


@pytest.mark.asyncio
async def test_set_referee_role():
    """Sets the referee role."""
    cog, mock_bot, tournament = init_mocks()
    new_role = tosurnament_mock.RoleMock("Referee Role", 123456)
    assert tournament.referee_role_id != new_role.id
    await cog.set_referee_role(cog, tosurnament_mock.CtxMock(mock_bot), role=new_role)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(referee_role_id=new_role.id)))


@pytest.mark.asyncio
async def test_set_streamer_role():
    """Sets the streamer role."""
    cog, mock_bot, tournament = init_mocks()
    new_role = tosurnament_mock.RoleMock("Streamer Role", 123456)
    assert tournament.streamer_role_id != new_role.id
    await cog.set_streamer_role(cog, tosurnament_mock.CtxMock(mock_bot), role=new_role)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(streamer_role_id=new_role.id)))


@pytest.mark.asyncio
async def test_set_commentator_role():
    """Sets the commentator role."""
    cog, mock_bot, tournament = init_mocks()
    new_role = tosurnament_mock.RoleMock("Commentator Role", 123456)
    assert tournament.commentator_role_id != new_role.id
    await cog.set_commentator_role(cog, tosurnament_mock.CtxMock(mock_bot), role=new_role)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(commentator_role_id=new_role.id))
    )


@pytest.mark.asyncio
async def test_set_player_role():
    """Sets the player role."""
    cog, mock_bot, tournament = init_mocks()
    new_role = tosurnament_mock.RoleMock("Player Role", 123456)
    assert tournament.player_role_id != new_role.id
    await cog.set_player_role(cog, tosurnament_mock.CtxMock(mock_bot), role=new_role)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(player_role_id=new_role.id)))


@pytest.mark.asyncio
async def test_set_team_captain_role():
    """Sets the team captain role."""
    cog, mock_bot, tournament = init_mocks()
    new_role = tosurnament_mock.RoleMock("Team Captain Role", 123456)
    assert tournament.team_captain_role_id != new_role.id
    await cog.set_team_captain_role(cog, tosurnament_mock.CtxMock(mock_bot), role=new_role)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(team_captain_role_id=new_role.id))
    )


@pytest.mark.asyncio
async def test_set_team_captain_role_remove():
    """Removes the team captain role."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.GUILD_ID, team_captain_role_id=1))
    cog = tosurnament_mock.mock_cog(tournament_module.get_class(mock_bot))

    await cog.set_team_captain_role(cog, tosurnament_mock.CtxMock(mock_bot))
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(team_captain_role_id=0)))


@pytest.mark.asyncio
async def test_set_ping_team():
    """Sets if team should be pinged or team captain should be pinged."""
    cog, mock_bot, tournament = init_mocks()
    assert tournament.reschedule_ping_team
    await cog.set_ping_team(cog, tosurnament_mock.CtxMock(mock_bot), ping_team=False)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(reschedule_ping_team=False)))


@pytest.mark.asyncio
async def test_set_post_result_message():
    """Sets the post result message."""
    cog, mock_bot, tournament = init_mocks()
    message = "A new message"
    assert tournament.post_result_message != message
    await cog.set_post_result_message(cog, tosurnament_mock.CtxMock(mock_bot), message=message)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(post_result_message=message)))


@pytest.mark.asyncio
async def test_set_post_result_message_team1_with_score():
    """Sets the post result message."""
    cog, mock_bot, tournament = init_mocks()
    message = "A new message"
    assert tournament.post_result_message_team1_with_score != message
    await cog.set_post_result_message_team1_with_score(cog, tosurnament_mock.CtxMock(mock_bot), message=message)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(post_result_message_team1_with_score=message))
    )


@pytest.mark.asyncio
async def test_set_post_result_message_team2_with_score():
    """Sets the post result message."""
    cog, mock_bot, tournament = init_mocks()
    message = "A new message"
    assert tournament.post_result_message_team2_with_score != message
    await cog.set_post_result_message_team2_with_score(cog, tosurnament_mock.CtxMock(mock_bot), message=message)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(post_result_message_team2_with_score=message))
    )


@pytest.mark.asyncio
async def test_set_post_result_message_mp_link():
    """Sets the post result message."""
    cog, mock_bot, tournament = init_mocks()
    message = "A new message"
    assert tournament.post_result_message_mp_link != message
    await cog.set_post_result_message_mp_link(cog, tosurnament_mock.CtxMock(mock_bot), message=message)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(post_result_message_mp_link=message))
    )


@pytest.mark.asyncio
async def test_set_post_result_message_rolls():
    """Sets the post result message."""
    cog, mock_bot, tournament = init_mocks()
    message = "A new message"
    assert tournament.post_result_message_rolls != message
    await cog.set_post_result_message_rolls(cog, tosurnament_mock.CtxMock(mock_bot), message=message)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(post_result_message_rolls=message))
    )


@pytest.mark.asyncio
async def test_set_post_result_message_bans():
    """Sets the post result message."""
    cog, mock_bot, tournament = init_mocks()
    message = "A new message"
    assert tournament.post_result_message_bans != message
    await cog.set_post_result_message_bans(cog, tosurnament_mock.CtxMock(mock_bot), message=message)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(post_result_message_bans=message))
    )


@pytest.mark.asyncio
async def test_set_post_result_message_tb_bans():
    """Sets the post result message."""
    cog, mock_bot, tournament = init_mocks()
    message = "A new message"
    assert tournament.post_result_message_tb_bans != message
    await cog.set_post_result_message_tb_bans(cog, tosurnament_mock.CtxMock(mock_bot), message=message)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(post_result_message_tb_bans=message))
    )


@pytest.mark.asyncio
async def test_set_reschedule_deadline_hours_before_current_time():
    """Allows to change the deadline (in hours) before the current match time to reschedule a match."""
    cog, mock_bot, tournament = init_mocks()
    hours = 2
    assert tournament.reschedule_deadline_hours_before_current_time != hours
    await cog.set_reschedule_deadline_hours_before_current_time(cog, tosurnament_mock.CtxMock(mock_bot), hours=hours)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(reschedule_deadline_hours_before_current_time=hours))
    )


@pytest.mark.asyncio
async def test_set_reschedule_deadline_hours_before_new_time():
    """Allows to change the deadline (in hours) before the new match time to reschedule a match."""
    cog, mock_bot, tournament = init_mocks()
    hours = 2
    assert tournament.reschedule_deadline_hours_before_new_time != hours
    await cog.set_reschedule_deadline_hours_before_new_time(cog, tosurnament_mock.CtxMock(mock_bot), hours=hours)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(reschedule_deadline_hours_before_new_time=hours))
    )


@pytest.mark.asyncio
async def test_set_reschedule_deadline_end_invalid_date():
    """Sets a reschedule deadline end but date is invalid."""
    cog, mock_bot, _ = init_mocks()
    with pytest.raises(discord.ext.commands.UserInputError):
        await cog.set_reschedule_deadline_end(cog, tosurnament_mock.CtxMock(mock_bot), date="some date")


@pytest.mark.asyncio
async def test_set_reschedule_deadline_end_empty():
    """Unsets a reschedule deadline end."""
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(
        Tournament(id=1, guild_id=tosurnament_mock.GUILD_ID, reschedule_deadline_end="tuesday 12:00")
    )
    cog = tosurnament_mock.mock_cog(tournament_module.get_class(mock_bot))

    await cog.set_reschedule_deadline_end(cog, tosurnament_mock.CtxMock(mock_bot), date="")
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(reschedule_deadline_end="")))


@given(day_name=day_name_strategy, day_time=day_time_strategy)
@pytest.mark.asyncio
async def test_set_reschedule_deadline_end(day_name, day_time):
    """Sets a reschedule deadline end."""
    cog, mock_bot, _ = init_mocks()
    date = day_name + day_time.strftime(" %H:%M")
    await cog.set_reschedule_deadline_end(cog, tosurnament_mock.CtxMock(mock_bot), date=date)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(reschedule_deadline_end=date)))


@pytest.mark.asyncio
async def test_set_notify_no_staff_reschedule():
    cog, mock_bot, tournament = init_mocks()
    assert tournament.notify_no_staff_reschedule
    await cog.set_notify_no_staff_reschedule(cog, tosurnament_mock.CtxMock(mock_bot), notify=False)
    mock_bot.session.update.assert_called_once_with(
        tosurnament_mock.Matcher(Tournament(notify_no_staff_reschedule=False))
    )


@pytest.mark.asyncio
async def test_set_utc_empty():
    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(Tournament(guild_id=tosurnament_mock.GUILD_ID, utc="+02:00"))
    cog = tosurnament_mock.mock_cog(tournament_module.get_class(mock_bot))
    await cog.set_utc(cog, tosurnament_mock.CtxMock(mock_bot), utc="")
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(utc="")))


@pytest.mark.asyncio
async def test_set_utc_input_error():
    cog, mock_bot, tournament = init_mocks()
    new_utc = "new_utc"
    assert tournament.utc != new_utc
    with pytest.raises(discord.ext.commands.UserInputError):
        await cog.set_utc(cog, tosurnament_mock.CtxMock(mock_bot), utc=new_utc)


@pytest.mark.asyncio
async def test_set_utc_invalid():
    cog, mock_bot, tournament = init_mocks()
    new_utc = "+08:32"
    assert tournament.utc != new_utc
    with pytest.raises(discord.ext.commands.UserInputError):
        await cog.set_utc(cog, tosurnament_mock.CtxMock(mock_bot), utc=new_utc)


@pytest.mark.asyncio
async def test_set_utc():
    cog, mock_bot, tournament = init_mocks()
    new_utc = "+02:00"
    assert tournament.utc != new_utc
    await cog.set_utc(cog, tosurnament_mock.CtxMock(mock_bot), utc=new_utc)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(utc=new_utc)))


@pytest.mark.asyncio
async def test_set_registration_phase():
    cog, mock_bot, tournament = init_mocks()
    assert not tournament.registration_phase
    await cog.set_registration_phase(cog, tosurnament_mock.CtxMock(mock_bot), boolean=True)
    mock_bot.session.update.assert_called_once_with(tosurnament_mock.Matcher(Tournament(registration_phase=True)))


@pytest.mark.asyncio
async def test_add_match_to_ignore(mocker):
    """Adds a match to ignore."""
    MATCH_ID_1 = "T1-1"
    MATCH_ID_2 = "t1-2"
    MATCH_ID_3 = "T1-3"
    INVALID_MATCH_ID = "Invalid"

    mock_bot = tosurnament_mock.BotMock()
    mock_bot.session.add_stub(
        Tournament(
            id=1,
            guild_id=tosurnament_mock.GUILD_ID,
            matches_to_ignore=MATCH_ID_3,
            current_bracket_id=1,
        )
    )
    mock_bot.session.add_stub(Bracket(id=1, tournament_id=1, schedules_spreadsheet_id=1))
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=1, spreadsheet_id="single", sheet_name="Tier 1"))

    cog = tosurnament_mock.mock_cog(tournament_module.get_class(mock_bot))
    cog.get_match_infos_from_id = mocker.AsyncMock(
        return_value=[
            MatchInfo(Cell(-1, -1, MATCH_ID_1)),
            MatchInfo(Cell(-1, -1, MATCH_ID_2.upper())),
        ]
    )

    mock_ctx = tosurnament_mock.CtxMock(mock_bot)
    await cog.add_match_to_ignore(cog, mock_ctx, MATCH_ID_1, MATCH_ID_2, INVALID_MATCH_ID)
    assert mock_bot.session.tables[Tournament.__tablename__][0].matches_to_ignore == "\n".join(
        [MATCH_ID_1, MATCH_ID_2.upper(), MATCH_ID_3]
    )
    expected_replies = [
        mocker.call(mocker.ANY, "success", " ".join([MATCH_ID_1, MATCH_ID_2.upper(), MATCH_ID_3])),
        mocker.call(mocker.ANY, "not_found", INVALID_MATCH_ID),
        mocker.call(mocker.ANY, "to_ignore", mocker.ANY, MATCH_ID_1, channel=mock_ctx),
        mocker.call(
            mocker.ANY,
            "to_ignore",
            mocker.ANY,
            MATCH_ID_2.upper(),
            channel=mock_ctx,
        ),
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

    cog = tosurnament_mock.mock_cog(tournament_module.get_class(mock_bot))
    cog.get_match_infos_from_id = mocker.AsyncMock(
        return_value=[
            MatchInfo(Cell(-1, -1, MATCH_ID_2.upper())),
            MatchInfo(Cell(-1, -1, MATCH_ID_3)),
        ]
    )

    await cog.remove_match_to_ignore(cog, tosurnament_mock.CtxMock(mock_bot), MATCH_ID_2, MATCH_ID_3)
    assert mock_bot.session.tables[Tournament.__tablename__][0].matches_to_ignore == MATCH_ID_1
    expected_replies = [
        mocker.call(mocker.ANY, "success", MATCH_ID_1),
        mocker.call(mocker.ANY, "not_found", MATCH_ID_2),
        mocker.call(
            mocker.ANY,
            "to_not_ignore",
            mocker.ANY,
            MATCH_ID_3,
            channel=tosurnament_mock.ChannelMock(tosurnament_mock.ChannelMock.STAFF_CHANNEL_ID),
        ),
    ]
    assert cog.send_reply.call_args_list == expected_replies


@pytest.mark.asyncio
async def test_sync_spreadsheet_no_spreadsheet(mocker):
    """Synchronizes local version of the spreadsheets with the online versions."""
    get_spreadsheet_mock = mocker.MagicMock(side_effect=(lambda x: x))
    cog, mock_bot, tournament = init_mocks()
    mock_bot.session.add_stub(Bracket(tournament_id=tournament.id))
    with mock.patch.object(BaseSpreadsheet, "get_spreadsheet", new=get_spreadsheet_mock):
        await cog.sync_spreadsheet(cog, tosurnament_mock.CtxMock(mock_bot))
    assert get_spreadsheet_mock.call_count == 0


@pytest.mark.asyncio
async def test_sync_spreadsheet_players_spreadsheet(mocker):
    """Synchronizes local version of the spreadsheets with the online versions."""
    get_spreadsheet_mock = mocker.AsyncMock()
    cog, mock_bot, tournament = init_mocks()
    mock_bot.session.add_stub(PlayersSpreadsheet(id=1, spreadsheet_id=1))
    mock_bot.session.add_stub(Bracket(tournament_id=tournament.id, players_spreadsheet_id=1))
    with mock.patch.object(BaseSpreadsheet, "get_spreadsheet", new=get_spreadsheet_mock):
        await cog.sync_spreadsheet(cog, tosurnament_mock.CtxMock(mock_bot))
    assert get_spreadsheet_mock.call_count == 1


@pytest.mark.asyncio
async def test_sync_spreadsheet_schedules_spreadsheet(mocker):
    """Synchronizes local version of the spreadsheets with the online versions."""
    get_spreadsheet_mock = mocker.AsyncMock()
    cog, mock_bot, tournament = init_mocks()
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=1, spreadsheet_id=1))
    mock_bot.session.add_stub(Bracket(tournament_id=tournament.id, schedules_spreadsheet_id=1))
    with mock.patch.object(BaseSpreadsheet, "get_spreadsheet", new=get_spreadsheet_mock):
        await cog.sync_spreadsheet(cog, tosurnament_mock.CtxMock(mock_bot))
    assert get_spreadsheet_mock.call_count == 1


@pytest.mark.asyncio
async def test_sync_spreadsheet_two_spreadsheets_same_id(mocker):
    """Synchronizes local version of the spreadsheets with the online versions."""
    get_spreadsheet_mock = mocker.AsyncMock()
    cog, mock_bot, tournament = init_mocks()
    mock_bot.session.add_stub(PlayersSpreadsheet(id=1, spreadsheet_id=1))
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=1, spreadsheet_id=1))
    mock_bot.session.add_stub(
        Bracket(tournament_id=tournament.id, players_spreadsheet_id=1, schedules_spreadsheet_id=1)
    )
    with mock.patch.object(BaseSpreadsheet, "get_spreadsheet", new=get_spreadsheet_mock):
        await cog.sync_spreadsheet(cog, tosurnament_mock.CtxMock(mock_bot))
    assert get_spreadsheet_mock.call_count == 1


@pytest.mark.asyncio
async def test_sync_spreadsheet_two_spreadsheets_different_id(mocker):
    """Synchronizes local version of the spreadsheets with the online versions."""
    get_spreadsheet_mock = mocker.AsyncMock()
    cog, mock_bot, tournament = init_mocks()
    mock_bot.session.add_stub(PlayersSpreadsheet(id=1, spreadsheet_id=1))
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=1, spreadsheet_id=2))
    mock_bot.session.add_stub(
        Bracket(tournament_id=tournament.id, players_spreadsheet_id=1, schedules_spreadsheet_id=1)
    )
    with mock.patch.object(BaseSpreadsheet, "get_spreadsheet", new=get_spreadsheet_mock):
        await cog.sync_spreadsheet(cog, tosurnament_mock.CtxMock(mock_bot))
    assert get_spreadsheet_mock.call_count == 2


@pytest.mark.asyncio
async def test_sync_spreadsheet_two_brackets_same_id(mocker):
    """Synchronizes local version of the spreadsheets with the online versions."""
    get_spreadsheet_mock = mocker.AsyncMock()
    cog, mock_bot, tournament = init_mocks()
    mock_bot.session.add_stub(PlayersSpreadsheet(id=1, spreadsheet_id=1))
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=1, spreadsheet_id=1))
    mock_bot.session.add_stub(Bracket(tournament_id=tournament.id, players_spreadsheet_id=1))
    mock_bot.session.add_stub(Bracket(tournament_id=tournament.id, schedules_spreadsheet_id=1))
    with mock.patch.object(BaseSpreadsheet, "get_spreadsheet", new=get_spreadsheet_mock):
        await cog.sync_spreadsheet(cog, tosurnament_mock.CtxMock(mock_bot))
    assert get_spreadsheet_mock.call_count == 1


@pytest.mark.asyncio
async def test_sync_spreadsheet_two_brackets_different_id(mocker):
    """Synchronizes local version of the spreadsheets with the online versions."""
    get_spreadsheet_mock = mocker.AsyncMock()
    cog, mock_bot, tournament = init_mocks()
    mock_bot.session.add_stub(PlayersSpreadsheet(id=1, spreadsheet_id=1))
    mock_bot.session.add_stub(SchedulesSpreadsheet(id=1, spreadsheet_id=2))
    mock_bot.session.add_stub(Bracket(tournament_id=tournament.id, players_spreadsheet_id=1))
    mock_bot.session.add_stub(Bracket(tournament_id=tournament.id, schedules_spreadsheet_id=1))
    with mock.patch.object(BaseSpreadsheet, "get_spreadsheet", new=get_spreadsheet_mock):
        await cog.sync_spreadsheet(cog, tosurnament_mock.CtxMock(mock_bot))
    assert get_spreadsheet_mock.call_count == 2
