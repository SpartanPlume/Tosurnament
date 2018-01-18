"""Admin commands"""

from discord.ext import commands

class Admin:
    """Admin commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='stop')
    @commands.is_owner()
    async def stop(self, ctx):
        """Stops the bot."""
        await self.bot.stop(ctx, 0)

    @commands.command(name='update')
    @commands.is_owner()
    async def update(self, ctx):
        """Updates the bot."""
        await self.bot.stop(ctx, 42)

    @commands.command(name='restart')
    @commands.is_owner()
    async def restart(self, ctx):
        """Restarts the bot."""
        await self.bot.stop(ctx, 43)

    @commands.command(name='test')
    @commands.is_owner()
    async def test(self, ctx, str1: str = "str1", *, string: str = "Nothing to test"):
        """Test."""
        await ctx.send(str1 + ": " + string)

def setup(bot):
    """Setups the cog"""
    bot.add_cog(Admin(bot))
