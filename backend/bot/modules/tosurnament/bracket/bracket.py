"""Contains all bracket settings commands related to Tosurnament."""

import asyncio
import datetime
import discord
from discord.ext import commands, tasks
from bot.modules.tosurnament import module as tosurnament
from common.api import challonge
from common.databases.tosurnament.bracket import Bracket
from common.api import osu
from common.api import tosurnament as tosurnament_api
from common.config import constants


class TosurnamentBracketCog(tosurnament.TosurnamentBaseModule, name="bracket"):
    """Tosurnament bracket settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.background_task_update_spreadsheet.start()

    def cog_unload(self):
        self.background_task_update_spreadsheet.stop()

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["sbn"])
    async def set_bracket_name(self, ctx, *, name: str):
        """Modifies the current bracket's name."""
        await self.set_bracket_values(ctx, {"name": name})

    @commands.command(aliases=["sbr"])
    async def set_bracket_role(self, ctx, *, role: discord.Role):
        """Modifies the current bracket's role."""
        await self.set_bracket_values(ctx, {"role_id": str(role.id)})

    @commands.command(aliases=["scbr"])
    async def set_current_bracket_round(self, ctx, *, current_round: str = ""):
        """Sets the round of the current bracket."""
        await self.set_bracket_values(ctx, {"current_round": current_round})

    @commands.command(aliases=["sprc"])
    async def set_post_result_channel(self, ctx, *, channel: discord.TextChannel):
        """Sets the post result's channel."""
        await self.set_bracket_values(ctx, {"post_result_channel_id": str(channel.id)})

    @commands.command(aliases=["sc"])
    async def set_challonge(self, ctx, challonge_tournament: str):
        """Sets the challonge."""
        challonge_tournament = challonge.extract_tournament_id(challonge_tournament)
        await self.set_bracket_values(ctx, {"challonge": challonge_tournament})

    @commands.command(aliases=["srrfr"])
    async def set_rank_range_for_registration(self, ctx, minimum_rank: int, maximum_rank: int = 0):
        """Sets the rank range to be able to register to a bracket."""
        await self.set_bracket_values(ctx, {"minimum_rank": minimum_rank, "maximum_rank": maximum_rank})

    @commands.command(aliases=["sre"])
    async def set_registration_end(self, ctx, *, date: str):
        """Sets the registration end date."""
        tournament = self.get_tournament(ctx.guild.id)
        try:
            new_date = tournament.parse_date(date, prefer_dates_from="future")
        except ValueError:
            raise commands.UserInputError()
        if not new_date:
            raise commands.UserInputError()
        new_date_string = new_date.strftime(tosurnament.DATABASE_DATE_FORMAT)
        await self.set_bracket_values(ctx, {"registration_end_date": new_date_string})

    def is_player_in_challonge(self, member, teams_info, participants):
        participants_casefold = [participant.casefold() for participant in participants]
        user = tosurnament.UserAbstraction.get_from_user(self.bot, member)
        if teams_info:
            for team_info in teams_info:
                if player := self.get_player_in_team(member, team_info):
                    if player.name.casefold() in participants_casefold:
                        return team_info, player.name.get()
                    else:
                        return None, None
        elif user.verified and user.name.casefold() in participants_casefold:
            return None, user.name
        return None, None

    def get_all_brackets_string(self, brackets):
        brackets_string = ""
        for i, bracket in enumerate(brackets):
            brackets_string += str(i + 1) + ": `" + bracket.name + "`\n"
        return brackets_string

    @commands.command(aliases=["cpr"])
    async def clear_player_role(self, ctx, bracket_index: int = None, remove_player_role: bool = True):
        """Removes the player role of users not present in the challonge."""
        tournament = self.get_tournament(ctx.guild.id)
        brackets = tournament.brackets
        bracket = self.get_bracket_from_index(brackets, bracket_index)
        if not bracket:
            await self.send_reply(ctx, "default", self.get_all_brackets_string(brackets))
            return
        if not bracket.challonge:
            raise tosurnament.NoChallonge(bracket.name)
        player_role = tosurnament.get_role(ctx.guild.roles, tournament.player_role_id, "Player")
        bracket_role = tosurnament.get_role(ctx.guild.roles, bracket.role_id, bracket.name)
        team_captain_role = tosurnament.get_role(ctx.guild.roles, tournament.team_captain_role_id, "Team Captain")
        if remove_player_role:
            roles_to_remove = list(filter(None, [player_role, bracket_role, team_captain_role]))
        else:
            roles_to_remove = list(filter(None, [bracket_role, team_captain_role]))

        teams_info, teams_roles = await self.get_all_teams_infos_and_roles(
            ctx.guild, await bracket.get_players_spreadsheet()
        )
        roles_to_remove = [*roles_to_remove, *teams_roles]

        challonge_tournament = challonge.get_tournament(bracket.challonge)
        running_participants = challonge_tournament.get_running_participants()

        players_found = []
        n_user_roles_removed = 0
        users_role_not_removed = []
        for member in ctx.guild.members:
            if bracket_role:
                if not tosurnament.get_role(member.roles, bracket_role.id):
                    continue
            elif player_role and not tosurnament.get_role(member.roles, player_role.id):
                continue
            _, player_name = self.is_player_in_challonge(member, teams_info, running_participants)
            if player_name:
                players_found.append(player_name.casefold())
            else:
                if member:
                    try:
                        await member.remove_roles(*roles_to_remove)
                        n_user_roles_removed += 1
                    except Exception:
                        users_role_not_removed.append(str(member))

        success_extra = ""
        players_not_found = []
        for participant in running_participants:
            if participant.casefold() not in players_found:
                players_not_found.append(participant)
        if players_not_found:
            success_extra += self.get_string(ctx, "players_not_found", "\n".join(players_not_found))
        if users_role_not_removed:
            success_extra += self.get_string(ctx, "users_role_not_removed", "\n".join(users_role_not_removed))
        await self.send_reply(ctx, "success", bracket.name, n_user_roles_removed, len(players_found), success_extra)

    @commands.command(aliases=["gpr"])
    async def give_player_role(self, ctx, bracket_index: int = None):
        """Gives the player role to users present in the challonge."""
        tournament = self.get_tournament(ctx.guild.id)
        brackets = tournament.brackets
        bracket = self.get_bracket_from_index(brackets, bracket_index)
        if not bracket:
            await self.send_reply(ctx, "default", self.get_all_brackets_string(brackets))
            return
        if not bracket.challonge:
            raise tosurnament.NoChallonge(bracket.name)
        player_role = tosurnament.get_role(ctx.guild.roles, tournament.player_role_id, "Player")
        bracket_role = tosurnament.get_role(ctx.guild.roles, bracket.role_id, bracket.name)
        team_captain_role = tosurnament.get_role(ctx.guild.roles, tournament.team_captain_role_id, "Team Captain")
        roles_to_add = list(filter(None, [player_role, bracket_role]))

        challonge_tournament = challonge.get_tournament(bracket.challonge)
        running_participants = challonge_tournament.get_running_participants()

        teams_info, _ = await self.get_all_teams_infos_and_roles(ctx.guild, await bracket.get_players_spreadsheet())

        n_user_roles_added = 0
        users_role_not_added = []
        players_found = []
        for member in ctx.guild.members:
            team_info, player_name = self.is_player_in_challonge(member, teams_info, running_participants)
            if player_name:
                players_found.append(player_name.casefold())
                roles_to_add_to_player = list(roles_to_add)
                if team_info:
                    team_role = tosurnament.get_role(ctx.guild.roles, None, team_info.team_name.get())
                    if team_role:
                        roles_to_add_to_player.append(team_role)
                    if team_captain_role and team_info.get_team_captain().name.casefold() == player_name.casefold():
                        roles_to_add_to_player.append(team_captain_role)
                try:
                    await member.add_roles(*roles_to_add_to_player)
                    n_user_roles_added += 1
                except Exception:
                    users_role_not_added.append(str(member))

        success_extra = ""
        players_not_found = []
        for participant in running_participants:
            if participant.casefold() not in players_found:
                players_not_found.append(participant)
        if players_not_found:
            success_extra += self.get_string(ctx, "players_not_found", "\n".join(players_not_found))
        if users_role_not_added:
            success_extra += self.get_string(ctx, "users_role_not_added", "\n".join(users_role_not_added))
        await self.send_reply(ctx, "success", bracket.name, n_user_roles_added, len(players_not_found), success_extra)

    async def set_bracket_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        for key, value in values.items():
            setattr(tournament.current_bracket, key, value)
        tosurnament_api.update_bracket(tournament.id, tournament.current_bracket)
        await self.send_reply(ctx, "success", value)
        await self.send_reply(ctx, "use_dashboard", constants.TOSURNAMENT_DASHBOARD_URI, ctx.guild.id)

    @commands.command(aliases=["cp"])
    async def copy_bracket(self, ctx, index_from: int, index_to: int):
        """Copies the settings of a bracket to another one."""
        tournament = self.get_tournament(ctx.guild.id)
        brackets = tournament.brackets
        if index_from > 0 and index_from <= len(brackets) and index_to > 0 and index_to <= len(brackets):
            bracket_from = brackets[index_from - 1]
            bracket_to = brackets[index_to - 1]
            bracket_to.post_result_channel_id = bracket_from.post_result_channel_id
            bracket_to.current_round = bracket_from.current_round

            for spreadsheet_type in Bracket.get_spreadsheet_types().keys():
                spreadsheet_from = bracket_from.get_spreadsheet_from_type(spreadsheet_type)
                if spreadsheet_from:
                    spreadsheet_to = bracket_to.get_spreadsheet_from_type(spreadsheet_type)
                    if not spreadsheet_to:
                        spreadsheet_to = getattr(tosurnament_api, "create_" + spreadsheet_type)(
                            tournament.id, bracket_to.id, spreadsheet_from
                        )
                    else:
                        spreadsheet_from.copy_to(spreadsheet_to)
                        getattr(tosurnament_api, "update_" + spreadsheet_type)(
                            tournament.id, bracket_to.id, spreadsheet_to
                        )

            await self.send_reply(ctx, "success", bracket_from.name, bracket_to.name)
            return
        raise commands.UserInputError()

    @commands.command(aliases=["sbs"])
    async def show_bracket_settings(self, ctx):
        """Shows the bracket settings."""
        tournament = self.get_tournament(ctx.guild.id)
        await self.show_object_settings(ctx, tournament.current_bracket, stack_depth=2)

    @commands.command(aliases=["gsrv"])
    async def get_spreadsheet_range_values(
        self, ctx, spreadsheet_type: str, range_name: str, only_filled: bool = False
    ):
        tournament = self.get_tournament(ctx.guild.id)
        bracket = tournament.current_bracket
        spreadsheet = getattr(bracket, "_" + spreadsheet_type + "_spreadsheet", None)
        if not spreadsheet:
            return
        spreadsheet_range = getattr(spreadsheet, range_name, None)
        if not spreadsheet_range:
            spreadsheet_range = getattr(spreadsheet, "range_" + range_name, None)
            if not spreadsheet_range:
                return
        await spreadsheet.get_spreadsheet(force_sync=True)
        cells = spreadsheet.spreadsheet.get_range(spreadsheet_range)
        to_send = ""
        for row in cells:
            for cell in row:
                if only_filled and not cell:
                    continue
                cell_as_str = repr(cell) + " "
                if len(to_send + cell_as_str) >= 2000:
                    await ctx.send(to_send)
                    to_send = ""
                to_send += cell_as_str
        await ctx.send(to_send)

    async def update_players_spreadsheet_registration(self, guild, tournament):
        now = datetime.datetime.now()
        for bracket in tournament.brackets:
            if not bracket.registration_end_date:
                continue
            registration_end_date = datetime.datetime.strptime(
                bracket.registration_end_date, tosurnament.DATABASE_DATE_FORMAT
            )
            if now > registration_end_date:
                continue
            players_spreadsheet = await bracket.get_players_spreadsheet()
            if not players_spreadsheet:
                continue
            team_infos, _ = await self.get_all_teams_infos_and_roles(guild, players_spreadsheet)
            update_spreadsheet = False
            for team_info in team_infos:
                for player_info in team_info.players:
                    osu_id = player_info.name.get()
                    if player_info.osu_id:
                        osu_id = player_info.osu_id.get()
                    osu_user = osu.get_user(osu_id, m=tournament.game_mode)
                    if not osu_user:
                        continue
                    if player_info.name != osu_user.name:
                        user = tosurnament.UserAbstraction.get_from_player_info(self.bot, player_info, guild)
                        member = user.get_member(guild)
                        if member:
                            try:
                                await member.edit(nick=osu_user.name)
                            except (discord.Forbidden, discord.HTTPException):
                                pass
                        player_info.name.set(osu_user.name)
                    player_info.rank.set(str(osu_user.rank))
                    player_info.bws_rank.set(str(osu_user.rank))
                    player_info.pp.set(str(int(float(osu_user.pp))))
                    update_spreadsheet = True
            if update_spreadsheet:
                await self.add_update_spreadsheet_background_task(players_spreadsheet)

    @tasks.loop(hours=18.0)
    async def background_task_update_players_spreadsheet_registration(self):
        for guild in self.bot.guilds:
            try:
                tournament = self.get_tournament(guild.id)
                if tournament.registration_background_update:
                    await self.update_players_spreadsheet_registration(guild, tournament)
            except Exception:
                continue

    @background_task_update_players_spreadsheet_registration.before_loop
    async def before_background_task_update_players_spreadsheet_registration(self):
        self.bot.info(
            "Waiting for bot to be ready before starting background_task_update_players_spreadsheet_registration background task..."
        )
        await self.bot.wait_until_ready()
        self.bot.info(
            "Bot is ready. background_task_update_players_spreadsheet_registration background task will start."
        )

    @tasks.loop(count=1)
    async def background_task_update_spreadsheet(self):
        spreadsheet_ids = self.get_spreadsheet_ids_to_update_pickle()
        for spreadsheet_id in spreadsheet_ids:
            self.bot.tasks.append(self.bot.loop.create_task(self.update_spreadsheet_background_task(spreadsheet_id)))


async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(TosurnamentBracketCog(bot))
