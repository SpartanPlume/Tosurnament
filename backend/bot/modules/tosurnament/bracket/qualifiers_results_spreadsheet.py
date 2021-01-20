"""Contains all qualifiers results spreadsheet settings commands related to Tosurnament."""

from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.api import spreadsheet


class TosurnamentQualifiersResultsSpreadsheetCog(
    tosurnament.TosurnamentBaseModule, name="qualifiers_results_spreadsheet"
):
    """Tosurnament qualifiers results spreadsheet settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["sqrs"])
    async def set_qualifiers_results_spreadsheet(self, ctx, spreadsheet_id: str, *, sheet_name: str = ""):
        """Sets the qualifiers results spreadsheet."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = tournament.current_bracket
        spreadsheet_id = bracket.update_spreadsheet_of_type(self.bot, "qualifiers_results", spreadsheet_id, sheet_name)
        await self.send_reply(ctx, ctx.command.name, "success", spreadsheet_id)

    async def set_qualifiers_results_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        any_spreadsheet = tournament.current_bracket.get_spreadsheet_from_type("qualifiers_results")
        if not any_spreadsheet:
            raise tosurnament.NoSpreadsheet("qualifiers_results")
        await self.update_table(ctx, any_spreadsheet, values)

    async def set_qualifiers_results_spreadsheet_range_value(self, ctx, range_name, range_value):
        """Puts the input values into the corresponding bracket."""
        if not spreadsheet.check_range(range_value):
            raise commands.UserInputError()
        await self.set_qualifiers_results_spreadsheet_values(ctx, {range_name: range_value})

    @commands.command(aliases=["sqrssn"])
    async def set_qualifiers_results_spreadsheet_sheet_name(self, ctx, *, sheet_name: str = ""):
        """Sets the sheet name of the qualifiers results spreadsheet."""
        await self.set_qualifiers_results_spreadsheet_values(ctx, {"sheet_name": sheet_name})

    @commands.command(aliases=["sqrsroi"])
    async def set_qualifiers_results_spreadsheet_range_osu_id(self, ctx, *, cell_range: str):
        """Sets the qualifiers results spreadsheet range osu id."""
        await self.set_qualifiers_results_spreadsheet_range_value(ctx, "range_osu_id", cell_range)

    @commands.command(aliases=["sqrsrs"])
    async def set_qualifiers_results_spreadsheet_range_score(self, ctx, *, cell_range: str):
        """Sets the qualifiers results spreadsheet range score."""
        await self.set_qualifiers_results_spreadsheet_range_value(ctx, "range_score", cell_range)


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentQualifiersResultsSpreadsheetCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentQualifiersResultsSpreadsheetCog(bot))
