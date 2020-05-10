"""Contains all guild settings commands."""

import discord
from discord.ext import commands
from bot.modules import module as base
from common.databases.guild import Guild
from common.databases.guild_verify_message import GuildVerifyMessage


class GuildCog(base.BaseModule, name="guild"):
    """Guild settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if ctx.guild.owner != ctx.author:
            raise base.NotGuildOwner()
        return True

    @commands.command(aliases=["sar"])
    async def set_admin_role(self, ctx, *, role: discord.Role):
        """Sets the bot admin role."""
        await self.set_guild_values(ctx, {"admin_role_id": role.id})

    @commands.command(aliases=["svr"])
    async def set_verified_role(self, ctx, *, role: discord.Role):
        """Sets the verified role."""
        await self.set_guild_values(ctx, {"verified_role_id": role.id})

    async def set_guild_values(self, ctx, values):
        """Puts the input values into the corresponding tournament."""
        guild = self.get_guild(ctx.guild.id)
        if not guild:
            guild = self.bot.session.add(Guild(guild_id=ctx.guild.id))
        for key, value in values.items():
            setattr(guild, key, value)
        self.bot.session.update(guild)
        await self.send_reply(ctx, ctx.command.name, "success")

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
        message = await self.send_reply(channel, ctx.command.name, "setup")
        guild_verify_message = (
            self.bot.session.query(GuildVerifyMessage).where(GuildVerifyMessage.guild_id == ctx.guild.id).first()
        )
        if guild_verify_message:
            guild_verify_message.message_id = message.id
            self.bot.session.update(guild_verify_message)
        else:
            self.bot.session.add(GuildVerifyMessage(message_id=message.id, guild_id=ctx.guild.id))
        await message.add_reaction("🛎️")

    async def on_raw_reaction_add(self, message_id, emoji, guild, channel, user):
        """on_raw_reaction_add of the Guild module."""
        await self.reaction_on_verify_message(message_id, emoji, guild, channel, user)

    async def reaction_on_verify_message(self, message_id, emoji, guild, channel, user):
        """Verifies the user."""
        if emoji.name == "🛎️":
            try:
                self.get_verified_user(user.id)
            except Exception as e:
                await self.on_cog_command_error(user, "setup_verification_channel", e)
                return
            await self.bot.on_verified_user(guild, user)

    async def on_verified_user(self, guild, user):
        bot_guild = self.get_guild(guild.id)
        verified_role_id = None
        if bot_guild:
            verified_role_id = bot_guild.verified_role_id
        verified_role = base.get_role(guild.roles, verified_role_id, "Verified")
        if verified_role:
            await user.add_roles(verified_role)


def get_class(bot):
    """Returns the main class of the module."""
    return GuildCog(bot)


def setup(bot):
    """Setups the cog."""
    bot.add_cog(GuildCog(bot))
