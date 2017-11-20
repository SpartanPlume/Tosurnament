"""Primary fonctions of the bot"""

import importlib
import logging
import os
import discord
import sqlalchemy
import api.spreadsheet
from databases.base import Base

MODULES_DIR = "modules"

class SelfBotClient(discord.Client):
    """Child of discord.Client to simplify event management"""

    def __init__(self):
        super(SelfBotClient, self).__init__()
        self.prefix = '::'
        self.session = None
        self.init_logger()
        self.init_modules()
        self.init_db()
        api.spreadsheet.start_service()
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
        self.modules = {}
        for filename in os.listdir(MODULES_DIR):
            if filename != "module.py" and filename.endswith(".py"):
                module_file = importlib.import_module(MODULES_DIR + "." + filename[:-3])
                module = module_file.Module(self)
                self.modules[module.prefix] = module

    def init_db(self):
        """Initializes the database"""
        engine = sqlalchemy.create_engine('sqlite:///:memory:', echo=True)
        Base.metadata.create_all(engine, checkfirst=True)
        Session = sqlalchemy.orm.sessionmaker(bind=engine)
        self.session = Session()

    def log(self, level, message):
        """Uses to log message"""
        self.logger.log(level, "SelfBot: %s", message, extra={})

    async def on_message(self, message):
        """Gets message written by any user"""
        content = message.content
        if content.startswith(self.prefix):
            print(content)
            content = content[len(self.prefix):]
            for module_prefix, module in self.modules.items():
                if content.startswith(module_prefix):
                    channel, text, embed = await module.on_message(message, content[len(module_prefix):])
                    if not message.channel.is_private:
                        await self.delete_message(message)
                    await self.send_message(channel, content=text, embed=embed)
                    return
