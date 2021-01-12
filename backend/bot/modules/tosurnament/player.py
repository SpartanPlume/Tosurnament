"""Player commands"""

import re
import asyncio
import datetime
import discord
from discord.ext import commands
from discord.utils import escape_markdown
from bot.modules.tosurnament import module as tosurnament
from common.databases.players_spreadsheet import TeamInfo, TeamNotFound
from common.databases.schedules_spreadsheet import MatchInfo, MatchIdNotFound, DateIsNotString
from common.databases.qualifiers_spreadsheet import LobbyInfo
from common.databases.reschedule_message import RescheduleMessage
from common.databases.staff_reschedule_message import StaffRescheduleMessage
from common.databases.allowed_reschedule import AllowedReschedule
from common.api.spreadsheet import HttpError, InvalidWorksheet
from common.api import osu


class InvalidTimezone(commands.CommandError):
    """Special exception in case the timezone provided is invalid."""

    def __init__(self, timezone):
        self.timezone = timezone


class TosurnamentPlayerCog(tosurnament.TosurnamentBaseModule, name="player"):
    """Tosurnament player commands"""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @commands.command()
    @commands.bot_has_permissions(manage_nicknames=True, manage_roles=True)
    async def register(self, ctx, osu_link: str, timezone: str = ""):  # TODO handle teams + multiples brackets
        """Registers the player to the tournament."""
        tournament = self.get_tournament(ctx.guild.id)
        if len(tournament.brackets) != 1:
            await self.send_reply(ctx, ctx.command.name, "not_supported_yet")
            return
        bracket = tournament.current_bracket
        if bracket.registration_end_date:
            registration_end_date = datetime.datetime.strptime(
                bracket.registration_end_date, tosurnament.DATABASE_DATE_FORMAT
            )
            if datetime.datetime.now() > registration_end_date:
                raise tosurnament.RegistrationEnded()
        players_spreadsheet = bracket.players_spreadsheet
        if players_spreadsheet.range_timezone:
            if not timezone:
                raise commands.MissingRequiredArgument("timezone")
            if not re.match(r"(UTC)?[-\+]([0-9]|1[0-4])$", timezone, re.IGNORECASE):
                raise InvalidTimezone(timezone)
            timezone = "UTC" + re.sub(r"^UTC", "", timezone, flags=re.IGNORECASE)
        if players_spreadsheet.range_team_name:
            await self.send_reply(ctx, ctx.command.name, "not_supported_yet")
            return
        await players_spreadsheet.get_spreadsheet()
        team_info = TeamInfo.get_first_blank_fields(players_spreadsheet)
        osu_name = osu.get_from_string(osu_link)
        osu_user = osu.get_user(osu_name)
        if not osu_user:
            raise tosurnament.UserNotFound(osu_name)
        team_info.players[0].value = osu_user.name
        team_info.discord[0].value = str(ctx.author)
        team_info.discord_ids[0].value = str(ctx.author.id)
        team_info.ranks[0].value = str(osu_user.rank)
        team_info.bws_ranks[0].value = str(osu_user.rank)  # TODO
        team_info.osu_ids[0].value = str(osu_user.id)
        team_info.pps[0].value = str(int(float(osu_user.pp)))
        team_info.timezones[0].value = timezone
        self.add_update_spreadsheet_background_task(players_spreadsheet)
        roles_to_give = [tosurnament.get_role(ctx.guild.roles, tournament.player_role_id, "Player")]
        roles_to_give.append(tosurnament.get_role(ctx.guild.roles, bracket.role_id, bracket.name))
        await ctx.author.add_roles(*filter(None, roles_to_give))
        try:
            await ctx.author.edit(nick=osu_user.name)
        except (discord.Forbidden, discord.HTTPException):
            pass
        await self.send_reply(ctx, ctx.command.name, "success")

    @register.error
    async def register_handler(self, ctx, error):
        """Error handler of register function."""
        if isinstance(error, InvalidTimezone):
            await self.send_reply(ctx, ctx.command.name, "invalid_timezone", error.timezone)
        elif isinstance(error, tosurnament.RegistrationEnded):
            await self.send_reply(ctx, ctx.command.name, "registration_ended")

    @commands.command(aliases=["rtl"])
    async def register_to_lobby(self, ctx, *, lobby_id: str):  # TODO: improve, was in a rush =)
        """Registers to a qualifier lobby."""
        tournament = self.get_tournament(ctx.guild.id)
        user = tosurnament.UserAbstraction.get_from_ctx(ctx)
        for bracket in tournament.brackets:
            qualifiers_spreadsheet = bracket.qualifiers_spreadsheet
            if not qualifiers_spreadsheet:
                continue
            await qualifiers_spreadsheet.get_spreadsheet()
            lobby_id_cells = qualifiers_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                qualifiers_spreadsheet.range_lobby_id
            )
            lobby_id_cells = [lobby_id_cell for lobby_id_cell in lobby_id_cells if lobby_id_cell.value]
            players_spreadsheet = bracket.players_spreadsheet
            if players_spreadsheet:
                await players_spreadsheet.get_spreadsheet()
                team_info = TeamInfo.from_discord_id(players_spreadsheet, user.discord_id)
                team_name = team_info.team_name.value
            else:
                if not user.verified:
                    continue
                team_name = user.name
            lobby_infos = []
            for lobby_id_cell in lobby_id_cells:
                lobby_infos.append(
                    LobbyInfo.from_lobby_id_cell(qualifiers_spreadsheet, lobby_id_cell, filled_only=False)
                )
            lobby_found = False
            for lobby_info in lobby_infos:
                if lobby_info.lobby_id.value.lower() == lobby_id.lower():
                    first_empty_cell = None
                    for team_cell in lobby_info.teams:
                        if not first_empty_cell and not team_cell.value:
                            first_empty_cell = team_cell
                        if team_name.lower() == team_cell.value.lower():
                            raise tosurnament.AlreadyInLobby()
                    if not first_empty_cell:
                        raise tosurnament.LobbyIsFull()
                    first_empty_cell.value = team_name
                    lobby_found = True
                    break
            if not lobby_found:
                continue
            for lobby_info in lobby_infos:
                for team_cell in lobby_info.teams:
                    if (
                        lobby_info.lobby_id.value.lower() != lobby_id.lower()
                        and team_name.lower() == team_cell.value.lower()
                    ):
                        team_cell.value = ""
                        break
            self.add_update_spreadsheet_background_task(qualifiers_spreadsheet)
            await self.send_reply(ctx, ctx.command.name, "success", lobby_id)
            return
        raise tosurnament.LobbyNotFound()

    @register_to_lobby.error
    async def register_to_lobby_handler(self, ctx, error):
        """Error handler of register_to_lobby function."""
        if isinstance(error, tosurnament.AlreadyInLobby):
            await self.send_reply(ctx, ctx.command.name, "already_in_lobby")
        elif isinstance(error, tosurnament.LobbyNotFound):
            await self.send_reply(ctx, ctx.command.name, "lobby_not_found")
        elif isinstance(error, tosurnament.LobbyIsFull):
            await self.send_reply(ctx, ctx.command.name, "lobby_is_full")

    async def is_a_player(self, bracket, user_name):
        """Returns if the user is a player in the bracket and its team_info if he is."""
        players_spreadsheet = bracket.players_spreadsheet
        if not players_spreadsheet:
            return False, None
        await players_spreadsheet.get_spreadsheet()
        if players_spreadsheet.range_team_name:
            team_name_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                players_spreadsheet.range_team_name
            )
            team_info = None
            for team_name_cell in team_name_cells:
                team_info = TeamInfo.from_team_name_cell(players_spreadsheet, team_name_cell)
                if user_name in [cell.value for cell in team_info.players]:
                    return True, team_info
            return False, None
        else:
            team_cells = players_spreadsheet.spreadsheet.find_cells(players_spreadsheet.range_team, user_name)
            if len(team_cells) < 1:
                return False, None
            elif len(team_cells) > 1:
                raise tosurnament.DuplicatePlayer(user_name)
            return True, None

    async def get_player_role_for_bracket(self, guild, tournament, user, user_name, player_role):
        """Gives the player role of the bracket to the user, if he is a player of this bracket."""
        bracket = tournament.current_bracket
        try:
            is_player, team_info = await self.is_a_player(bracket, user_name)
        except HttpError as e:
            raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "players", e.error)
        if not is_player:
            return False
        roles_to_give = [player_role]
        bracket_role = tosurnament.get_role(guild.roles, bracket.role_id, bracket.name)
        if bracket_role:
            roles_to_give.append(bracket_role)
        if team_info:
            team_name = team_info.team_name.value
            team_role = tosurnament.get_role(guild.roles, None, team_name)
            if not team_role:
                try:
                    team_role = await guild.create_role(name=team_name, mentionable=False)
                except discord.InvalidArgument:
                    raise tosurnament.InvalidRoleName(team_name)
            if team_role:
                roles_to_give.append(team_role)
            if team_name == team_info.players[0].value:
                team_captain_role = tosurnament.get_role(guild.roles, tournament.team_captain_role_id, "Team Captain")
                if team_captain_role:
                    roles_to_give.append(team_captain_role)
        await user.add_roles(*roles_to_give)
        return True

    async def get_player_role_for_user(self, guild, user, channel=None):
        """Gives the corresponding player role to the user."""
        tournament = self.get_tournament(guild.id)
        player_role_id = tournament.player_role_id
        if tosurnament.get_role(user.roles, player_role_id, "Player"):
            raise tosurnament.UserAlreadyPlayer()
        try:
            tosurnament_user = self.get_verified_user(user.id)
            user_name = tosurnament_user.osu_name
        except (tosurnament.UserNotLinked, tosurnament.UserNotVerified):
            user_name = user.display_name
        roles = guild.roles
        player_role = tosurnament.get_role(roles, player_role_id, "Player")
        if not player_role:
            raise tosurnament.RoleDoesNotExist("Player")
        got_role = False
        for bracket in tournament.brackets:
            tournament.current_bracket_id = bracket.id
            try:
                got_role |= await self.get_player_role_for_bracket(guild, tournament, user, user_name, player_role)
            except Exception as e:
                if channel:
                    await self.on_cog_command_error(channel, "get_player_role", e)
        return got_role

    @commands.command()
    @commands.bot_has_permissions(manage_nicknames=True, manage_roles=True)
    async def get_player_role(self, ctx):
        """Gives a player the player related roles, if applicable."""
        got_role = await self.get_player_role_for_user(ctx.guild, ctx.author, ctx)
        if got_role:
            await self.send_reply(ctx, "get_player_role", "success")
        else:
            raise tosurnament.NotAPlayer()

    def validate_reschedule_feasibility(
        self, ctx, tournament, schedules_spreadsheet, match_info, now, new_date, skip_deadline_validation
    ):
        date_format = "%d %B"
        if schedules_spreadsheet.date_format:
            date_format = schedules_spreadsheet.date_format
        previous_date_string = match_info.get_datetime()
        if not previous_date_string:
            return None
        previous_date = tournament.parse_date(
            previous_date_string, date_formats=list(filter(None, [date_format + " %H:%M"]))
        )
        if not previous_date:
            raise tosurnament.InvalidDateOrFormat()
        if not skip_deadline_validation:
            reschedule_deadline_hours = tournament.reschedule_deadline_hours_before_current_time
            deadline = previous_date - datetime.timedelta(hours=reschedule_deadline_hours)
            if now > deadline:
                referees_mentions = self.get_referees_mentions_of_match(ctx, match_info)
                raise tosurnament.PastDeadline(reschedule_deadline_hours, referees_mentions, match_info.match_id.value)
            if tournament.reschedule_deadline_end:
                try:
                    deadline_end = tournament.parse_date(
                        tournament.reschedule_deadline_end, prefer_dates_from="future", relative_base=previous_date
                    )
                except ValueError:
                    # TODO: handle error
                    return
                if new_date >= deadline_end:
                    raise tosurnament.PastDeadlineEnd()
        if previous_date == new_date:
            raise tosurnament.SameDate()
        return previous_date

    def validate_new_date(
        self, ctx, tournament, schedules_spreadsheet, match_info, now, new_date, skip_deadline_validation
    ):
        reschedule_deadline_hours = tournament.reschedule_deadline_hours_before_new_time
        if skip_deadline_validation:
            reschedule_deadline_hours = 0
        if now > new_date:
            raise tosurnament.TimeInThePast()
        if new_date.minute % 15 != 0:
            raise tosurnament.InvalidMinute()
        if new_date.hour == 0 and new_date.minute == 0:
            new_date = new_date + datetime.timedelta(minutes=1)
        if now.month == 12 and new_date.month == 1 and new_date < now:
            try:
                new_date = new_date.replace(year=new_date.year + 1)
            except ValueError:
                new_date = new_date + (
                    datetime.new_date(new_date.year + 1, 1, 1) - datetime.new_date(new_date.year, 1, 1)
                )
        deadline = new_date - datetime.timedelta(hours=reschedule_deadline_hours)
        if now > deadline:
            referees_mentions = self.get_referees_mentions_of_match(ctx, match_info)
            raise tosurnament.ImpossibleReschedule(
                reschedule_deadline_hours, referees_mentions, match_info.match_id.value
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
                referees_mentions = "Admins (please contact them)"
        return referees_mentions

    async def get_teams_info(self, ctx, tournament, players_spreadsheet, match_info, user):
        """Returns ally and enemy team info"""
        try:
            team1_info = TeamInfo.from_team_name(players_spreadsheet, match_info.team1.value)
            team2_info = TeamInfo.from_team_name(players_spreadsheet, match_info.team2.value)
        except tosurnament.SpreadsheetHttpError as e:
            await self.on_cog_command_error(ctx, ctx.command.name, e)
            return None, None
        if players_spreadsheet.range_team_name:
            team_captain_role = tosurnament.get_role(ctx.guild.roles, tournament.team_captain_role_id, "Team Captain")
            if team_captain_role:
                if not tosurnament.get_role(ctx.author.roles, tournament.team_captain_role_id, "Team Captain"):
                    raise tosurnament.NotRequiredRole(team_captain_role.name)
                if user.verified:
                    if user.name in [cell.value.lower() for cell in team1_info.players]:
                        return team1_info, team2_info
                    elif user.name in [cell.value.lower() for cell in team2_info.players]:
                        return team2_info, team1_info
                if str(ctx.author) in [cell.value for cell in team1_info.discord]:
                    return team1_info, team2_info
                elif str(ctx.author) in [cell.value for cell in team2_info.discord]:
                    return team2_info, team1_info
                raise tosurnament.InvalidMatch()
        if user.verified:
            if user.name == team1_info.players[0].value:
                return team1_info, team2_info
            elif user.name == team2_info.players[0].value:
                return team2_info, team1_info
        if str(ctx.author) == team1_info.discord[0].value:
            return team1_info, team2_info
        elif str(ctx.author) == team2_info.discord[0].value:
            return team2_info, team1_info
        raise tosurnament.InvalidMatch()

    @tosurnament.retry_and_update_spreadsheet_pickle_on_false_or_exceptions(
        exceptions=[tosurnament.InvalidMatch, TeamNotFound, tosurnament.OpponentNotFound, DateIsNotString]
    )
    async def reschedule_for_bracket(
        self,
        ctx,
        tournament,
        bracket,
        schedules_spreadsheet,
        players_spreadsheet,
        match_id,
        new_date,
        user,
        skip_deadline_validation,
        retry=False,
    ):
        try:
            match_info = MatchInfo.from_id(schedules_spreadsheet, match_id)
        except (tosurnament.SpreadsheetHttpError, InvalidWorksheet) as e:
            if retry:
                await self.on_cog_command_error(ctx, ctx.command.name, e)
            return False
        except MatchIdNotFound as e:
            if retry:
                self.bot.info_exception(e)
            return False
        match_id = match_info.match_id.value

        players_spreadsheet = bracket.players_spreadsheet
        if players_spreadsheet:
            await players_spreadsheet.get_spreadsheet()
            ally_team_info, opponent_team_info = await self.get_teams_info(
                ctx, tournament, players_spreadsheet, match_info, user
            )
            if not ally_team_info:
                return False
            team_name = ally_team_info.team_name.value
            opponent_team_name = opponent_team_info.team_name.value
            opponent_user = tosurnament.UserAbstraction.get_from_osu_name(
                ctx.bot, opponent_team_info.players[0].value, opponent_team_info.discord[0].value
            )
        else:
            team_name = user.name
            if team_name == match_info.team1.value:
                opponent_team_name = match_info.team2.value
            elif team_name == match_info.team2.value:
                opponent_team_name = match_info.team1.value
            else:
                raise tosurnament.InvalidMatch()
            opponent_user = tosurnament.UserAbstraction.get_from_osu_name(ctx.bot, opponent_team_name)

        now = datetime.datetime.utcnow()
        new_date = self.validate_new_date(
            ctx, tournament, schedules_spreadsheet, match_info, now, new_date, skip_deadline_validation
        )
        previous_date = self.validate_reschedule_feasibility(
            ctx, tournament, schedules_spreadsheet, match_info, now, new_date, skip_deadline_validation
        )

        opponent_team_captain = opponent_user.get_member(ctx.guild)
        if not opponent_team_captain:
            raise tosurnament.OpponentNotFound(ctx.author.mention)

        opponent_to_ping = opponent_team_captain
        if players_spreadsheet and players_spreadsheet.range_team_name and tournament.reschedule_ping_team:
            role = tosurnament.get_role(ctx.guild.roles, None, opponent_team_name)
            if role:
                opponent_to_ping = role

        reschedule_message = RescheduleMessage(tournament_id=tournament.id, bracket_id=bracket.id, in_use=False)
        role = tosurnament.get_role(ctx.guild.roles, None, team_name)
        if role:
            reschedule_message.ally_team_role_id = role.id
        reschedule_message.match_id = match_id
        reschedule_message.match_id_hash = match_id
        reschedule_message.ally_user_id = ctx.author.id
        reschedule_message.opponent_user_id = opponent_team_captain.id
        if previous_date:
            previous_date_string = tosurnament.get_pretty_date(tournament, previous_date)
            reschedule_message.previous_date = previous_date.strftime(tosurnament.DATABASE_DATE_FORMAT)
        else:
            previous_date_string = "**No previous date**"
            reschedule_message.previous_date = ""
        new_date_string = tosurnament.get_pretty_date(tournament, new_date)
        reschedule_message.new_date = new_date.strftime(tosurnament.DATABASE_DATE_FORMAT)
        sent_message = await self.send_reply(
            ctx,
            ctx.command.name,
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
        skip_deadline_validation = False
        allowed_reschedule_match_ids = [
            allowed_reschedule.match_id.upper()
            for allowed_reschedule in self.bot.session.query(AllowedReschedule)
            .where(AllowedReschedule.tournament_id == tournament.id)
            .all()
        ]
        if match_id.upper() in allowed_reschedule_match_ids:
            skip_deadline_validation = True

        user = tosurnament.UserAbstraction.get_from_ctx(ctx)
        bracket_role_present = False
        for bracket in tournament.brackets:
            bracket_role = tosurnament.get_role(ctx.guild.roles, bracket.role_id)
            if bracket_role and not tosurnament.get_role(ctx.author.roles, bracket.role_id):
                bracket_role_present = True
                continue
            schedules_spreadsheet = bracket.schedules_spreadsheet
            if not schedules_spreadsheet:
                continue
            await schedules_spreadsheet.get_spreadsheet()
            players_spreadsheet = bracket.players_spreadsheet
            if players_spreadsheet:
                await players_spreadsheet.get_spreadsheet()

            if await self.reschedule_for_bracket(
                ctx,
                tournament,
                bracket,
                schedules_spreadsheet,
                players_spreadsheet,
                match_id,
                new_date,
                user,
                skip_deadline_validation,
            ):
                return
        if bracket_role_present:
            raise tosurnament.InvalidMatchIdOrNoBracketRole()
        raise tosurnament.InvalidMatchId()

    @reschedule.error
    async def reschedule_handler(self, ctx, error):
        """Error handler of reschedule function."""
        if isinstance(error, tosurnament.InvalidMinute):
            await self.send_reply(ctx, ctx.command.name, "invalid_minute")
        elif isinstance(error, tosurnament.InvalidMatch):
            await self.send_reply(ctx, ctx.command.name, "invalid_match")
        elif isinstance(error, tosurnament.PastDeadline):
            await self.send_reply(
                ctx,
                ctx.command.name,
                "past_deadline",
                error.reschedule_deadline_hours,
                error.referees_mentions,
                error.match_id,
            )
        elif isinstance(error, tosurnament.ImpossibleReschedule):
            await self.send_reply(
                ctx,
                ctx.command.name,
                "impossible_reschedule",
                error.reschedule_deadline_hours,
                error.referees_mentions,
                error.match_id,
            )
        elif isinstance(error, tosurnament.PastDeadlineEnd):
            await self.send_reply(ctx, ctx.command.name, "past_deadline_end")
        elif isinstance(error, tosurnament.SameDate):
            await self.send_reply(ctx, ctx.command.name, "same_date")
        elif isinstance(error, tosurnament.TimeInThePast):
            await self.send_reply(ctx, ctx.command.name, "past_now")

    async def on_raw_reaction_add(self, message_id, emoji, guild, channel, user):
        """on_raw_reaction_add of the Tosurnament player module."""
        await self.reaction_on_reschedule_message(message_id, emoji, guild, channel, user)

    async def reaction_on_reschedule_message(self, message_id, emoji, guild, channel, user):
        """Reschedules a match or denies the reschedule."""
        reschedule_message = (
            self.bot.session.query(RescheduleMessage).where(RescheduleMessage.message_id == message_id).first()
        )
        if not reschedule_message or reschedule_message.in_use:
            return
        if user.id != reschedule_message.opponent_user_id:
            return
        reschedule_message.in_use = True
        self.bot.session.update(reschedule_message)
        bracket = None
        try:
            tournament = self.get_tournament(guild.id)
            tournament.current_bracket_id = reschedule_message.bracket_id
            if not tournament.current_bracket:
                raise tosurnament.UnknownError("Bracket not found")
            if emoji.name == "👍":
                await self.agree_to_reschedule(reschedule_message, guild, channel, user, tournament)
            elif emoji.name == "👎":
                self.bot.session.delete(reschedule_message)
                ally_to_mention = None
                if reschedule_message.ally_team_role_id:
                    ally_to_mention = tosurnament.get_role(guild.roles, reschedule_message.ally_team_role_id)
                if not ally_to_mention:
                    ally_to_mention = guild.get_member(reschedule_message.ally_user_id)
                if ally_to_mention:
                    await self.send_reply(
                        channel, "reschedule", "refused", ally_to_mention.mention, reschedule_message.match_id
                    )
                else:
                    raise tosurnament.OpponentNotFound(user.mention)
            else:
                reschedule_message.in_use = False
                self.bot.session.update(reschedule_message)
        except Exception as e:
            reschedule_message.in_use = False
            self.bot.session.update(reschedule_message)
            await self.reaction_on_reschedule_message_handler(channel, e, bracket)

    async def agree_to_reschedule(self, reschedule_message, guild, channel, user, tournament):
        """Updates the schedules spreadsheet with reschedule time."""
        schedules_spreadsheet = tournament.current_bracket.schedules_spreadsheet
        if not schedules_spreadsheet:
            raise tosurnament.NoSpreadsheet(tournament.current_bracket.name, "schedules")
        await schedules_spreadsheet.get_spreadsheet()
        match_id = reschedule_message.match_id
        match_info = MatchInfo.from_id(schedules_spreadsheet, match_id)

        if reschedule_message.previous_date:
            previous_date = datetime.datetime.strptime(
                reschedule_message.previous_date, tosurnament.DATABASE_DATE_FORMAT
            )
            previous_date_string = tosurnament.get_pretty_date(tournament, previous_date)
        else:
            previous_date_string = "**No previous date**"
        new_date = datetime.datetime.strptime(reschedule_message.new_date, tosurnament.DATABASE_DATE_FORMAT)
        date_format = "%d %B"
        if schedules_spreadsheet.date_format:
            date_format = schedules_spreadsheet.date_format
        if schedules_spreadsheet.range_date and schedules_spreadsheet.range_time:
            match_info.date.value = new_date.strftime(date_format)
            match_info.time.value = new_date.strftime("%H:%M")
        elif schedules_spreadsheet.range_date:
            match_info.date.value = new_date.strftime(date_format + " %H:%M")
        elif schedules_spreadsheet.range_time:
            match_info.time.value = new_date.strftime(date_format + " %H:%M")
        else:
            raise tosurnament.UnknownError("No date range")

        self.add_update_spreadsheet_background_task(schedules_spreadsheet)
        self.bot.session.delete(reschedule_message)

        ally_to_mention = None
        if reschedule_message.ally_team_role_id:
            ally_to_mention = tosurnament.get_role(guild.roles, reschedule_message.ally_team_role_id)
        if not ally_to_mention:
            ally_to_mention = guild.get_member(reschedule_message.ally_user_id)
        if ally_to_mention:
            await self.send_reply(channel, "reschedule", "accepted", ally_to_mention.mention, match_id)
        else:
            # TODO not raise
            raise tosurnament.OpponentNotFound(user.mention)

        referees_to_ping, _ = self.find_staff_to_ping(guild, match_info.referees)
        streamers_to_ping, _ = self.find_staff_to_ping(guild, match_info.streamers)
        commentators_to_ping, _ = self.find_staff_to_ping(guild, match_info.commentators)

        new_date_string = tosurnament.get_pretty_date(tournament, new_date)
        staff_channel = None
        if tournament.staff_channel_id:
            staff_channel = self.bot.get_channel(tournament.staff_channel_id)
        if referees_to_ping + streamers_to_ping + commentators_to_ping:
            if staff_channel:
                to_channel = staff_channel
            else:
                to_channel = channel
            sent_message = await self.send_reply(
                to_channel,
                "reschedule",
                "staff_notification",
                match_id,
                match_info.team1.value,
                match_info.team2.value,
                previous_date_string,
                new_date_string,
                " / ".join([referee.mention for referee in referees_to_ping]),
                " / ".join([streamer.mention for streamer in streamers_to_ping]),
                " / ".join([commentator.mention for commentator in commentators_to_ping]),
            )
            staff_reschedule_message = StaffRescheduleMessage(
                tournament_id=reschedule_message.tournament_id,
                bracket_id=tournament.current_bracket.id,
                message_id=sent_message.id,
                team1=match_info.team1.value,
                team2=match_info.team2.value,
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
                staff_channel,
                "reschedule",
                "no_staff_notification",
                match_id,
                match_info.team1.value,
                match_info.team2.value,
                previous_date_string,
                new_date_string,
            )
        allowed_reschedules = (
            self.bot.session.query(AllowedReschedule).where(AllowedReschedule.tournament_id == tournament.id).all()
        )
        for allowed_reschedule in allowed_reschedules:
            if allowed_reschedule.match_id.upper() == match_id.upper():
                self.bot.session.delete(allowed_reschedule)

    async def reaction_on_reschedule_message_handler(self, channel, error, bracket):
        await self.on_cog_command_error(channel, "reschedule", error)

    async def on_verified_user(self, guild, user):
        await self.get_player_role_for_user(guild, user)

    async def give_player_role(self, guild, tournament):  # TODO: better
        player_role = tosurnament.get_role(guild.roles, tournament.player_role_id, "Player")
        if not player_role:
            return
        for bracket in tournament.brackets:
            players_spreadsheet = bracket.players_spreadsheet
            if not players_spreadsheet:
                continue
            bracket_role = tosurnament.get_role(guild.roles, bracket.role_id, bracket.name)
            await players_spreadsheet.get_spreadsheet()
            if players_spreadsheet.range_team_name:
                team_name_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    players_spreadsheet.range_team_name
                )
                for team_name_cell in team_name_cells:
                    team_info = TeamInfo.from_team_name(players_spreadsheet, team_name_cell.value)
                    team_name = team_info.team_name.value
                    team_role = tosurnament.get_role(guild.roles, None, team_name)
                    if not team_role:
                        team_role = await guild.create_role(name=team_name, mentionable=False)
                    for i, player_cell in enumerate(team_info.players):
                        player_name = player_cell.value
                        if not player_name:
                            continue
                        discord_tag = None
                        if len(team_info.discord) > i and team_info.discord[i].value:
                            discord_tag = team_info.discord[i].value
                        user = tosurnament.UserAbstraction.get_from_osu_name(self.bot, player_name, discord_tag)
                        member = user.get_member(guild)
                        if not member:
                            member = guild.get_member_named(user.name)
                        if member:
                            await member.add_roles(*filter(None, [player_role, bracket_role, team_role]))
            else:
                team_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    players_spreadsheet.range_team
                )
                for cell in team_cells:
                    try:
                        team_info = TeamInfo.from_player_name(players_spreadsheet, cell.value)
                        if team_info.discord[0].value:
                            user = guild.get_member_named(team_info.discord[0].value)
                        else:
                            user = guild.get_member_named(team_info.team_name.value)
                        if user:
                            await user.add_roles(*filter(None, [player_role, bracket_role]))
                    except Exception:
                        continue

    async def background_task_give_player_role(self):
        try:
            await self.bot.wait_until_ready()
            while not self.bot.is_closed():
                for guild in self.bot.guilds:
                    try:
                        tournament = self.get_tournament(guild.id)
                        if tournament.registration_phase:
                            await self.give_player_role(guild, tournament)
                    except asyncio.CancelledError:
                        return
                    except Exception:
                        continue
                await asyncio.sleep(18000)
        except asyncio.CancelledError:
            return

    def background_task(self):
        self.bot.tasks.append(self.bot.loop.create_task(self.background_task_give_player_role()))
        pass


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentPlayerCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentPlayerCog(bot))
