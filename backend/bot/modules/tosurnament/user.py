"""User commands"""

import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.api import osu
from common.api import tosurnament as tosurnament_api
from common.databases.tosurnament.spreadsheets.schedules_spreadsheet import MatchInfo


class TosurnamentUserCog(tosurnament.TosurnamentBaseModule, name="user"):
    """Tosurnament user commands"""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    async def change_name_in_player_spreadsheet(self, ctx, bracket, previous_name, new_name):
        players_spreadsheet = await bracket.get_players_spreadsheet()
        if not players_spreadsheet:
            return
        changed_name = players_spreadsheet.spreadsheet.change_value_in_range(
            players_spreadsheet.range_team, previous_name, new_name
        )
        if changed_name:
            self.add_update_spreadsheet_background_task(players_spreadsheet)

    async def change_name_in_schedules_spreadsheet(self, ctx, bracket, previous_name, new_name, user_details):
        schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
        if not schedules_spreadsheet:
            return
        changed_name = False
        spreadsheet = schedules_spreadsheet.spreadsheet
        if user_details.player:
            changed_name |= spreadsheet.change_value_in_range(
                schedules_spreadsheet.range_team1, previous_name, new_name
            )
            changed_name |= spreadsheet.change_value_in_range(
                schedules_spreadsheet.range_team2, previous_name, new_name
            )
        for role_store in user_details.get_staff_roles():
            changed_name |= spreadsheet.change_value_in_range(
                getattr(schedules_spreadsheet, "range_" + role_store.name.lower()),
                previous_name,
                new_name,
            )
        if changed_name:
            self.add_update_spreadsheet_background_task(schedules_spreadsheet)

    @commands.command(aliases=["nc", "change_name", "cn"])
    @commands.guild_only()
    async def name_change(self, ctx):
        """Allows users to change their nickname to their osu! username or update it."""
        user = self.get_verified_user(ctx.author.id)
        current_name = user.osu_name
        osu_user = osu.get_user(user.osu_id)
        if not osu_user:
            await self.send_reply(ctx, "osu_get_user_error")
            return
        if osu_user.name == current_name:
            await self.send_reply(ctx, "change_name_unneeded")
            return
        previous_name = current_name
        new_name = osu_user.name

        # TODO: allow disabling write on spreadsheet
        # user_details = tosurnament.UserDetails.get_from_ctx(ctx)
        # if user_details.is_user():
        #     tournament = self.get_tournament(ctx.guild.id)
        #     for bracket in tournament.brackets:
        #         try:
        #             if user_details.player:
        #                 await self.change_name_in_player_spreadsheet(ctx, bracket, previous_name, new_name)
        #             if user_details.player or user_details.is_staff():
        #                 await self.change_name_in_schedules_spreadsheet(
        #                     ctx, bracket, previous_name, new_name, user_details
        #                 )
        #             if bracket.challonge:
        #                 participants = challonge.get_participants(bracket.challonge)
        #                 for participant in participants:
        #                     if participant.name == previous_name:
        #                         participant.update_name(new_name)
        #         except Exception as e:
        #             await self.on_cog_command_error(ctx, e)
        #             return
        try:
            await ctx.author.edit(nick=new_name)
        except discord.Forbidden:
            await self.send_reply(ctx, "change_nickname_forbidden")
        user.osu_previous_name = previous_name
        user.osu_name = new_name
        user.osu_name_hash = new_name
        tosurnament_api.update_user(user)
        await self.send_reply(ctx, "success")

    async def find_team_name_of_member(self, ctx, bracket):
        players_spreadsheet = await bracket.get_players_spreadsheet()
        if not players_spreadsheet or not players_spreadsheet.range_team_name:
            user = tosurnament.UserAbstraction.get_from_user(self.bot, ctx.author)
            if user.verified:
                return user.name
            return ctx.author.display_name
        team_infos, _ = await self.get_all_teams_infos_and_roles(ctx.guild, players_spreadsheet)
        for team_info in team_infos:
            if self.get_player_in_team(ctx.author, team_info):
                return team_info.team_name.get()
        return None

    async def fill_matches_info_for_roles(self, ctx, tournament, bracket, user_details):
        user_name = user_details.name
        team_name = None
        if user_details.player:
            bracket_role = tosurnament.get_role(ctx.guild.roles, bracket.role_id)
            if not bracket_role or tosurnament.get_role(ctx.author.roles, bracket.role_id):
                team_name = await self.find_team_name_of_member(ctx, bracket)
        matches_data = await self.get_next_matches_info_for_bracket(tournament, bracket)
        for match_info, match_date in matches_data:
            if isinstance(match_info, MatchInfo):
                if team_name and (match_info.team1.has_value(team_name) or match_info.team2.has_value(team_name)):
                    user_details.player.taken_matches.append((bracket.name, match_info, match_date))
                if user_details.referee:
                    for referee_cell in match_info.referees:
                        if referee_cell.has_value(user_name):
                            user_details.referee.taken_matches.append((bracket.name, match_info, match_date))
                            break
                if user_details.streamer:
                    for streamer_cell in match_info.streamers:
                        if streamer_cell.has_value(user_name):
                            user_details.streamer.taken_matches.append((bracket.name, match_info, match_date))
                            break
                if user_details.commentator:
                    for commentator_cell in match_info.commentators:
                        if commentator_cell.has_value(user_name):
                            user_details.commentator.taken_matches.append((bracket.name, match_info, match_date))
                            break
            else:
                if team_name:
                    for team_cell in match_info.teams:
                        if team_cell.has_value(team_name):
                            user_details.player.taken_matches.append((bracket.name, match_info, match_date))
                if user_details.referee and match_info.referee and match_info.referee.has_value(user_name):
                    user_details.referee.taken_matches.append((bracket.name, match_info, match_date))

    @commands.command(aliases=["get_match", "gm", "list_matches", "list_match", "lm", "see_matches", "see_match", "sm"])
    @commands.guild_only()
    async def get_matches(self, ctx):
        """Sends a private message to the author with the list of matches they are in (as a player or staff)."""
        tournament = self.get_tournament(ctx.guild.id)
        user_details = tosurnament.UserDetails.get_as_all(ctx.bot, ctx.author)
        for bracket in tournament.brackets:
            try:
                await self.fill_matches_info_for_roles(ctx, tournament, bracket, user_details)
            except Exception as e:
                await self.on_cog_command_error(ctx, e)
        reply_string = self.get_string(ctx, "success", tournament.acronym, tournament.name) + "\n"
        for role_store in user_details.get_all_roles():
            if role_store.taken_matches:
                tmp_reply_string = "\n"
                tmp_reply_string += self.get_string(ctx, "role_match", role_store.name)
                for bracket_name, match_info, match_date in sorted(role_store.taken_matches, key=lambda x: x[2]):
                    tmp_reply_string += tosurnament.get_pretty_date(tournament, match_date)
                    if len(tournament.brackets) > 1:
                        tmp_reply_string += " | " + bracket_name
                    if isinstance(match_info, MatchInfo):
                        tmp_reply_string += " | **" + match_info.match_id.get() + "**:\n"
                        tmp_reply_string += match_info.team1.get() + " vs " + match_info.team2.get() + "\n"
                    else:
                        tmp_reply_string += " | Qualifiers **" + match_info.lobby_id.get() + "**\n"
                    if len(reply_string) + len(tmp_reply_string) >= 2000:
                        await ctx.author.send(reply_string)
                        reply_string = tmp_reply_string
                    else:
                        reply_string += tmp_reply_string
                    tmp_reply_string = ""
        await ctx.author.send(reply_string)

    @commands.command(aliases=["smi"])
    async def show_my_info(self, ctx):
        """Sends a private message to the author with their user information stored in the bot."""
        user = self.get_user(ctx.author.id)
        if not user:
            raise tosurnament.UserNotLinked()
        dm_channel = await ctx.author.create_dm()
        await self.send_reply(
            ctx,
            "success",
            user.discord_id_snowflake,
            user.osu_id,
            user.osu_name,
            user.osu_previous_name,
            str(user.verified),
            channel=dm_channel,
        )


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentUserCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentUserCog(bot))
