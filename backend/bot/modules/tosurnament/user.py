"""User commands"""

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
        players_spreadsheet = self.get_players_spreadsheet(bracket)
        if not players_spreadsheet:
            return
        try:
            spreadsheet, worksheet = self.get_spreadsheet_worksheet(players_spreadsheet)
        except HttpError as e:
            raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "players")
        changed_name = worksheet.change_value_in_range(players_spreadsheet.range_team, previous_name, new_name)
        if changed_name:
            try:
                spreadsheet.update()
            except HttpError as e:
                raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "players")

    async def change_name_in_schedules_spreadsheet(self, ctx, bracket, previous_name, new_name, user_roles):
        schedules_spreadsheet = self.get_schedules_spreadsheet(bracket)
        if not schedules_spreadsheet:
            return
        try:
            spreadsheet, worksheet = self.get_spreadsheet_worksheet(schedules_spreadsheet)
        except HttpError as e:
            raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "schedules")
        if not spreadsheet:
            return
        changed_name = False
        if user_roles.player:
            changed_name |= worksheet.change_value_in_range(schedules_spreadsheet.range_team1, previous_name, new_name)
            changed_name |= worksheet.change_value_in_range(schedules_spreadsheet.range_team2, previous_name, new_name)
        for role_name, role_store in user_roles.get_staff_roles_as_dict().items():
            if role_store:
                changed_name |= worksheet.change_value_in_range(
                    getattr(schedules_spreadsheet, "range_" + role_name.lower()), previous_name, new_name,
                )
        if changed_name:
            try:
                spreadsheet.update()
            except HttpError as e:
                raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "schedules")

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
        tournament = self.get_tournament(ctx.guild.id)
        brackets = self.get_all_brackets(tournament)
        user_roles = tosurnament.UserRoles.get_from_context(ctx)

        if user_roles.is_user():
            for bracket in brackets:
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

    def fill_matches_info_for_roles(self, ctx, bracket, user_roles, user_name):
        team_name = None
        if user_roles.player:
            team_name = self.find_player_identification(ctx, bracket, user_name)
        schedules_spreadsheet = self.get_schedules_spreadsheet(bracket)
        if not schedules_spreadsheet:
            return
        try:
            spreadsheet, worksheet = self.get_spreadsheet_worksheet(schedules_spreadsheet)
        except HttpError as e:
            raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "schedules")
        match_ids_cells = worksheet.get_cells_with_value_in_range(schedules_spreadsheet.range_match_id)
        for match_id_cell in match_ids_cells:
            match_info = MatchInfo.from_match_id_cell(schedules_spreadsheet, worksheet, match_id_cell)
            if team_name and (match_info.team1.has_value(team_name) or match_info.team2.has_value(team_name)):
                user_roles.player.taken_matches.append((bracket.name, match_info))
            for referee_cell in match_info.referees:
                if referee_cell.has_value(user_name):
                    user_roles.referee.taken_matches.append((bracket.name, match_info))
            for streamer_cell in match_info.streamers:
                if streamer_cell.has_value(user_name):
                    user_roles.streamer.taken_matches.append((bracket.name, match_info))
            for commentator_cell in match_info.commentators:
                if commentator_cell.has_value(user_name):
                    user_roles.commentator.taken_matches.append((bracket.name, match_info))

    @commands.command(aliases=["get_match", "gm", "list_matches", "list_match", "lm", "see_matches", "see_match", "sm"])
    @commands.guild_only()
    async def get_matches(self, ctx):
        """Sends a private message to the author with the list of matches they are in (as a player or staff)."""
        tournament = self.get_tournament(ctx.guild.id)
        brackets = self.get_all_brackets(tournament)
        user_roles = tosurnament.UserRoles.get_from_context(ctx)
        tosurnament_user = self.get_verified_user(ctx.author.id)
        for bracket in brackets:
            try:
                self.fill_matches_info_for_roles(ctx, bracket, user_roles, tosurnament_user.osu_name)
            except Exception as e:
                await self.on_cog_command_error(ctx, ctx.command.name, e)
        reply_string = self.get_string(ctx.command.name, "success", tournament.acronym, tournament.name) + "\n"
        for role_name, role_store in user_roles.get_as_dict().items():
            if role_store.taken_matches:
                reply_string += "\n"
                reply_string += self.get_string(ctx.command.name, "role_match", role_name)
                for bracket_name, match_info in role_store.taken_matches:
                    reply_string += (
                        "**" + dateparser.parse(match_info.get_datetime()).strftime("%d %B at %H:%M UTC") + "**"
                    )
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
