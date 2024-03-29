"""Contains all guild settings commands."""

import discord
from discord.ext import commands
from bot.modules import module as base
from common.databases.tosurnament_message.reaction_for_role_message import ReactionForRoleMessage
from common.databases.tosurnament_message.base_message import with_corresponding_message, on_raw_reaction_with_context


class ReactionForRoleMessageCog(base.BaseModule, name="reaction_for_role_message"):
    """ReactionForRoleMessage settings commands."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        return self.admin_cog_check(ctx)

    async def delete_setup_messages(self, reaction_for_role_message):
        try:
            setup_channel = self.bot.get_channel(int(reaction_for_role_message.setup_channel_id))
            message = await setup_channel.fetch_message(int(reaction_for_role_message.setup_message_id))
            await message.delete()
            message = await setup_channel.fetch_message(int(reaction_for_role_message.preview_message_id))
            await message.delete()
        except Exception:
            return

    @commands.command(aliases=["crfrm"])
    async def create_reaction_for_role_message(self, ctx, channel: discord.TextChannel, *, message_text: str):
        """Creates a message to react on to have specific roles."""
        reaction_for_role_message = (
            self.bot.session.query(ReactionForRoleMessage)
            .where(ReactionForRoleMessage.guild_id == str(ctx.guild.id))
            .where(ReactionForRoleMessage.author_id == str(ctx.author.id))
            .first()
        )
        if reaction_for_role_message and reaction_for_role_message.setup_channel_id:
            await self.delete_setup_messages(reaction_for_role_message)
            self.bot.session.delete(reaction_for_role_message)
        setup_message = await self.send_reply(ctx, "success", self.get_string(ctx, "none") + "\n")
        preview_message = await ctx.send(message_text)
        reaction_for_role_message = ReactionForRoleMessage(
            guild_id=str(ctx.guild.id),
            author_id=str(ctx.author.id),
            setup_channel_id=str(ctx.channel.id),
            setup_message_id=setup_message.id,
            preview_message_id=preview_message.id,
            channel_id=str(channel.id),
            text=message_text,
        )
        self.bot.session.add(reaction_for_role_message)

    @commands.command(aliases=["aerp"])
    async def add_emoji_role_pair(self, ctx, new_emoji: str, new_role: discord.Role):
        """Adds an emoji to react on to give the corresponding role."""
        reaction_for_role_message = (
            self.bot.session.query(ReactionForRoleMessage)
            .where(ReactionForRoleMessage.guild_id == str(ctx.guild.id))
            .where(ReactionForRoleMessage.author_id == str(ctx.author.id))
            .first()
        )
        if not reaction_for_role_message:
            await self.send_reply(ctx, "error")
            return
        emojis = list(filter(None, reaction_for_role_message.emojis.split("\n")))
        if new_emoji in emojis:
            await self.send_reply(ctx, "emoji_duplicate")
            return
        try:
            await ctx.message.add_reaction(new_emoji)
        except discord.InvalidArgument:
            await self.send_reply(ctx, "invalid_emoji", new_emoji)
            return
        except discord.NotFound:
            await self.send_reply(ctx, "emoji_not_found", new_emoji)
            return
        except discord.HTTPException as e:
            if e.status == 400:
                await self.send_reply(ctx, "emoji_not_found", new_emoji)
                return
            raise e
        roles = list(filter(None, reaction_for_role_message.roles.split("\n")))
        current_emoji_role_pairs = ""
        for emoji, role_id in zip(emojis, roles):
            role = ctx.guild.get_role(int(role_id))
            role_name = self.get_string(ctx, "unknown_role")
            if role:
                role_name = role.name
            current_emoji_role_pairs += emoji + " | " + role_name + "\n"
        current_emoji_role_pairs += new_emoji + " | " + new_role.name + "\n"
        emojis.append(new_emoji)
        roles.append(str(new_role.id))

        await self.delete_setup_messages(reaction_for_role_message)
        setup_message = await self.send_reply(ctx, "success", current_emoji_role_pairs)
        preview_message = await ctx.send(reaction_for_role_message.text)

        reaction_for_role_message.setup_channel_id = str(ctx.channel.id)
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
            .where(ReactionForRoleMessage.guild_id == str(ctx.guild.id))
            .where(ReactionForRoleMessage.author_id == str(ctx.author.id))
            .first()
        )
        if not reaction_for_role_message:
            await self.send_reply(ctx, "error")
            return
        if not reaction_for_role_message.emojis or not reaction_for_role_message.roles:
            await self.send_reply(ctx, "no_emoji")
            return

        channel = self.bot.get_channel(int(reaction_for_role_message.channel_id))
        if not channel:
            await self.send_reply(ctx, "channel_error")
            self.bot.session.delete(reaction_for_role_message)
            return
        message = await channel.send(reaction_for_role_message.text)
        for emoji in filter(None, reaction_for_role_message.emojis.split("\n")):
            try:
                await message.add_reaction(emoji)
            except Exception:
                await self.send_reply(ctx, "add_reaction_error")
                try:
                    await message.delete()
                except Exception:
                    await self.send_reply(ctx, "message_not_deleted")
                    return
                await self.send_reply(ctx, "message_deleted")
                return

        await self.delete_setup_messages(reaction_for_role_message)
        reaction_for_role_message.author_id = ""
        reaction_for_role_message.setup_channel_id = ""
        reaction_for_role_message.setup_message_id = 0
        reaction_for_role_message.preview_message_id = 0
        reaction_for_role_message.message_id = message.id
        self.bot.session.update(reaction_for_role_message)

    @commands.command(aliases=["crfrmc"])
    async def cancel_reaction_for_role_message_creation(self, ctx):
        """Cancels message creation."""
        reaction_for_role_message = (
            self.bot.session.query(ReactionForRoleMessage)
            .where(ReactionForRoleMessage.guild_id == str(ctx.guild.id))
            .where(ReactionForRoleMessage.author_id == str(ctx.author.id))
            .first()
        )
        if not reaction_for_role_message:
            await self.send_reply(ctx, "error")
            return
        await self.delete_setup_messages(reaction_for_role_message)
        self.bot.session.delete(reaction_for_role_message)
        await self.send_reply(ctx, "success")

    @on_raw_reaction_with_context("add")
    @with_corresponding_message(ReactionForRoleMessage)
    async def on_reaction_add_to_message(self, ctx, emoji, reaction_for_role_message):
        await self.reaction_on_message(ctx, emoji, reaction_for_role_message, True)

    @on_raw_reaction_with_context("remove")
    @with_corresponding_message(ReactionForRoleMessage)
    async def on_reaction_remove_to_message(self, ctx, emoji, reaction_for_role_message):
        await self.reaction_on_message(ctx, emoji, reaction_for_role_message, False)

    async def reaction_on_message(self, ctx, emoji, reaction_for_role_message, add):
        """Gives or removes the appropriate role."""
        emojis = list(filter(None, reaction_for_role_message.emojis.split("\n")))
        emoji_name = str(emoji)
        if emoji_name not in emojis:
            return
        roles = list(filter(None, reaction_for_role_message.roles.split("\n")))
        index = emojis.index(emoji_name)

        role = ctx.guild.get_role(int(roles[index]))
        if not role:
            return
        try:
            if add:
                await ctx.author.add_roles(role)
            else:
                await ctx.author.remove_roles(role)
        except Exception:
            return


async def setup(bot):
    """Setups the cog."""
    await bot.add_cog(ReactionForRoleMessageCog(bot))
