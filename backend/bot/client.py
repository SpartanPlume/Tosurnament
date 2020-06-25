"""Primary fonctions of the bot"""

import importlib
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import datetime
import asyncio
import discord
from discord.ext import commands
import MySQLdb
from mysqldb_wrapper import Session
from common.utils import load_json
from common.config import constants
from common.api import spreadsheet

MODULES_DIR = "bot/modules"


async def add_command_feedback(ctx):
    """Adds a :white_check_mark: reaction to any command."""
    await ctx.message.add_reaction("✅")


class Client(commands.Bot):
    """Child of discord.Client to simplify event management"""

    def __init__(self):
        super(Client, self).__init__(command_prefix=";")
        self.owner_id = constants.BOT_OWNER_ID
        self.error_code = 0
        self.modules = []
        self.init_logger()
        self.init_ressources()
        self.init_modules()
        self.init_db()
        self.init_spreadsheet_service()
        self.init_background_tasks()
        if self.error_code != 0:
            return
        self.before_invoke(add_command_feedback)
        self.log(logging.INFO, "Bot is ready!")
        print("Ready!")

    def init_logger(self):
        """Initializes the logger"""
        self.handler = TimedRotatingFileHandler(
            filename="log/bot.log", when="W1", utc=True, backupCount=4, atTime=datetime.time(hour=12),
        )
        self.handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s: %(message)s"))
        self.logger = logging.getLogger("bot")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.handler)

        discord_logger = logging.getLogger("discord")
        discord_logger.setLevel(logging.INFO)
        discord_logger.addHandler(self.handler)

    def init_ressources(self):
        """Initializes all ressources"""
        self.strings = load_json.load_directory("bot/replies")
        self.strings = load_json.replace_placeholders(self.strings)

    def init_modules(self):
        """Initializes all modules"""
        for root, _, files in os.walk(MODULES_DIR):
            for filename in files:
                if filename != "module.py" and filename.endswith(".py"):
                    module_name = root.replace("/", ".") + "." + filename[:-3]
                    try:
                        self.load_extension(module_name)
                        module_file = importlib.import_module(module_name)
                        module = module_file.get_class(self)
                        self.modules.append(module)
                        print("Module " + filename + " loaded")
                    except discord.errors.ClientException:
                        print("The module " + filename + " could not be loaded.")
                    except AttributeError:
                        print("The module " + filename + " could not be added to the modules list.")

    def init_db(self):
        """Initializes the database"""
        try:
            self.session = Session(
                constants.DB_USERNAME, constants.DB_PASSWORD, constants.DB_NAME, constants.ENCRYPTION_KEY, self.handler,
            )
        except MySQLdb._exceptions.OperationalError:
            print("ERROR: Couldn't initialize the db session. Is the mysql service started ?")
            self.error_code = 2

    def init_spreadsheet_service(self):
        """Initializes the connection to the Google Spreadsheet API."""
        spreadsheet.start_service()

    def log(self, level, message):
        """Uses to log message"""
        self.logger.log(level, "%s", message, extra={})

    async def on_command(self, ctx):
        """Logs the command used"""
        command = "COMMAND: "
        if ctx.cog:
            command += type(ctx.cog).__name__ + ": "
        command += str(ctx.command)
        self.log(logging.INFO, command)

    async def on_command_error(self, ctx, error):
        """Logs the error"""
        command = "COMMAND: "
        if ctx.cog:
            command += type(ctx.cog).__name__ + ": "
        command += str(ctx.command) + ": "
        command += type(error).__name__
        self.log(logging.INFO, command)

    async def stop(self, code, ctx=None):
        """Stops the bot"""
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                self.log(logging.DEBUG, "Background task cancelled.")
        self.error_code = code
        if ctx and ctx.guild:
            await ctx.message.delete()
        self.log(logging.INFO, "Closing the bot...\n")
        await self.close()

    def init_background_tasks(self):
        self.tasks = []
        for module in self.modules:
            if hasattr(module, "background_task"):
                module.background_task()

    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id:
            return
        channel = self.get_channel(payload.channel_id)
        guild = channel.guild
        user = guild.get_member(payload.user_id)
        if user.bot:
            return
        for module in self.modules:
            if hasattr(module, "on_raw_reaction_add"):
                await module.on_raw_reaction_add(payload.message_id, payload.emoji, guild, channel, user)

    async def on_raw_reaction_remove(self, payload):
        if not payload.guild_id:
            return
        channel = self.get_channel(payload.channel_id)
        guild = channel.guild
        user = guild.get_member(payload.user_id)
        if user.bot:
            return
        for module in self.modules:
            if hasattr(module, "on_raw_reaction_remove"):
                await module.on_raw_reaction_remove(payload.message_id, payload.emoji, guild, channel, user)

    async def on_member_join(self, member):
        try:
            self.get_verified_user(member.id)
        except Exception:
            return
        await self.on_verified_user(member.guild, member)

    async def on_verified_user(self, guild, user):
        for module in self.modules:
            if hasattr(module, "on_verified_user"):
                try:
                    await module.on_verified_user(guild, user)
                except Exception:
                    continue
