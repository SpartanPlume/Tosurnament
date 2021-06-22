"""Contains all authentification commands."""

import os
import base64
import requests
from discord.ext import commands
from bot.modules import module as base
from common.databases.user import User
from common.api import osu


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
    async def link(self, ctx, *, osu_name: str):
        """
        Sends a private message to the command runner to link his account.
        If the user is already linked but not verified, a new code is generated (in case the previous one is lost).
        """
        user = self.get_user(ctx.author.id)
        if user and user.verified:
            raise UserAlreadyVerified()

        osu_user = osu.get_user(osu_name)
        if not osu_user:
            raise base.UserNotFound(osu_name)

        osu_id = osu_user.id
        code = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b"=").decode("ascii")
        if not user:
            user = User(
                discord_id=ctx.author.id,
                discord_id_snowflake=ctx.author.id,
                osu_id=osu_id,
                verified=False,
                code=code,
                osu_name=osu_name,
                osu_name_hash=osu_name.lower(),
            )
            self.bot.session.add(user)
        else:
            user.osu_id = osu_id
            user.code = code
            user.osu_name = osu_name
            user.osu_name_hash = osu_name.lower()
            self.bot.session.update(user)

        dm_channel = await ctx.author.create_dm()
        await self.send_reply(ctx, "success", code, channel=dm_channel)

    @link.error
    async def link_handler(self, ctx, error):
        """Error handler of link function."""
        if isinstance(error, UserAlreadyVerified):
            await self.send_reply(ctx, "already_verified")

    @commands.command()
    async def new_link(self, ctx):
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
            self.bot.session.add(user)
        else:
            user.code = code
            self.bot.session.update(user)

        dm_channel = await ctx.author.create_dm()
        await self.send_reply(ctx, "success", code, channel=dm_channel)

    @new_link.error
    async def new_link_handler(self, ctx, error):
        """Error handler of link function."""
        if isinstance(error, UserAlreadyVerified):
            await self.send_reply(ctx, "already_verified")

    @commands.command()
    async def auth(self, ctx):
        """Sends a private message to the command runner to auth his account."""
        user = self.get_user(ctx.author.id)
        if not user:
            raise base.UserNotLinked()
        if user.verified:
            raise UserAlreadyVerified()

        osu_id = user.osu_id
        request = requests.get("https://osu.ppy.sh/u/" + osu_id)
        if request.status_code != 200:
            raise base.OsuError()

        index = 0
        try:
            to_find = 'location":"'
            index = request.text.index(to_find)
            index += len(to_find)
        except ValueError:
            raise base.OsuError()
        location = request.text[index:]
        location = location[: len(user.code)]
        if location != user.code:
            raise WrongCodeError()
        else:
            user.verified = True
            self.bot.session.update(user)

        dm_channel = await ctx.author.create_dm()
        await self.send_reply(ctx, "success", channel=dm_channel)

    @auth.error
    async def auth_handler(self, ctx, error):
        if isinstance(error, UserAlreadyVerified):
            await self.send_reply(ctx, "already_verified")
        elif isinstance(error, WrongCodeError):
            await self.send_reply(ctx, "wrong_code")


def get_class(bot):
    """Returns the main class of the module."""
    return AuthCog(bot)


def setup(bot):
    """Setups the cog."""
    bot.add_cog(AuthCog(bot))
