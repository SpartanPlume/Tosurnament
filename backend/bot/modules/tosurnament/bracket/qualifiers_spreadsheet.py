"""Contains all qualifiers spreadsheet settings commands related to Tosurnament."""

from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.tosurnament.spreadsheets.qualifiers_spreadsheet import QualifiersSpreadsheet
from common.api import spreadsheet
from common.api import tosurnament as tosurnament_api


class TosurnamentQualifiersCog(tosurnament.TosurnamentBaseModule, name="qualifiers_spreadsheet"):
    """Tosurnament qualifiers spreadsheet settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["sqs"])
    async def set_qualifiers_spreadsheet(self, ctx, spreadsheet_id: str, *, sheet_name: str = ""):
        """Sets the qualifiers spreadsheet."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = tournament.current_bracket
        if not bracket.qualifiers_spreadsheet:
            tosurnament_api.create_qualifiers_spreadsheet(
                tournament.id, bracket.id, QualifiersSpreadsheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name)
            )
        else:
            bracket.qualifiers_spreadsheet.update(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name)
            tosurnament_api.update_qualifiers_spreadsheet(tournament.id, bracket.id, bracket.qualifiers_spreadsheet)
        await self.send_reply(ctx, "success", spreadsheet_id)

    async def set_qualifiers_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        qualifiers_spreadsheet = tournament.current_bracket.get_spreadsheet_from_type("qualifiers")
        if not qualifiers_spreadsheet:
            raise tosurnament.NoSpreadsheet("qualifiers")
        for key, value in values.items():
            setattr(qualifiers_spreadsheet, key, value)
        tosurnament_api.update_qualifiers_spreadsheet(
            tournament.id, tournament.current_bracket.id, qualifiers_spreadsheet
        )
        await self.send_reply(ctx, "success", value)

    async def set_qualifiers_spreadsheet_range_value(self, ctx, range_name, range_value):
        """Puts the input values into the corresponding bracket."""
        if not spreadsheet.check_range(range_value):
            raise commands.UserInputError()
        await self.set_qualifiers_spreadsheet_values(ctx, {range_name: range_value})

    @commands.command(aliases=["sqssn"])
    async def set_qualifiers_spreadsheet_sheet_name(self, ctx, *, sheet_name: str = ""):
        """Sets the sheet name of the qualifiers spreadsheet."""
        await self.set_qualifiers_spreadsheet_values(ctx, {"sheet_name": sheet_name})

    @commands.command(aliases=["sqsrli"])
    async def set_qualifiers_spreadsheet_range_lobby_id(self, ctx, *, cell_range: str):
        """Sets the qualifiers spreadsheet range lobby id."""
        await self.set_qualifiers_spreadsheet_range_value(ctx, "range_lobby_id", cell_range)

    @commands.command(aliases=["sqsrts"])
    async def set_qualifiers_spreadsheet_range_teams(self, ctx, *, cell_range: str):
        """Sets the qualifiers spreadsheet range teams."""
        await self.set_qualifiers_spreadsheet_range_value(ctx, "range_teams", cell_range)

    @commands.command(aliases=["sqsrr"])
    async def set_qualifiers_spreadsheet_range_referee(self, ctx, *, cell_range: str):
        """Sets the qualifiers spreadsheet range referee."""
        await self.set_qualifiers_spreadsheet_range_value(ctx, "range_referee", cell_range)

    @commands.command(aliases=["sqsrd"])
    async def set_qualifiers_spreadsheet_range_date(self, ctx, *, cell_range: str):
        """Sets the qualifiers spreadsheet range date."""
        await self.set_qualifiers_spreadsheet_range_value(ctx, "range_date", cell_range)

    @commands.command(aliases=["sqsrt"])
    async def set_qualifiers_spreadsheet_range_time(self, ctx, *, cell_range: str = ""):
        """Sets the qualifiers spreadsheet range time."""
        await self.set_qualifiers_spreadsheet_range_value(ctx, "range_time", cell_range)

    @commands.command(aliases=["sqsmtir"])
    async def set_qualifiers_spreadsheet_max_teams_in_row(self, ctx, *, max_teams_in_row: int):
        """Sets the qualifiers spreadsheet range time."""
        await self.set_qualifiers_spreadsheet_values(ctx, {"max_teams_in_row": max_teams_in_row})

    @commands.command(aliases=["sqss"])
    async def show_qualifiers_spreadsheet_settings(self, ctx):
        """Shows the qualifiers spreadsheet settings."""
        await self.show_spreadsheet_settings(ctx, "qualifiers")


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentQualifiersCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentQualifiersCog(bot))
