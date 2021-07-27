"""Contains all authentification commands."""

import discord
from discord.ext import commands
from bot.modules import module as base


class AdminCog(base.BaseModule, name="admin"):
    """Admin commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["sui"])
    async def show_user_info(self, ctx, member: discord.Member):
        user = self.get_user(member.id)
        if not user:
            raise base.UserNotLinked()
        await self.send_reply(
            ctx,
            "success",
            user.discord_id_snowflake,
            user.osu_id,
            user.osu_name,
            user.osu_previous_name,
            str(user.verified),
        )


def get_class(bot):
    """Returns the main class of the module."""
    return AdminCog(bot)


def setup(bot):
    """Setups the cog."""
    bot.add_cog(AdminCog(bot))
