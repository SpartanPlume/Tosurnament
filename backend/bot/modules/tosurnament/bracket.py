"""Contains all bracket settings commands related to Tosurnament."""

import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.api import spreadsheet
from common.api import challonge
from common.databases.players_spreadsheet import PlayersSpreadsheet, TeamInfo
from common.databases.schedules_spreadsheet import SchedulesSpreadsheet


class TosurnamentBracketCog(tosurnament.TosurnamentBaseModule, name="bracket"):
    """Tosurnament bracket settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if ctx.guild.owner == ctx.author:
            return True
        guild = self.get_guild(ctx.guild.id)
        if not guild or not guild.admin_role_id:
            raise tosurnament.NotBotAdmin()
        if not tosurnament.get_role(ctx.author.roles, guild.admin_role_id):
            raise tosurnament.NotBotAdmin()
        return True

    @commands.command(aliases=["sbn"])
    async def set_bracket_name(self, ctx, *, name: str):
        """Modifies the current bracket's name."""
        if not name:
            raise commands.UserInputError()
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
        if "/" in challonge_tournament:
            challonge_tournament = challonge_tournament.rstrip("/")
            challonge_tournament = challonge_tournament.split("/")[-1]
        await self.set_bracket_values(ctx, {"challonge": challonge_tournament})

    def is_player_in_challonge(self, member_id, teams_info, participants):
        for team_info in teams_info:
            if member_id == team_info.discord[0]:
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

    @commands.command(aliases=["sps"])
    async def set_players_spreadsheet(self, ctx, spreadsheet_id: str, *, sheet_name: str = ""):
        """Sets the players spreadsheet."""
        await self.set_bracket_spreadsheet(ctx, "players", spreadsheet_id, sheet_name)

    @commands.command(aliases=["sss"])
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
        if getattr(bracket, spreadsheet_type + "_spreadsheet_id") > 0:
            if spreadsheet_type == "players":
                any_spreadsheet = bracket.players_spreadsheet
            elif spreadsheet_type == "schedules":
                any_spreadsheet = bracket.schedules_spreadsheet
            else:
                return
        else:
            if spreadsheet_type == "players":
                any_spreadsheet = PlayersSpreadsheet()
            elif spreadsheet_type == "schedules":
                any_spreadsheet = SchedulesSpreadsheet()
            else:
                return
            self.bot.session.add(any_spreadsheet)
            setattr(bracket, spreadsheet_type + "_spreadsheet_id", any_spreadsheet.id)
            self.bot.session.update(bracket)
        any_spreadsheet.spreadsheet_id = spreadsheet_id
        if sheet_name:
            any_spreadsheet.sheet_name = sheet_name
        self.bot.session.update(any_spreadsheet)
        await self.send_reply(ctx, ctx.command.name, "success", spreadsheet_id)

    @commands.command(aliases=["ssssn"])
    async def set_schedules_spreadsheet_sheet_name(self, ctx, *, sheet_name: str = ""):
        """Sets the sheet name of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"sheet_name": sheet_name})

    @commands.command(aliases=["sssdf"])
    async def set_schedules_spreadsheet_date_format(self, ctx, *, date_format: str = ""):
        """Sets the date format used in the date range of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"date_format": date_format})

    @commands.command(aliases=["ssssir"])
    async def set_schedules_spreadsheet_staff_is_range(self, ctx, use_range: bool):
        """Sets the staff_is_range of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"use_range": use_range})

    @commands.command(aliases=["sssrmi"])
    async def set_schedules_spreadsheet_range_match_id(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range match id."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_match_id": cell_range})

    @commands.command(aliases=["sssrt1"])
    async def set_schedules_spreadsheet_range_team1(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range team1."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_team1": cell_range})

    @commands.command(aliases=["sssrt2"])
    async def set_schedules_spreadsheet_range_team2(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range team2."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_team2": cell_range})

    @commands.command(aliases=["sssrst1"])
    async def set_schedules_spreadsheet_range_score_team1(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range score team1."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_score_team1": cell_range})

    @commands.command(aliases=["sssrst2"])
    async def set_schedules_spreadsheet_range_score_team2(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range score team2."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_score_team2": cell_range})

    @commands.command(aliases=["sssrd"])
    async def set_schedules_spreadsheet_range_date(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range date."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_date": cell_range})

    @commands.command(aliases=["sssrt"])
    async def set_schedules_spreadsheet_range_time(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range time."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_time": cell_range})

    @commands.command(aliases=["sssrr"])
    async def set_schedules_spreadsheet_range_referee(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range referee."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_referee": cell_range})

    @commands.command(aliases=["sssrs"])
    async def set_schedules_spreadsheet_range_streamer(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range streamer."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_streamer": cell_range})

    @commands.command(aliases=["sssrc"])
    async def set_schedules_spreadsheet_range_commentator(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range commentator."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_commentator": cell_range})

    @commands.command(aliases=["sssrml"])
    async def set_schedules_spreadsheet_range_mp_links(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range mp links."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {"range_mp_links": cell_range})

    async def set_schedules_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        schedules_spreadsheet = tournament.current_bracket.schedules_spreadsheet
        for key, value in values.items():
            setattr(schedules_spreadsheet, key, value)
        self.bot.session.update(schedules_spreadsheet)
        await self.send_reply(ctx, ctx.command.name, "success", value)

    @commands.command(aliases=["spsrtn"])
    async def set_players_spreadsheet_range_team_name(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range team name."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_players_spreadsheet_values(ctx, {"range_team_name": cell_range})

    @commands.command(aliases=["spsrt"])
    async def set_players_spreadsheet_range_team(self, ctx, *, cell_range: str):
        """Sets the players spreadsheet range team."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_players_spreadsheet_values(ctx, {"range_team": cell_range})

    @commands.command(aliases=["spsrd"])
    async def set_players_spreadsheet_range_discord(self, ctx, *, cell_range: str):
        """Sets the players spreadsheet range team."""
        if not self.check_range(cell_range):
            raise commands.UserInputError()
        await self.set_players_spreadsheet_values(ctx, {"range_discord": cell_range})

    async def set_players_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        players_spreadsheet = tournament.current_bracket.players_spreadsheet
        for key, value in values.items():
            setattr(players_spreadsheet, key, value)
        self.bot.session.update(players_spreadsheet)
        await self.send_reply(ctx, ctx.command.name, "success", value)

    def check_range(self, cell_range):
        """Checks if the range is valid."""
        # TODO
        return True


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentBracketCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentBracketCog(bot))
