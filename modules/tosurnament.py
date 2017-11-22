"""Module for all Tosurnament related commands"""

import collections
import secrets
import requests
import discord
import modules.module
import api.osu
import api.spreadsheet
import helpers.crypt
from databases.user import User

EMBED_COLOUR = 3447003

class Module(modules.module.BaseModule):
    """Class that contains commands to use"""

    def __init__(self, client):
        super(Module, self).__init__(client)
        self.prefix = ""
        self.name = "tosurnament"
        self.commands = {
            "help": self.help,
            "link": self.link,
            "auth": self.auth,
            "register": self.register
        }
        self.help_messages = collections.OrderedDict([
            ("link", ("<username>", "Links your osu! account to your discord account")),
            ("auth", ("", "Links your osu! account to your discord account")),
            ("register", ("", "Registers you and gives you the `Player` role on discord (if you're on the player list)"))
        ])

    async def link(self, message, parameter):
        """Sends a private message to the command runner to link his account"""
        discord_id = message.author.id
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        user = helpers.crypt.decrypt_obj(user)
        if user:
            if user.verified:
                text = "Your account is already verified. Maybe you wanted to use the `"
                text += self.client.prefix + self.prefix + "register` command ?"
                return (message.channel, text, None)
        if parameter == "":
            text = "Usage: " + self.client.prefix + self.prefix + "link"
            text += " " + self.help_messages["link"][0]
            return (message.channel, text, None)
        osu_name = api.osu.User.get_from_string(parameter)
        osu_users = api.osu.OsuApi.get_user(osu_name)
        if not osu_users:
            text = "User `" + osu_name + "` not found."
            return (message.channel, text, None)
        osu_id = osu_users[0][api.osu.User.ID]
        code = secrets.token_urlsafe(16)
        if not user:
            user = User(discord_id=discord_id, osu_id=osu_id, verified=False, code=code)
            self.client.session.add(helpers.crypt.encrypt_obj(user))
        else:
            user.osu_id = osu_id
            user.code = code
        self.client.session.commit()
        text = "Please authenticate your osu! account by setting the following code\n"
        text += code + "\n"
        text += "as your location on your osu! profile.\n"
        text += "Once done, send the `" + self.client.prefix + self.prefix
        text += "auth` command."
        return (message.author, text, None)

    async def auth(self, message, parameter):
        """Sends a private message to the command runner to auth his account"""
        discord_id = message.author.id
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        user = helpers.crypt.decrypt_obj(user)
        if not user:
            text = "Your account is not linked. Please run the `"
            text += self.client.prefix + self.prefix + "link` command."
            return (message.channel, text, None)
        if user.verified:
            text = "Your account is already verified. Maybe you wanted to use the `"
            text += self.client.prefix + self.prefix + "register` command ?"
            return (message.channel, text, None)
        osu_id = user.osu_id
        request = requests.get("https://osu.ppy.sh/u/" + osu_id)
        if request.status_code != 200:
            text = "Oops. An error has occured. Please retry again later."
            text += "If the problem persists, contact me at spartan.plume@gmail.com"
            return (message.author, text, None)
        index = 0
        try:
            to_find = "<div title='Location'><i class='icon-map-marker'></i><div>"
            index = request.text.index(to_find)
            index += len(to_find)
        except ValueError:
            text = "Oops. An error has occured. Please retry again later."
            text += "If the problem persists, contact me at spartan.plume@gmail.com"
            return (message.author, text, None)
        location = request.text[index:]
        location = location.split("</div>", 1)[0]
        if location != user.code:
            text = "Your location is not your given code."
            text += " If you forgot your code or did a mistake in your username,"
            text += " please reuse the `" + self.client.prefix + self.prefix + "link` command."
        else:
            user.verified = True
            user = helpers.crypt.encrypt_obj(user)
            self.client.session.commit()
            text = "Congrats, your account has been verified."
        return (message.author, text, None)

    async def register(self, message, parameter):
        """Registers a player"""
        if not message.server:
            text = "This command can only be ran on a server."
            return (message.channel, text, None)
        discord_id = message.author.id
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        user = helpers.crypt.decrypt_obj(user)
        if not user:
            text = "Your account is not linked. Please run the `"
            text += self.client.prefix + self.prefix + "link` command."
            return (message.channel, text, None)
        if not user.verified:
            text = "Your account is not verified. Please run the `"
            text += self.client.prefix + self.prefix + "auth` command."
            return (message.channel, text, None)
        osu_id = user.osu_id
        osu_users = api.osu.OsuApi.get_user(osu_id)
        if not osu_users:
            text = "Oops, something went wrong, retry again later."
            return (message.channel, text, None)
        osu_name = osu_users[0][api.osu.User.NAME]
        try:
            await self.client.change_nickname(message.author, osu_name)
        except discord.Forbidden:
            text = "Sorry, I can't change your nickname. Either you have better rights than the bot"
            text += " or the bot doesn't have the `Change nicknames` right."
            text += " Please contact an admin."
            return (message.channel, text, None)
        players = api.spreadsheet.get_range("1xRkVAPECBrH_alxfuBAhjXVjIzO0bk6CWd7P8Ch4P5k", "A2:A")
        for player_row in players:
            for player in player_row:
                if osu_name == player:
                    roles = message.server.roles
                    for role in roles:
                        if role.name == "Player":
                            try:
                                self.client.add_roles(message.author, role)
                            except discord.Forbidden:
                                text = "Sorry, I can't add you the `Player` role, you have better rights than the bot."
                                return (message.channel, text, None)
                            text = "You're now registered. Congrats !"
                            return (message.channel, text, None)
                    text = "There's no `Player` role. Ask an admin to create it."
                    return (message.channel, text, None)
        text = "You're not on the player list. I can't register you. ='("
        return (message.channel, text, None)
