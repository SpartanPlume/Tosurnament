"""Contains all commands executable by the owner of the bot."""

from discord.ext import commands
from bot.modules import module as base
from common.databases.tournament import Tournament


class AdminCog(base.BaseModule, name="admin"):
    """Admin commands."""

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if ctx.author.id != self.bot.owner_id:
            raise commands.NotOwner()
        return True

    @commands.command(hidden=True)
    async def stop(self, ctx):
        """Stops the bot."""
        await self.bot.stop(0, ctx)

    @commands.command(hidden=True)
    async def update(self, ctx):
        """Updates the bot."""
        await self.bot.stop(42, ctx)

    @commands.command(hidden=True)
    async def restart(self, ctx):
        """Restarts the bot."""
        await self.bot.stop(43, ctx)

    @commands.command(hidden=True)
    async def ping(self, ctx):
        """Pings the bot."""
        await ctx.send("pong")

    @commands.command(hidden=True)
    async def say(self, ctx, *args):
        """Bot says the input."""
        await ctx.send(" ".join(args))

    @commands.command(hidden=True)
    async def announce(self, ctx, *, message: str):
        """Sends an annoucement to all servers that have a tournament running."""
        users_already_sent_to = []
        for guild in self.bot.guilds:
            tournament = self.bot.session.query(Tournament).where(Tournament.guild_id == guild.id).first()
            if tournament:
                staff_channel = self.bot.get_channel(tournament.staff_channel_id)
                tosurnament_guild = self.get_guild(guild.id)
                admin_role = base.get_role(guild.roles, tosurnament_guild.admin_role_id, "Admin")
                if admin_role:
                    admin_role_mention = admin_role.mention
                else:
                    admin_role_mention = guild.owner.mention
                try:
                    if staff_channel:
                        await staff_channel.send(admin_role_mention + "\n\n" + message)
                        continue
                except Exception:
                    pass
            if guild.owner.id not in users_already_sent_to:
                try:
                    await guild.owner.send(message)
                    users_already_sent_to.append(guild.owner.id)
                except Exception:
                    continue


def get_class(bot):
    """Returns the main class of the module."""
    return AdminCog(bot)


def setup(bot):
    """Setups the cog."""
    bot.add_cog(AdminCog(bot))
