"""Base for message tables"""

import functools
from discord.ext import commands
from mysqldb_wrapper import Base, Id
from common.api.spreadsheet import spreadsheet
from mysqldb_wrapper import crypt


class BaseMessage(Base):
    """Base message class"""

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.id = Id()
        cls.message_id = bytes()
        cls.created_at = int()
        cls.updated_at = int()


class BaseLockMessage(BaseMessage):
    """Base lock message class"""

    __tablename__ = ""

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.locked = bool()


class BaseAuthorLockMessage(BaseLockMessage):
    """Base author lock message class"""

    __tablename__ = ""

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.author_id = bytes()


def with_corresponding_message(message_cls):
    def decorator_with_corresponding_message(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            session = args[0].bot.session
            ctx = args[1]
            message_obj = session.query(message_cls).where(message_cls.message_id == ctx.message.id).first()
            if not message_obj:
                return
            if (
                isinstance(message_obj, BaseAuthorLockMessage)
                and crypt.hash_value(ctx.author.id) != message_obj.author_id
            ):
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
            channel = bot.get_channel(payload.channel_id)
            guild = channel.guild
            user = guild.get_member(payload.user_id)
            if not user or user.bot:
                return
            message = await channel.fetch_message(payload.message_id)
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
