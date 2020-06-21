"""Contains all tournament settings commands related to Tosurnament."""

import discord
from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.bracket import Bracket


class TosurnamentTournamentCog(tosurnament.TosurnamentBaseModule, name="tournament"):
    """Tosurnament tournament settings commands."""

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

    @commands.command(aliases=["stn"])
    async def set_tournament_name(self, ctx, *, name: str):
        """Sets the tournament name."""
        await self.set_tournament_values(ctx, {"name": name})

    @commands.command(aliases=["cb"])
    async def create_bracket(self, ctx, *, name: str):
        """Creates a bracket and sets it as current bracket (for bracket settings purpose)."""
        tournament = self.get_tournament(ctx.guild.id)
        bracket = Bracket(tournament_id=tournament.id, name=name)
        self.bot.session.add(bracket)
        tournament.current_bracket_id = bracket.id
        self.bot.session.update(tournament)
        await self.send_reply(ctx, ctx.command.name, "success", name)

    @commands.command(aliases=["get_brackets", "gb"])
    async def get_bracket(self, ctx, *, number: int = None):
        """Sets a bracket as current bracket or shows them all."""
        tournament = self.get_tournament(ctx.guild.id)
        brackets = tournament.brackets
        if number or number == 0:
            number -= 1
            if not (number >= 0 and number < len(brackets)):
                raise commands.UserInputError()
            tournament.current_bracket_id = brackets[number].id
            self.bot.session.update(tournament)
            await self.send_reply(ctx, ctx.command.name, "success", brackets[number].name)
        else:
            brackets_string = ""
            for i, bracket in enumerate(brackets):
                brackets_string += str(i + 1) + ": `" + bracket.name + "`"
                if bracket.id == tournament.current_bracket_id:
                    brackets_string += " (current bracket)"
                brackets_string += "\n"
            await self.send_reply(ctx, ctx.command.name, "default", brackets_string)

    @commands.command(aliases=["ssc"])
    async def set_staff_channel(self, ctx, *, channel: discord.TextChannel):
        """Sets the staff channel."""
        await self.set_tournament_values(ctx, {"staff_channel_id": channel.id})

    @commands.command(aliases=["srr"])
    async def set_referee_role(self, ctx, *, role: discord.Role):
        """Sets the referee role."""
        await self.set_tournament_values(ctx, {"referee_role_id": role.id})

    @commands.command(aliases=["ssr"])
    async def set_streamer_role(self, ctx, *, role: discord.Role):
        """Sets the streamer role."""
        await self.set_tournament_values(ctx, {"streamer_role_id": role.id})

    @commands.command(aliases=["scr"])
    async def set_commentator_role(self, ctx, *, role: discord.Role):
        """Sets the commentator role."""
        await self.set_tournament_values(ctx, {"commentator_role_id": role.id})

    @commands.command(aliases=["spr"])
    async def set_player_role(self, ctx, *, role: discord.Role):
        """Sets the player role."""
        await self.set_tournament_values(ctx, {"player_role_id": role.id})

    @commands.command(aliases=["stcr", "set_team_leader_role", "stlr"])
    async def set_team_captain_role(self, ctx, *, role: discord.Role = None):
        """Sets the team captain role."""
        if not role:
            await self.set_tournament_values(ctx, {"team_captain_role_id": 0})
        else:
            await self.set_tournament_values(ctx, {"team_captain_role_id": role.id})

    @commands.command(aliases=["spt"])
    async def set_ping_team(self, ctx, ping_team: bool):
        """Sets if team should be pinged or team captain should be pinged."""
        await self.set_tournament_values(ctx, {"reschedule_ping_team": ping_team})

    @commands.command(aliases=["sprm"])
    async def set_post_result_message(self, ctx, *, message: str = ""):
        """Sets the post result message."""
        await self.set_tournament_values(ctx, {"post_result_message": message})

    @commands.command(aliases=["srdh", "set_reschedule_deadline", "srd"])
    async def set_reschedule_deadline_hours(self, ctx, hours: int):
        """Allows to change the deadline (in hours) to reschedule a match."""
        await self.set_tournament_values(ctx, {"reschedule_hours_deadline": hours})

    async def set_tournament_values(self, ctx, values):
        """Puts the input values into the corresponding tournament."""
        tournament = self.get_tournament(ctx.guild.id)
        for key, value in values.items():
            setattr(tournament, key, value)
        self.bot.session.update(tournament)
        await self.send_reply(ctx, ctx.command.name, "success", value)


def get_class(bot):
    """Returns the main class of the module."""
    return TosurnamentTournamentCog(bot)


def setup(bot):
    """Setups the cog."""
    bot.add_cog(TosurnamentTournamentCog(bot))
