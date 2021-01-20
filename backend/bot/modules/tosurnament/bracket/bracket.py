"""Contains all bracket settings commands related to Tosurnament."""

import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.api import spreadsheet
from common.api import challonge
from common.databases.players_spreadsheet import TeamInfo
from common.databases.bracket import Bracket


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
        user = tosurnament.UserAbstraction.get_from_user(self.bot, member)
        if teams_info:
            for team_info in teams_info:
                if (
                    (user.verified and user.name.lower() in [str(cell.value) for cell in team_info.players])
                    or (str(user.discord_id) in [str(cell.value) for cell in team_info.discord_ids])
                    or (str(member) in [str(cell.value) for cell in team_info.discord])
                ):
                    if team_info.team_name.value.lower() in participants:
                        return team_info.team_name.value
                    else:
                        return None
        elif user.verified and user.name.lower() in participants:
            return user.name
        return None

    @commands.command(aliases=["cpr"])
    async def clear_player_role(self, ctx, bracket_index: int = None, remove_player_role: bool = True):
        """Removes the player role of users not present in the challonge."""
        tournament = self.get_tournament(ctx.guild.id)
        brackets = tournament.brackets
        if len(brackets) != 1:
            if bracket_index is None:
                brackets_string = ""
                for i, bracket in enumerate(brackets):
                    brackets_string += str(i + 1) + ": `" + bracket.name + "`\n"
                await self.send_reply(ctx, ctx.command.name, "default", brackets_string)
                return
            elif bracket_index <= 0 or bracket_index > len(brackets):
                raise commands.UserInputError()
            bracket_index -= 1
        else:
            bracket_index = 0
        bracket = brackets[bracket_index]
        if not bracket.challonge:
            raise tosurnament.NoChallonge(bracket.name)
        player_role = tosurnament.get_role(ctx.guild.roles, tournament.player_role_id, "Player")
        bracket_role = tosurnament.get_role(ctx.guild.roles, bracket.role_id, bracket.name)
        team_captain_role = tosurnament.get_role(ctx.guild.roles, tournament.team_captain_role_id, "Team Captain")
        if remove_player_role:
            roles_to_removes = list(filter(None, [player_role, bracket_role, team_captain_role]))
        else:
            roles_to_removes = list(filter(None, [bracket_role, team_captain_role]))

        challonge_tournament = challonge.get_tournament(bracket.challonge)
        participants = [participant.name for participant in challonge_tournament.participants]
        participants_lower = [participant.lower() for participant in participants]

        players_spreadsheet = bracket.players_spreadsheet
        teams_info = []
        if players_spreadsheet:
            await players_spreadsheet.get_spreadsheet()
            if players_spreadsheet.range_team_name:
                team_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    players_spreadsheet.range_team_name
                )
            else:
                team_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    players_spreadsheet.range_team
                )
            teams_info = []
            for cell in team_cells:
                try:
                    team_info = TeamInfo.from_team_name(players_spreadsheet, cell.value)
                except Exception:
                    continue
                if players_spreadsheet.range_team_name:
                    if team_role := tosurnament.get_role(ctx.guild.roles, None, team_info.team_name.value):
                        roles_to_removes.append(team_role)
                teams_info.append(team_info)

        players_found = []
        n_user_roles_removed = 0
        users_role_not_removed = []
        for member in ctx.guild.members:
            if bracket_role:
                if not tosurnament.get_role(member.roles, bracket_role.id):
                    continue
            elif player_role and not tosurnament.get_role(member.roles, player_role.id):
                continue
            if player_name := self.is_player_in_challonge(member, teams_info, participants_lower):
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
        for participant in participants:
            if participant.lower() not in players_found:
                players_not_found.append(participant)
        if players_not_found:
            success_extra += self.get_string(ctx.command.name, "players_not_found", "\n".join(players_not_found))
        if users_role_not_removed:
            success_extra += self.get_string(
                ctx.command.name, "users_role_not_removed", "\n".join(users_role_not_removed)
            )
        await self.send_reply(
            ctx, ctx.command.name, "success", bracket.name, n_user_roles_removed, len(players_found), success_extra
        )

    @commands.command(aliases=["gpr"])
    async def give_player_role(self, ctx, bracket_index: int = None):
        """Gives the player role of users not present in the challonge."""
        tournament = self.get_tournament(ctx.guild.id)
        brackets = tournament.brackets
        if len(brackets) != 1:
            if bracket_index is None:
                brackets_string = ""
                for i, bracket in enumerate(brackets):
                    brackets_string += str(i + 1) + ": `" + bracket.name + "`\n"
                await self.send_reply(ctx, ctx.command.name, "default", brackets_string)
                return
            elif bracket_index <= 0 or bracket_index > len(brackets):
                raise commands.UserInputError()
            bracket_index -= 1
        else:
            bracket_index = 0
        bracket = brackets[bracket_index]
        if not bracket.challonge:
            raise tosurnament.NoChallonge(bracket.name)
        player_role = tosurnament.get_role(ctx.guild.roles, tournament.player_role_id, "Player")
        bracket_role = tosurnament.get_role(ctx.guild.roles, bracket.role_id, bracket.name)
        # TODO
        # team_captain_role = tosurnament.get_role(ctx.guild.roles, tournament.team_captain_role_id, "Team Captain")
        roles_to_add = list(filter(None, [player_role, bracket_role]))

        challonge_tournament = challonge.get_tournament(bracket.challonge)
        participants = [participant.name for participant in challonge_tournament.participants]
        participants_lower = [participant.lower() for participant in participants]

        players_spreadsheet = bracket.players_spreadsheet
        teams_info = []
        if players_spreadsheet:
            await players_spreadsheet.get_spreadsheet()
            if players_spreadsheet.range_team_name:
                team_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    players_spreadsheet.range_team_name
                )
            else:
                team_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    players_spreadsheet.range_team
                )
            teams_info = []
            for cell in team_cells:
                try:
                    team_info = TeamInfo.from_team_name(players_spreadsheet, cell.value)
                except Exception:
                    continue
                if players_spreadsheet.range_team_name:
                    if team_role := tosurnament.get_role(ctx.guild.roles, None, team_info.team_name.value):
                        roles_to_add.append(team_role)
                teams_info.append(team_info)

        n_user_roles_added = 0
        users_role_not_added = []
        players_found = []
        for member in ctx.guild.members:
            if player_name := self.is_player_in_challonge(member, teams_info, participants_lower):
                players_found.append(player_name.lower())
                try:
                    await member.add_roles(*roles_to_add)
                    n_user_roles_added += 1
                except Exception:
                    users_role_not_added.append(str(member))

        success_extra = ""
        players_not_found = []
        for participant in participants:
            if participant.lower() not in players_found:
                players_not_found.append(participant)
        if players_not_found:
            success_extra += self.get_string(ctx.command.name, "players_not_found", "\n".join(players_not_found))
        if users_role_not_added:
            success_extra += self.get_string(ctx.command.name, "users_role_not_added", "\n".join(users_role_not_added))
        await self.send_reply(
            ctx, ctx.command.name, "success", bracket.name, n_user_roles_added, len(players_not_found), success_extra
        )

    async def set_bracket_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        for key, value in values.items():
            setattr(tournament.current_bracket, key, value)
        self.bot.session.update(tournament.current_bracket)
        await self.send_reply(ctx, ctx.command.name, "success", value)

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

            await self.send_reply(ctx, ctx.command.name, "success", bracket_from.name, bracket_to.name)
            return
        raise commands.UserInputError()

    def background_task(self):
        spreadsheet_ids = self.get_spreadsheet_ids_to_update_pickle()
        for spreadsheet_id in spreadsheet_ids:
            self.bot.tasks.append(self.bot.loop.create_task(self.update_spreadsheet_background_task(spreadsheet_id)))


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentBracketCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentBracketCog(bot))
