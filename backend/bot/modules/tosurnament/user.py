"""User commands"""

import datetime
import dateparser
import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.schedules_spreadsheet import MatchInfo
from common.api.spreadsheet import HttpError
from common.api import osu
from common.api import challonge


class TosurnamentUserCog(tosurnament.TosurnamentBaseModule, name="user"):
    """Tosurnament user commands"""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    async def change_name_in_player_spreadsheet(self, ctx, bracket, previous_name, new_name):
        players_spreadsheet = bracket.players_spreadsheet
        if not bracket.players_spreadsheet:
            return
        changed_name = players_spreadsheet.spreadsheet.change_value_in_range(
            players_spreadsheet.range_team, previous_name, new_name
        )
        if changed_name:
            try:
                players_spreadsheet.spreadsheet.update()
            except HttpError as e:
                raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "players", e.error)

    async def change_name_in_schedules_spreadsheet(self, ctx, bracket, previous_name, new_name, user_roles):
        schedules_spreadsheet = bracket.schedules_spreadsheet
        if not schedules_spreadsheet:
            return
        changed_name = False
        spreadsheet = schedules_spreadsheet.spreadsheet
        if user_roles.player:
            changed_name |= spreadsheet.change_value_in_range(
                schedules_spreadsheet.range_team1, previous_name, new_name
            )
            changed_name |= spreadsheet.change_value_in_range(
                schedules_spreadsheet.range_team2, previous_name, new_name
            )
        for role_name, role_store in user_roles.get_staff_roles_as_dict().items():
            if role_store:
                changed_name |= spreadsheet.change_value_in_range(
                    getattr(schedules_spreadsheet, "range_" + role_name.lower()), previous_name, new_name,
                )
        if changed_name:
            try:
                schedules_spreadsheet.spreadsheet.update()
            except HttpError as e:
                raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "schedules", e.error)

    @commands.command(aliases=["nc", "change_name", "cn"])
    @commands.bot_has_permissions(manage_nicknames=True, manage_roles=True)
    async def name_change(self, ctx):
        """Allows users to change their nickname to their osu! username or update it."""
        user = self.get_verified_user(ctx.author.id)
        previous_name = user.osu_previous_name
        new_name = user.osu_name
        osu_user = osu.get_user(user.osu_id)
        if not osu_user:
            await self.send_reply(ctx, ctx.command.name, "osu_get_user_error")
        if osu_user.name != new_name:
            previous_name = new_name
            new_name = osu_user.name
        if not previous_name:
            await self.send_reply(ctx, ctx.command.name, "change_name_unneeded")
            return
        user_roles = tosurnament.UserRoles.get_from_context(ctx)

        if user_roles.is_user():
            tournament = self.get_tournament(ctx.guild.id)
            for bracket in tournament.brackets:
                try:
                    if user_roles.player:
                        await self.change_name_in_player_spreadsheet(ctx, bracket, previous_name, new_name)
                    if user_roles.player or user_roles.is_staff():
                        await self.change_name_in_schedules_spreadsheet(
                            ctx, bracket, previous_name, new_name, user_roles
                        )
                    if bracket.challonge:
                        participants = challonge.get_participants(bracket.challonge)
                        for participant in participants:
                            if participant.name == previous_name:
                                participant.update_name(new_name)
                except Exception as e:
                    await self.on_cog_command_error(ctx, ctx.command.name, e)
                    return
        try:
            await ctx.author.edit(nick=new_name)
        except discord.Forbidden:
            await self.send_reply(ctx, ctx.command.name, "change_nickname_forbidden")
        user.osu_previous_name = previous_name
        user.osu_name = new_name
        self.bot.session.update(user)
        await self.send_reply(ctx, ctx.command.name, "success")

    def fill_matches_info_for_roles(self, ctx, bracket, matches_to_ignore, user_roles, user_name):
        team_name = None
        if user_roles.player:
            team_name = self.find_player_identification(ctx, bracket, user_name)
        schedules_spreadsheet = bracket.schedules_spreadsheet
        if not schedules_spreadsheet:
            return
        match_ids_cells = schedules_spreadsheet.spreadsheet.get_cells_with_value_in_range(
            schedules_spreadsheet.range_match_id
        )
        now = datetime.datetime.utcnow()
        for match_id_cell in match_ids_cells:
            if match_id_cell.value in matches_to_ignore:
                continue
            match_info = MatchInfo.from_match_id_cell(schedules_spreadsheet, match_id_cell)
            date_format = "%d %B"
            if schedules_spreadsheet.date_format:
                date_format = schedules_spreadsheet.date_format
            match_date = dateparser.parse(
                match_info.get_datetime(), date_formats=list(filter(None, [date_format + " %H:%M"])),
            )
            if not match_date:
                continue
            if match_date < now:
                continue
            if (
                user_roles.player
                and team_name
                and (match_info.team1.has_value(team_name) or match_info.team2.has_value(team_name))
            ):
                user_roles.player.taken_matches.append((bracket.name, match_info, match_date))
            for referee_cell in match_info.referees:
                if user_roles.referee and referee_cell.has_value(user_name):
                    user_roles.referee.taken_matches.append((bracket.name, match_info, match_date))
            for streamer_cell in match_info.streamers:
                if user_roles.streamer and streamer_cell.has_value(user_name):
                    user_roles.streamer.taken_matches.append((bracket.name, match_info, match_date))
            for commentator_cell in match_info.commentators:
                if user_roles.commentator and commentator_cell.has_value(user_name):
                    user_roles.commentator.taken_matches.append((bracket.name, match_info, match_date))

    @commands.command(aliases=["get_match", "gm", "list_matches", "list_match", "lm", "see_matches", "see_match", "sm"])
    @commands.guild_only()
    async def get_matches(self, ctx):
        """Sends a private message to the author with the list of matches they are in (as a player or staff)."""
        tournament = self.get_tournament(ctx.guild.id)
        # ! Temporary for nik's tournament
        # tosurnament_user = self.get_verified_user(ctx.author.id)
        osu_name = ctx.author.display_name
        user_roles = tosurnament.UserRoles.get_as_all()
        matches_to_ignore = tournament.matches_to_ignore.split("\n")
        for bracket in tournament.brackets:
            try:
                self.fill_matches_info_for_roles(ctx, bracket, matches_to_ignore, user_roles, osu_name)
            except Exception as e:
                await self.on_cog_command_error(ctx, ctx.command.name, e)
        reply_string = self.get_string(ctx.command.name, "success", tournament.acronym, tournament.name) + "\n"
        for role_name, role_store in user_roles.get_as_dict().items():
            if role_store and role_store.taken_matches:
                reply_string += "\n"
                reply_string += self.get_string(ctx.command.name, "role_match", role_name)
                for bracket_name, match_info, match_date in sorted(role_store.taken_matches, key=lambda x: x[2]):
                    match_date = match_date.strftime(tosurnament.PRETTY_DATE_FORMAT)
                    reply_string += match_date
                    if bracket_name and bracket_name != tournament.name:
                        reply_string += " | " + bracket_name
                    reply_string += " | **" + match_info.match_id.value + "**:\n"
                    reply_string += match_info.team1.value + " vs " + match_info.team2.value + "\n"
        await ctx.author.send(reply_string)


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentUserCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentUserCog(bot))
