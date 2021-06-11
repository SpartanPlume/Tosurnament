"""Base of all modules. Contains utility functions."""

import copy
import inspect
import discord
from discord.ext import commands
from common.exceptions import *
from common.utils import load_json
from common.databases.guild import Guild
from common.databases.user import User


class UserAbstraction:
    def __init__(self, name, discord_id, verified):
        self.name = name
        self.discord_id = discord_id
        self.verified = verified

    @staticmethod
    def get_from_ctx(ctx):
        return UserAbstraction.get_from_user(ctx.bot, ctx.author)

    @staticmethod
    def get_from_user(bot, user):
        tosurnament_user = bot.session.query(User).where(User.discord_id == user.id).first()
        if tosurnament_user and tosurnament_user.verified:
            return UserAbstraction(tosurnament_user.osu_name, user.id, True)
        return UserAbstraction(user.display_name, user.id, False)

    @staticmethod
    def get_from_osu_name(bot, osu_name, default_discord_tag=None):
        tosurnament_user = bot.session.query(User).where(User.osu_name_hash == osu_name.lower()).first()
        if tosurnament_user and tosurnament_user.verified:
            return UserAbstraction(tosurnament_user.osu_name, tosurnament_user.discord_id_snowflake, True)
        return UserAbstraction(osu_name, default_discord_tag, False)

    @staticmethod
    def get_from_player_info(bot, player_info, guild=None):
        tosurnament_user = None
        discord_id = player_info.discord_id.get()
        if discord_id:
            tosurnament_user = bot.session.query(User).where(User.discord_id == discord_id).first()
        osu_name = player_info.name.get()
        if not tosurnament_user and osu_name:
            tosurnament_user = bot.session.query(User).where(User.osu_name_hash == osu_name.lower()).first()
        discord_tag = player_info.discord.get()
        if not tosurnament_user and guild and discord_tag:
            member = guild.get_member_named(discord_tag)
            if member:
                tosurnament_user = bot.session.query(User).where(User.discord_id == member.id).first()
        if tosurnament_user and tosurnament_user.verified:
            return UserAbstraction(tosurnament_user.osu_name, tosurnament_user.discord_id_snowflake, True)
        elif discord_id:
            return UserAbstraction(osu_name, discord_id, False)
        return UserAbstraction(osu_name, discord_tag, False)

    def get_member(self, guild):
        if self.discord_id:
            if isinstance(self.discord_id, int):
                return guild.get_member(self.discord_id)
            elif isinstance(self.discord_id, str):
                return guild.get_member_named(self.discord_id)
        return None


class BaseModule(commands.Cog):
    """Contains utility functions used by modules."""

    def __init__(self, bot):
        self.bot = bot

    def guild_owner_cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if ctx.guild.owner != ctx.author:
            raise NotGuildOwner()
        return True

    def admin_cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if not self.is_admin(ctx):
            raise NotBotAdmin()
        return True

    def is_admin(self, ctx):
        if ctx.guild.owner == ctx.author:
            return True
        guild = self.get_guild(ctx.guild.id)
        if not guild or not guild.admin_role_id:
            return False
        if not get_role(ctx.author.roles, guild.admin_role_id):
            return False
        return True

    async def update_table(self, ctx, table, values):
        for key, value in values.items():
            setattr(table, key, value)
        self.bot.session.update(table)
        await self.send_reply(ctx, "success", value, stack_depth=2)

    def get_guild(self, guild_id):
        return self.bot.session.query(Guild).where(Guild.guild_id == guild_id).first()

    def get_user(self, discord_id):
        """Gets the User from their discord id."""
        return self.bot.session.query(User).where(User.discord_id == discord_id).first()

    def get_verified_user(self, discord_id):
        """Gets the User from their discord id, but only if they are verified."""
        user = self.get_user(discord_id)
        if not user:
            raise UserNotLinked()
        if not user.verified:
            raise UserNotVerified()
        return user

    def get_module_name_from_stack(self, stack_depth):
        stack = inspect.currentframe().f_back
        while stack_depth > 0:
            stack = stack.f_back
            stack_depth -= 1
        return stack.f_globals["__name__"][12:]

    def get_string(self, ctx, field_name, *args, stack_depth=1):
        """Gets string from strings.json file"""
        module_name = self.get_module_name_from_stack(stack_depth)
        modules = module_name.split(".")[:-1]
        reply = self.find_reply(
            ctx.guild, self.bot.strings, field_name, modules + [ctx.command.cog_name], ctx.command.name
        )
        if reply:
            return load_json.replace_in_string(reply, self.bot.command_prefix, *args)
        else:
            if field_name not in ["parameter", "example_parameter"]:
                self.bot.error("Reply not found: " + ctx.command.cog_name + ": " + ctx.command.name + ": " + field_name)
        return ""

    def get_simple_string(self, guild, field_name):
        """Gets a simple string from strings.json file"""
        reply = self.find_reply(guild, self.bot.strings, field_name, [], None)
        if reply:
            return reply
        else:
            if field_name not in ["parameter", "example_parameter"]:
                self.bot.error("Simple string not found: " + field_name)
        return ""

    async def send_message(self, channel, reply, *args):
        """Sends back a message/embed response."""
        content = None
        embed = None
        if isinstance(reply, dict):
            reply = copy.deepcopy(reply)
            reply = load_json.replace_in_object(reply, self.bot.command_prefix, *args)
            if "content" in reply:
                content = reply["content"]
            if "embed" in reply:
                embed = discord.Embed.from_dict(reply["embed"])
        else:
            content = load_json.replace_in_string(reply, self.bot.command_prefix, *args)
        return await channel.send(content, embed=embed)

    def find_reply(self, guild, replies, field_name, modules, command_name):
        language = "en"
        if guild:
            tosurnament_guild = self.bot.session.query(Guild).where(Guild.guild_id == guild.id).first()
            if tosurnament_guild and tosurnament_guild.language:
                language = tosurnament_guild.language
        return self.find_reply_recursive(language, replies, field_name, modules, command_name)

    def find_reply_recursive(self, language, replies, field_name, modules, command_name):
        reply = None
        if modules and modules[0] in replies:
            reply = self.find_reply_recursive(language, replies[modules[0]], field_name, modules[1:], command_name)
        if reply:
            return reply
        elif (
            language in replies and command_name in replies[language] and field_name in replies[language][command_name]
        ):
            return replies[language][command_name][field_name]
        elif "en" in replies and command_name in replies["en"] and field_name in replies["en"][command_name]:
            return replies["en"][command_name][field_name]
        elif "module" in replies:
            if language in replies["module"] and field_name in replies["module"][language]:
                return replies["module"][language][field_name]
            elif "en" in replies["module"] and field_name in replies["module"]["en"]:
                return replies["module"]["en"][field_name]
        return None

    async def send_reply(self, ctx, field_name, *args, channel=None, stack_depth=1):
        """Sends a reply found in the replies files."""
        module_name = self.get_module_name_from_stack(stack_depth)
        reply = self.find_reply(ctx.guild, self.bot.strings, field_name, module_name.split("."), ctx.command.name)
        if reply:
            if not channel:
                channel = ctx.channel
            return await self.send_message(channel, reply, *args)
        else:
            self.bot.error("Reply not found: " + ctx.command.cog_name + ": " + ctx.command.name + ": " + field_name)
        return None

    async def send_reply_in_bg_task(self, guild, channel, command_name, field_name, *args):
        """Sends a reply found in the replies files."""
        module_name = self.get_module_name_from_stack(1)
        reply = self.find_reply(guild, self.bot.strings, field_name, module_name.split("."), command_name)
        if reply:
            return await self.send_message(channel, reply, *args)
        else:
            self.bot.error("Reply not found: bg_task: " + command_name + ": " + field_name)
        return None

    async def send_usage(self, ctx):
        """Sends a usage reply found in the replies files."""
        command_string = self.bot.command_prefix + ctx.command.name
        reply = self.get_string(ctx, "usage") + ": `" + command_string
        parameters = self.get_string(ctx, "parameter", stack_depth=3)
        if parameters:
            reply += " " + parameters + "`"
            example = self.get_string(ctx, "example_parameter", stack_depth=3)
            if example:
                reply += "\n\n" + self.get_string(ctx, "example") + ": `" + command_string + " " + example + "`"
        else:
            reply += "`"
        usage_info = self.get_string(ctx, "usage_info", stack_depth=3)
        if usage_info:
            reply += "\n\n" + usage_info
        if reply:
            return await self.send_message(ctx, reply)
        return None

    async def show_object_settings(self, ctx, obj, stack_depth=1):
        """Shows the object settings."""
        output = self.get_string(ctx, "title", stack_depth=stack_depth)
        for key, value in obj.get_table_dict().items():
            value = str(value)
            if not value:
                value = self.get_string(ctx, "undefined")
            output += "__" + key + "__: `" + value + "`\n"
        await ctx.send(output)

    async def cog_command_error(self, ctx, error):
        await self.on_cog_command_error(ctx, error)

    async def on_cog_command_error(self, ctx, error, channel=None):
        if not channel:
            channel = ctx.channel
        self.bot.info_exception(error)
        if isinstance(error, commands.MissingRequiredArgument):
            await self.send_usage(ctx)
        elif isinstance(error, commands.BadArgument):
            await self.send_usage(ctx)
        elif isinstance(error, commands.UserInputError):
            await self.send_usage(ctx)
        elif isinstance(error, commands.NoPrivateMessage):
            await self.send_reply(ctx, "not_on_a_server", channel=channel)
        elif isinstance(error, commands.DisabledCommand):
            await self.send_reply(ctx, "disabled_command", channel=channel)
        elif isinstance(error, commands.BotMissingPermissions):
            for missing_permission in error.missing_perms:
                if missing_permission == "manage_nicknames":
                    await self.send_reply(ctx, "change_nickname_forbidden", channel=channel)
                    return True
                elif missing_permission == "manage_roles":
                    await self.send_reply(ctx, "change_role_forbidden", channel=channel)
                    return True
            return False
        elif isinstance(error, discord.Forbidden):
            if error.code == 50007:
                await self.send_reply(ctx, "restricted_dm", channel=channel)
                return True
            elif error.code == 50013:
                dm_channel = await ctx.author.create_dm()
                await self.send_reply(ctx, "lack_permission", channel=dm_channel)
            return False
        elif isinstance(error, UnknownError):
            await self.send_reply(ctx, "unknown_error", channel=channel)
        elif isinstance(error, NotGuildOwner):
            await self.send_reply(ctx, "not_guild_owner", channel=channel)
        elif isinstance(error, NotBotAdmin):
            await self.send_reply(ctx, "no_rights", channel=channel)
        elif isinstance(error, InvalidRoleName):
            await self.send_reply(ctx, "invalid_role_name", error.role_name, channel=channel)
        elif isinstance(error, RoleDoesNotExist):
            await self.send_reply(ctx, "role_does_not_exist", error.role, channel=channel)
        elif isinstance(error, NotRequiredRole):
            await self.send_reply(ctx, "not_required_role", error.role, channel=channel)
        elif isinstance(error, UserNotFound):
            await self.send_reply(ctx, "user_not_found", error.username, channel=channel)
        elif isinstance(error, UserNotLinked):
            await self.send_reply(ctx, "not_linked", channel=channel)
        elif isinstance(error, UserNotVerified):
            await self.send_reply(ctx, "not_verified", channel=channel)
        elif isinstance(error, OsuError):
            await self.send_reply(ctx, "osu_error", channel=channel)
        elif isinstance(error, commands.CommandInvokeError):
            return await self.on_cog_command_error(ctx, error.original, channel=channel)
        else:
            return False
        return True


def is_guild_owner():
    """Check function to know if the author is the guild owner."""

    async def predicate(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if ctx.guild.owner != ctx.author:
            raise NotGuildOwner()
        return True

    return commands.check(predicate)


def get_role(roles, role_id=None, role_name=None):
    """Gets a role from its id or name."""
    for role in roles:
        if role_id and role.id == role_id:
            return role
        if role_name and role.name == role_name:
            return role
    return None
