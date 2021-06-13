"""Contains all players spreadsheet settings commands related to Tosurnament."""

from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.api import spreadsheet
from common.exceptions import NoSpreadsheet


class TosurnamentPlayersSpreadsheetCog(tosurnament.TosurnamentBaseModule, name="players_spreadsheet"):
    """Tosurnament players spreadsheet settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["sps"])
    async def set_players_spreadsheet(self, ctx, spreadsheet_id: str, *, sheet_name: str = ""):
        """Sets the players spreadsheet."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = tournament.current_bracket
        spreadsheet_id = bracket.update_spreadsheet_of_type(self.bot, "players", spreadsheet_id, sheet_name)
        await self.send_reply(ctx, "success", spreadsheet_id)

    async def set_players_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        any_spreadsheet = tournament.current_bracket.get_spreadsheet_from_type("players")
        if not any_spreadsheet:
            raise tosurnament.NoSpreadsheet("players")
        await self.update_table(ctx, any_spreadsheet, values)

    async def set_players_spreadsheet_range_value(self, ctx, range_name, range_value):
        """Puts the input values into the corresponding bracket."""
        if not spreadsheet.check_range(range_value):
            raise commands.UserInputError()
        await self.set_players_spreadsheet_values(ctx, {range_name: range_value})

    @commands.command(aliases=["spssn"])
    async def set_players_spreadsheet_sheet_name(self, ctx, *, sheet_name: str = ""):
        """Sets the sheet name of the players spreadsheet."""
        await self.set_players_spreadsheet_values(ctx, {"sheet_name": sheet_name})

    @commands.command(aliases=["spsrtn"])
    async def set_players_spreadsheet_range_team_name(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range team name."""
        await self.set_players_spreadsheet_range_value(ctx, "range_team_name", cell_range)

    @commands.command(aliases=["spsrt"])
    async def set_players_spreadsheet_range_team(self, ctx, *, cell_range: str):
        """Sets the players spreadsheet range team."""
        await self.set_players_spreadsheet_range_value(ctx, "range_team", cell_range)

    @commands.command(aliases=["spsrd"])
    async def set_players_spreadsheet_range_discord(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range discord."""
        await self.set_players_spreadsheet_range_value(ctx, "range_discord", cell_range)

    @commands.command(aliases=["spsrdi"])
    async def set_players_spreadsheet_range_discord_id(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range discord id."""
        await self.set_players_spreadsheet_range_value(ctx, "range_discord_id", cell_range)

    @commands.command(aliases=["spsrr"])
    async def set_players_spreadsheet_range_rank(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range rank."""
        await self.set_players_spreadsheet_range_value(ctx, "range_rank", cell_range)

    @commands.command(aliases=["spsrbr"])
    async def set_players_spreadsheet_range_bws_rank(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range bws rank."""
        await self.set_players_spreadsheet_range_value(ctx, "range_bws_rank", cell_range)

    @commands.command(aliases=["spsroi"])
    async def set_players_spreadsheet_range_osu_id(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range osu id."""
        await self.set_players_spreadsheet_range_value(ctx, "range_osu_id", cell_range)

    @commands.command(aliases=["spsrp"])
    async def set_players_spreadsheet_range_pp(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range pp."""
        await self.set_players_spreadsheet_range_value(ctx, "range_pp", cell_range)

    @commands.command(aliases=["spsrc"])
    async def set_players_spreadsheet_range_country(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range country."""
        await self.set_players_spreadsheet_range_value(ctx, "range_country", cell_range)

    @commands.command(aliases=["spsrtz"])
    async def set_players_spreadsheet_range_timezone(self, ctx, *, cell_range: str = ""):
        """Sets the players spreadsheet range timezone."""
        await self.set_players_spreadsheet_range_value(ctx, "range_timezone", cell_range)

    @commands.command(aliases=["spsmrft"])
    async def set_players_spreadsheet_max_range_for_teams(self, ctx, *, length: int):
        """Sets the players spreadsheet max range length for teams."""
        await self.set_players_spreadsheet_values(ctx, {"max_range_for_teams": length})

    @commands.command(aliases=["spss"])
    async def show_players_spreadsheet_settings(self, ctx):
        """Shows the players spreadsheet settings."""
        await self.show_spreadsheet_settings(ctx, "players")

    @commands.command(aliases=["spst"])
    async def show_players_spreadsheet_team(self, ctx, index: int):
        """Shows the players spreadsheet settings."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = tournament.current_bracket
        players_spreadsheet = await bracket.get_players_spreadsheet()
        if not players_spreadsheet:
            raise NoSpreadsheet("players")
        team_infos, _ = await self.get_all_teams_infos_and_roles(ctx.guild, players_spreadsheet)
        try:
            selected_team_info = team_infos[index]
        except Exception:
            return
        output = "**__" + selected_team_info.team_name + ":__**\n\n"
        for player_info in selected_team_info.players:
            output += "__Player name:__ " + str(player_info.name) + "\n"
            if player_info.discord:
                output += "__Discord tag:__ " + str(player_info.discord) + "\n"
            if player_info.discord_id:
                output += "__Discord id:__ " + str(player_info.discord_id) + "\n"
            # TODO other fields
            output += "\n"
        await ctx.send(output)


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentPlayersSpreadsheetCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentPlayersSpreadsheetCog(bot))
