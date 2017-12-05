"""Module for all Tosurnament related commands"""

import collections
import secrets
import requests
import discord
import modules.module
import api.osu
import api.spreadsheet
import helpers.crypt
import helpers.load_json
from databases.user import User
from databases.tournament import Tournament

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
            "create_tournament": self.create_tournament,
            "set_admin_role": self.set_admin_role,
            "register": self.register
        }
        self.help_messages = collections.OrderedDict([])
        command_strings = self.client.strings[self.name]
        for key, value in command_strings.items():
            self.help_messages[key] = (value["parameter"], value["help"])

    async def link(self, message, parameter):
        """Sends a private message to the command runner to link his account"""
        discord_id = message.author.id
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        user = helpers.crypt.decrypt_obj(user)
        if user:
            if user.verified:
                return (message.channel, self.get_string("link", "already_verified", self.client.prefix, self.prefix), None)
        if parameter == "":
            return (message.channel, self.get_string("link", "usage", self.client.prefix, self.prefix), None)
        osu_name = api.osu.User.get_from_string(parameter)
        osu_users = api.osu.OsuApi.get_user(osu_name)
        if not osu_users:
            return (message.channel, self.get_string("link", "user_not_found", osu_name), None)
        osu_id = osu_users[0][api.osu.User.ID]
        code = secrets.token_urlsafe(16)
        if not user:
            user = User(discord_id=discord_id, osu_id=osu_id, verified=False, code=code)
            self.client.session.add(helpers.crypt.encrypt_obj(user))
        else:
            user.osu_id = osu_id
            user.code = code
        self.client.session.commit()
        return (message.author, self.get_string("link", "success", code, self.client.prefix, self.prefix), None)

    async def auth(self, message, parameter):
        """Sends a private message to the command runner to auth his account"""
        discord_id = message.author.id
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        user = helpers.crypt.decrypt_obj(user)
        if not user:
            return (message.channel, self.get_string("auth", "not_linked", self.client.prefix, self.prefix), None)
        if user.verified:
            return (message.channel, self.get_string("auth", "already_verified", self.client.prefix, self.prefix), None)
        osu_id = user.osu_id
        request = requests.get("https://osu.ppy.sh/u/" + osu_id)
        if request.status_code != 200:
            return (message.author, self.get_string("auth", "osu_error"), None)
        index = 0
        try:
            to_find = "<div title='Location'><i class='icon-map-marker'></i><div>"
            index = request.text.index(to_find)
            index += len(to_find)
        except ValueError:
            return (message.author, self.get_string("auth", "osu_error"), None)
        location = request.text[index:]
        location = location.split("</div>", 1)[0]
        if location != user.code:
            return (message.author, self.get_string("auth", "wrong_code", self.client.prefix, self.prefix), None)
        else:
            user.verified = True
            user = helpers.crypt.encrypt_obj(user)
            self.client.session.commit()
        return (message.author, self.get_string("auth", "success"), None)

    async def create_tournament(self, message, parameter):
        """Create a tournament"""
        parameters = parameter.split(" ", 1)
        if len(parameters) < 2:
            return (message.channel, self.get_string("create_tournament", "usage", self.client.prefix, self.prefix), None)
        if not message.server:
            return (message.channel, self.get_string("create_tournament", "not_on_a_server"), None)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(message.server.id)).filter(Tournament.acronym == parameters[0]).first()
        if tournament:
            return (message.channel, self.get_string("create_tournament", "acronym_used"), None)
        tournament = Tournament(server_id=message.server.id, acronym=parameters[0], name=parameters[1])
        self.client.session.add(helpers.crypt.encrypt_obj(tournament))
        self.client.session.commit()
        return (message.channel, self.get_string("create_tournament", "success"), None)

    async def set_admin_role(self, message, parameter):
        """Set the admin role"""
        if not message.server:
            return (message.channel, self.get_string("set_admin_role", "not_on_a_server"), None)
        if len(message.role_mentions) == 1:
            tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(message.server.id)).first()
            if not tournament:
                return (message.channel, self.get_string("set_admin_role", "no_tournament", self.client.prefix, self.prefix), None)
            tournament = helpers.crypt.decrypt_obj(tournament)
            tournament.admin_role_id = message.role_mentions[0].id
            tournament = helpers.crypt.encrypt_obj(tournament)
            self.client.session.commit()
        else:
            return (message.channel, self.get_string("set_admin_role", "usage", self.client.prefix, self.prefix), None)
        return (message.channel, self.get_string("set_admin_role", "success"), None)

    async def register(self, message, parameter):
        """Registers a player"""
        if not message.server:
            return (message.channel, self.get_string("register", "not_on_a_server"), None)
        discord_id = message.author.id
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        user = helpers.crypt.decrypt_obj(user)
        if not user:
            return (message.channel, self.get_string("register", "not_linked", self.client.prefix, self.prefix), None)
        if not user.verified:
            return (message.channel, self.get_string("register", "not_verified", self.client.prefix, self.prefix), None)
        osu_id = user.osu_id
        osu_users = api.osu.OsuApi.get_user(osu_id)
        if not osu_users:
            return (message.channel, self.get_string("register", "osu_error"), None)
        osu_name = osu_users[0][api.osu.User.NAME]
        try:
            await self.client.change_nickname(message.author, osu_name)
        except discord.Forbidden:
            return (message.channel, self.get_string("register", "change_nickname_forbidden"), None)
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
                                return (message.channel, self.get_string("register", "change_role_forbidden", "Player"), None)
                            return (message.channel, self.get_string("register", "success"), None)
                    return (message.channel, self.get_string("register", "no_player_role"), None)
        return (message.channel, self.get_string("register", "not_a_player"), None)
