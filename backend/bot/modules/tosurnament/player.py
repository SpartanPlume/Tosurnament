"""Player commands"""

import asyncio
import datetime
import dateparser
import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.bracket import Bracket
from common.databases.players_spreadsheet import TeamInfo, TeamNotFound, DuplicateTeam
from common.databases.schedules_spreadsheet import MatchInfo, MatchIdNotFound, DuplicateMatchId
from common.databases.reschedule_message import RescheduleMessage
from common.databases.staff_reschedule_message import StaffRescheduleMessage
from common.api.spreadsheet import HttpError, InvalidWorksheet


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

    async def is_a_player(self, bracket, user_name):
        """Returns if the user is a player in the bracket and its team_info if he is."""
        players_spreadsheet = self.get_players_spreadsheet(bracket)
        if not players_spreadsheet:
            return False, None
        _, worksheet = self.get_spreadsheet_worksheet(players_spreadsheet)
        if players_spreadsheet.range_team_name:
            team_name_cells = worksheet.get_cells_with_value_in_range(players_spreadsheet.range_team_name)
            team_info = None
            for team_name_cell in team_name_cells:
                team_info = TeamInfo.from_team_name(players_spreadsheet, worksheet, team_name_cell.value)
            if not team_info:
                return False, None
            if user_name not in [cell.value for cell in team_info.players]:
                return False, None
            return True, team_info
        else:
            team_cells = worksheet.find_cells(players_spreadsheet.range_team, user_name)
            if len(team_cells) < 1:
                return False, None
            elif len(team_cells) > 1:
                raise tosurnament.DuplicatePlayer(user_name)
            return True, None

    async def get_player_role_for_bracket(self, guild, tournament, bracket, user, user_name, player_role):
        """Gives the player role of the bracket to the user, if he is a player of this bracket."""
        try:
            is_player, team_info = await self.is_a_player(bracket, user_name)
        except HttpError as e:
            raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "players")
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
        brackets = self.get_all_brackets(tournament)
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
        for bracket in brackets:
            try:
                got_role |= await self.get_player_role_for_bracket(
                    guild, tournament, bracket, user, user_name, player_role,
                )
            except Exception as e:
                if channel:
                    await self.on_cog_command_error(channel, "get_player_role", e)
        return got_role

    @commands.command(aliases=["gpr"])
    @commands.bot_has_permissions(manage_nicknames=True, manage_roles=True)
    async def get_player_role(self, ctx):
        """Gives a player the player related roles, if applicable."""
        got_role = await self.get_player_role_for_user(ctx.guild, ctx.author, ctx)
        if got_role:
            await self.send_reply(ctx, "get_player_role", "success")
        else:
            raise tosurnament.NotAPlayer()

    @commands.command(aliases=["r"])
    async def reschedule(self, ctx, match_id: str, *, date: str):
        """Allows players to reschedule their matches."""
        try:
            new_date = dateparser.parse(date)
        except ValueError:
            raise commands.UserInputError()
        tournament = self.get_tournament(ctx.guild.id)
        brackets = self.get_all_brackets(tournament)
        player_role = tosurnament.get_role(ctx.guild.roles, tournament.player_role_id, "Player")
        if not player_role:
            raise tosurnament.RoleDoesNotExist("Player")
        if not tosurnament.get_role(ctx.author.roles, tournament.player_role_id, "Player"):
            raise tosurnament.NotRequiredRole("Player")
        now = datetime.datetime.utcnow()
        if now.month == 12 and new_date.month == 1 and new_date < now:
            try:
                new_date = new_date.replace(year=new_date.year + 1)
            except ValueError:
                new_date = new_date + (
                    datetime.new_date(new_date.year + 1, 1, 1) - datetime.new_date(new_date.year, 1, 1)
                )
        deadline = new_date - datetime.timedelta(hours=tournament.reschedule_deadline_hours)
        if now > deadline:
            raise tosurnament.ImpossibleReschedule()
        # ? is this really a good idea ?
        # reschedule_deadline_begin, reschedule_deadline_end = tournament.create_date_from_week_times(
        #     tournament.reschedule_deadline_begin,
        #     tournament.reschedule_deadline_end,
        #     now,
        # )
        # if now < reschedule_deadline_begin or now > reschedule_deadline_end:
        #     raise tosurnament.ImpossibleReschedule()
        # reschedule_allowed_begin, reschedule_allowed_end = tournament.create_date_from_week_times(
        #     tournament.reschedule_allowed_begin, tournament.reschedule_allowed_end, new_date
        # )
        # if new_date < reschedule_allowed_begin or now > reschedule_allowed_end:
        #     raise tosurnament.ImpossibleReschedule()
        tosurnament_user = self.get_verified_user(ctx.author.id)
        user_name = tosurnament_user.osu_name
        for bracket in brackets:
            schedules_spreadsheet = self.get_schedules_spreadsheet(bracket)
            if not schedules_spreadsheet:
                continue
            try:
                spreadsheet, worksheet = self.get_spreadsheet_worksheet(schedules_spreadsheet)
            except HttpError as e:
                raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "schedules")
                continue
            except InvalidWorksheet:
                continue
            try:
                match_info = MatchInfo.from_id(schedules_spreadsheet, worksheet, match_id)
            except MatchIdNotFound:
                continue
            except DuplicateMatchId:
                await self.send_reply(ctx, ctx.command.name, "duplicate_match_id", match_id)
                continue

            previous_date = dateparser.parse(
                match_info.get_datetime(),
                date_formats=list(filter(None, [schedules_spreadsheet.date_format + " %H:%M"])),
            )
            if not previous_date:
                raise tosurnament.InvalidDateOrFormat()
            deadline = previous_date - datetime.timedelta(hours=tournament.reschedule_deadline_hours)
            if now > deadline:
                raise tosurnament.PastDeadline()
            if previous_date == new_date:
                raise tosurnament.SameDate()

            players_spreadsheet = self.get_players_spreadsheet(bracket)
            if players_spreadsheet and players_spreadsheet.range_team_name:
                try:
                    _, worksheet = self.get_spreadsheet_worksheet(players_spreadsheet)
                except HttpError as e:
                    raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "players")
                    continue
                except InvalidWorksheet:
                    continue
                try:
                    team1_info = TeamInfo.from_team_name(players_spreadsheet, worksheet, match_info.team1.value)
                    team2_info = TeamInfo.from_team_name(players_spreadsheet, worksheet, match_info.team2.value)
                except (TeamNotFound, DuplicateTeam):
                    continue
                if user_name in [cell.value for cell in team1_info.players]:
                    team_name = team1_info.team_name.value
                    opponent_team_name = team2_info.team_name.value
                    opponent_team_captain_name = team2_info.players[0].value
                else:
                    team_name = team2_info.team_name.value
                    opponent_team_name = team1_info.team_name.value
                    opponent_team_captain_name = team1_info.players[0].value
            else:
                team_name = user_name
                if match_info.team1.value == user_name:
                    opponent_team_name = match_info.team2.value
                    opponent_team_captain_name = opponent_team_name
                elif match_info.team2.value == user_name:
                    opponent_team_name = match_info.team1.value
                    opponent_team_captain_name = opponent_team_name
                else:
                    continue

            opponent_team_captain = ctx.guild.get_member_named(opponent_team_captain_name)
            if not opponent_team_captain:
                raise tosurnament.OpponentNotFound(ctx.author.mention)

            reschedule_message = RescheduleMessage(tournament_id=tournament.id, bracket_id=bracket.id, in_use=False)

            opponent_to_ping = opponent_team_captain
            if tournament.reschedule_ping_team:
                role = tosurnament.get_role(ctx.guild.roles, None, opponent_team_name)
                if role:
                    opponent_to_ping = role
                role = tosurnament.get_role(ctx.guild.roles, None, team_name)
                if role:
                    reschedule_message.ally_team_role_id = role.id

            reschedule_message.match_id = match_id
            reschedule_message.ally_user_id = ctx.author.id
            reschedule_message.opponent_user_id = opponent_team_captain.id
            previous_date_string = previous_date.strftime("**%d %B at %H:%M UTC**")
            reschedule_message.previous_date = previous_date.strftime("%d/%m/%y %H:%M")
            new_date_string = new_date.strftime("**%d %B at %H:%M UTC**")
            reschedule_message.new_date = new_date.strftime("%d/%m/%y %H:%M")
            sent_message = await self.send_reply(
                ctx,
                ctx.command.name,
                "success",
                opponent_to_ping.mention,
                user_name,
                match_id,
                previous_date_string,
                new_date_string,
            )
            reschedule_message.message_id = sent_message.id
            self.bot.session.add(reschedule_message)
            await sent_message.add_reaction("👍")
            await sent_message.add_reaction("👎")
            return
        raise tosurnament.InvalidMatchId()

    @reschedule.error
    async def reschedule_handler(self, ctx, error):
        """Error handler of reschedule function."""
        if isinstance(error, tosurnament.InvalidMatch):
            await self.send_reply(ctx, ctx.command.name, "invalid_match")
        elif isinstance(error, tosurnament.InvalidMatchId):
            await self.send_reply(ctx, ctx.command.name, "invalid_match_id")
        elif isinstance(error, tosurnament.PastDeadline):
            await self.send_reply(ctx, ctx.command.name, "past_deadline")
        elif isinstance(error, tosurnament.ImpossibleReschedule):
            await self.send_reply(ctx, ctx.command.name, "impossible_reschedule")
        elif isinstance(error, tosurnament.SameDate):
            await self.send_reply(ctx, ctx.command.name, "same_date")

    async def on_raw_reaction_add(self, message_id, emoji, guild, channel, user):
        """on_raw_reaction_add of the Tosurnament player module."""
        await self.reaction_on_reschedule_message(message_id, emoji, guild, channel, user)
        await self.reaction_on_staff_reschedule_message(message_id, emoji, guild, channel, user)

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
            bracket = self.bot.session.query(Bracket).where(Bracket.id == reschedule_message.bracket_id).first()
            if not bracket:
                raise tosurnament.UnknownError("Bracket not found")
            if emoji.name == "👍":
                await self.agree_to_reschedule(reschedule_message, guild, channel, user, tournament, bracket)
            elif emoji.name == "👎":
                self.bot.session.delete(reschedule_message)
                ally_to_mention = None
                if reschedule_message.ally_team_role_id:
                    ally_to_mention = tosurnament.get_role(guild.roles, reschedule_message.ally_team_role_id)
                if not ally_to_mention:
                    ally_to_mention = guild.get_member(reschedule_message.ally_user_id)
                if ally_to_mention:
                    await self.send_reply(
                        channel, "reschedule", "refused", ally_to_mention.mention, reschedule_message.match_id,
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

    async def agree_to_reschedule(self, reschedule_message, guild, channel, user, tournament, bracket):
        """Updates the schedules spreadsheet with reschedule time."""
        schedules_spreadsheet = self.get_schedules_spreadsheet(bracket)
        if not schedules_spreadsheet:
            raise tosurnament.NoSpreadsheet(bracket.name, "schedules")
        try:
            spreadsheet, worksheet = self.get_spreadsheet_worksheet(schedules_spreadsheet)
        except HttpError as e:
            raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "schedules")
        match_info = MatchInfo.from_id(schedules_spreadsheet, worksheet, reschedule_message.match_id)

        previous_date = datetime.datetime.strptime(reschedule_message.previous_date, "%d/%m/%y %H:%M")
        new_date = datetime.datetime.strptime(reschedule_message.new_date, "%d/%m/%y %H:%M")
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

        staff_name_to_ping = set()
        staff_cells = match_info.referees + match_info.streamers + match_info.commentators
        for staff_cell in staff_cells:
            if schedules_spreadsheet.use_range:
                staff_name_to_ping.add(staff_cell.value)
            else:
                staffs = staff_cell.value.split("/")
                for staff in staffs:
                    staff_name_to_ping.add(staff.strip())
        staff_to_ping = list(filter(None, [guild.get_member_named(name) for name in staff_name_to_ping]))

        try:
            spreadsheet.update()
        except HttpError as e:
            raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "schedules")

        self.bot.session.delete(reschedule_message)

        ally_to_mention = None
        if reschedule_message.ally_team_role_id:
            ally_to_mention = tosurnament.get_role(guild.roles, reschedule_message.ally_team_role_id)
        if not ally_to_mention:
            ally_to_mention = guild.get_member(reschedule_message.ally_user_id)
        if ally_to_mention:
            await self.send_reply(
                channel, "reschedule", "accepted", ally_to_mention.mention, reschedule_message.match_id,
            )
        else:
            raise tosurnament.OpponentNotFound(user.mention)

        previous_date_string = previous_date.strftime("**%d %B at %H:%M UTC**")
        new_date_string = new_date.strftime("**%d %B at %H:%M UTC**")
        staff_channel = None
        if tournament.staff_channel_id:
            staff_channel = self.bot.get_channel(tournament.staff_channel_id)
        if staff_to_ping:
            if staff_channel:
                to_channel = staff_channel
            else:
                to_channel = channel
            for staff in staff_to_ping:
                sent_message = await self.send_reply(
                    to_channel,
                    "reschedule",
                    "staff_notification",
                    staff.mention,
                    reschedule_message.match_id,
                    match_info.team1.value,
                    match_info.team2.value,
                    previous_date_string,
                    new_date_string,
                )
                staff_reschedule_message = StaffRescheduleMessage(
                    tournament_id=reschedule_message.tournament_id,
                    bracket_id=bracket.id,
                    message_id=sent_message.id,
                    match_id=reschedule_message.match_id,
                    new_date=reschedule_message.new_date,
                    staff_id=staff.id,
                )
                self.bot.session.add(staff_reschedule_message)
        elif staff_channel:
            await self.send_reply(
                staff_channel,
                "reschedule",
                "no_staff_notification",
                reschedule_message.match_id,
                match_info.team1.value,
                match_info.team2.value,
                previous_date_string,
                new_date_string,
            )

    async def reaction_on_reschedule_message_handler(self, channel, error, bracket):
        await self.on_cog_command_error(channel, "reschedule", error)

    async def reaction_on_staff_reschedule_message(self, message_id, emoji, guild, channel, user):
        """Removes the referee from the schedule spreadsheet"""
        staff_reschedule_message = (
            self.bot.session.query(StaffRescheduleMessage)
            .where(StaffRescheduleMessage.message_id == message_id)
            .first()
        )
        if not staff_reschedule_message or staff_reschedule_message.in_use:
            return
        if user.id != staff_reschedule_message.staff_id:
            return
        if emoji.name != "❌":
            return
        tosurnament_user = self.get_verified_user(user.id)
        staff_reschedule_message.in_use = True
        self.bot.session.update(staff_reschedule_message)
        try:
            tournament = self.get_tournament(guild.id)
            bracket = self.bot.session.query(Bracket).where(Bracket.id == staff_reschedule_message.bracket_id).first()
            if not bracket:
                raise tosurnament.UnknownError("Bracket not found")
            schedules_spreadsheet = self.get_schedules_spreadsheet(bracket)
            if not schedules_spreadsheet:
                raise tosurnament.NoSpreadsheet()
            try:
                spreadsheet, worksheet = self.get_spreadsheet_worksheet(schedules_spreadsheet)
            except HttpError as e:
                raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "schedules")
            match_info = MatchInfo.from_id(schedules_spreadsheet, worksheet, staff_reschedule_message.match_id)
            staff_cells = match_info.referees + match_info.streamers + match_info.commentators
            for staff_cell in staff_cells:
                if staff_cell.has_value(tosurnament_user.osu_name):
                    if schedules_spreadsheet.use_range:
                        staff_cell.value = ""
                    else:
                        staffs = staff_cell.split("/")
                        if len(staffs) == 2 and staffs[0].strip() == tosurnament_user.osu_name:
                            staff_cell.value = staffs[1].strip()
                        elif len(staffs) == 2 and staffs[1].strip == tosurnament_user.osu_name:
                            staff_cell.value = staffs[0].strip()
                        elif len(staffs) == 1 and staffs[0].strip() == tosurnament_user.osu_name:
                            staff_cell.value = ""
            try:
                spreadsheet.update()
            except HttpError as e:
                raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "schedules")
            to_channel = channel
            staff_channel = self.bot.get_channel(tournament.staff_channel_id)
            if staff_channel:
                to_channel = staff_channel
            await self.send_reply(
                to_channel, "reschedule", "removed_from_match", user.mention, staff_reschedule_message.match_id,
            )
            self.bot.session.delete(staff_reschedule_message)
        except Exception as e:
            staff_reschedule_message.in_use = False
            self.bot.session.update(staff_reschedule_message)
            await self.reaction_on_staff_reschedule_message_handler(channel, e)

    async def reaction_on_staff_reschedule_message_handler(self, channel, error):
        await self.on_cog_command_error(channel, "reschedule", error)

    async def on_verified_user(self, guild, user):
        await self.get_player_role_for_user(guild, user)

    async def give_player_role(self, guild):
        tournament = self.get_tournament(guild.id)
        player_role = tosurnament.get_role(guild.roles, tournament.player_role_id, "Player")
        if not player_role:
            return
        brackets = self.get_all_brackets(tournament)
        for bracket in brackets:
            players_spreadsheet = self.get_players_spreadsheet(bracket)
            if not players_spreadsheet:
                continue
            spreadsheet, worksheet = self.get_spreadsheet_worksheet(players_spreadsheet)
            if players_spreadsheet.range_team_name:
                team_name_cells = worksheet.get_cells_with_value_in_range(players_spreadsheet.range_team_name)
                team_info = None
                for team_name_cell in team_name_cells:
                    team_info = TeamInfo.from_team_name(players_spreadsheet, worksheet, team_name_cell.value)
                if not team_info:
                    continue
                for player_cell in team_info.players:
                    user = guild.get_member_named(player_cell.value)
                    if user:
                        await user.add_roles(player_role)
            else:
                team_cells = worksheet.get_cells_with_value_in_range(players_spreadsheet.range_team)
                for cell in team_cells:
                    try:
                        team_info = TeamInfo.from_player_name(players_spreadsheet, spreadsheet, worksheet, cell.value)
                        if team_info.discord[0]:
                            user = guild.get_member_named(team_info.discord[0])
                        else:
                            user = guild.get_member_named(team_info.team_name.value)
                        if user:
                            await user.add_roles(player_role)
                    except Exception as e:
                        if isinstance(e, asyncio.CancelledError):
                            raise e
                        continue

    # async def background_task(self):
    #     try:
    #         await self.bot.wait_until_ready()
    #         while not self.bot.is_closed():
    #             for guild in self.bot.guilds:
    #                 try:
    #                     await self.give_player_role(guild)
    #                 except Exception as e:
    #                     if isinstance(e, asyncio.CancelledError):
    #                         return
    #                     continue
    #             await asyncio.sleep(18000)
    #     except asyncio.CancelledError:
    #         return


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentPlayerCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentPlayerCog(bot))
