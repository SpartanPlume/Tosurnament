"""Primary fonctions of the bot"""

import importlib
import logging
import os
import constants
import challonge
import discord
from discord.ext import commands
import sqlalchemy
import api.spreadsheet
import helpers.load_json
import helpers.crypt
from databases.base import Base

MODULES_DIR = "modules"
engine = sqlalchemy.create_engine('sqlite:///tosurnament.db', echo=True)
Session = sqlalchemy.orm.sessionmaker(bind=engine)

class Client(commands.Bot):
    """Child of discord.Client to simplify event management"""

    def __init__(self):
        super(Client, self).__init__(command_prefix="::")
        self.session = None
        self.strings = None
        self.owner_id = 100648380174192640
        self.error_code = 0
        self.modules = []
        #self.init_logger()
        self.init_ressources()
        self.init_modules()
        self.init_db()
        api.spreadsheet.start_service()
        challonge.set_credentials(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY)
        print("Ready !")

    def init_logger(self):
        """Initializes the logger"""
        self.logger = logging.getLogger('discord')
        self.logger.setLevel(logging.DEBUG)
        self.handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
        self.handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.logger.addHandler(self.handler)

    def init_modules(self):
        """Initializes all modules"""
        for filename in os.listdir(MODULES_DIR):
            if filename != "module.py" and filename.endswith(".py"):
                try:
                    self.load_extension(MODULES_DIR + "." + filename[:-3])
                except discord.errors.ClientException:
                    print("The module " + filename + " could not be loaded.")
                module_file = importlib.import_module(MODULES_DIR + "." + filename[:-3])
                try:
                    module = module_file.get_class(self)
                    self.modules.append(module)
                except AttributeError:
                    print("The module " + filename + " could not be added to the modules list.")                    

    def init_ressources(self):
        """Initializes all ressources"""
        self.strings = helpers.load_json.open_file("strings.json")

    def init_db(self):
        """Initializes the database"""
        Base.metadata.create_all(engine, checkfirst=True)
        self.session = Session()

    def log(self, level, message):
        """Uses to log message"""
        self.logger.log(level, "SelfBot: %s", message, extra={})

    @sqlalchemy.event.listens_for(Session, "before_flush")
    def before_flush(session, context, instances):
        """Encrypts all dirty object before the flush"""
        for obj in session.new:
            obj = helpers.crypt.encrypt_obj(obj)
        for obj in session.dirty:
            obj = helpers.crypt.encrypt_obj(obj)

    async def stop(self, ctx, code):
        """Stops the bot"""
        self.error_code = code
        if ctx.guild:
            await ctx.message.delete()
        await self.logout()
