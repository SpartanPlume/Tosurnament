"""Player commands"""

import re
import asyncio
import datetime
import dateutil
import dateparser
import discord
from discord.ext import commands, tasks
from discord.utils import escape_markdown
from bot.modules.tosurnament import module as tosurnament
from common.databases.tosurnament.spreadsheets.players_spreadsheet import TeamInfo, TeamNotFound
from common.databases.tosurnament.spreadsheets.schedules_spreadsheet import MatchInfo, MatchIdNotFound, DateIsNotString
from common.databases.tosurnament.spreadsheets.qualifiers_spreadsheet import LobbyIdNotFound, LobbyInfo
from common.databases.tosurnament_message.reschedule_message import RescheduleMessage
from common.databases.tosurnament_message.staff_reschedule_message import StaffRescheduleMessage
from common.databases.tosurnament_message.base_message import with_corresponding_message, on_raw_reaction_with_context
from common.api import osu
from common.api import tosurnament as tosurnament_api
from common.api import challonge as challonge_api


class TosurnamentPlayerCog(tosurnament.TosurnamentBaseModule, name="player"):
    """Tosurnament player commands"""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.background_task_give_player_role.start()

    def cog_unload(self):
        self.background_task_give_player_role.cancel()
        
    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @commands.command()
    @commands.bot_has_permissions(manage_nicknames=True, manage_roles=True)
    async def register(self, ctx, timezone: str = ""):  # TODO handle teams + multiples brackets
        """Registers the player to the tournament."""
        verified_user = self.get_verified_user(ctx.author.id)
        tournament = self.get_tournament(ctx.guild.id)
        if len(tournament.brackets) != 1:
            await self.send_reply(ctx, "not_supported_yet")
            return
        player_role = tosurnament.get_role(ctx.guild.roles, tournament.player_role_id, "Player")
        if not player_role:
            raise tosurnament.RoleDoesNotExist("Player")
        # TODO: should check if name/discord_id/discord already present
        if tosurnament.get_role(ctx.author.roles, tournament.player_role_id, "Player"):
            raise tosurnament.UserAlreadyPlayer()
        bracket = tournament.current_bracket
        if bracket.registration_end_date:
            registration_end_date = datetime.datetime.strptime(
                bracket.registration_end_date, tosurnament.DATABASE_DATE_FORMAT
            )
            if datetime.datetime.now() > registration_end_date:
                raise tosurnament.RegistrationEnded()

        players_spreadsheet = await bracket.get_players_spreadsheet()
        if not players_spreadsheet:
            raise tosurnament.NoSpreadsheet("players")
        if players_spreadsheet.range_team_name:
            await self.send_reply(ctx, "not_supported_yet")
            return
        if players_spreadsheet.range_timezone:
            if not timezone:
                raise commands.UserInputError()
            if not re.match(r"(UTC)?[-\+]([0-9]|1[0-4])(:[0-5][0-9])?$", timezone, re.IGNORECASE):
                raise tosurnament.InvalidTimezone(timezone)
            timezone = "UTC" + re.sub(r"^UTC", "", timezone, flags=re.IGNORECASE)
        osu_user = osu.get_user(verified_user.osu_id, m=tournament.game_mode)
        if not osu_user:
            raise tosurnament.UserNotFound(verified_user.osu_id)
        osu_rank = int(osu_user.rank)
        if osu_rank < bracket.minimum_rank or (bracket.maximum_rank > 0 and osu_rank > bracket.maximum_rank):
            raise tosurnament.NotInRankRange()
        team_info = TeamInfo.get_first_blank_fields(players_spreadsheet)
        player_info = team_info.players[0]
        player_info.name.set(osu_user.name)
        player_info.discord.set(str(ctx.author))
        player_info.discord_id.set(str(ctx.author.id))
        player_info.rank.set(str(osu_rank))
        player_info.bws_rank.set(str(osu_rank))
        player_info.osu_id.set(str(osu_user.id))
        player_info.pp.set(str(int(float(osu_user.pp))))
        player_info.country.set(str(osu_user.country))
        team_info.timezone.set(timezone)
        await self.add_update_spreadsheet_background_task(players_spreadsheet)
        roles_to_give = [tosurnament.get_role(ctx.guild.roles, tournament.player_role_id, "Player")]
        roles_to_give.append(tosurnament.get_role(ctx.guild.roles, bracket.role_id, bracket.name))
        await ctx.author.add_roles(*filter(None, roles_to_give))
        try:
            await ctx.author.edit(nick=osu_user.name)
        except Exception:
            pass
        if bracket.challonge:
            try:
                challonge_api.add_participant_to_tournament(bracket.challonge, osu_user.name)
            except Exception:
                tosurnament_guild = self.get_guild(ctx.guild.id)
                admin_role = tosurnament.get_role(ctx.guild.roles, tosurnament_guild.admin_role_id)
                await self.send_reply(
                    ctx, "challonge_participant_addition_error", admin_role if admin_role else "Admins", osu_user.name
                )
        await self.send_reply(ctx, "success")

    @register.error
    async def register_handler(self, ctx, error):
        """Error handler of register function."""
        if isinstance(error, tosurnament.InvalidTimezone):
            await self.send_reply(ctx, "invalid_timezone", error.timezone)
        elif isinstance(error, tosurnament.RegistrationEnded):
            await self.send_reply(ctx, "registration_ended")
        elif isinstance(error, tosurnament.NotInRankRange):
            await self.send_reply(ctx, "not_in_rank_range")

    def clear_team_from_other_lobbies(self, qualifiers_spreadsheet, lobby_id, team_name):
        """Removes the team name from other lobbies if present."""
        lobby_id_cells = qualifiers_spreadsheet.spreadsheet.get_cells_with_value_in_range(
            qualifiers_spreadsheet.range_lobby_id
        )
        for lobby_id_cell in lobby_id_cells:
            lobby_info = LobbyInfo.from_lobby_id_cell(qualifiers_spreadsheet, lobby_id_cell, filled_only=False)
            if lobby_info.lobby_id.casefold() != lobby_id.casefold():
                for team_cell in lobby_info.teams:
                    if team_name.casefold() == team_cell.casefold():
                        team_cell.set("")
                        return

    def add_team_to_lobby(self, qualifiers_spreadsheet, lobby_id, team_name):
        """Adds the team name to the lobby if found, not already in the lobby and the lobby is not full."""
        try:
            lobby_info = LobbyInfo.from_id(qualifiers_spreadsheet, lobby_id, filled_only=False)
        except LobbyIdNotFound:
            return False
        first_empty_cell = None
        for team_cell in lobby_info.teams:
            if first_empty_cell is None and not team_cell:
                first_empty_cell = team_cell
            if team_name.casefold() == team_cell.casefold():
                raise tosurnament.AlreadyInLobby()
        if first_empty_cell is None:
            raise tosurnament.LobbyIsFull()
        first_empty_cell.set(team_name)
        return True

    async def get_team_of_author(self, ctx, players_spreadsheet):
        team_infos, _ = await self.get_all_teams_infos_and_roles(ctx.guild, players_spreadsheet)
        user_name = None
        user = tosurnament.UserAbstraction.get_from_ctx(ctx)
        if user and user.verified:
            user_name = user.name
        for team_info in team_infos:
            player = team_info.find_player(user_name, ctx.author.id, str(ctx.author))
            if player:
                return team_info
        return None

    @commands.command(aliases=["rtl"])
    async def register_to_lobby(self, ctx, *, lobby_id: str):
        """Registers to a qualifier lobby."""
        tournament = self.get_tournament(ctx.guild.id)
        qualifiers_spreadsheet_found = False
        team_found = False
        for bracket in tournament.brackets:
            qualifiers_spreadsheet = await bracket.get_qualifiers_spreadsheet()
            if not qualifiers_spreadsheet:
                continue
            qualifiers_spreadsheet_found = True
            players_spreadsheet = await bracket.get_players_spreadsheet()
            if not players_spreadsheet:
                raise tosurnament.NoSpreadsheet("players")
            team_info = await self.get_team_of_author(ctx, players_spreadsheet)
            if not team_info:
                continue
            team_found = True
            team_name = team_info.team_name.get()
            if not self.add_team_to_lobby(qualifiers_spreadsheet, lobby_id, team_name):
                continue
            self.clear_team_from_other_lobbies(qualifiers_spreadsheet, lobby_id, team_name)
            await self.add_update_spreadsheet_background_task(qualifiers_spreadsheet)
            await self.send_reply(ctx, "success", lobby_id)
            return
        if not qualifiers_spreadsheet_found:
            raise tosurnament.NoSpreadsheet("qualifiers")
        if not team_found:
            raise tosurnament.NotAPlayer()
        raise tosurnament.LobbyNotFound(lobby_id)

    @register_to_lobby.error
    async def register_to_lobby_handler(self, ctx, error):
        """Error handler of register_to_lobby function."""
        if isinstance(error, tosurnament.AlreadyInLobby):
            await self.send_reply(ctx, "already_in_lobby")
        elif isinstance(error, tosurnament.LobbyNotFound):
            await self.send_reply(ctx, "lobby_not_found")
        elif isinstance(error, tosurnament.LobbyIsFull):
            await self.send_reply(ctx, "lobby_is_full")

    async def get_player_role_for_bracket(self, guild, tournament, member, player_role):
        """Gives the player role of the bracket to the user, if he is a player of this bracket."""
        bracket = tournament.current_bracket
        team_infos, _ = await self.get_all_teams_infos_and_roles(guild, await bracket.get_players_spreadsheet())
        for team_info in team_infos:
            player = self.get_player_in_team(member, team_info)
            if not player:
                continue
            roles_to_give = [player_role]
            team_name = team_info.team_name.get()
            team_role = tosurnament.get_role(guild.roles, None, team_name)
            if not team_role:
                try:
                    team_role = await guild.create_role(name=team_name, mentionable=False)
                except discord.InvalidArgument:
                    raise tosurnament.InvalidRoleName(team_name)
            if team_role:
                roles_to_give.append(team_role)
            if player.is_captain:
                team_captain_role = tosurnament.get_role(guild.roles, tournament.team_captain_role_id, "Team Captain")
                if team_captain_role:
                    roles_to_give.append(team_captain_role)
            await member.add_roles(*roles_to_give)
            return True
        return False

    async def get_player_role_for_user(self, ctx, guild, member):
        """Gives the corresponding player role to the user."""
        tournament = self.get_tournament(guild.id)
        player_role_id = tournament.player_role_id
        if tosurnament.get_role(member.roles, player_role_id, "Player"):
            raise tosurnament.UserAlreadyPlayer()
        player_role = tosurnament.get_role(guild.roles, player_role_id, "Player")
        if not player_role:
            raise tosurnament.RoleDoesNotExist("Player")
        got_role = False
        for bracket in tournament.brackets:
            tournament.current_bracket_id = bracket.id
            try:
                got_role |= await self.get_player_role_for_bracket(guild, tournament, member, player_role)
            except Exception as e:
                if ctx:
                    await self.on_cog_command_error(ctx, e)
        return got_role

    @commands.command()
    @commands.bot_has_permissions(manage_nicknames=True, manage_roles=True)
    async def get_player_role(self, ctx):
        """Gives a player the player related roles, if applicable."""
        got_role = await self.get_player_role_for_user(ctx, ctx.guild, ctx.author)
        if got_role:
            await self.send_reply(ctx, "success")
        else:
            raise tosurnament.NotAPlayer()

    def validate_reschedule_feasibility(
        self, ctx, tournament, schedules_spreadsheet, match_info, new_date, skip_deadline_validation
    ):
        date_format = "%d %B"
        if schedules_spreadsheet.date_format:
            date_format = schedules_spreadsheet.date_format
        previous_date_string = match_info.get_datetime()
        if not previous_date_string:
            return None
        previous_date = tournament.parse_date(previous_date_string, date_formats=[date_format + " %H:%M"])
        if not previous_date:
            raise tosurnament.InvalidDateOrFormat()
        if not skip_deadline_validation:
            reschedule_deadline_hours = tournament.reschedule_deadline_hours_before_current_time
            deadline = previous_date - datetime.timedelta(hours=reschedule_deadline_hours)
            now = datetime.datetime.now(datetime.timezone.utc)
            if now > deadline:
                referees_mentions = self.get_referees_mentions_of_match(ctx, match_info)
                raise tosurnament.PastDeadline(reschedule_deadline_hours, referees_mentions, match_info.match_id.get())
            if tournament.reschedule_deadline_end:
                deadline_end = tournament.parse_date(
                    tournament.reschedule_deadline_end, prefer_dates_from="future", relative_base=previous_date
                )
                if new_date >= deadline_end:
                    raise tosurnament.PastDeadlineEnd()
                if tournament.reschedule_before_date:
                    before_date = tournament.parse_date(
                        tournament.reschedule_before_date, prefer_dates_from="past", relative_base=deadline_end
                    )
                    if now >= before_date:
                        raise tosurnament.PastAllowedDate()
        if previous_date == new_date:
            raise tosurnament.SameDate()
        return previous_date

    def validate_new_date(self, ctx, tournament, match_info, new_date, skip_deadline_validation):
        reschedule_deadline_hours = tournament.reschedule_deadline_hours_before_new_time
        if skip_deadline_validation:
            reschedule_deadline_hours = 0
        now = datetime.datetime.now(datetime.timezone.utc)
        if now > new_date:
            raise tosurnament.TimeInThePast()
        if new_date.minute % 15 != 0:
            raise tosurnament.InvalidMinute()
        deadline = new_date - datetime.timedelta(hours=reschedule_deadline_hours)
        if new_date.hour == 0 and new_date.minute == 0:
            new_date = new_date - datetime.timedelta(minutes=1)
        if now > deadline:
            referees_mentions = self.get_referees_mentions_of_match(ctx, match_info)
            raise tosurnament.ImpossibleReschedule(
                reschedule_deadline_hours, referees_mentions, match_info.match_id.get()
            )
        return new_date

    def get_referees_mentions_of_match(self, ctx, match_info):
        referees_to_ping, _ = self.find_staff_to_ping(ctx.guild, match_info.referees)
        referees_mentions = " / ".join([referee.mention for referee in referees_to_ping])
        if not referees_mentions:
            tosurnament_guild = self.get_guild(ctx.guild.id)
            admin_role = tosurnament.get_role(ctx.guild.roles, tosurnament_guild.admin_role_id)
            if admin_role:
                referees_mentions = admin_role.mention
            else:
                referees_mentions = self.get_string(ctx, "no_admin_role")
        return referees_mentions

    @tosurnament.retry_and_update_spreadsheet_pickle_on_exceptions(exceptions=[TeamNotFound, tosurnament.InvalidMatch])
    async def get_teams_info(self, ctx, tournament, players_spreadsheet, match_info, retry=False):
        """Returns ally and enemy team info"""
        try:
            team1_info = TeamInfo.from_team_name(players_spreadsheet, match_info.team1.get())
            team2_info = TeamInfo.from_team_name(players_spreadsheet, match_info.team2.get())
        except tosurnament.SpreadsheetHttpError as e:
            await self.on_cog_command_error(ctx, e)
            return None, None
        if players_spreadsheet.range_team_name:
            team_captain_role = tosurnament.get_role(ctx.guild.roles, tournament.team_captain_role_id, "Team Captain")
            if team_captain_role and not tosurnament.get_role(
                ctx.author.roles, tournament.team_captain_role_id, "Team Captain"
            ):
                raise tosurnament.NotRequiredRole(team_captain_role.name)
        if self.get_player_in_team(ctx.author, team1_info):
            return team1_info, team2_info
        if self.get_player_in_team(ctx.author, team2_info):
            return team2_info, team1_info
        raise tosurnament.InvalidMatch()

    def is_skip_deadline_validation(self, tournament, match_id):
        allowed_reschedule_match_ids = [
            allowed_reschedule.match_id.casefold()
            for allowed_reschedule in tosurnament_api.get_allowed_reschedules(tournament.id)
        ]
        if match_id.casefold() in allowed_reschedule_match_ids:
            return True
        return False

    @tosurnament.retry_and_update_spreadsheet_pickle_on_exceptions(exceptions=[DateIsNotString, MatchIdNotFound])
    async def get_match_from_id(self, schedules_spreadsheet, match_id, retry=False):
        try:
            return MatchInfo.from_id(schedules_spreadsheet, match_id)
        except MatchIdNotFound as e:
            if not retry:
                raise e
            return None

    async def reschedule_for_bracket(
        self,
        ctx,
        tournament,
        bracket,
        match_id,
        new_date,
    ):
        schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
        if not schedules_spreadsheet:
            return False
        match_info = await self.get_match_from_id(schedules_spreadsheet, match_id)
        if not match_info:
            return False
        match_id = match_info.match_id.get()

        players_spreadsheet = await bracket.get_players_spreadsheet()
        if not players_spreadsheet:
            raise tosurnament.NoSpreadsheet("players")
        ally_team_info, opponent_team_info = await self.get_teams_info(ctx, tournament, players_spreadsheet, match_info)
        if not ally_team_info:
            raise tosurnament.InvalidMatch()

        skip_deadline_validation = self.is_skip_deadline_validation(tournament, match_id)
        new_date = self.validate_new_date(ctx, tournament, match_info, new_date, skip_deadline_validation)
        previous_date = self.validate_reschedule_feasibility(
            ctx, tournament, schedules_spreadsheet, match_info, new_date, skip_deadline_validation
        )

        team_name = ally_team_info.team_name.get()
        opponent_team_name = opponent_team_info.team_name.get()
        opponent_user = tosurnament.UserAbstraction.get_from_player_info(
            ctx.bot, opponent_team_info.get_team_captain(), ctx.guild
        )

        opponent_team_captain = opponent_user.get_member(ctx.guild)
        if not opponent_team_captain:
            raise tosurnament.OpponentNotFound(ctx.author.mention)

        reschedule_message = RescheduleMessage(tournament_id=tournament.id, bracket_id=bracket.id)

        opponent_to_ping = opponent_team_captain
        if players_spreadsheet.range_team_name and tournament.reschedule_ping_team:
            opponent_team_role = tosurnament.get_role(ctx.guild.roles, None, opponent_team_name)
            if opponent_team_role:
                opponent_to_ping = opponent_team_role
            ally_team_role = tosurnament.get_role(ctx.guild.roles, None, team_name)
            if ally_team_role:
                reschedule_message.ally_team_role_id = str(ally_team_role.id)

        reschedule_message.match_id = match_id
        reschedule_message.match_id_hash = match_id
        reschedule_message.ally_user_id = str(ctx.author.id)
        reschedule_message.opponent_user_id = str(opponent_team_captain.id)
        if previous_date:
            reschedule_message.previous_date = str(int(previous_date.timestamp()))
            previous_date_string = "<t:{0}:F>".format(reschedule_message.previous_date)
        else:
            reschedule_message.previous_date = ""
            previous_date_string = self.get_string(ctx, "no_previous_date")
        reschedule_message.new_date = str(int(new_date.timestamp()))
        new_date_string = "<t:{0}:F>".format(reschedule_message.new_date)
        sent_message = await self.send_reply(
            ctx,
            "success",
            opponent_to_ping.mention,
            escape_markdown(team_name),
            match_id,
            previous_date_string,
            new_date_string,
        )
        reschedule_message.message_id = sent_message.id

        previous_reschedule_message = (
            self.bot.session.query(RescheduleMessage)
            .where(RescheduleMessage.tournament_id == tournament.id)
            .where(RescheduleMessage.match_id_hash == match_id)
            .first()
        )
        if previous_reschedule_message:
            self.bot.session.delete(previous_reschedule_message)

        self.bot.session.add(reschedule_message)
        await sent_message.add_reaction("👍")
        await sent_message.add_reaction("👎")
        return True

    @commands.command(aliases=["r"])
    @tosurnament.has_tournament_role("Player")
    async def reschedule(self, ctx, match_id: str, *, date: str):
        """Allows players to reschedule their matches."""
        tournament = self.get_tournament(ctx.guild.id)
        try:
            new_date = tournament.parse_date(date, prefer_dates_from="future")
        except ValueError:
            raise commands.UserInputError()
        if not new_date:
            raise commands.UserInputError()

        for bracket in tournament.brackets:
            if await self.reschedule_for_bracket(
                ctx,
                tournament,
                bracket,
                match_id,
                new_date,
            ):
                return
        raise tosurnament.InvalidMatchId()

    @reschedule.error
    async def reschedule_handler(self, ctx, error):
        """Error handler of reschedule function."""
        if isinstance(error, tosurnament.InvalidMinute):
            await self.send_reply(ctx, "invalid_minute")
        elif isinstance(error, tosurnament.InvalidMatch):
            await self.send_reply(ctx, "invalid_match")
        elif isinstance(error, tosurnament.PastDeadline):
            await self.send_reply(
                ctx,
                "past_deadline",
                error.reschedule_deadline_hours,
                error.referees_mentions,
                error.match_id,
            )
        elif isinstance(error, tosurnament.ImpossibleReschedule):
            await self.send_reply(
                ctx,
                "impossible_reschedule",
                error.reschedule_deadline_hours,
                error.referees_mentions,
                error.match_id,
            )
        elif isinstance(error, tosurnament.PastDeadlineEnd):
            await self.send_reply(ctx, "past_deadline_end")
        elif isinstance(error, tosurnament.PastAllowedDate):
            await self.send_reply(ctx, "past_allowed_date")
        elif isinstance(error, tosurnament.SameDate):
            await self.send_reply(ctx, "same_date")
        elif isinstance(error, tosurnament.TimeInThePast):
            await self.send_reply(ctx, "past_now")

    @on_raw_reaction_with_context("add", valid_emojis=["👍", "👎"])
    @with_corresponding_message(RescheduleMessage)
    async def reaction_on_reschedule_message(self, ctx, emoji, reschedule_message):
        """Reschedules a match or denies the reschedule."""
        if str(ctx.author.id) != reschedule_message.opponent_user_id:
            return
        try:
            tournament = self.get_tournament(ctx.guild.id)
            tournament.current_bracket_id = reschedule_message.bracket_id
            if not tournament.current_bracket:
                raise tosurnament.UnknownError("Bracket not found")
            if emoji.name == "👍":
                await self.agree_to_reschedule(ctx, reschedule_message, tournament)
            else:
                self.bot.session.delete(reschedule_message)
                ally_to_mention = None
                if reschedule_message.ally_team_role_id:
                    ally_to_mention = tosurnament.get_role(ctx.guild.roles, reschedule_message.ally_team_role_id)
                if not ally_to_mention:
                    ally_to_mention = ctx.guild.get_member(int(reschedule_message.ally_user_id))
                if ally_to_mention:
                    await self.send_reply(ctx, "refused", ally_to_mention.mention, reschedule_message.match_id)
                else:
                    raise tosurnament.OpponentNotFound(ctx.author.mention)
        except Exception as e:
            await self.on_cog_command_error(ctx, e)

    async def agree_to_reschedule(self, ctx, reschedule_message, tournament):
        """Updates the schedules spreadsheet with reschedule time."""
        schedules_spreadsheet = await tournament.current_bracket.get_schedules_spreadsheet()
        if not schedules_spreadsheet:
            raise tosurnament.NoSpreadsheet(tournament.current_bracket.name, "schedules")
        match_id = reschedule_message.match_id
        match_info = MatchInfo.from_id(schedules_spreadsheet, match_id)

        if reschedule_message.previous_date:
            previous_date_string = "<t:{0}:F>".format(reschedule_message.previous_date)
        else:
            previous_date_string = self.get_string(ctx, "no_previous_date")
        timezone_offset = 0
        tournament_utc = "UTC{0}".format(tournament.utc)
        for timezone in dateparser.timezones.timezone_info_list[0]["timezones"]:
            if re.match(timezone[0], tournament_utc):
                timezone_offset = timezone[1]
                break
        new_date = datetime.datetime.fromtimestamp(
            int(reschedule_message.new_date), dateutil.tz.tzoffset(None, timezone_offset)
        )
        date_format = "%d %B"
        if schedules_spreadsheet.date_format:
            date_format = schedules_spreadsheet.date_format
        if tournament.date_format:
            date_format = tournament.date_format
        match_info.set_datetime(schedules_spreadsheet, new_date, date_format)

        await self.add_update_spreadsheet_background_task(schedules_spreadsheet)
        self.bot.session.delete(reschedule_message)

        ally_to_mention = None
        if reschedule_message.ally_team_role_id:
            ally_to_mention = tosurnament.get_role(ctx.guild.roles, reschedule_message.ally_team_role_id)
        if not ally_to_mention:
            ally_to_mention = ctx.guild.get_member(int(reschedule_message.ally_user_id))
        if ally_to_mention:
            await self.send_reply(ctx, "accepted", ally_to_mention.mention, match_id)
        else:
            # TODO not raise
            raise tosurnament.OpponentNotFound(ctx.author.mention)

        referees_to_ping, _ = self.find_staff_to_ping(ctx.guild, match_info.referees)
        streamers_to_ping, _ = self.find_staff_to_ping(ctx.guild, match_info.streamers)
        commentators_to_ping, _ = self.find_staff_to_ping(ctx.guild, match_info.commentators)

        new_date_string = "<t:{0}:F>".format(reschedule_message.new_date)
        staff_channel = None
        if tournament.staff_channel_id:
            staff_channel = self.bot.get_channel(int(tournament.staff_channel_id))
        if referees_to_ping or streamers_to_ping or commentators_to_ping:
            if staff_channel:
                to_channel = staff_channel
            else:
                to_channel = ctx.channel
            sent_message = await self.send_reply(
                ctx,
                "staff_notification",
                match_id,
                match_info.team1.get(),
                match_info.team2.get(),
                previous_date_string,
                new_date_string,
                " / ".join([referee.mention for referee in referees_to_ping]),
                " / ".join([streamer.mention for streamer in streamers_to_ping]),
                " / ".join([commentator.mention for commentator in commentators_to_ping]),
                channel=to_channel,
            )
            staff_reschedule_message = StaffRescheduleMessage(
                tournament_id=reschedule_message.tournament_id,
                bracket_id=tournament.current_bracket.id,
                message_id=sent_message.id,
                team1=match_info.team1.get(),
                team2=match_info.team2.get(),
                match_id=match_id,
                previous_date=reschedule_message.previous_date,
                new_date=reschedule_message.new_date,
                referees_id="\n".join([str(referee.id) for referee in referees_to_ping]),
                streamers_id="\n".join([str(streamer.id) for streamer in streamers_to_ping]),
                commentators_id="\n".join([str(commentator.id) for commentator in commentators_to_ping]),
            )
            self.bot.session.add(staff_reschedule_message)
        elif staff_channel and tournament.notify_no_staff_reschedule:
            await self.send_reply(
                ctx,
                "no_staff_notification",
                match_id,
                match_info.team1.get(),
                match_info.team2.get(),
                previous_date_string,
                new_date_string,
                channel=staff_channel,
            )
        allowed_reschedules = tosurnament_api.get_allowed_reschedules(tournament.id)
        for allowed_reschedule in allowed_reschedules:
            if allowed_reschedule.match_id.upper() == match_id.upper():
                tosurnament_api.delete_allowed_reschedule(tournament.id, match_id.upper())

    async def on_verified_user(self, guild, user):
        await self.get_player_role_for_user(None, guild, user)

    async def give_player_role(self, guild, tournament):
        player_role = tosurnament.get_role(guild.roles, tournament.player_role_id, "Player")
        if not player_role:
            return
        for bracket in tournament.brackets:
            players_spreadsheet = await bracket.get_players_spreadsheet(retry=True, force_sync=True)
            if not players_spreadsheet:
                continue
            bracket_role = tosurnament.get_role(guild.roles, bracket.role_id, bracket.name)
            team_infos, team_roles = await self.get_all_teams_infos_and_roles(guild, players_spreadsheet)
            for team_info_index, team_info in enumerate(team_infos):
                team_role = None
                if players_spreadsheet.range_team_name:
                    team_role = team_roles[team_info_index]
                    if not team_role:
                        team_role = await guild.create_role(name=team_info.team_name.get(), mentionable=False)
                for player in team_info.players:
                    user = tosurnament.UserAbstraction.get_from_player_info(self.bot, player, guild)
                    member = user.get_member(guild)
                    if member:
                        try:
                            await member.add_roles(*filter(None, [player_role, bracket_role, team_role]))
                            await member.edit(nick=player.name.get())
                        except Exception:
                            continue

    @tasks.loop(hours=5.0)
    async def background_task_give_player_role(self):
        for guild in self.bot.guilds:
            try:
                tournament = self.get_tournament(guild.id)
                if tournament.registration_phase:
                    await self.give_player_role(guild, tournament)
            except Exception:
                continue

    @background_task_give_player_role.before_loop
    async def before_background_task_give_player_role(self):
        self.bot.info("Waiting for bot to be ready before starting give_player_role background task...")
        await self.bot.wait_until_ready()
        self.bot.info("Bot is ready. give_player_role background task will start.")


async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(TosurnamentPlayerCog(bot))
