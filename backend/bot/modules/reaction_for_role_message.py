"""Contains all guild settings commands."""

import discord
from discord.ext import commands
from bot.modules import module as base
from common.databases.reaction_for_role_message import ReactionForRoleMessage


class ReactionForRoleMessageCog(base.BaseModule, name="guild"):
    """ReactionForRoleMessage settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if ctx.guild.owner == ctx.author:
            return True
        guild = self.get_guild(ctx.guild.id)
        if not guild or not guild.admin_role_id:
            raise base.NotBotAdmin()
        if not base.get_role(ctx.author.roles, guild.admin_role_id):
            raise base.NotBotAdmin()
        return True

    async def delete_setup_messages(self, reaction_for_role_message):
        try:
            setup_channel = self.bot.get_channel(reaction_for_role_message.setup_channel_id)
            message = await setup_channel.fetch_message(reaction_for_role_message.setup_message_id)
            await message.delete()
            message = await setup_channel.fetch_message(reaction_for_role_message.preview_message_id)
            await message.delete()
        except Exception:
            return

    @commands.command(aliases=["crfrm"])
    async def create_reaction_for_role_message(self, ctx, channel: discord.TextChannel, *, message_text: str):
        """Creates a message to react on to have specific roles."""
        reaction_for_role_message = (
            self.bot.session.query(ReactionForRoleMessage)
            .where(ReactionForRoleMessage.guild_id == ctx.guild.id)
            .where(ReactionForRoleMessage.author_id == ctx.author.id)
            .first()
        )
        if reaction_for_role_message and reaction_for_role_message.setup_channel_id:
            await self.delete_setup_messages(reaction_for_role_message)
            self.bot.session.delete(reaction_for_role_message)
        setup_message = await self.send_reply(ctx, ctx.command.name, "success", "None\n")
        preview_message = await ctx.send(message_text)
        reaction_for_role_message = ReactionForRoleMessage(
            guild_id=ctx.guild.id,
            author_id=ctx.author.id,
            setup_channel_id=ctx.channel.id,
            setup_message_id=setup_message.id,
            preview_message_id=preview_message.id,
            channel_id=channel.id,
            text=message_text,
        )
        self.bot.session.add(reaction_for_role_message)

    @commands.command(aliases=["aerp"])
    async def add_emoji_role_pair(self, ctx, new_emoji: str, new_role: discord.Role):
        """Adds an emoji to react on to give the corresponding role."""
        reaction_for_role_message = (
            self.bot.session.query(ReactionForRoleMessage)
            .where(ReactionForRoleMessage.guild_id == ctx.guild.id)
            .where(ReactionForRoleMessage.author_id == ctx.author.id)
            .first()
        )
        if not reaction_for_role_message:
            await self.send_reply(ctx, ctx.command.name, "error")
            return
        emojis = list(filter(None, reaction_for_role_message.emojis.split("\n")))
        if new_emoji in emojis:
            await self.send_reply(ctx, ctx.command.name, "emoji_duplicate")
            return
        try:
            await ctx.message.add_reaction(new_emoji)
        except discord.InvalidArgument:
            await self.send_reply(ctx, ctx.command.name, "invalid_emoji", new_emoji)
            return
        except discord.NotFound:
            await self.send_reply(ctx, ctx.command.name, "emoji_not_found", new_emoji)
            return
        except discord.HTTPException as e:
            if e.status == 400:
                await self.send_reply(ctx, ctx.command.name, "emoji_not_found", new_emoji)
                return
            raise e
        roles = list(filter(None, reaction_for_role_message.roles.split("\n")))
        current_emoji_role_pairs = ""
        for emoji, role_id in zip(emojis, roles):
            role = ctx.guild.get_role(int(role_id))
            role_name = "Unknown role"
            if role:
                role_name = role.name
            current_emoji_role_pairs += emoji + " | " + role_name + "\n"
        current_emoji_role_pairs += new_emoji + " | " + new_role.name + "\n"
        emojis.append(new_emoji)
        roles.append(str(new_role.id))

        await self.delete_setup_messages(reaction_for_role_message)
        setup_message = await self.send_reply(ctx, ctx.command.name, "success", current_emoji_role_pairs)
        preview_message = await ctx.send(reaction_for_role_message.text)

        reaction_for_role_message.setup_channel_id = ctx.channel.id
        reaction_for_role_message.setup_message_id = setup_message.id
        reaction_for_role_message.preview_message_id = preview_message.id
        reaction_for_role_message.emojis = "\n".join(emojis)
        reaction_for_role_message.roles = "\n".join(roles)
        self.bot.session.update(reaction_for_role_message)

        for emoji in emojis:
            await preview_message.add_reaction(emoji)

    @commands.command(aliases=["prfrm"])
    async def post_reaction_for_role_message(self, ctx):
        """Posts the reaction for role message."""
        reaction_for_role_message = (
            self.bot.session.query(ReactionForRoleMessage)
            .where(ReactionForRoleMessage.guild_id == ctx.guild.id)
            .where(ReactionForRoleMessage.author_id == ctx.author.id)
            .first()
        )
        if not reaction_for_role_message:
            await self.send_reply(ctx, ctx.command.name, "error")
            return
        if not reaction_for_role_message.emojis or not reaction_for_role_message.roles:
            await self.send_reply(ctx, ctx.command.name, "no_emoji")
            return

        await self.delete_setup_messages(reaction_for_role_message)
        reaction_for_role_message.guild_id = ""
        reaction_for_role_message.author_id = ""
        reaction_for_role_message.setup_channel_id = 0
        reaction_for_role_message.setup_message_id = 0
        reaction_for_role_message.preview_message_id = 0

        channel = self.bot.get_channel(reaction_for_role_message.channel_id)
        if not channel:
            await self.send_reply(ctx, ctx.command.name, "channel_error")
            self.bot.session.delete(reaction_for_role_message)
            return
        message = await channel.send(reaction_for_role_message.text)
        reaction_for_role_message.message_id = message.id
        self.bot.session.update(reaction_for_role_message)

        for emoji in filter(None, reaction_for_role_message.emojis.split("\n")):
            try:
                await message.add_reaction(emoji)
            except Exception:
                continue

    @commands.command(aliases=["crfrmc"])
    async def cancel_reaction_for_role_message_creation(self, ctx):
        """Cancels message creation."""
        reaction_for_role_message = (
            self.bot.session.query(ReactionForRoleMessage)
            .where(ReactionForRoleMessage.guild_id == ctx.guild.id)
            .where(ReactionForRoleMessage.author_id == ctx.author.id)
            .first()
        )
        if not reaction_for_role_message:
            await self.send_reply(ctx, ctx.command.name, "error")
            return
        await self.delete_setup_messages(reaction_for_role_message)
        self.bot.session.delete(reaction_for_role_message)
        await self.send_reply(ctx, ctx.command.name, "success")

    async def on_raw_reaction_add(self, message_id, emoji, guild, channel, user):
        """on_raw_reaction_add of the reaction_for_role_message module"""
        await self.reaction_on_message(message_id, emoji, guild, channel, user, True)

    async def on_raw_reaction_remove(self, message_id, emoji, guild, channel, user):
        """on_raw_reaction_remove of the reaction_for_role_message module"""
        await self.reaction_on_message(message_id, emoji, guild, channel, user, False)

    async def reaction_on_message(self, message_id, emoji, guild, channel, user, add):
        """Gives or removes the appropriate role."""
        reaction_for_role_message = (
            self.bot.session.query(ReactionForRoleMessage)
            .where(ReactionForRoleMessage.message_id == message_id)
            .first()
        )
        if not reaction_for_role_message:
            return
        emojis = list(filter(None, reaction_for_role_message.emojis.split("\n")))
        emoji_name = str(emoji)
        if emoji_name not in emojis:
            return
        roles = list(filter(None, reaction_for_role_message.roles.split("\n")))
        index = emojis.index(emoji_name)

        role = guild.get_role(int(roles[index]))
        if not role:
            return
        try:
            if add:
                await user.add_roles(role)
            else:
                await user.remove_roles(role)
        except Exception:
            return


def get_class(bot):
    """Returns the main class of the module."""
    return ReactionForRoleMessageCog(bot)


def setup(bot):
    """Setups the cog."""
    bot.add_cog(ReactionForRoleMessageCog(bot))
