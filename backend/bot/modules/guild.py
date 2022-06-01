"""Contains all guild settings commands."""

import discord
from discord.ext import commands
from bot.modules import module as base
from common.databases.tosurnament.guild import Guild
from common.databases.tosurnament_message.guild_verify_message import GuildVerifyMessage
from common.databases.tosurnament_message.base_message import with_corresponding_message, on_raw_reaction_with_context
from common.api import tosurnament as tosurnament_api


class GuildCog(base.BaseModule, name="guild"):
    """Guild settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        return self.admin_cog_check(ctx)

    @commands.command(aliases=["sar"])
    async def set_admin_role(self, ctx, *, role: discord.Role):
        """Sets the bot admin role."""
        self.guild_owner_cog_check(ctx)
        await self.set_guild_values(ctx, {"admin_role_id": str(role.id)})

    @commands.command(aliases=["svr"])
    async def set_verified_role(self, ctx, *, role: discord.Role):
        """Sets the verified role."""
        await self.set_guild_values(ctx, {"verified_role_id": str(role.id)})

    @commands.command(aliases=["sl"])
    async def set_language(self, ctx, *, language: str = None):
        """Sets the language the bot needs to use on this server."""
        if language:
            if language in self.bot.languages:
                await self.set_guild_values(ctx, {"language": language})
            else:
                await self.send_reply(ctx, "invalid_language")
        else:
            await self.send_reply(ctx, "default", ", ".join(self.bot.languages))

    async def set_guild_values(self, ctx, values):
        """Puts the input values into the corresponding tournament."""
        guild = self.get_guild(ctx.guild.id)
        if not guild:
            guild = tosurnament_api.create_guild(
                Guild(guild_id=str(ctx.guild.id), guild_id_snowflake=str(ctx.guild.id))
            )
        for key, value in values.items():
            setattr(guild, key, value)
        tosurnament_api.update_guild(guild)
        await self.send_reply(ctx, "success", value)
        await self.send_reply(ctx, "use_dashboard", ctx.guild.id)

    @commands.command(aliases=["svc"])
    async def setup_verification_channel(self, ctx, channel: discord.TextChannel):
        """Setups a channel with a message to react on to be verified."""
        guild = self.get_guild(ctx.guild.id)
        verified_role_id = None
        if guild:
            verified_role_id = guild.verified_role_id
        verified_role = base.get_role(ctx.guild.roles, verified_role_id, "Verified")
        if not verified_role:
            raise base.RoleDoesNotExist("Verified")
        message = await self.send_reply(ctx, "setup", channel=channel)
        guild_verify_message = (
            self.bot.session.query(GuildVerifyMessage).where(GuildVerifyMessage.guild_id == ctx.guild.id).first()
        )
        if guild_verify_message:
            guild_verify_message.message_id = message.id
            self.bot.session.update(guild_verify_message)
        else:
            self.bot.session.add(GuildVerifyMessage(message_id=message.id, guild_id=ctx.guild.id))
        await message.add_reaction("🛎️")

    @commands.command(aliases=["sgs"])
    async def show_guild_settings(self, ctx):
        """Shows the guild settings."""
        guild = self.get_guild(ctx.guild.id)
        await self.show_object_settings(ctx, guild)

    @on_raw_reaction_with_context("add", valid_emojis=["🛎️"])
    @with_corresponding_message(GuildVerifyMessage)
    async def reaction_on_verify_message(self, ctx, emoji, guild_verify_message):
        """Verifies the user."""
        try:
            self.get_verified_user(ctx.author.id)
        except (base.UserNotLinked, base.UserNotVerified) as e:
            dm_channel = await ctx.author.create_dm()
            await self.on_cog_command_error(ctx, e, channel=dm_channel)
            return
        await self.bot.on_verified_user(ctx.guild, ctx.author)

    async def on_verified_user(self, guild, user):
        verified_user = self.get_verified_user(user.id)
        bot_guild = self.get_guild(guild.id)
        verified_role_id = None
        if bot_guild:
            verified_role_id = bot_guild.verified_role_id
        verified_role = base.get_role(guild.roles, verified_role_id, "Verified")
        if verified_user.osu_name:
            try:
                await user.edit(nick=verified_user.osu_name)
            except Exception:
                self.bot.info("Missing manage_nicknames permission or error while changing the nickname of the user")
        if verified_role:
            try:
                await user.add_roles(verified_role)
            except Exception:
                self.bot.info("Missing manage_roles permission or error while changing the role of the user")


def get_class(bot):
    """Returns the main class of the module."""
    return GuildCog(bot)


def setup(bot):
    """Setups the cog."""
    bot.add_cog(GuildCog(bot))
