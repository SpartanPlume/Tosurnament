"""Module for all Tosurnament related commands"""

import collections
import secrets
import requests
import discord
import modules.module
import api.osu
import api.spreadsheet
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
            "auth": self.auth
        }
        self.help_messages = collections.OrderedDict([
            ("link", ("<username>", "Links your osu! account to your discord account")),
            ("auth", ("", "Links your osu! account to your discord account"))
        ])

    async def link(self, message, parameter):
        """Sends a private message to the command runner to link his account"""
        discord_id = message.author.id
        user = self.client.session.query(User).filter(User.discord_id == discord_id).first()
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
        else:
            user.osu_id = osu_id
            user.code = code
        self.client.session.add(user)
        self.client.session.commit()
        code = user.code
        text = "Please authenticate your osu! account by setting the following code\n"
        text += code + "\n"
        text += "as your location on your osu! profile.\n"
        text += "Once done, send the `" + self.client.prefix + self.prefix
        text += "auth` command."
        return (message.author, text, None)

    async def auth(self, message, parameter):
        """Sends a private message to the command runner to auth his account"""
        discord_id = message.author.id
        user = self.client.session.query(User).filter(User.discord_id == discord_id).first()
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
            self.client.session.commit()
            text = "Congrats, your account has been verified."
        return (message.author, text, None)
