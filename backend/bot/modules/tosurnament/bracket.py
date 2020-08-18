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

    def cog_check(self, ctx):  # pragma: no cover
        """Check function called before any command of the cog."""
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["sbn"])  # pragma: no cover
    async def set_bracket_name(self, ctx, *, name: str):
        """Modifies the current bracket's name."""
        await self.set_bracket_values(ctx, {"name": name})

    @commands.command(aliases=["sbr"])  # pragma: no cover
    async def set_bracket_role(self, ctx, *, role: discord.Role):
        """Modifies the current bracket's role."""
        await self.set_bracket_values(ctx, {"role_id": role.id})

    @commands.command(aliases=["scbr"])  # pragma: no cover
    async def set_current_bracket_round(self, ctx, *, current_round: str = ""):
        """Sets the round of the current bracket."""
        await self.set_bracket_values(ctx, {"current_round": current_round})

    @commands.command(aliases=["sprc"])  # pragma: no cover
    async def set_post_result_channel(self, ctx, *, channel: discord.TextChannel):
        """Sets the post result's channel."""
        await self.set_bracket_values(ctx, {"post_result_channel_id": channel.id})

    @commands.command(aliases=["sc"])
    async def set_challonge(self, ctx, challonge_tournament: str):
        """Sets the challonge."""
        if "/" in challonge_tournament:
            challonge_tournament = challonge_tournament.rstrip("/")
            challonge_tournament = challonge_tournament.split("/")[-1]
        await self.set_bracket_values(ctx, {"challonge": challonge_tournament})

    def is_player_in_challonge(self, member_id, teams_info, participants):
        for team_info in teams_info:
            if member_id == team_info.discord[0].value:
                player_name = team_info.players[0].value
                if player_name in participants:
                    return player_name
                else:
                    return None
        return None

    @commands.command(aliases=["cpr"])
    async def clear_player_role(self, ctx, *, number: int = None):
        """Removes the player role of users not present in the challonge."""
        # TODO improve to handle teams, bracket roles, team captain role
        # TODO and remove special code for nik's tournament and handle challonge error
        tournament = self.get_tournament(ctx.guild.id)
        player_role = tosurnament.get_role(ctx.guild.roles, tournament.player_role_id, "Player")
        if not player_role:
            return
        for bracket in tournament.brackets:
            players_spreadsheet = bracket.players_spreadsheet
            if not bracket.challonge or not players_spreadsheet:
                continue
            challonge_tournament = challonge.get_tournament(tournament.current_bracket.challonge)
            participants = [participant.name for participant in challonge_tournament.participants]
            team_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(players_spreadsheet.range_team)
            teams_info = []
            for cell in team_cells:
                try:
                    team_info = TeamInfo.from_player_name(players_spreadsheet, cell.value)
                    teams_info.append(team_info)
                except Exception:
                    continue

            players_found = []
            users_role_not_removed = []
            n_roles_removed = 0
            for member in ctx.guild.members:
                member_id = str(member)
                if player_name := self.is_player_in_challonge(member_id, teams_info, participants):
                    players_found.append(player_name)
                else:
                    try:
                        user = ctx.guild.get_member_named(member_id)
                        if user and tosurnament.get_role(user.roles, player_role.id, "Player"):
                            await user.remove_roles(player_role)
                            n_roles_removed += 1
                    except Exception:
                        users_role_not_removed.append(member_id)
                        continue
            success_extra = ""
            players_not_found = "\n".join(list(set(participants) - set(players_found)))
            if players_not_found:
                success_extra += self.get_string(ctx.command.name, "players_not_found", players_not_found)
            if users_role_not_removed:
                success_extra += self.get_string(
                    ctx.command.name, "users_role_not_removed", "\n".join(users_role_not_removed)
                )
            await self.send_reply(
                ctx, ctx.command.name, "success", bracket.name, n_roles_removed, len(players_found), success_extra,
            )

    @commands.command(aliases=["sps"])  # pragma: no cover
    async def set_players_spreadsheet(self, ctx, spreadsheet_id: str, *, sheet_name: str = ""):
        """Sets the players spreadsheet."""
        await self.set_bracket_spreadsheet(ctx, "players", spreadsheet_id, sheet_name)

    @commands.command(aliases=["sss"])  # pragma: no cover
    async def set_schedules_spreadsheet(self, ctx, spreadsheet_id: str, *, sheet_name: str = ""):
        """Sets the schedules spreadsheet."""
        await self.set_bracket_spreadsheet(ctx, "schedules", spreadsheet_id, sheet_name)

    async def set_bracket_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        for key, value in values.items():
            setattr(tournament.current_bracket, key, value)
        self.bot.session.update(tournament.current_bracket)
        await self.send_reply(ctx, ctx.command.name, "success", value)

    async def set_bracket_spreadsheet(self, ctx, spreadsheet_type, spreadsheet_id, sheet_name):
        """Puts the input spreadsheet into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = tournament.current_bracket
        spreadsheet_id = spreadsheet.extract_spreadsheet_id(spreadsheet_id)
        any_spreadsheet = bracket.get_spreadsheet_from_type(spreadsheet_type)
        if not any_spreadsheet:
            any_spreadsheet = bracket.create_spreadsheet_from_type(self.bot, spreadsheet_type)
        any_spreadsheet.spreadsheet_id = spreadsheet_id
        if sheet_name:
            any_spreadsheet.sheet_name = sheet_name
        self.bot.session.update(any_spreadsheet)
        await self.send_reply(ctx, ctx.command.name, "success", spreadsheet_id)

    @commands.command(aliases=["ssssn"])  # pragma: no cover
    async def set_schedules_spreadsheet_sheet_name(self, ctx, *, sheet_name: str = ""):
        """Sets the sheet name of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"sheet_name": sheet_name})

    @commands.command(aliases=["sssdf"])  # pragma: no cover
    async def set_schedules_spreadsheet_date_format(self, ctx, *, date_format: str = ""):
        """Sets the date format used in the date range of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"date_format": date_format})

    @commands.command(aliases=["ssssir"])  # pragma: no cover
    async def set_schedules_spreadsheet_staff_is_range(self, ctx, use_range: bool):
        """Sets the staff_is_range of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"use_range": use_range})

    @commands.command(aliases=["sssrmi"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_match_id(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range match id."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_match_id": cell_range})

    @commands.command(aliases=["sssrt1"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_team1(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range team1."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_team1": cell_range})

    @commands.command(aliases=["sssrt2"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_team2(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range team2."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_team2": cell_range})

    @commands.command(aliases=["sssrst1"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_score_team1(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range score team1."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_score_team1": cell_range})

    @commands.command(aliases=["sssrst2"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_score_team2(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range score team2."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_score_team2": cell_range})

    @commands.command(aliases=["sssrd"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_date(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range date."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_date": cell_range})

    @commands.command(aliases=["sssrt"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_time(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range time."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_time": cell_range})

    @commands.command(aliases=["sssrr"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_referee(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range referee."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_referee": cell_range})

    @commands.command(aliases=["sssrs"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_streamer(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range streamer."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_streamer": cell_range})

    @commands.command(aliases=["sssrc"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_commentator(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range commentator."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_commentator": cell_range})

    @commands.command(aliases=["sssrml"])  # pragma: no cover
    async def set_schedules_spreadsheet_range_mp_links(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range mp links."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_mp_links": cell_range})

    @commands.command(aliases=["spssn"])  # pragma: no cover
    async def set_players_spreadsheet_sheet_name(self, ctx, *, sheet_name: str = ""):
        """Sets the sheet name of the players spreadsheet."""
        await self.set_players_spreadsheet_values(ctx, {"sheet_name": sheet_name})

    @commands.command(aliases=["spsrtn"])  # pragma: no cover
    async def set_players_spreadsheet_range_team_name(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range team name."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_players_spreadsheet_values(ctx, {"range_team_name": cell_range})

    @commands.command(aliases=["spsrt"])  # pragma: no cover
    async def set_players_spreadsheet_range_team(self, ctx, *, cell_range: str):
        """Sets the players spreadsheet range team."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_players_spreadsheet_values(ctx, {"range_team": cell_range})

    @commands.command(aliases=["spsrd"])  # pragma: no cover
    async def set_players_spreadsheet_range_discord(self, ctx, *, cell_range: str):
        """Sets the players spreadsheet range team."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_players_spreadsheet_values(ctx, {"range_discord": cell_range})

    async def set_schedules_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        await self.set_spreadsheet_values(ctx, "schedules", values)

    async def set_players_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        await self.set_spreadsheet_values(ctx, "players", values)

    async def set_spreadsheet_values(self, ctx, spreadsheet_type, values):
        tournament = self.get_tournament(ctx.guild.id)
        any_spreadsheet = tournament.current_bracket.get_spreadsheet_from_type(spreadsheet_type)
        if not any_spreadsheet:
            raise tosurnament.NoSpreadsheet(spreadsheet_type)
        await self.update_table(ctx, any_spreadsheet, values)

    def check_range(self, cell_range):
        """Checks if the range is valid."""
        # TODO
        return True

    @commands.command(aliases=["cp"])
    async def copy_bracket(self, ctx, index_from: int, index_to: int):
        """Copies the settings of a bracket to another one."""
        tournament = self.get_tournament(ctx.guild.id)
        brackets = tournament.brackets
        if index_from > 0 and index_from <= len(brackets) and index_to > 0 and index_to <= len(brackets):
            index_from -= 1
            index_to -= 1

            bracket_from = brackets[index_from]
            bracket_to = brackets[index_to]
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


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentBracketCog(bot)


def setup(bot):  # pragma: no cover
    """Setups the cog"""
    bot.add_cog(TosurnamentBracketCog(bot))
