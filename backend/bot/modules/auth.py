"""Contains all authentification commands."""

import os
import base64
from discord.ext import commands
from bot.modules import module as base
from common.databases.tosurnament.user import User
from common.api import tosurnament as tosurnament_api


class UserAlreadyVerified(commands.CommandError):
    """Special exception in case the user is already verified."""

    pass


class WrongCodeError(commands.CommandError):
    """Special exception in case an authentification code is wrong."""

    pass


class AuthCog(base.BaseModule, name="auth"):
    """Auth commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    @commands.command()
    async def link(self, ctx):
        """
        Sends a private message to the command runner to link his account.
        If the user is already linked but not verified, a new code is generated (in case the previous one is lost).
        """
        user = self.get_user(ctx.author.id)
        if user and user.verified:
            raise UserAlreadyVerified()

        code = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b"=").decode("ascii")
        if not user:
            user = User(
                discord_id=ctx.author.id,
                discord_id_snowflake=ctx.author.id,
                verified=False,
                code=code,
            )
            user = tosurnament_api.create_user(user)
        else:
            user.code = code
            tosurnament_api.update_user(user)

        dm_channel = await ctx.author.create_dm()
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await self.send_reply(ctx, "success", code, channel=dm_channel)

    @link.error
    async def link_handler(self, ctx, error):
        """Error handler of link function."""
        if isinstance(error, UserAlreadyVerified):
            await self.send_reply(ctx, "already_verified")


def get_class(bot):
    """Returns the main class of the module."""
    return AuthCog(bot)


def setup(bot):
    """Setups the cog."""
    bot.add_cog(AuthCog(bot))
