"""Contains all schedules spreadsheet settings commands related to Tosurnament."""

from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.api import spreadsheet


class TosurnamentSchedulesSpreadsheetCog(tosurnament.TosurnamentBaseModule, name="schedules_spreadsheet"):
    """Tosurnament schedules spreadsheet settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["sss"])
    async def set_schedules_spreadsheet(self, ctx, spreadsheet_id: str, *, sheet_name: str = ""):
        """Sets the schedules spreadsheet."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = tournament.current_bracket
        spreadsheet_id = bracket.update_spreadsheet_of_type(self.bot, "schedules", spreadsheet_id, sheet_name)
        await self.send_reply(ctx, "success", spreadsheet_id)

    async def set_schedules_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        any_spreadsheet = tournament.current_bracket.get_spreadsheet_from_type("schedules")
        if not any_spreadsheet:
            raise tosurnament.NoSpreadsheet("schedules")
        await self.update_table(ctx, any_spreadsheet, values)

    async def set_schedules_spreadsheet_range_value(self, ctx, range_name, range_value):
        """Puts the input values into the corresponding bracket."""
        if not spreadsheet.check_range(range_value):
            raise commands.UserInputError()
        await self.set_schedules_spreadsheet_values(ctx, {range_name: range_value})

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
        await self.set_schedules_spreadsheet_range_value(ctx, "range_match_id", cell_range)

    @commands.command(aliases=["sssrt1"])
    async def set_schedules_spreadsheet_range_team1(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range team1."""
        await self.set_schedules_spreadsheet_range_value(ctx, "range_team1", cell_range)

    @commands.command(aliases=["sssrt2"])
    async def set_schedules_spreadsheet_range_team2(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range team2."""
        await self.set_schedules_spreadsheet_range_value(ctx, "range_team2", cell_range)

    @commands.command(aliases=["sssrst1"])
    async def set_schedules_spreadsheet_range_score_team1(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range score team1."""
        await self.set_schedules_spreadsheet_range_value(ctx, "range_score_team1", cell_range)

    @commands.command(aliases=["sssrst2"])
    async def set_schedules_spreadsheet_range_score_team2(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range score team2."""
        await self.set_schedules_spreadsheet_range_value(ctx, "range_score_team2", cell_range)

    @commands.command(aliases=["sssrd"])
    async def set_schedules_spreadsheet_range_date(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range date."""
        await self.set_schedules_spreadsheet_range_value(ctx, "range_date", cell_range)

    @commands.command(aliases=["sssrt"])
    async def set_schedules_spreadsheet_range_time(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range time."""
        await self.set_schedules_spreadsheet_range_value(ctx, "range_time", cell_range)

    @commands.command(aliases=["sssrr"])
    async def set_schedules_spreadsheet_range_referee(self, ctx, *, cell_range: str):
        """Sets the schedules spreadsheet range referee."""
        await self.set_schedules_spreadsheet_range_value(ctx, "range_referee", cell_range)

    @commands.command(aliases=["sssrs"])
    async def set_schedules_spreadsheet_range_streamer(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range streamer."""
        await self.set_schedules_spreadsheet_range_value(ctx, "range_streamer", cell_range)

    @commands.command(aliases=["sssrc"])
    async def set_schedules_spreadsheet_range_commentator(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range commentator."""
        await self.set_schedules_spreadsheet_range_value(ctx, "range_commentator", cell_range)

    @commands.command(aliases=["sssrml"])
    async def set_schedules_spreadsheet_range_mp_links(self, ctx, *, cell_range: str = ""):
        """Sets the schedules spreadsheet range mp links."""
        await self.set_schedules_spreadsheet_range_value(ctx, "range_mp_links", cell_range)


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentSchedulesSpreadsheetCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentSchedulesSpreadsheetCog(bot))
