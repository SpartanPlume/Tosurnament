"""Contains all commands executable by the owner of the bot."""

from discord.ext import commands


class AdminCog(commands.Cog):
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


def get_class(bot):
    """Returns the main class of the module."""
    return AdminCog(bot)


def setup(bot):
    """Setups the cog."""
    bot.add_cog(AdminCog(bot))
