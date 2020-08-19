"""Contains all guild owner commands related to Tosurnament."""

from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.reschedule_message import RescheduleMessage
from common.databases.staff_reschedule_message import StaffRescheduleMessage
from common.databases.end_tournament_message import EndTournamentMessage


class TosurnamentGuildOwnerCog(tosurnament.TosurnamentBaseModule, name="guild_owner"):
    """Tosurnament guild owner only commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):  # pragma: no cover
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
        await self.send_reply(ctx, ctx.command.name, "success", acronym, name, bracket_name)

    @create_tournament.error  # pragma: no cover
    async def create_tournament_handler(self, ctx, error):
        """Error handler of create_tournament function."""
        if isinstance(error, tosurnament.TournamentAlreadyCreated):
            await self.send_reply(ctx, ctx.command.name, "tournament_already_created")

    @commands.command(aliases=["et"])
    async def end_tournament(self, ctx):
        """Sends a message to react on, to be sure that the user wants to end the tournament."""
        self.get_tournament(ctx.guild.id)  # Check if there is a running tournament
        message = await self.send_reply(ctx, ctx.command.name, "are_you_sure")
        end_tournament_message = EndTournamentMessage(message_id=message.id)
        self.bot.session.add(end_tournament_message)

    async def on_raw_reaction_add(self, message_id, emoji, guild, channel, user):  # pragma: no cover
        """on_raw_reaction_add of the Tosurnament guild_owner module."""
        await self.reaction_on_end_tournament_message(message_id, emoji, guild, channel, user)

    async def reaction_on_end_tournament_message(self, message_id, emoji, guild, channel, user):
        """Ends a tournament."""
        if user.id != guild.owner.id:
            return
        if emoji.name != "✅" and emoji.name != "❎":
            return
        end_tournament_message = (
            self.bot.session.query(EndTournamentMessage).where(EndTournamentMessage.message_id == message_id).first()
        )
        if not end_tournament_message:
            return
        try:
            tournament = self.get_tournament(guild.id)
        except tosurnament.NoTournament:
            self.bot.session.delete(end_tournament_message)
            return
        if emoji.name == "✅":
            for bracket in tournament.brackets:
                self.bot.session.delete(bracket.players_spreadsheet)
                self.bot.session.delete(bracket.schedules_spreadsheet)
                self.bot.session.delete(bracket)
            self.bot.session.query(RescheduleMessage).where(RescheduleMessage.tournament_id == tournament.id).delete()
            self.bot.session.query(StaffRescheduleMessage).where(
                StaffRescheduleMessage.tournament_id == tournament.id
            ).delete()
            self.bot.session.delete(tournament)
            self.bot.session.delete(end_tournament_message)
            await self.send_reply(channel, "end_tournament", "success")
        else:
            self.bot.session.delete(end_tournament_message)
            await self.send_reply(channel, "end_tournament", "refused")


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentGuildOwnerCog(bot)


def setup(bot):  # pragma: no cover
    """Setups the cog"""
    bot.add_cog(TosurnamentGuildOwnerCog(bot))
