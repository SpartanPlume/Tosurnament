"""Base for message tables"""

import functools
from discord.ext import commands
from common.api.spreadsheet import spreadsheet

from encrypted_mysqldb.table import Table
from encrypted_mysqldb.fields import HashField, BoolField, DatetimeField


class BaseMessage(Table):
    """Base message class"""

    message_id = HashField()
    created_at = DatetimeField()
    updated_at = DatetimeField()


class BaseLockMessage(BaseMessage):
    """Base lock message class"""

    locked = BoolField()


class BaseAuthorLockMessage(BaseLockMessage):
    """Base author lock message class"""

    author_id = HashField()


def with_corresponding_message(message_cls):
    def decorator_with_corresponding_message(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            session = args[0].bot.session
            ctx = args[1]
            message_query = session.query(message_cls).where(message_cls.message_id == ctx.message.id)
            if issubclass(message_cls, BaseAuthorLockMessage):
                message_query.where(message_cls.author_id == ctx.author.id)
            message_obj = message_query.first()
            if not message_obj:
                return
            if isinstance(message_obj, BaseLockMessage):
                if message_obj.locked:
                    return
                message_obj.locked = True
                session.update(message_obj)
            await func(*args, message_obj, **kwargs)
            if message_obj.id > 0 and isinstance(message_obj, BaseLockMessage):
                message_obj.locked = False
                session.update(message_obj)

        return wrapper

    return decorator_with_corresponding_message


class ReactionCommand:
    def __init__(self, cog_name="", name=""):
        self.cog_name = cog_name
        self.name = name


def on_raw_reaction_with_context(reaction_type, valid_emojis=[]):
    def with_context(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            bot = args[0].bot
            payload = args[1]
            if not payload.guild_id:
                return
            if valid_emojis and payload.emoji.name not in valid_emojis:
                return
            channel = bot.get_channel(int(payload.channel_id))
            guild = channel.guild
            user = guild.get_member(int(payload.user_id))
            if not user or user.bot:
                return
            message = await channel.fetch_message(int(payload.message_id))
            ctx = commands.Context(
                bot=bot,
                channel=channel,
                guild=guild,
                message=message,
                prefix=bot.command_prefix,
                command=ReactionCommand(),
            )
            # Author needs to be changed after creation as it reassigns it during creation
            ctx.author = user
            ctx.command.cog_name = args[0].qualified_name
            ctx.command.name = func.__name__
            await func(args[0], ctx, payload.emoji)
            spreadsheet.Spreadsheet.pickle_from_id.cache_clear()

        return commands.Cog.listener("on_raw_reaction_" + reaction_type)(wrapper)

    return with_context
