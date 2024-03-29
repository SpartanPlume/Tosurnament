"""Staff commands"""

import asyncio
import datetime
import discord
from discord.utils import escape_markdown
from discord.ext import commands, tasks
from bot.modules.tosurnament import module as tosurnament
from common.databases.tosurnament.spreadsheets.schedules_spreadsheet import (
    MatchInfo,
    MatchIdNotFound,
    DuplicateMatchId,
    DateIsNotString,
    SchedulesSpreadsheet,
)
from common.databases.tosurnament.spreadsheets.qualifiers_spreadsheet import LobbyInfo, LobbyIdNotFound
from common.databases.tosurnament.spreadsheets.qualifiers_results_spreadsheet import QualifiersResultInfo
from common.databases.tosurnament.spreadsheets.players_spreadsheet import TeamInfo
from common.databases.tosurnament.guild import Guild
from common.databases.tosurnament_message.match_notification import MatchNotification
from common.databases.tosurnament_message.staff_reschedule_message import StaffRescheduleMessage
from common.databases.tosurnament_message.base_message import with_corresponding_message, on_raw_reaction_with_context
from common.databases.tosurnament.allowed_reschedule import AllowedReschedule
from common.databases.tosurnament_message.qualifiers_results_message import QualifiersResultsMessage
from common.api.spreadsheet import Spreadsheet, InvalidWorksheet
from common.api import osu
from common.api import tosurnament as tosurnament_api


class TosurnamentStaffCog(tosurnament.TosurnamentBaseModule, name="staff"):
    """Tosurnament staff commands"""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.background_task_match_notification.start()
        self.background_task_clean_allowed_reschedule.start()

    def cog_unload(self):
        self.background_task_match_notification.cancel()
        self.background_task_clean_allowed_reschedule.cancel()

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    async def create_or_update_qualifiers_results_message(self, ctx, qualifiers_results_message, status):
        tournament = self.get_tournament(ctx.guild.id)
        referee_role = tosurnament.get_role(ctx.author.roles, tournament.referee_role_id, "Referee")
        if not self.is_admin(ctx) and not ctx.guild.owner == ctx.author and not referee_role:
            raise tosurnament.NotRequiredRole("Referee")
        if len(tournament.brackets) > 1:
            await self.send_reply(ctx, "not_supported_yet")
            return
        bracket = tournament.current_bracket
        qualifiers_results_spreadsheet = await bracket.get_qualifiers_results_spreadsheet(retry=True, force_sync=True)
        if not qualifiers_results_spreadsheet:
            raise tosurnament.NoSpreadsheet("qualifiers_results")
        results_info = QualifiersResultInfo.get_all(qualifiers_results_spreadsheet)
        top10 = []
        scores = []
        cut_off = None
        for i, result_info in enumerate(results_info):
            score = result_info.score.get()
            if score <= 0.0:
                continue
            scores.append(score)
            if i < 10:
                top10.append(result_info)
            if i == 31:
                cut_off = result_info
        avg_score = sum(scores) / len(scores)
        top10_string = ""
        for i, result_info in enumerate(top10):
            osu_name = result_info.osu_id.get()
            osu_user = osu.get_user(osu_name)
            if not osu_user:
                flag = ":flag_white:"
            else:
                flag = ":flag_" + osu_user.country.lower() + ":"
            top10_string += "`" + str(i + 1)
            if i < 9:
                top10_string += ". `"
            else:
                top10_string += ".`"
            top10_string += flag + " **" + escape_markdown(osu_name) + "** "
            top10_string += "(%.2f%%)\n" % (result_info.score.get() * 100)
        channel = ctx.guild.get_channel(int(qualifiers_results_message.channel_id))
        if qualifiers_results_message.message_id:
            message = await channel.fetch_message(int(qualifiers_results_message.message_id))
            await message.delete()
        message = await self.send_reply(
            ctx,
            "embed",
            tournament.name,
            status,
            top10_string,
            escape_markdown(top10[0].osu_id.get()),
            "%.2f%%" % (avg_score * 100),
            "%.2f%% `(32. %s)`" % ((cut_off.score.get() * 100), escape_markdown(cut_off.osu_id.get())),
            str(ctx.guild.icon_url),
            channel=channel,
        )
        qualifiers_results_message.message_id = message.id
        self.bot.session.update(qualifiers_results_message)

    @commands.command(aliases=["uqrm"])
    async def update_qualifiers_results_message(self, ctx, status: str = "ONGOING"):
        """Updates the qualifiers results message."""
        tournament = self.get_tournament(ctx.guild.id)
        qualifiers_results_message = (
            self.bot.session.query(QualifiersResultsMessage)
            .where(QualifiersResultsMessage.tournament_id == tournament.id)
            .first()
        )
        if qualifiers_results_message:
            await self.create_or_update_qualifiers_results_message(ctx, qualifiers_results_message, status)

    @commands.command(aliases=["cqrm"])
    async def create_qualifiers_results_message(self, ctx, channel: discord.TextChannel, status: str = "ONGOING"):
        """Creates the qualifiers results message."""
        tournament = self.get_tournament(ctx.guild.id)
        qualifiers_results_message = (
            self.bot.session.query(QualifiersResultsMessage)
            .where(QualifiersResultsMessage.tournament_id == tournament.id)
            .first()
        )
        if qualifiers_results_message:
            self.bot.session.delete(qualifiers_results_message)
        qualifiers_results_message = QualifiersResultsMessage(
            tournament_id=tournament.id, bracket_id=tournament.current_bracket.id, channel_id=str(channel.id)
        )
        self.bot.session.add(qualifiers_results_message)
        await self.create_or_update_qualifiers_results_message(ctx, qualifiers_results_message, status)

    @commands.command(aliases=["anr"])
    async def allow_next_reschedule(self, ctx, match_id: str, allowed_hours: int = 24):
        """Allows a match to be reschedule without any time constraint applied."""
        tournament = self.get_tournament(ctx.guild.id)
        is_admin = self.is_admin(ctx)
        referee_role = tosurnament.get_role(ctx.author.roles, tournament.referee_role_id, "Referee")
        if is_admin and not ctx.guild.owner == ctx.author and not referee_role:
            raise tosurnament.NotRequiredRole("Referee")
        match_found = False
        for bracket in tournament.brackets:
            schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
            if not schedules_spreadsheet:
                continue
            try:
                match_info = MatchInfo.from_id(schedules_spreadsheet, match_id)
            except (tosurnament.SpreadsheetHttpError, InvalidWorksheet) as e:
                await self.on_cog_command_error(ctx, e)
                continue
            except MatchIdNotFound as e:
                self.bot.info(str(type(e)) + ": " + str(e))
                continue
            match_found = True
            if is_admin:
                break
            user = tosurnament.UserAbstraction.get_from_ctx(ctx)
            is_referee_of_match = False
            for referee_cell in match_info.referees:
                if referee_cell.has_value(user.name):
                    is_referee_of_match = True
                    break
            if not is_referee_of_match:
                raise tosurnament.NotRefereeOfMatch()
            break
        if not match_found:
            raise MatchIdNotFound(match_id)
        players_spreadsheet = await bracket.get_players_spreadsheet()
        team1 = await self.get_team_mention(ctx.guild, players_spreadsheet, match_info.team1.get())
        team2 = await self.get_team_mention(ctx.guild, players_spreadsheet, match_info.team2.get())
        allowed_reschedule = AllowedReschedule(
            tournament_id=tournament.id, match_id=match_id, allowed_hours=allowed_hours
        )
        allowed_reschedule = tosurnament_api.create_allowed_reschedule(tournament.id, allowed_reschedule)
        await self.send_reply(ctx, "success", match_id, allowed_hours, team1, team2)

    @allow_next_reschedule.error
    async def allow_next_reschedule_handler(self, ctx, error):
        """Error handler of allow_next_reschedule function."""
        if isinstance(error, tosurnament.NotRefereeOfMatch):
            await self.send_reply(ctx, "not_referee_of_match")

    @commands.command(aliases=["take_matches", "tm"])
    async def take_match(self, ctx, *args):
        """Allows staffs to take matches"""
        user_details = tosurnament.UserDetails.get_from_ctx(ctx)
        if not user_details.is_staff():
            await self.send_reply(ctx, "not_staff")
        else:
            await self.take_or_drop_match(ctx, args, True, user_details)

    @commands.command(aliases=["take_matches_as_referee", "tmar"])
    @tosurnament.has_tournament_role("Referee")
    async def take_match_as_referee(self, ctx, *args):
        """Allows referees to take matches"""
        await self.take_or_drop_match(ctx, args, True, tosurnament.UserDetails.get_as_referee(self.bot, ctx.author))

    @commands.command(aliases=["take_matches_as_streamer", "tmas"])
    @tosurnament.has_tournament_role("Streamer")
    async def take_match_as_streamer(self, ctx, *args):
        """Allows streamers to take matches"""
        await self.take_or_drop_match(ctx, args, True, tosurnament.UserDetails.get_as_streamer(self.bot, ctx.author))

    @commands.command(aliases=["take_matches_as_commentator", "tmac"])
    @tosurnament.has_tournament_role("Commentator")
    async def take_match_as_commentator(self, ctx, *args):
        """Allows commentators to take matches"""
        await self.take_or_drop_match(ctx, args, True, tosurnament.UserDetails.get_as_commentator(self.bot, ctx.author))

    @commands.command(aliases=["drop_matches", "dm"])
    async def drop_match(self, ctx, *args):
        """Allows staffs to drop matches"""
        user_details = tosurnament.UserDetails.get_from_ctx(ctx)
        if not user_details.is_staff():
            await self.send_reply(ctx, "not_staff")
        else:
            await self.take_or_drop_match(ctx, args, False, user_details)

    @commands.command(aliases=["drop_matches_as_referee", "dmar"])
    @tosurnament.has_tournament_role("Referee")
    async def drop_match_as_referee(self, ctx, *args):
        """Allows referees to drop matches"""
        await self.take_or_drop_match(ctx, args, False, tosurnament.UserDetails.get_as_referee(self.bot, ctx.author))

    @commands.command(aliases=["drop_matches_as_streamer", "dmas"])
    @tosurnament.has_tournament_role("Streamer")
    async def drop_match_as_streamer(self, ctx, *args):
        """Allows streamers to drop matches"""
        await self.take_or_drop_match(ctx, args, False, tosurnament.UserDetails.get_as_streamer(self.bot, ctx.author))

    @commands.command(aliases=["drop_matches_as_commentator", "dmac"])
    @tosurnament.has_tournament_role("Commentator")
    async def drop_match_as_commentator(self, ctx, *args):
        """Allows commentators to drop matches"""
        await self.take_or_drop_match(
            ctx, args, False, tosurnament.UserDetails.get_as_commentator(self.bot, ctx.author)
        )

    def take_match_for_roles(self, schedules_spreadsheet, match_info, user_details, take):
        """Takes or drops a match of a bracket for specified roles, if possible."""
        write_cells = False
        staff_name = user_details.name.casefold()
        for role_store in user_details.get_staff_roles():
            take_match = False
            role_cells = getattr(match_info, role_store.name.lower() + "s")
            if schedules_spreadsheet.use_range:
                if not (take and staff_name in [cell.casefold() for cell in role_cells]):
                    for role_cell in role_cells:
                        if take and not role_cell:
                            role_cell.set(user_details.name)
                            take_match = True
                            break
                        elif not take and role_cell.casefold() == staff_name:
                            role_cell.set("")
                            take_match = True
                            break
            elif len(role_cells) > 0:
                role_cell = role_cells[0]
                max_take = getattr(schedules_spreadsheet, "max_" + role_store.name.lower())
                staffs = list(filter(None, [staff.strip() for staff in role_cell.split("/")]))
                casefold_staffs = [staff.casefold() for staff in staffs]
                if take and len(staffs) < max_take and staff_name not in casefold_staffs:
                    staffs.append(user_details.name)
                    role_cell.set(" / ".join(staffs))
                    take_match = True
                elif not take:
                    try:
                        idx = casefold_staffs.index(staff_name)
                        staffs.pop(idx)
                        role_cell.set(" / ".join(staffs))
                        role_store.taken_matches.append(match_info.match_id.get())
                        return True
                    except ValueError:
                        pass
            if take_match:
                role_store.taken_matches.append(match_info.match_id.get())
                write_cells = True
            if not take_match:
                role_store.not_taken_matches.append(match_info.match_id.get())
        return write_cells

    def take_lobby_for_roles(self, lobby_info, user_details, take):
        """Takes or drops a match of a bracket for specified roles, if possible."""
        staff_name = user_details.name
        role_cell = lobby_info.referee
        casefold_staff = role_cell.get().casefold()
        if not casefold_staff and take:
            role_cell.set(staff_name)
            user_details.referee.taken_matches.append(lobby_info.lobby_id.get())
            return True
        elif not take and casefold_staff == staff_name.casefold():
            role_cell.set("")
            user_details.referee.taken_matches.append(lobby_info.lobby_id.get())
            return True
        user_details.referee.not_taken_matches.append(lobby_info.lobby_id.get())
        return False

    @tosurnament.retry_and_update_spreadsheet_pickle_on_exceptions(
        exceptions=[DuplicateMatchId, DateIsNotString, MatchIdNotFound]
    )
    async def take_or_drop_match_in_spreadsheets(self, match_ids, user_details, take, *spreadsheets, retry=False):
        """Takes or drops matches of a bracket, if possible."""
        spreadsheets = list(filter(None, spreadsheets))
        user_details.clear_matches()
        invalid_match_ids = set()
        for match_id in match_ids:
            match_taken = False
            for spreadsheet in spreadsheets:
                if isinstance(spreadsheet, SchedulesSpreadsheet):
                    try:
                        match_info = MatchInfo.from_id(spreadsheet, match_id, False)
                    except MatchIdNotFound:
                        continue
                    self.take_match_for_roles(spreadsheet, match_info, user_details, take)
                    match_taken = True
                    break
                elif user_details.referee:  # TODO better error for other roles
                    try:
                        lobby_info = LobbyInfo.from_id(spreadsheet, match_id, False)
                    except LobbyIdNotFound:
                        continue
                    self.take_lobby_for_roles(lobby_info, user_details, take)
                    match_taken = True
                    break
            if not match_taken:
                if not retry:
                    raise MatchIdNotFound(match_id)
                else:
                    invalid_match_ids.add(match_id)
        for spreadsheet in spreadsheets:
            await self.add_update_spreadsheet_background_task(spreadsheet)
        return invalid_match_ids

    def format_take_match_string(self, string, match_ids):
        """Appends the match ids separated by a comma to the string."""
        if match_ids:
            return string + ", ".join(str(match_id) for match_id in match_ids) + "\n"
        return ""

    def build_take_match_reply(self, ctx, user_details, invalid_match_ids):
        """Builds the reply depending on matches taken or not and invalid matches."""
        staff_name = escape_markdown(user_details.name)
        reply = ""
        for staff in user_details.get_staff_roles():
            for match_id in invalid_match_ids.copy():
                if match_id.lower() in [match.lower() for match in staff.taken_matches] or match_id.lower() in [
                    match.lower() for match in staff.not_taken_matches
                ]:
                    invalid_match_ids.remove(match_id)
                    continue
            reply += self.format_take_match_string(
                self.get_string(ctx, "taken_match_ids", staff.name, staff_name),
                staff.taken_matches,
            )
            reply += self.format_take_match_string(
                self.get_string(ctx, "not_taken_match_ids", staff.name, staff_name),
                staff.not_taken_matches,
            )
        reply += self.format_take_match_string(self.get_string(ctx, "invalid_match_ids"), invalid_match_ids)
        return reply

    async def take_or_drop_match(self, ctx, match_ids, take, user_details):
        if not match_ids:
            raise commands.UserInputError()
        match_ids = set(match_ids)
        tournament = self.get_tournament(ctx.guild.id)
        invalid_match_ids = set()
        schedules_spreadsheets = []
        qualifiers_spreadsheets = []
        for bracket in tournament.brackets:
            if schedules_spreadsheet := await bracket.get_schedules_spreadsheet():
                schedules_spreadsheets.append(schedules_spreadsheet)
            if qualifiers_spreadsheet := await bracket.get_qualifiers_spreadsheet():
                qualifiers_spreadsheets.append(qualifiers_spreadsheet)
        invalid_match_ids = await self.take_or_drop_match_in_spreadsheets(
            match_ids, user_details, take, *schedules_spreadsheets, *qualifiers_spreadsheets
        )
        await ctx.send(self.build_take_match_reply(ctx, user_details, invalid_match_ids))

    @commands.command(aliases=["snm", "show_next_match"])
    async def show_next_matches(self, ctx, n_match_to_show: int = 5, where_has_no_referee: bool = False):
        tournament = self.get_tournament(ctx.guild.id)
        matches = []
        for bracket in tournament.brackets:
            matches_data = await self.get_next_matches_info_for_bracket(tournament, bracket)
            if where_has_no_referee:
                for match_info, match_date in matches_data:
                    if isinstance(match_info, MatchInfo):
                        if list(filter(None, [cell.get() for cell in match_info.referees])):
                            continue
                    elif not match_info.referee.get():
                        continue
                    matches.append((match_info, match_date))
            else:
                matches = [*matches, *matches_data]
        reply_string = ""
        previous_match_date = None
        for i, match_data in enumerate(sorted(matches, key=lambda x: x[1])):
            match_info, match_date = match_data
            if i >= n_match_to_show and match_date != previous_match_date:
                break
            previous_match_date = match_date
            tmp_reply_string = ""
            if reply_string:
                tmp_reply_string += "\n-------------------------------\n"
            if isinstance(match_info, MatchInfo):
                tmp_reply_string += "**" + self.get_string(ctx, "match") + " " + match_info.match_id.get() + ":** "
                tmp_reply_string += (
                    escape_markdown(match_info.team1.get()) + " vs " + escape_markdown(match_info.team2.get()) + "\n"
                )
                tmp_reply_string += "<t:{0}:F>".format(int(match_date.timestamp())) + "\n\n"
                referees = list(filter(None, [cell.get() for cell in match_info.referees]))
                tmp_reply_string += "__" + self.get_string(ctx, "referee") + ":__ "
                if referees:
                    tmp_reply_string += "/".join(referees)
                else:
                    tmp_reply_string += "**" + self.get_string(ctx, "none") + "**"
                streamers = list(filter(None, [cell.get() for cell in match_info.streamers]))
                if streamers:
                    tmp_reply_string += "\n__" + self.get_string(ctx, "streamer") + ":__ " + "/".join(streamers)
                commentators = list(filter(None, [cell.get() for cell in match_info.commentators]))
                if commentators:
                    tmp_reply_string += "\n__" + self.get_string(ctx, "commentator") + ":__ " + "/".join(commentators)
            else:
                tmp_reply_string += "**" + self.get_string(ctx, "qualifier") + " " + match_info.lobby_id.get() + "**"
                tmp_reply_string += " on <t:{0}:F>:\n\n".format(int(match_date.timestamp()))
                tmp_reply_string += "__" + self.get_string(ctx, "teams") + ":__ "
                teams = [escape_markdown(team_cell.get()) for team_cell in match_info.teams if team_cell.get()]
                if teams:
                    tmp_reply_string += " | ".join(teams)
                else:
                    tmp_reply_string += self.get_string(ctx, "none")
                tmp_reply_string += "\n__" + self.get_string(ctx, "referee") + ":__ "
                if match_info.referee.get():
                    tmp_reply_string += match_info.referee.get()
                else:
                    tmp_reply_string += "**" + self.get_string(ctx, "none") + "**"
            if len(reply_string) + len(tmp_reply_string) >= 2000:
                await ctx.send(reply_string)
                reply_string = tmp_reply_string
            else:
                reply_string += tmp_reply_string
        if reply_string:
            await ctx.send(reply_string)
        elif where_has_no_referee:
            await self.send_reply(ctx, "no_match_without_referee")
        else:
            await self.send_reply(ctx, "no_match")

    async def get_team_mention(self, guild, players_spreadsheet, team_name):
        if not players_spreadsheet:
            return escape_markdown(team_name)
        try:
            team_info = TeamInfo.from_team_name(players_spreadsheet, team_name)
            if players_spreadsheet.range_team_name:
                team_role = tosurnament.get_role(guild.roles, None, team_name)
                if team_role:
                    return team_role.mention
            user = tosurnament.UserAbstraction.get_from_player_info(self.bot, team_info.get_team_captain(), guild)
            member = user.get_member(guild)
            if member:
                return member.mention
            return escape_markdown(team_name)
        except Exception as e:
            self.bot.info(str(type(e)) + ": " + str(e))
            return escape_markdown(team_name)

    async def qualifier_match_notification(self, guild, tournament, bracket, channel, lobby_info, match_date, delta):
        if not (delta.days == 0 and delta.seconds >= 900 and delta.seconds < 1800):
            return
        players_spreadsheet = await bracket.get_players_spreadsheet()
        teams = []
        for team_cell in lobby_info.teams:
            if team_cell.get():
                team = await self.get_team_mention(guild, players_spreadsheet, team_cell.get())
                teams.append(team)
        if not teams:
            return
        referee_name = lobby_info.referee.get()
        referee_role = None
        notification_type = "notification"
        if referee_name:
            user = tosurnament.UserAbstraction.get_from_osu_name(self.bot, referee_name)
            if user.verified:
                referee = user.get_member(guild)
            else:
                referee = guild.get_member_named(referee_name)
            if referee:
                referee = referee.mention
            else:
                referee = referee_name
        else:
            referee_role = tosurnament.get_role(guild.roles, tournament.referee_role_id, "Referee")
            if referee_role:
                referee = referee_role.mention
                notification_type = "notification_no_referee"
            else:
                referee = ""
                notification_type = "notification_no_referre_no_role"
        match_date_timestamp = str(int(match_date.timestamp()))
        teams_mentions = "\n".join(teams)
        message = await self.send_reply_in_bg_task(
            guild,
            channel,
            "qualifier_match_notification",
            notification_type,
            lobby_info.lobby_id.get(),
            teams_mentions,
            referee,
            match_date_timestamp,
        )
        if referee_role:
            match_notification = MatchNotification(
                message_id_int=message.id,
                message_id=message.id,
                tournament_id=tournament.id,
                bracket_id=bracket.id,
                match_id=lobby_info.lobby_id.get(),
                teams_mentions=teams_mentions,
                date_info=match_date_timestamp,
                notification_type=2,
            )
            self.bot.session.add(match_notification)
        try:
            await message.add_reaction("👀")
            if referee_role:
                await message.add_reaction("💪")
        except Exception as e:
            self.bot.info(str(type(e)) + ": " + str(e))

    async def player_match_notification(self, guild, tournament, bracket, channel, match_info, match_date, delta):
        if not (delta.days == 0 and delta.seconds >= 900 and delta.seconds < 1800):
            return
        players_spreadsheet = await bracket.get_players_spreadsheet()
        team1 = await self.get_team_mention(guild, players_spreadsheet, match_info.team1.get())
        team2 = await self.get_team_mention(guild, players_spreadsheet, match_info.team2.get())
        referee_name = match_info.referees[0].get()
        referee_role = None
        notification_type = "notification"
        if referee_name:
            user = tosurnament.UserAbstraction.get_from_osu_name(self.bot, referee_name)
            if user.verified:
                referee = user.get_member(guild)
            else:
                referee = guild.get_member_named(referee_name)
            if referee:
                referee = referee.mention
            else:
                referee = referee_name
        else:
            referee_role = tosurnament.get_role(guild.roles, tournament.referee_role_id, "Referee")
            if referee_role:
                referee = referee_role.mention
                notification_type = "notification_no_referee"
            else:
                referee = ""
                notification_type = "notification_no_referre_no_role"
        match_date_timestamp = str(int(match_date.timestamp()))
        message = await self.send_reply_in_bg_task(
            guild,
            channel,
            "player_match_notification",
            notification_type,
            match_info.match_id.get(),
            team1,
            team2,
            referee,
            match_date_timestamp,
        )
        if referee_role:
            match_notification = MatchNotification(
                message_id_int=message.id,
                message_id=message.id,
                tournament_id=tournament.id,
                bracket_id=bracket.id,
                match_id=match_info.match_id.get(),
                team1_mention=team1,
                team2_mention=team2,
                date_info=match_date_timestamp,
                notification_type=0,
            )
            self.bot.session.add(match_notification)
        try:
            await message.add_reaction("👀")
            if referee_role:
                await message.add_reaction("💪")
        except Exception as e:
            self.bot.info(str(type(e)) + ": " + str(e))

    async def referee_match_notification(self, guild, tournament, bracket, channel, match_info, match_date, delta):
        if list(filter(None, [cell for cell in match_info.referees])):
            return
        if not (delta.days == 0 and delta.seconds >= 20700 and delta.seconds < 21600):
            return
        referee_role = tosurnament.get_role(guild.roles, tournament.referee_role_id, "Referee")
        if referee_role:
            referee = referee_role.mention
        else:
            referee = self.get_simple_string(guild, "referee")
        match_date_timestamp = str(int(match_date.timestamp()))
        team1 = escape_markdown(match_info.team1.get())
        team2 = escape_markdown(match_info.team2.get())
        message = await self.send_reply_in_bg_task(
            guild,
            channel,
            "referee_match_notification",
            "notification",
            match_info.match_id.get(),
            team1,
            team2,
            referee,
            match_date_timestamp,
        )
        match_notification = MatchNotification(
            message_id_int=message.id,
            message_id=message.id,
            tournament_id=tournament.id,
            bracket_id=bracket.id,
            match_id=match_info.match_id.get(),
            team1_mention=team1,
            team2_mention=team2,
            date_info=match_date_timestamp,
            notification_type=1,
        )
        self.bot.session.add(match_notification)
        try:
            await message.add_reaction("😱")
            await message.add_reaction("💪")
        except Exception as e:
            self.bot.info(str(type(e)) + ": " + str(e))

    async def match_notification(self, guild, tournament):
        player_match_notification_channel = None
        if tournament.match_notification_channel_id:
            player_match_notification_channel = self.bot.get_channel(int(tournament.match_notification_channel_id))
        staff_channel = None
        if tournament.staff_channel_id:
            staff_channel = self.bot.get_channel(int(tournament.staff_channel_id))
        if not player_match_notification_channel and not staff_channel:
            return
        matches_to_ignore = [match_id.casefold() for match_id in tournament.matches_to_ignore.split("\n")]
        for bracket in tournament.brackets:
            now = datetime.datetime.now(datetime.timezone.utc)
            schedules_spreadsheet = await bracket.get_schedules_spreadsheet(retry=True)
            if schedules_spreadsheet:
                match_ids = schedules_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    schedules_spreadsheet.range_match_id
                )
                for match_id_cell in match_ids:
                    if match_id_cell.casefold() in matches_to_ignore:
                        continue
                    match_info = MatchInfo.from_match_id_cell(schedules_spreadsheet, match_id_cell)
                    date_format = "%d %B"
                    if schedules_spreadsheet.date_format:
                        date_format = schedules_spreadsheet.date_format
                    match_date = tournament.parse_date(
                        match_info.get_datetime(),
                        date_formats=list(filter(None, [date_format + " %H:%M"])),
                    )
                    if match_date:
                        delta = match_date - now
                        if player_match_notification_channel:
                            await self.player_match_notification(
                                guild,
                                tournament,
                                bracket,
                                player_match_notification_channel,
                                match_info,
                                match_date,
                                delta,
                            )
                        if staff_channel:
                            await self.referee_match_notification(
                                guild, tournament, bracket, staff_channel, match_info, match_date, delta
                            )
            if qualifiers_spreadsheet := await bracket.get_qualifiers_spreadsheet(retry=True):
                lobby_ids = qualifiers_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    qualifiers_spreadsheet.range_lobby_id
                )
                for lobby_id_cell in lobby_ids:
                    if lobby_id_cell.casefold() in matches_to_ignore:
                        continue
                    lobby_info = LobbyInfo.from_lobby_id_cell(qualifiers_spreadsheet, lobby_id_cell)
                    date_format = "%d %B"
                    if schedules_spreadsheet and schedules_spreadsheet.date_format:
                        date_format = schedules_spreadsheet.date_format
                    lobby_date = tournament.parse_date(
                        lobby_info.get_datetime(),
                        date_formats=list(filter(None, [date_format + " %H:%M"])),
                    )
                    if lobby_date:
                        delta = lobby_date - now
                        if player_match_notification_channel:
                            await self.qualifier_match_notification(
                                guild,
                                tournament,
                                bracket,
                                player_match_notification_channel,
                                lobby_info,
                                match_date,
                                delta,
                            )

    async def match_notification_wrapper(self, guild, tournament):
        previous_notification_date = None
        try:
            now = datetime.datetime.utcnow()
            guild_id = str(guild.id)
            tosurnament_guild = self.get_guild(guild_id)
            if not tosurnament_guild:
                tosurnament_guild = tosurnament_api.create_guild(Guild(guild_id=guild_id, guild_id_snowflake=guild_id))
            elif tosurnament_guild.last_notification_date:
                previous_notification_date = tosurnament_guild.last_notification_date
                delta = now - previous_notification_date
                if (
                    delta.days == 0
                    and delta.seconds < 900
                    and int(now.minute / 15) == int(previous_notification_date.minute / 15)
                ):
                    return
            tosurnament_guild.last_notification_date = now
            tosurnament_api.update_guild(tosurnament_guild)
            await self.match_notification(guild, tournament)
        except (asyncio.CancelledError, tosurnament.SpreadsheetHttpError, tosurnament.DateIsNotString):
            return
        except Exception as e:
            self.bot.info_exception(e)
        finally:
            Spreadsheet.pickle_from_id.cache_clear()

    @tasks.loop(minutes=15.0)
    async def background_task_match_notification(self):
        tasks = []
        try:
            for guild in self.bot.guilds:
                try:
                    tournament = self.get_tournament(guild.id)
                except tosurnament.NoTournament:
                    continue
                tasks.append(self.bot.loop.create_task(self.match_notification_wrapper(guild, tournament)))
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    continue
            raise

    @background_task_match_notification.before_loop
    async def before_background_task_match_notification(self):
        self.bot.info("Waiting for bot to be ready before starting match_notification background task...")
        await self.bot.wait_until_ready()
        self.bot.info("Bot is ready. match_notification background task will start.")
        await self.background_task_match_notification()
        now = datetime.datetime.utcnow()
        delta_minutes = 15 - now.minute % 15
        await asyncio.sleep(delta_minutes * 60)

    @tasks.loop(hours=1.0)
    async def background_task_clean_allowed_reschedule(self):
        for guild in self.bot.guilds:
            try:
                tournament = self.get_tournament(guild.id)
                # This call cleans up outdated AllowedReschedules
                tosurnament_api.get_allowed_reschedules(tournament.id)
            except Exception:
                continue

    @background_task_clean_allowed_reschedule.before_loop
    async def before_background_task_clean_allowed_reschedule(self):
        self.bot.info("Waiting for bot to be ready before starting clean_allowed_reschedule background task...")
        await self.bot.wait_until_ready()
        self.bot.info("Bot is ready. clean_allowed_reschedule background task will start.")

    @on_raw_reaction_with_context("add", valid_emojis=["💪"])
    @with_corresponding_message(MatchNotification)
    async def reaction_on_match_notification(self, ctx, emoji, match_notification):
        """Allows a referee to take a match from its notification."""
        tournament = tosurnament_api.get_tournament(match_notification.tournament_id)
        if not tournament:
            self.bot.session.delete(match_notification)
            return
        referee_role = tosurnament.get_role(ctx.author.roles, tournament.referee_role_id, "Referee")
        if not referee_role:
            return
        bracket = tosurnament_api.get_bracket(tournament.id, match_notification.bracket_id)
        if not bracket:
            self.bot.session.delete(match_notification)
            return
        try:
            await self.take_or_drop_match_in_spreadsheets(
                [match_notification.match_id],
                tosurnament.UserDetails.get_as_referee(self.bot, ctx.author),
                True,
                await bracket.get_schedules_spreadsheet(),
                await bracket.get_qualifiers_spreadsheet(),
            )
            # TODO if return of function not empty send error
        except Exception as e:
            await self.on_cog_command_error(ctx, e)
            return
        ctx.command.name = "player_match_notification"
        if match_notification.notification_type == 1:
            ctx.command.name = "referee_match_notification"
        elif match_notification.notification_type == 2:
            ctx.command.name = "qualifier_match_notification"
        match_notification_message = await ctx.channel.fetch_message(match_notification.message_id_int)
        if match_notification.notification_type == 2:
            await match_notification_message.edit(
                content=self.get_string(
                    ctx,
                    "edited",
                    match_notification.match_id,
                    match_notification.teams_mentions,
                    referee_role.mention,
                    match_notification.date_info,
                    ctx.author.mention,
                )
            )
        else:
            await match_notification_message.edit(
                content=self.get_string(
                    ctx,
                    "edited",
                    match_notification.match_id,
                    match_notification.team1_mention,
                    match_notification.team2_mention,
                    referee_role.mention,
                    match_notification.date_info,
                    ctx.author.mention,
                )
            )
        self.bot.session.delete(match_notification)

    @on_raw_reaction_with_context("add", valid_emojis=["❌"])
    @with_corresponding_message(StaffRescheduleMessage)
    async def reaction_on_staff_reschedule_message(self, ctx, emoji, staff_reschedule_message):
        """Removes the referee from the schedule spreadsheet"""
        referees_id = [referee_id for referee_id in staff_reschedule_message.referees_id.split("\n") if referee_id]
        streamers_id = [streamer_id for streamer_id in staff_reschedule_message.streamers_id.split("\n") if streamer_id]
        commentators_id = [
            commentator_id for commentator_id in staff_reschedule_message.commentators_id.split("\n") if commentator_id
        ]
        author_id = str(ctx.author.id)
        if author_id not in referees_id and author_id not in streamers_id and author_id not in commentators_id:
            return
        tournament = tosurnament_api.get_tournament(staff_reschedule_message.tournament_id)
        if not tournament:
            self.bot.session.delete(staff_reschedule_message)
            return
        bracket = tosurnament_api.get_bracket(tournament.id, staff_reschedule_message.bracket_id)
        if not bracket:
            self.bot.session.delete(staff_reschedule_message)
            return
        schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
        if not schedules_spreadsheet:
            return
        try:
            user_details = tosurnament.UserDetails.get_from_user(self.bot, ctx.author, tournament)
            await self.take_or_drop_match_in_spreadsheets(
                [staff_reschedule_message.match_id], user_details, False, schedules_spreadsheet
            )
            # TODO if return of function not empty send error + update message instead of reply
            if author_id in referees_id:
                referees_id.remove(author_id)
                staff_reschedule_message.referees_id = "\n".join([str(referee_id) for referee_id in referees_id])
            if author_id in streamers_id:
                streamers_id.remove(author_id)
                staff_reschedule_message.streamers_id = "\n".join([str(streamer_id) for streamer_id in streamers_id])
            if author_id in commentators_id:
                commentators_id.remove(author_id)
                staff_reschedule_message.commentators_id = "\n".join(
                    [str(commentator_id) for commentator_id in commentators_id]
                )
            self.bot.session.update(staff_reschedule_message)

            if staff_reschedule_message.previous_date:
                previous_date_string = "<t:{0}:F>".format(staff_reschedule_message.previous_date)
            else:
                previous_date_string = self.get_string(ctx, "no_previous_date")
            new_date_string = "<t:{0}:F>".format(staff_reschedule_message.new_date)
            message = await ctx.channel.fetch_message(ctx.message.id)
            referees = [
                referee.mention
                for referee in list(filter(None, [ctx.guild.get_member(int(referee_id)) for referee_id in referees_id]))
            ]
            streamers = [
                streamer.mention
                for streamer in list(
                    filter(None, [ctx.guild.get_member(int(streamer_id)) for streamer_id in streamers_id])
                )
            ]
            commentators = [
                commentator.mention
                for commentator in list(
                    filter(None, [ctx.guild.get_member(int(commentator_id)) for commentator_id in commentators_id])
                )
            ]
            if referees + streamers + commentators:
                await message.edit(
                    content=self.get_string(
                        ctx,
                        "staff_notification",
                        staff_reschedule_message.match_id,
                        staff_reschedule_message.team1,
                        staff_reschedule_message.team2,
                        previous_date_string,
                        new_date_string,
                        " / ".join(referees),
                        " / ".join(streamers),
                        " / ".join(commentators),
                    )
                )
            else:
                self.bot.session.delete(staff_reschedule_message)
                await message.edit(
                    content=self.get_string(
                        ctx,
                        "staff_notification_all_staff_removed",
                        staff_reschedule_message.match_id,
                        staff_reschedule_message.team1,
                        staff_reschedule_message.team2,
                        previous_date_string,
                        new_date_string,
                    )
                )
        except Exception as e:
            await self.on_cog_command_error(ctx, e)


async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(TosurnamentStaffCog(bot))
