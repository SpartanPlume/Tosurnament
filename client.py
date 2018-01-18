"""Primary fonctions of the bot"""

import importlib
import logging
import os
import sys
import discord
from discord.ext import commands
import sqlalchemy
import api.spreadsheet
import helpers.load_json
import helpers.crypt
from databases.base import Base
from databases.reschedule_message import RescheduleMessage

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
        #self.init_logger()
        self.init_ressources()
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
        for filename in os.listdir(MODULES_DIR):
            if filename != "module.py" and filename.endswith(".py"):
                try:
                    self.load_extension(MODULES_DIR + "." + filename[:-3])
                except discord.errors.ClientException:
                    print("The module " + filename + " could not be loaded.")

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

    async def on_raw_reaction_add(self, emoji, message_id, channel_id, user_id):
        """Called every added reaction"""
        channel = self.get_channel(channel_id)
        guild = channel.guild
        user = guild.get_member(user_id)
        reschedule_message = self.session.query(RescheduleMessage).filter(RescheduleMessage.message_id == helpers.crypt.hash_str(str(message_id))).first()
        if not reschedule_message:
            return
        ally_role = None
        if str(user.id) == reschedule_message.enemy_user_id:
            ally_role = guild.get_member(reschedule_message.ally_user_id)
        elif any(reschedule_message.enemy_role_id == str(role.id) for role in user.roles):
            for role in user.roles:
                if reschedule_message.enemy_role_id == str(role.id):
                    ally_role = role
        if ally_role:
            if emoji.name == "👍":
                await channel.send(helpers.load_json.replace_in_string(self.strings["tosurnament"]["reschedule"]["accepted"], ally_role.mention))
                self.session.delete(reschedule_message)
                self.session.commit()
            elif emoji.name == "👎":
                await channel.send(helpers.load_json.replace_in_string(self.strings["tosurnament"]["reschedule"]["refused"], ally_role.mention))
                self.session.delete(reschedule_message)
                self.session.commit()
