"""Primary fonctions of the bot"""

import inspect
import importlib
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import datetime
import discord
from discord.ext import commands
from cryptography.fernet import Fernet
from encrypted_mysqldb.database import Database
from encrypted_mysqldb.errors import DatabaseInitializationError
from common.utils import load_json
from common.config import constants
from common.api.spreadsheet import spreadsheet

MODULES_DIR = "bot/modules"


async def add_command_feedback(ctx):
    """Adds a :white_check_mark: reaction to any command."""
    try:
        await ctx.message.add_reaction("⏲️")
    except Exception:
        return


class Client(commands.Bot):
    """Child of discord.Client to simplify event management"""

    def __init__(self, intents=discord.Intents.default()):
        super(Client, self).__init__(command_prefix=constants.COMMAND_PREFIX, intents=intents)
        self.owner_id = int(constants.BOT_OWNER_ID)
        self.error_code = 0
        self.modules = []
        self.tasks = []
        self.init_logger()
        self.init_ressources()
        self.init_db()
        self.init_spreadsheet_service()
        # self.init_background_tasks()
        self.init_available_languages()
        if self.error_code != 0:
            return
        self.before_invoke(add_command_feedback)
        self.info("Bot is ready!")
        print("Ready!")

    async def setup_hook(self):
        await self.init_modules()

    def init_logger(self):
        """Initializes the logger"""
        if not os.path.exists("logs"):
            os.mkdir("logs")
        self.handler = TimedRotatingFileHandler(
            filename="logs/bot.log",
            when="W1",
            utc=True,
            backupCount=4,
            atTime=datetime.time(hour=12),
        )
        self.handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s: %(message)s"))
        self.logger = logging.getLogger("bot")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.handler)

        discord_logger = logging.getLogger("discord")
        discord_logger.setLevel(logging.INFO)
        discord_logger.addHandler(self.handler)

        requests_logger = logging.getLogger("urllib3.connectionpool")
        requests_logger.setLevel(logging.DEBUG)
        requests_logger.addHandler(self.handler)
        requests_logger.propagate = True

    def init_ressources(self):
        """Initializes all ressources"""
        self.strings = load_json.load_directory("bot/replies")
        self.strings = load_json.replace_placeholders(self.strings)

    async def init_modules(self):
        """Initializes all modules"""
        for root, _, files in os.walk(MODULES_DIR):
            for filename in files:
                if filename != "module.py" and filename.endswith(".py"):
                    module_name = root.replace("/", ".") + "." + filename[:-3]
                    try:
                        await self.load_extension(module_name)
                        print("Module " + filename + " loaded")
                    except discord.errors.ClientException:
                        print("The module " + filename + " could not be loaded.")
                    except AttributeError:
                        print("The module " + filename + " could not be added to the modules list.")

    def init_db(self):
        """Initializes the database"""
        for root, _, files in os.walk("common/databases/tosurnament_message"):
            for filename in files:
                if filename.endswith(".py"):
                    importlib.import_module(root.replace("/", ".") + "." + filename[:-3])
        try:
            self.session = Database(
                constants.MYSQL_USER,
                constants.MYSQL_PASSWORD,
                constants.MYSQL_MESSAGE_DATABASE,
                Fernet(constants.ENCRYPTION_KEY),
                host=constants.MYSQL_HOST,
                pool_name="tosurnament_message_pool",
            )
        except DatabaseInitializationError:
            print("ERROR: Couldn't initialize the db session. Is the mysql service started ?")
            self.error_code = 2

    def init_spreadsheet_service(self):
        """Initializes the connection to the Google Spreadsheet API."""
        spreadsheet.start_service()

    def init_available_languages(self):
        """Initializes the list of available languages of the bot."""
        languages = set()
        for root, _, files in os.walk("bot/replies"):
            for filename in files:
                if filename.endswith(".json"):
                    languages.add(filename[:-5])
        self.languages = list(sorted(languages))

    def log(self, level, message, exc_info=False):
        """Logs message."""
        stack = inspect.stack()
        functions_to_ignore = ["debug", "info", "error", "info_exception", "on_cog_command_error", "cog_command_error"]
        index = 0
        while True:
            index += 1
            caller = inspect.getframeinfo(stack[index][0])
            if caller.function not in functions_to_ignore:
                break
        self.logger.log(
            level,
            "<%s:%d> - %s",
            os.path.basename(caller.filename),
            caller.lineno,
            message,
            extra={},
            exc_info=exc_info,
        )

    def debug(self, message):
        """Log debug message."""
        self.log(logging.DEBUG, message)

    def info(self, message):
        """Logs info message."""
        self.log(logging.INFO, message)

    def info_exception(self, error):
        """Logs info message."""
        self.log(logging.INFO, str(type(error)) + ": " + str(error))
        self.log(logging.INFO, error, exc_info=True)

    def error(self, message):
        """Logs error message."""
        self.log(logging.ERROR, message)

    async def on_command(self, ctx):
        """Logs the command used"""
        command = "COMMAND: "
        if ctx.cog:
            command += type(ctx.cog).__name__ + ": "
        command += str(ctx.command)
        self.info(command)

    async def on_command_completion(self, ctx):
        try:
            spreadsheet.Spreadsheet.pickle_from_id.cache_clear()
            await ctx.message.add_reaction("✅")
            await ctx.message.remove_reaction("⏲️", self.user)
        except Exception:
            return

    async def on_command_error(self, ctx, error):
        """Logs the error"""
        try:
            spreadsheet.Spreadsheet.pickle_from_id.cache_clear()
            if isinstance(error, commands.CommandNotFound):
                command_message = ctx.message.content.lstrip(self.command_prefix)
                if not command_message or not command_message[0].isalpha() or self.command_prefix in command_message:
                    return
            await ctx.message.add_reaction("❌")
            await ctx.message.remove_reaction("⏲️", self.user)
            if isinstance(error, commands.CommandNotFound):
                await ctx.send("Command not found. Please check the spelling.")
        except Exception:
            return
        command = "COMMAND: "
        if ctx.cog:
            command += type(ctx.cog).__name__ + ": "
        command += str(ctx.command) + ": "
        command += type(error).__name__
        self.info(command)

    async def stop(self, code, ctx=None):
        """Stops the bot"""
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except Exception:
                self.debug("Background task cancelled.")
        self.error_code = code
        if ctx and ctx.guild:
            try:
                await ctx.message.delete()
            except Exception:
                pass
        self.info("Closing the bot...\n")
        await self.close()

    def init_background_tasks(self):
        self.tasks = []
        for module in self.modules:
            if hasattr(module, "background_task"):
                module.background_task()

    async def on_member_join(self, member):
        try:
            self.get_verified_user(member.id)
        except Exception:
            return
        await self.on_verified_user(member.guild, member)

    async def on_verified_user(self, guild, user):
        # TODO
        return
        for module in self.modules:
            if hasattr(module, "on_verified_user"):
                try:
                    await module.on_verified_user(guild, user)
                except Exception:
                    continue
        spreadsheet.Spreadsheet.pickle_from_id.cache_clear()
