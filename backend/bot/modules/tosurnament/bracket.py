"""Contains all bracket settings commands related to Tosurnament."""

import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.api import spreadsheet
from common.databases.players_spreadsheet import PlayersSpreadsheet
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

    @commands.command(aliases=["sc"])
    async def set_challonge(self, ctx, challonge_tournament: str):
        """Sets the challonge."""
        if "/" in challonge_tournament:
            challonge_tournament = challonge_tournament.rstrip("/")
            challonge_tournament = challonge_tournament.split("/")[-1]
        await self.set_bracket_values(ctx, {"challonge": challonge_tournament})

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
        bracket = self.get_current_bracket(tournament)
        for key, value in values.items():
            setattr(bracket, key, value)
        self.bot.session.update(bracket)
        await self.send_reply(ctx, ctx.command.name, "success")

    async def set_bracket_spreadsheet(self, ctx, spreadsheet_type, spreadsheet_id, sheet_name):
        """Puts the input spreadsheet into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = self.get_current_bracket(tournament)
        spreadsheet_id = spreadsheet.extract_spreadsheet_id(spreadsheet_id)
        if getattr(bracket, spreadsheet_type + "_spreadsheet_id") > 0:
            if spreadsheet_type == "players":
                any_spreadsheet = self.get_players_spreadsheet()
            elif spreadsheet_type == "schedules":
                any_spreadsheet = self.get_schedules_spreadsheet()
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
        await self.send_reply(ctx, ctx.command.name, "success")

    @commands.command(aliases=["ssssn"])
    async def set_schedules_spreadsheet_sheet_name(self, ctx, sheet_name: str):
        """Sets the sheet name of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"sheet_name": sheet_name})

    @commands.command(aliases=["sssdf"])
    async def set_schedules_spreadsheet_date_format(self, ctx, date_format: str):
        """Sets the date format used in the date range of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"date_format": date_format})

    @commands.command(aliases=["ssssir"])
    async def set_schedules_spreadsheet_staff_is_range(self, ctx, use_range: bool):
        """Sets the staff_is_range of the schedules spreadsheet."""
        await self.set_schedules_spreadsheet_values(ctx, {"use_range": use_range})

    async def set_schedules_spreadsheet_values(self, ctx, values):
        """Puts the input values into the corresponding bracket."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = self.get_current_bracket(tournament)
        schedules_spreadsheet = self.get_schedules_spreadsheet(bracket)
        for key, value in values.items():
            setattr(schedules_spreadsheet, key, value)
        self.bot.session.update(schedules_spreadsheet)
        await self.send_reply(ctx, ctx.command.name, "success")


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentBracketCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentBracketCog(bot))
