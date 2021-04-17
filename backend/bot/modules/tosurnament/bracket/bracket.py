"""Contains all bracket settings commands related to Tosurnament."""

import asyncio
import datetime
import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.api import challonge
from common.databases.bracket import Bracket
from common.databases.players_spreadsheet import TeamInfo
from common.api import osu


class TosurnamentBracketCog(tosurnament.TosurnamentBaseModule, name="bracket"):
    """Tosurnament bracket settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

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
        await self.set_bracket_values(ctx, {"role_id": role.id})

    @commands.command(aliases=["scbr"])
    async def set_current_bracket_round(self, ctx, *, current_round: str = ""):
        """Sets the round of the current bracket."""
        await self.set_bracket_values(ctx, {"current_round": current_round})

    @commands.command(aliases=["sprc"])
    async def set_post_result_channel(self, ctx, *, channel: discord.TextChannel):
        """Sets the post result's channel."""
        await self.set_bracket_values(ctx, {"post_result_channel_id": channel.id})

    @commands.command(aliases=["sc"])
    async def set_challonge(self, ctx, challonge_tournament: str):
        """Sets the challonge."""
        challonge_tournament = challonge.extract_tournament_id(challonge_tournament)
        await self.set_bracket_values(ctx, {"challonge": challonge_tournament})

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
                if player_index := self.get_index_of_player_in_team(member, team_info):
                    player_name = team_info.players[player_index].value
                    if player_name.casefold() in participants_casefold:
                        return team_info, player_name
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
            roles_to_removes = list(filter(None, [player_role, bracket_role, team_captain_role]))
        else:
            roles_to_removes = list(filter(None, [bracket_role, team_captain_role]))

        teams_info, teams_roles = await self.get_all_teams_infos_and_roles(ctx.guild, bracket.players_spreadsheet)
        roles_to_removes = [*roles_to_removes, *teams_roles]

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
                players_found.append(player_name.lower())
            else:
                if member:
                    try:
                        await member.remove_roles(*roles_to_removes)
                        n_user_roles_removed += 1
                    except Exception:
                        users_role_not_removed.append(str(member))

        success_extra = ""
        players_not_found = []
        for participant in running_participants:
            if participant.lower() not in players_found:
                players_not_found.append(participant)
        if players_not_found:
            success_extra += self.get_string(ctx, "players_not_found", "\n".join(players_not_found))
        if users_role_not_removed:
            success_extra += self.get_string(ctx, "users_role_not_removed", "\n".join(users_role_not_removed))
        await self.send_reply(ctx, "success", bracket.name, n_user_roles_removed, len(players_found), success_extra)

    @commands.command(aliases=["gpr"])
    async def give_player_role(self, ctx, bracket_index: int = None):
        """Gives the player role of users not present in the challonge."""
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

        teams_info, _ = await self.get_all_teams_infos_and_roles(ctx.guild, bracket.players_spreadsheet)

        n_user_roles_added = 0
        users_role_not_added = []
        players_found = []
        for member in ctx.guild.members:
            team_info, player_name = self.is_player_in_challonge(member, teams_info, running_participants)
            if player_name:
                players_found.append(player_name.lower())
                team_role = tosurnament.get_role(ctx.guild.roles, None, team_info.team_name.value)
                roles_to_add_to_player = list(filter(None, [*roles_to_add, team_role]))
                if team_captain_role and team_info.players[0].value == player_name:
                    roles_to_add_to_player.append(team_captain_role)
                try:
                    await member.add_roles(*roles_to_add_to_player)
                    n_user_roles_added += 1
                except Exception:
                    users_role_not_added.append(str(member))

        success_extra = ""
        players_not_found = []
        for participant in running_participants:
            if participant.lower() not in players_found:
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
        self.bot.session.update(tournament.current_bracket)
        await self.send_reply(ctx, "success", value)

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
                        spreadsheet_to = bracket_to.create_spreadsheet_from_type(self.bot, spreadsheet_type)
                    spreadsheet_from.copy_to(spreadsheet_to)
                    self.bot.session.update(spreadsheet_to)

            await self.send_reply(ctx, "success", bracket_from.name, bracket_to.name)
            return
        raise commands.UserInputError()

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
            team_infos, _ = await self.get_all_teams_infos_and_roles(guild, bracket.players_spreadsheet)
            update_spreadsheet = False
            for team_info in team_infos:
                for i, player_cell in enumerate(team_info.players):
                    osu_id = str(player_cell.value)
                    if team_info.osu_ids[i].value:
                        osu_id = str(team_info.osu_ids[i].value)
                    osu_user = osu.get_user(osu_id, m=tournament.game_mode)
                    if not osu_user:
                        continue
                    if player_cell.value != osu_user.name:
                        user = guild.get_member_named(str(player_cell.value))
                        if user:
                            try:
                                await user.edit(nick=osu_user.name)
                            except (discord.Forbidden, discord.HTTPException):
                                pass
                        player_cell.value = osu_user.name
                    team_info.ranks[i].value = str(osu_user.rank)
                    team_info.bws_ranks[i].value = str(osu_user.rank)
                    team_info.pps[i].value = str(int(float(osu_user.pp)))
                    update_spreadsheet = True
            if update_spreadsheet:
                self.add_update_spreadsheet_background_task(bracket.players_spreadsheet)

    async def background_task_update_players_spreadsheet_registration(self):
        try:
            await self.bot.wait_until_ready()
            while not self.bot.is_closed():
                for guild in self.bot.guilds:
                    try:
                        tournament = self.get_tournament(guild.id)
                        if tournament.registration_background_update:
                            await self.update_players_spreadsheet_registration(guild, tournament)
                    except asyncio.CancelledError:
                        return
                    except Exception:
                        continue
                await asyncio.sleep(86000)
        except asyncio.CancelledError:
            return

    def background_task(self):
        spreadsheet_ids = self.get_spreadsheet_ids_to_update_pickle()
        for spreadsheet_id in spreadsheet_ids:
            self.bot.tasks.append(self.bot.loop.create_task(self.update_spreadsheet_background_task(spreadsheet_id)))
        self.bot.tasks.append(self.bot.loop.create_task(self.background_task_update_players_spreadsheet_registration()))


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentBracketCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentBracketCog(bot))
