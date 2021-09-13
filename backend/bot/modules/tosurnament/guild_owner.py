"""Contains all guild owner commands related to Tosurnament."""

from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.tosurnament.tournament import Tournament
from common.databases.tosurnament_message.qualifiers_results_message import QualifiersResultsMessage
from common.databases.tosurnament_message.reschedule_message import RescheduleMessage
from common.databases.tosurnament_message.staff_reschedule_message import StaffRescheduleMessage
from common.databases.tosurnament_message.end_tournament_message import EndTournamentMessage
from common.databases.tosurnament_message.post_result_message import PostResultMessage
from common.databases.tosurnament_message.match_notification import MatchNotification
from common.databases.tosurnament_message.base_message import on_raw_reaction_with_context, with_corresponding_message
from common.api import tosurnament as tosurnament_api


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
        guild_id = str(ctx.guild.id)
        tournament = tosurnament_api.get_tournament_by_discord_guild_id(guild_id)
        if tournament:
            raise tosurnament.TournamentAlreadyCreated()
        tournament = Tournament(guild_id=guild_id, guild_id_snowflake=guild_id, acronym=acronym, name=name)
        tournament = tosurnament_api.create_tournament(tournament)
        if bracket_name:
            tournament.current_bracket.name = bracket_name
            tosurnament_api.update_bracket(tournament.id, tournament.current_bracket)
        await self.send_reply(ctx, "success", acronym, name, bracket_name)

    @create_tournament.error
    async def create_tournament_handler(self, ctx, error):
        """Error handler of create_tournament function."""
        if isinstance(error, tosurnament.TournamentAlreadyCreated):
            await self.send_reply(ctx, "tournament_already_created")

    @commands.command(aliases=["et"])
    async def end_tournament(self, ctx):
        """Sends a message to react on, to be sure that the user wants to end the tournament."""
        tournament = self.get_tournament(ctx.guild.id)
        message = await self.send_reply(ctx, "are_you_sure")
        end_tournament_message = EndTournamentMessage(
            message_id=message.id, author_id=str(ctx.author.id), tournament_id=tournament.id
        )
        self.bot.session.add(end_tournament_message)

    @on_raw_reaction_with_context("add", valid_emojis=["✅", "❎"])
    @with_corresponding_message(EndTournamentMessage)
    async def reaction_on_end_tournament_message(self, ctx, emoji, end_tournament_message):
        """Ends a tournament."""
        try:
            tournament = self.get_tournament(ctx.guild.id)
        except tosurnament.NoTournament:
            self.bot.session.delete(end_tournament_message)
            return
        if emoji.name == "✅":
            tosurnament_api.delete_tournament(tournament)
            self.bot.session.query(RescheduleMessage).where(RescheduleMessage.tournament_id == tournament.id).delete()
            self.bot.session.query(StaffRescheduleMessage).where(
                StaffRescheduleMessage.tournament_id == tournament.id
            ).delete()
            self.bot.session.query(MatchNotification).where(MatchNotification.tournament_id == tournament.id).delete()
            self.bot.session.query(PostResultMessage).where(PostResultMessage.tournament_id == tournament.id).delete()
            self.bot.session.query(QualifiersResultsMessage).where(
                QualifiersResultsMessage.tournament_id == tournament.id
            ).delete()
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
