"""Contains all guild owner commands related to Tosurnament."""

from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.messages.reschedule_message import RescheduleMessage
from common.databases.messages.staff_reschedule_message import StaffRescheduleMessage
from common.databases.messages.end_tournament_message import EndTournamentMessage
from common.databases.messages.base_message import on_raw_reaction_with_context, with_corresponding_message


class TosurnamentGuildOwnerCog(tosurnament.TosurnamentBaseModule, name="guild_owner"):
    """Tosurnament guild owner only commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        return self.guild_owner_cog_check(ctx)

    @commands.command(aliases=["ct"])
    async def create_tournament(self, ctx, acronym: str, name: str, bracket_name: str = ""):
        """
        Creates a tournament.
        If a bracket name is not specified, the bracket takes the tournament's name as its name too.
        """
        guild_id = ctx.guild.id
        tournament = self.bot.session.query(Tournament).where(Tournament.guild_id == guild_id).first()
        if tournament:
            raise tosurnament.TournamentAlreadyCreated()
        tournament = Tournament(guild_id=guild_id, acronym=acronym, name=name)
        self.bot.session.add(tournament)
        if not bracket_name:
            bracket_name = name
        bracket = Bracket(tournament_id=tournament.id, name=bracket_name)
        self.bot.session.add(bracket)
        tournament.current_bracket_id = bracket.id
        self.bot.session.update(tournament)
        await self.send_reply(ctx, "success", acronym, name, bracket_name)

    @create_tournament.error
    async def create_tournament_handler(self, ctx, error):
        """Error handler of create_tournament function."""
        if isinstance(error, tosurnament.TournamentAlreadyCreated):
            await self.send_reply(ctx, "tournament_already_created")

    @commands.command(aliases=["et"])
    async def end_tournament(self, ctx):
        """Sends a message to react on, to be sure that the user wants to end the tournament."""
        self.get_tournament(ctx.guild.id)  # Check if there is a running tournament
        message = await self.send_reply(ctx, "are_you_sure")
        end_tournament_message = EndTournamentMessage(message_id=message.id)
        self.bot.session.add(end_tournament_message)

    @on_raw_reaction_with_context("add", valid_emojis=["✅", "❎"])
    @with_corresponding_message(EndTournamentMessage)
    async def reaction_on_end_tournament_message(self, ctx, emoji, end_tournament_message):
        """Ends a tournament."""
        if ctx.author.id != ctx.guild.owner.id:
            return
        try:
            tournament = self.get_tournament(ctx.guild.id)
        except tosurnament.NoTournament:
            self.bot.session.delete(end_tournament_message)
            return
        if emoji.name == "✅":
            for bracket in tournament.brackets:
                for spreadsheet_type in Bracket.get_spreadsheet_types().keys():
                    self.bot.session.delete(bracket.get_spreadsheet_from_type(spreadsheet_type))
                self.bot.session.delete(bracket)
            self.bot.session.query(RescheduleMessage).where(RescheduleMessage.tournament_id == tournament.id).delete()
            self.bot.session.query(StaffRescheduleMessage).where(
                StaffRescheduleMessage.tournament_id == tournament.id
            ).delete()
            self.bot.session.delete(tournament)
            self.bot.session.delete(end_tournament_message)
            await self.send_reply(ctx, "success")
        else:
            self.bot.session.delete(end_tournament_message)
            await self.send_reply(ctx, "refused")


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentGuildOwnerCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentGuildOwnerCog(bot))
