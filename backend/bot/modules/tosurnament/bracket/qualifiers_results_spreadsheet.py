"""Contains all qualifiers results spreadsheet settings commands related to Tosurnament."""

from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.tosurnament.spreadsheets.qualifiers_results_spreadsheet import QualifiersResultsSpreadsheet
from common.api import spreadsheet as spreadsheet_api
from common.api import tosurnament as tosurnament_api


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
        spreadsheet_id = spreadsheet_api.extract_spreadsheet_id(spreadsheet_id)
        qualifiers_results_spreadsheet = bracket._qualifiers_results_spreadsheet
        if not qualifiers_results_spreadsheet:
            qualifiers_results_spreadsheet = tosurnament_api.create_qualifiers_results_spreadsheet(
                tournament.id,
                bracket.id,
                QualifiersResultsSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name),
            )
        else:
            qualifiers_results_spreadsheet.spreadsheet_id = spreadsheet_id
            if sheet_name:
                qualifiers_results_spreadsheet.sheet_name = sheet_name
            tosurnament_api.update_qualifiers_results_spreadsheet(
                tournament.id, bracket.id, qualifiers_results_spreadsheet
            )
        await self.send_reply(ctx, "success", qualifiers_results_spreadsheet.spreadsheet_id)

    async def set_qualifiers_results_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        qualifiers_results_spreadsheet = tournament.current_bracket.get_spreadsheet_from_type("qualifiers_results")
        if not qualifiers_results_spreadsheet:
            raise tosurnament.NoSpreadsheet("qualifiers_results")
        for key, value in values.items():
            setattr(qualifiers_results_spreadsheet, key, value)
        tosurnament_api.update_qualifiers_results_spreadsheet(
            tournament.id, tournament.current_bracket.id, qualifiers_results_spreadsheet
        )
        await self.send_reply(ctx, "success", value)

    async def set_qualifiers_results_spreadsheet_range_value(self, ctx, range_name, range_value):
        """Puts the input values into the corresponding bracket."""
        if not spreadsheet_api.check_range(range_value):
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

    @commands.command(aliases=["sqrss"])
    async def show_qualifiers_results_spreadsheet_settings(self, ctx):
        """Shows the qualifiers results spreadsheet settings."""
        await self.show_spreadsheet_settings(ctx, "qualifiers_results")


async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(TosurnamentQualifiersResultsSpreadsheetCog(bot))
