"""Module for all Tosurnament related commands"""

import collections
import secrets
import re
import requests
import discord
import modules.module
import api.osu
import api.spreadsheet
import helpers.crypt
import helpers.load_json
from databases.user import User
from databases.tournament import Tournament
from databases.players_spreadsheet import PlayersSpreadsheet

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
            "set_staff_channel": self.set_staff_channel,
            "set_admin_role": self.set_admin_role,
            "set_referee_role": self.set_referee_role,
            "set_player_role": self.set_player_role,
            "set_players_spreadsheet": self.set_players_spreadsheet,
            "register": self.register,
            "print_players": self.print_players
        }
        self.help_messages = collections.OrderedDict([])
        command_strings = self.client.strings[self.name]
        for key, value in command_strings.items():
            self.help_messages[key] = (value["parameter"], value["help"])

    async def link(self, message, parameter):
        """Sends a private message to the command runner to link his account"""
        discord_id = message.author.id
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
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
            self.client.session.add(user)
        else:
            user.osu_id = osu_id
            user.code = code
        self.client.session.commit()
        return (message.author, self.get_string("link", "success", code, self.client.prefix, self.prefix), None)

    async def auth(self, message, parameter):
        """Sends a private message to the command runner to auth his account"""
        discord_id = message.author.id
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
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
            self.client.session.commit()
        return (message.author, self.get_string("auth", "success"), None)

    async def create_tournament(self, message, parameter):
        """Create a tournament"""
        parameters = parameter.split(" ", 1)
        if len(parameters) < 2:
            return (message.channel, self.get_string("create_tournament", "usage", self.client.prefix, self.prefix), None)
        if not message.server:
            return (message.channel, self.get_string("create_tournament", "not_on_a_server"), None)
        if message.server.owner != message.author:
            return (message.channel, self.get_string("create_tournament", "not_owner"), None)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(message.server.id)).filter(Tournament.acronym == parameters[0]).first()
        if tournament:
            return (message.channel, self.get_string("create_tournament", "acronym_used"), None)
        tournament = Tournament(server_id=message.server.id, acronym=parameters[0], name=parameters[1])
        self.client.session.add(tournament)
        self.client.session.commit()
        return (message.channel, self.get_string("create_tournament", "success"), None)

    async def set_staff_channel(self, message, parameter):
        """Set the staff channel"""
        if not message.server:
            return (message.channel, self.get_string("set_staff_channel", "not_on_a_server"), None)
        if len(message.channel_mentions) == 1:
            tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(message.server.id)).first()
            if not tournament:
                return (message.channel, self.get_string("set_staff_channel", "no_tournament", self.client.prefix, self.prefix), None)
            if not tournament.admin_role_id and message.server.owner != message.author:
                return (message.channel, self.get_string("set_staff_channel", "no_rights", self.client.prefix, self.prefix), None)
            if message.server.owner != message.author and not any(role.id == tournament.admin_role_id for role in message.author.roles):
                return (message.channel, self.get_string("set_staff_channel", "no_rights", self.client.prefix, self.prefix), None)
            tournament.staff_channel_id = message.channel_mentions[0].id
            self.client.session.commit()
        else:
            return (message.channel, self.get_string("set_staff_channel", "usage", self.client.prefix, self.prefix), None)
        return (message.channel, self.get_string("set_staff_channel", "success"), None)

    async def set_admin_role(self, message, parameter):
        """Set the admin role"""
        if not message.server:
            return (message.channel, self.get_string("set_admin_role", "not_on_a_server"), None)
        if message.server.owner != message.author:
            return (message.channel, self.get_string("set_admin_role", "not_owner"), None)
        if len(message.role_mentions) == 1:
            tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(message.server.id)).first()
            if not tournament:
                return (message.channel, self.get_string("set_admin_role", "no_tournament", self.client.prefix, self.prefix), None)
            tournament.admin_role_id = message.role_mentions[0].id
            self.client.session.commit()
        else:
            return (message.channel, self.get_string("set_admin_role", "usage", self.client.prefix, self.prefix), None)
        return (message.channel, self.get_string("set_admin_role", "success"), None)

    async def set_referee_role(self, message, parameter):
        """Set the referee role"""
        if not message.server:
            return (message.channel, self.get_string("set_referee_role", "not_on_a_server"), None)
        if len(message.role_mentions) == 1:
            tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(message.server.id)).first()
            if not tournament:
                return (message.channel, self.get_string("set_referee_role", "no_tournament", self.client.prefix, self.prefix), None)
            if not tournament.admin_role_id and message.server.owner != message.author:
                return (message.channel, self.get_string("set_referee_role", "no_rights", self.client.prefix, self.prefix), None)
            if message.server.owner != message.author and not any(role.id == tournament.admin_role_id for role in message.author.roles):
                return (message.channel, self.get_string("set_referee_role", "no_rights", self.client.prefix, self.prefix), None)
            tournament.player_referee_id = message.role_mentions[0].id
            self.client.session.commit()
        else:
            return (message.channel, self.get_string("set_referee_role", "usage", self.client.prefix, self.prefix), None)
        return (message.channel, self.get_string("set_referee_role", "success"), None)

    async def set_player_role(self, message, parameter):
        """Set the player role"""
        if not message.server:
            return (message.channel, self.get_string("set_player_role", "not_on_a_server"), None)
        if len(message.role_mentions) == 1:
            tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(message.server.id)).first()
            if not tournament:
                return (message.channel, self.get_string("set_player_role", "no_tournament", self.client.prefix, self.prefix), None)
            if not tournament.admin_role_id and message.server.owner != message.author:
                return (message.channel, self.get_string("set_player_role", "no_rights", self.client.prefix, self.prefix), None)
            if message.server.owner != message.author and not any(role.id == tournament.admin_role_id for role in message.author.roles):
                return (message.channel, self.get_string("set_player_role", "no_rights", self.client.prefix, self.prefix), None)
            tournament.player_role_id = message.role_mentions[0].id
            self.client.session.commit()
        else:
            return (message.channel, self.get_string("set_player_role", "usage", self.client.prefix, self.prefix), None)
        return (message.channel, self.get_string("set_player_role", "success"), None)    

    async def set_players_spreadsheet(self, message, parameter):
        """Sets the players spreadsheet"""
        if not message.server:
            return (message.channel, self.get_string("set_players_spreadsheet", "not_on_a_server"), None)
        parameters = parameter.split(" ")
        if len(parameters) != 6:
            return (message.channel, self.get_string("set_players_spreadsheet", "usage", self.client.prefix, self.prefix), None)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(message.server.id)).first()
        if not tournament:
            return (message.channel, self.get_string("set_players_spreadsheet", "no_tournament", self.client.prefix, self.prefix), None)
        if tournament.players_spreadsheet_id:
            players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == tournament.players_spreadsheet_id).first()
        else:
            players_spreadsheet = PlayersSpreadsheet()
            self.client.session.add(players_spreadsheet)
        players_spreadsheet.spreadsheet_id = parameters[0]
        players_spreadsheet.range_team_name = parameters[1]
        players_spreadsheet.range_team = parameters[2]
        regex = re.compile(re.escape("n"), re.IGNORECASE)
        try:
            eval(regex.sub("1", parameters[3]))
            eval(regex.sub("1", parameters[4]))
        except NameError:
            return (message.channel, self.get_string("set_players_spreadsheet", "usage", self.client.prefix, self.prefix), None)
        players_spreadsheet.incr_column = parameters[3]
        players_spreadsheet.incr_row = parameters[4]
        try:
            players_spreadsheet.n_team = int(parameters[5])
        except ValueError:
            return (message.channel, self.get_string("set_players_spreadsheet", "usage", self.client.prefix, self.prefix), None)
        self.client.session.commit()
        tournament.players_spreadsheet_id = players_spreadsheet.id
        self.client.session.commit()
        return (message.channel, self.get_string("set_players_spreadsheet", "success"), None)

    async def print_players(self, message, parameter):
        """Debug function"""
        if not message.server:
            return (message.channel, self.get_string("register", "not_on_a_server"), None)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(message.server.id)).first()
        if not tournament:
            return (message.channel, self.get_string("register", "no_tournament", self.client.prefix, self.prefix), None)
        players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == tournament.players_spreadsheet_id).first()
        if not players_spreadsheet:
            return (message.channel, self.get_string("register", "no_tournament", self.client.prefix, self.prefix), None)
        regex = re.compile(re.escape("n"), re.IGNORECASE)
        max_column = eval(regex.sub(str(players_spreadsheet.n_team), players_spreadsheet.incr_column))
        max_row = eval(regex.sub(str(players_spreadsheet.n_team), players_spreadsheet.incr_row))
        if "!" in players_spreadsheet.range_team_name:
            range_team_name = players_spreadsheet.range_team_name.split("!")[1]
        else:
            range_team_name = players_spreadsheet.range_team_name            
        if "!" in players_spreadsheet.range_team:
            sheet_team = players_spreadsheet.range_team.split("!")[0]
            range_team = players_spreadsheet.range_team.split("!")[1]
        else:
            sheet_team = ""
            range_team = players_spreadsheet.range_team
        if range_team_name.lower() != "none":
            cells_team_name = range_team_name.split(":")
            cells_team = range_team.split(":")
            x1, y1 = api.spreadsheet.from_cell(cells_team_name[0])
            x2, y2 = api.spreadsheet.from_cell(cells_team[0])
            if x1 <= x2 and y1 <= y2:
                x_min = x1
                y_min = y1
            else:
                x_min = x2
                y_min = y2
            if len(cells_team_name) > 1:
                x1, y1 = api.spreadsheet.from_cell(cells_team_name[1])
            if len(cells_team) > 1:
                x2, y2 = api.spreadsheet.from_cell(cells_team[1])
            if x1 >= x2 and y1 >= y2:
                x_max = x1
                y_max = y1
            else:
                x_max = x2
                y_max = y2
        else:
            cells_team = range_team.split(":")
            x_min, y_min = api.spreadsheet.from_cell(cells_team[0])
            if len(cells_team) > 1:
                x_max, y_max = api.spreadsheet.from_cell(cells_team[1])
            else:
                x_max, y_max = x_min, y_min
        x_max += max_column
        y_max += max_row
        cell_min = api.spreadsheet.to_cell((x_min, y_min))
        cell_max = api.spreadsheet.to_cell((x_max, y_max))
        all_range = cell_min + ":" + cell_max
        if sheet_team:
            all_range = sheet_team + "!" + all_range
        cells = api.spreadsheet.get_range(players_spreadsheet.spreadsheet_id, all_range)
        print (cells)
        return (message.channel, "Ok c'est print", None)

    async def register(self, message, parameter):
        """Registers a player"""
        if not message.server:
            return (message.channel, self.get_string("register", "not_on_a_server"), None)
        discord_id = message.author.id
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
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
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(message.server.id)).first()
        if not tournament:
            return (message.channel, self.get_string("register", "no_tournament", self.client.prefix, self.prefix), None)
        players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == tournament.players_spreadsheet_id).first()
        if not players_spreadsheet:
            return (message.channel, self.get_string("register", "no_players_spreadsheet", self.client.prefix, self.prefix), None)
        players = api.spreadsheet.get_range(players_spreadsheet.spreadsheet_id, "A2:A")
        for player_row in players:
            for player in player_row:
                if osu_name == player:
                    player_role = tournament.player_role_id
                    roles = message.server.roles
                    if not player_role:
                        for role in roles:
                            if role.name == "Player":
                                player_role = role
                                break
                    else:
                        role_id = player_role
                        player_role = None
                        print(role_id)
                        for role in roles:
                            print(role.id)
                            if role.id == role_id:
                                player_role = role
                                break
                    if not player_role:
                        return (message.channel, self.get_string("register", "no_player_role"), None)
                    try:
                        await self.client.add_roles(message.author, player_role)
                    except discord.Forbidden:
                        return (message.channel, self.get_string("register", "change_role_forbidden", player_role.name), None)
                    return (message.channel, self.get_string("register", "success"), None)
        return (message.channel, self.get_string("register", "not_a_player"), None)
