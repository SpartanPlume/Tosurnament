"""Module for all Tosurnament related commands"""

import base64
import datetime
import re
import os
import requests
import googleapiclient
import discord
from discord.ext import commands
import modules.module
import api.osu
import api.spreadsheet
import helpers.crypt
import helpers.load_json
from databases.user import User
from databases.tournament import Tournament
from databases.players_spreadsheet import PlayersSpreadsheet
from databases.schedules_spreadsheet import SchedulesSpreadsheet
from databases.reschedule_message import RescheduleMessage
from databases.referee_notification import RefereeNotification

EMBED_COLOUR = 3447003

class NotGuildOwner(commands.CheckFailure):
    """Special exception if not guild owner"""
    pass

def is_guild_owner():
    """Check function to know if the author is the guild owner"""
    async def predicate(ctx):
        if ctx.guild.owner != ctx.author:
            raise NotGuildOwner()
        return True
    return commands.check(predicate)

class Tosurnament(modules.module.BaseModule):
    """Class that contains commands to use"""

    def __init__(self, bot):
        super().__init__(bot)
        self.client = bot
        self.name = "tosurnament"

    @commands.command(name='link')
    async def link(self, ctx, *, osu_name: str):
        """Sends a private message to the command runner to link his account"""
        discord_id = str(ctx.author.id)
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        if user:
            if user.verified:
                await ctx.send(self.get_string("link", "already_verified", ctx.prefix))
                return
        osu_name = api.osu.User.get_from_string(osu_name)
        osu_users = api.osu.OsuApi.get_user(osu_name)
        if not osu_users:
            await ctx.send(self.get_string("link", "user_not_found", osu_name))
            return
        osu_id = osu_users[0][api.osu.User.ID]
        code = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b'=').decode('ascii')
        if not user:
            user = User(discord_id=discord_id, osu_id=osu_id, verified=False, code=code)
            self.client.session.add(user)
        else:
            user.osu_id = osu_id
            user.code = code
        self.client.session.commit()
        await ctx.author.send(self.get_string("link", "success", code, ctx.prefix))

    @link.error
    async def link_handler(self, ctx, error):
        """Error handler of link function"""
        await ctx.send(self.get_string("link", "usage", ctx.prefix))

    @commands.command(name='auth')
    async def auth(self, ctx):
        """Sends a private message to the command runner to auth his account"""
        discord_id = str(ctx.author.id)
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        if not user:
            await ctx.send(self.get_string("auth", "not_linked", ctx.prefix))
            return
        if user.verified:
            await ctx.send(self.get_string("auth", "already_verified", ctx.prefix))
            return
        osu_id = user.osu_id
        request = requests.get("https://osu.ppy.sh/u/" + osu_id)
        if request.status_code != 200:
            await ctx.author.send(self.get_string("auth", "osu_error"))
            return
        index = 0
        try:
            to_find = "<div title='Location'><i class='icon-map-marker'></i><div>"
            index = request.text.index(to_find)
            index += len(to_find)
        except ValueError:
            await ctx.author.send(self.get_string("auth", "osu_error"))
            return
        location = request.text[index:]
        location = location.split("</div>", 1)[0]
        if location != user.code:
            await ctx.author.send(self.get_string("auth", "wrong_code", ctx.prefix))
            return
        else:
            user.verified = True
            self.client.session.commit()
        await ctx.author.send(self.get_string("auth", "success"))

    @commands.command(name='create_tournament')
    @commands.guild_only()
    @is_guild_owner()
    async def create_tournament(self, ctx, acronym: str, *, name: str):
        """Create a tournament"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).filter(Tournament.acronym == acronym).first()
        if tournament:
            await ctx.send(self.get_string("create_tournament", "acronym_used"))
            return
        tournament = Tournament(server_id=guild_id, acronym=acronym, name=name)
        self.client.session.add(tournament)
        self.client.session.commit()
        await ctx.send(self.get_string("create_tournament", "success"))

    @create_tournament.error
    async def create_tournament_handler(self, ctx, error):
        """Error handler of create_tournament function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("create_tournament", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("create_tournament", "usage", ctx.prefix))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(self.get_string("create_tournament", "not_on_a_server"))
        elif isinstance(error, NotGuildOwner):
            await ctx.send(self.get_string("create_tournament", "not_owner"))

    @commands.command(name='set_staff_channel')
    @commands.guild_only()
    async def set_staff_channel(self, ctx, *, channel: discord.TextChannel):
        """Set the staff channel"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            await ctx.send(self.get_string("set_staff_channel", "no_tournament", ctx.prefix))
            return
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            await ctx.send(self.get_string("set_staff_channel", "no_rights", ctx.prefix))
            return
        if ctx.guild.owner != ctx.author and not any(role.id == tournament.admin_role_id for role in ctx.author.roles):
            await ctx.send(self.get_string("set_staff_channel", "no_rights", ctx.prefix))
            return
        tournament.staff_channel_id = str(channel.id)
        self.client.session.commit()
        await ctx.send(self.get_string("set_staff_channel", "success"))

    @set_staff_channel.error
    async def set_staff_channel_handler(self, ctx, error):
        """Error handler of set_staff_channel function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_staff_channel", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_staff_channel", "usage", ctx.prefix))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(self.get_string("set_staff_channel", "not_on_a_server"))

    @commands.command(name='set_admin_role')
    @commands.guild_only()
    @is_guild_owner()
    async def set_admin_role(self, ctx, *, admin_role: discord.Role):
        """Set the admin role"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            await ctx.send(self.get_string("set_admin_role", "no_tournament", ctx.prefix))
            return
        tournament.admin_role_id = str(admin_role.id)
        self.client.session.commit()
        await ctx.send(self.get_string("set_admin_role", "success"))

    @set_admin_role.error
    async def set_admin_role_handler(self, ctx, error):
        """Error handler of set_admin_role function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_admin_role", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_admin_role", "usage", ctx.prefix))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(self.get_string("set_admin_role", "not_on_a_server"))
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(self.get_string("set_admin_role", "not_owner"))

    @commands.command(name='set_referee_role')
    @commands.guild_only()
    async def set_referee_role(self, ctx, *, referee_role: discord.Role):
        """Set the referee role"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            await ctx.send(self.get_string("set_referee_role", "no_tournament", ctx.prefix))
            return
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            await ctx.send(self.get_string("set_referee_role", "no_rights", ctx.prefix))
            return
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            await ctx.send(self.get_string("set_referee_role", "no_rights", ctx.prefix))
            return
        tournament.referee_role_id = str(referee_role.id)
        self.client.session.commit()
        await ctx.send(self.get_string("set_referee_role", "success"))

    @set_referee_role.error
    async def set_referee_role_handler(self, ctx, error):
        """Error handler of set_referee_role function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_referee_role", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_referee_role", "usage", ctx.prefix))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(self.get_string("set_referee_role", "not_on_a_server"))

    @commands.command(name='set_player_role')
    @commands.guild_only()
    async def set_player_role(self,ctx, *, player_role: discord.Role):
        """Set the player role"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            await ctx.send(self.get_string("set_player_role", "no_tournament", ctx.prefix))
            return
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            await ctx.send(self.get_string("set_player_role", "no_rights", ctx.prefix))
            return
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            await ctx.send(self.get_string("set_player_role", "no_rights", ctx.prefix))
            return
        tournament.player_role_id = str(player_role.id)
        self.client.session.commit()
        await ctx.send(self.get_string("set_player_role", "success"))  

    @set_player_role.error
    async def set_player_role_handler(self, ctx, error):
        """Error handler of set_player_role function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_player_role", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_player_role", "usage", ctx.prefix))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(self.get_string("set_player_role", "not_on_a_server"))

    @commands.command(name='set_players_spreadsheet')
    @commands.guild_only()
    async def set_players_spreadsheet(self, ctx, spreadsheet_id: str, range_team_name: str, range_team: str, incr_column: str, incr_row: str, n_team: int):
        """Sets the players spreadsheet"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            await ctx.send(self.get_string("set_players_spreadsheet", "no_tournament", ctx.prefix))
            return
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            await ctx.send(self.get_string("set_players_spreadsheet", "no_rights", ctx.prefix))
            return
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            await ctx.send(self.get_string("set_players_spreadsheet", "no_rights", ctx.prefix))
            return
        if not re.match(r'^((.+!)?[A-Z]+\d*(:[A-Z]+\d*)?|[Nn][Oo][Nn][Ee])$', range_team_name):
            await ctx.send(self.get_string("set_players_spreadsheet", "usage", ctx.prefix))
            return
        if not re.match(r'^(.+!)?[A-Z]+\d*(:[A-Z]+\d*)?$', range_team):
            await ctx.send(self.get_string("set_players_spreadsheet", "usage", ctx.prefix))
            return
        regex = re.compile(re.escape("n"), re.IGNORECASE)
        try:
            eval(regex.sub("1", incr_column))
            eval(regex.sub("1", incr_row))
        except NameError:
            await ctx.send(self.get_string("set_players_spreadsheet", "usage", ctx.prefix))
            return
        if tournament.players_spreadsheet_id:
            players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == tournament.players_spreadsheet_id).first()
        else:
            players_spreadsheet = PlayersSpreadsheet()
            self.client.session.add(players_spreadsheet)
        players_spreadsheet.spreadsheet_id = spreadsheet_id
        players_spreadsheet.range_team_name = range_team_name
        players_spreadsheet.range_team = range_team
        players_spreadsheet.incr_column = incr_column
        players_spreadsheet.incr_row = incr_row
        players_spreadsheet.n_team = n_team
        self.client.session.commit()
        tournament.players_spreadsheet_id = players_spreadsheet.id
        self.client.session.commit()
        await ctx.send(self.get_string("set_players_spreadsheet", "success"))

    @set_players_spreadsheet.error
    async def set_players_spreadsheet_handler(self, ctx, error):
        """Error handler of set_players_spreadsheet function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_players_spreadsheet", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_players_spreadsheet", "usage", ctx.prefix))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(self.get_string("set_players_spreadsheet", "not_on_a_server"))

    def get_incremented_range(self, cells, sheet_name, incr_column, incr_row):
        """Returns a range from the incremented list of cells"""
        incremented_cells = self.increment_cells(cells, incr_column, incr_row)
        range_name = incremented_cells[0]
        if len(incremented_cells) > 1:
            range_name += ":" + incremented_cells[1]
        if sheet_name:
            range_name = sheet_name + "!" + range_name
        return range_name

    def increment_cells(self, cells, incr_column, incr_row):
        """Returns the incremented cells"""
        incremented_cells = []
        for cell in cells:
            x, y = api.spreadsheet.from_cell(cell)
            x += incr_column
            y += incr_row
            incremented_cells.append(api.spreadsheet.to_cell((x, y)))
        return incremented_cells

    @commands.command(name='register')
    @commands.guild_only()
    async def register(self, ctx):
        """Registers a player"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            await ctx.send(self.get_string("register", "no_tournament", ctx.prefix))
            return
        player_role_id = tournament.player_role_id
        if self.get_role(ctx.author.roles, player_role_id, "Player"):
            await ctx.send(self.get_string("register", "already_registered", ctx.prefix))
            return
        discord_id = str(ctx.author.id)
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        if not user:
            await ctx.send(self.get_string("register", "not_linked", ctx.prefix))
            return
        if not user.verified:
            await ctx.send(self.get_string("register", "not_verified", ctx.prefix))
            return
        osu_id = user.osu_id
        osu_users = api.osu.OsuApi.get_user(osu_id)
        if not osu_users:
            await ctx.send(self.get_string("register", "osu_error"))
            return
        osu_name = osu_users[0][api.osu.User.NAME]
        print("2")
        #try:
        #    await ctx.author.edit(nick=osu_name)
        #except discord.Forbidden:
        #    await ctx.send(self.get_string("register", "change_nickname_forbidden"))
        #    return
        players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == tournament.players_spreadsheet_id).first()
        if not players_spreadsheet:
            await ctx.send(self.get_string("register", "no_players_spreadsheet", ctx.prefix))
            return
        if "!" in players_spreadsheet.range_team_name:
            range_team_name = players_spreadsheet.range_team_name.split("!")[1]
        else:
            range_team_name = players_spreadsheet.range_team_name            
        if "!" in players_spreadsheet.range_team:
            sheet_name = players_spreadsheet.range_team.split("!")[0]
            range_team = players_spreadsheet.range_team.split("!")[1]
        else:
            sheet_name = ""
            range_team = players_spreadsheet.range_team
        range_names = []
        cells_team_name = range_team_name.split(":")
        cells_team = range_team.split(":")
        regex = re.compile(re.escape("n"), re.IGNORECASE)
        for i in range(0, players_spreadsheet.n_team):
            incr_column = int(eval(regex.sub(str(i), players_spreadsheet.incr_column)))
            incr_row = int(eval(regex.sub(str(i), players_spreadsheet.incr_row)))
            if range_team_name.lower() != "none":
                range_names.append(self.get_incremented_range(cells_team_name, sheet_name, incr_column, incr_row))
            range_names.append(self.get_incremented_range(cells_team, sheet_name, incr_column, incr_row))
        try:
            cells = api.spreadsheet.get_ranges(players_spreadsheet.spreadsheet_id, range_names)
        except googleapiclient.errors.HttpError:
            await ctx.send(self.get_string("register", "spreadsheet_error", ctx.prefix))
            return
        i = 0
        while i < len(cells):
            team_name = ""
            if range_team_name.lower() != "none":
                for row in cells[i]:
                    for cell in row:
                        if cell:
                            team_name = cell
                            break
                i += 1
            for player_row in cells[i]:
                for player in player_row:
                    if osu_name == player:
                        roles = ctx.guild.roles
                        player_role = self.get_role(roles, player_role_id, "Player")
                        if not player_role:
                            await ctx.send(self.get_string("register", "no_player_role"))
                            return
                        try:
                            await ctx.author.add_roles(player_role)
                        except discord.Forbidden:
                            await ctx.send(self.get_string("register", "change_role_forbidden", player_role.name))
                            return
                        if team_name:
                            team_role = None
                            for role in roles:
                                if role.name == team_name:
                                    team_role = role
                                    break
                            if not team_role:
                                try:
                                    team_role = await ctx.guild.create_role(name=team_name, mentionable=True)
                                except discord.Forbidden:
                                    await ctx.send(self.get_string("register", "create_role_forbidden", team_name))
                                    return
                            try:
                                await ctx.author.add_roles(team_role)
                            except discord.Forbidden:
                                await ctx.send(self.get_string("register", "change_role_forbidden", team_name))
                                return
                        await ctx.send(self.get_string("register", "success"))
                        return
            i += 1
        await ctx.send(self.get_string("register", "not_a_player"))

    @register.error
    async def register_handler(self, ctx, error):
        """Error handler of register function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("register", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("register", "usage", ctx.prefix))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(self.get_string("register", "not_on_a_server"))

    def get_role(self, roles, role_id=None, role_name=""):
        """Gets a role from its id or name"""
        wanted_role = None
        if not role_id:
            for role in roles:
                if role.name == role_name:
                    wanted_role = role
                    break
        else:
            for role in roles:
                if role.id == role_id:
                    wanted_role = role
                    break
        return wanted_role

    @commands.command(name='set_schedules_spreadsheet')
    @commands.guild_only()
    async def set_schedules_spreadsheet(self, ctx, spreadsheet_id: str, range_name: str, *, parameters: str):
        """Sets the schedules spreadsheet"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            await ctx.send(self.get_string("set_schedules_spreadsheet", "no_tournament", ctx.prefix))
            return
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            await ctx.send(self.get_string("set_schedules_spreadsheet", "no_rights", ctx.prefix))
            return
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            await ctx.send(self.get_string("set_schedules_spreadsheet", "no_rights", ctx.prefix))
            return
        if not re.match(r'^(.+!)?[A-Z]+\d*(:[A-Z]+\d*)?$', range_name):
            await ctx.send(self.get_string("set_schedules_spreadsheet", "usage", ctx.prefix))
            return
        if not re.match(r'^((\(\d+, ?\d+)\) ?){3}( ?\((\d+, ?){2}"(?:[^"\\]|\\.)*"\))*$', parameters):
            await ctx.send(self.get_string("set_schedules_spreadsheet", "usage", ctx.prefix))
            return
        if tournament.schedules_spreadsheet_id:
            schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == tournament.schedules_spreadsheet_id).first()
        else:
            schedules_spreadsheet = SchedulesSpreadsheet()
            self.client.session.add(schedules_spreadsheet)
        schedules_spreadsheet.spreadsheet_id = spreadsheet_id
        schedules_spreadsheet.range_name = range_name
        schedules_spreadsheet.parameters = parameters
        self.client.session.commit()
        tournament.schedules_spreadsheet_id = schedules_spreadsheet.id
        self.client.session.commit()
        await ctx.send(self.get_string("set_schedules_spreadsheet", "success", ctx.prefix))

    @set_schedules_spreadsheet.error
    async def set_schedules_spreadsheet_handler(self, ctx, error):
        """Error handler of set_schedules_spreadsheet function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_schedules_spreadsheet", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_schedules_spreadsheet", "usage", ctx.prefix))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(self.get_string("set_schedules_spreadsheet", "not_on_a_server"))

    @commands.command(name='reschedule')
    @commands.guild_only()
    async def reschedule(self, ctx, match_id: str, *, date: str):
        """Allows players to reschedule their matches"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            await ctx.send(self.get_string("reschedule", "no_tournament", ctx.prefix))
            return
        schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == tournament.schedules_spreadsheet_id).first()
        if not schedules_spreadsheet:
            await ctx.send(self.get_string("reschedule", "no_schedules_spreadsheet", ctx.prefix))
            return
        roles = ctx.guild.roles
        player_role = self.get_role(roles, tournament.player_role_id, "Player")
        if not player_role:
            await ctx.send(self.get_string("reschedule", "no_player_role", ctx.prefix))
            return
        if not any(player_role.id == role.id for role in ctx.author.roles):
            await ctx.send(self.get_string("reschedule", "not_a_player", ctx.prefix))
            return
        date = datetime.datetime.strptime(date + "2008", '%d/%m %H:%M%Y')
        try:
            values = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name)
        except googleapiclient.errors.HttpError:
            await ctx.send(self.get_string("reschedule", "spreadsheet_error", ctx.prefix))
            return
        tuples = schedules_spreadsheet.parse_parameters()
        for y, row in enumerate(values):
            for x, value in enumerate(row):
                if value == match_id:
                    incr_x, incr_y = tuples[0]
                    team_name1 = values[y + incr_y][x + incr_x]
                    incr_x, incr_y = tuples[1]
                    team_name2 = values[y + incr_y][x + incr_x]
                    tuples = tuples[3:]
                    date_string = ""
                    date_flags = ""
                    for tup in tuples:
                        incr_x, incr_y, date_flag = tup
                        if y + incr_y < len(values) and x + incr_x < len(values[y + incr_y]):
                            date_flags += date_flag
                            date_string += values[y + incr_y][x + incr_x]
                    previous_date = datetime.datetime.strptime(date_string, date_flags)
                    player_name = ctx.author.nick
                    if not player_name:
                        player_name = ctx.author.name
                    role_team1 = self.get_role(roles, role_name=team_name1)
                    role_team2 = self.get_role(roles, role_name=team_name2)
                    reschedule_message = RescheduleMessage()
                    reschedule_message.match_id = match_id
                    reschedule_message.ally_user_id = bytes('', 'utf-8')
                    reschedule_message.ally_role_id = bytes('', 'utf-8')
                    reschedule_message.enemy_user_id = bytes('', 'utf-8')
                    reschedule_message.enemy_role_id = bytes('', 'utf-8')
                    if role_team1 and role_team2 and any(role_team1.id == role.id for role in ctx.author.roles):
                        ally_mention = role_team1.mention
                        enemy_mention = role_team2.mention
                        reschedule_message.ally_role_id = str(role_team1.id)
                        reschedule_message.enemy_role_id = str(role_team2.id)
                    elif role_team1 and role_team2 and any(role_team2.id == role.id for role in ctx.author.roles):
                        ally_mention = role_team2.mention
                        enemy_mention = role_team1.mention
                        reschedule_message.ally_role_id = str(role_team2.id)
                        reschedule_message.enemy_role_id = str(role_team1.id)
                    elif team_name1 == player_name:
                        enemy = ctx.guild.get_member_named(team_name2)
                        ally_mention = ctx.author.mention
                        enemy_mention = enemy.mention
                        reschedule_message.ally_user_id = str(ctx.author.id)
                        reschedule_message.enemy_user_id = str(enemy.id)
                    elif team_name2 == player_name:
                        enemy = ctx.guild.get_member_named(team_name1)
                        ally_mention = ctx.author.mention
                        enemy_mention = enemy.mention
                        reschedule_message.ally_user_id = str(ctx.author.id)
                        reschedule_message.enemy_user_id = str(enemy.id)
                    else:
                        await ctx.send(self.get_string("reschedule", "invalid_match"))
                        return
                    previous_date_string = previous_date.strftime("**%d %B at %H:%M UTC**")
                    new_date_string = date.strftime("**%d %B at %H:%M UTC**")
                    reschedule_message.previous_date = previous_date.strftime("%d/%m/%y %H:%M")
                    reschedule_message.new_date = date.strftime("%d/%m/%y %H:%M")
                    reschedule_message.ally_user_id = ally_mention
                    reschedule_message.enemy_mention = enemy_mention
                    sent_message = await ctx.send(self.get_string("reschedule", "success", enemy_mention, ally_mention, match_id, previous_date_string, new_date_string))
                    reschedule_message.message_id = str(sent_message.id)
                    self.client.session.add(reschedule_message)
                    self.client.session.commit()
                    await sent_message.add_reaction("👍")
                    await sent_message.add_reaction("👎")
                    return
        await ctx.send(self.get_string("reschedule", "invalid_match_id"))

    @reschedule.error
    async def reschedule_handler(self, ctx, error):
        """Error handler of reschedule function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("reschedule", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("reschedule", "usage", ctx.prefix))
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(self.get_string("reschedule", "not_on_a_server"))

    async def on_raw_reaction_add(self, emoji, message_id, channel_id, user_id):
        """on_raw_reaction_add of the Tosurnament module"""
        channel = self.client.get_channel(channel_id)
        guild = channel.guild
        user = guild.get_member(user_id)
        await self.reaction_on_reschedule_message(emoji, message_id, channel, guild, user)
        await self.reaction_on_referee_notification(emoji, message_id, channel, guild, user)        

    async def reaction_on_reschedule_message(self, emoji, message_id, channel, guild, user):
        """Reschedules a match or denies the reschedule"""
        reschedule_message = self.client.session.query(RescheduleMessage).filter(RescheduleMessage.message_id == helpers.crypt.hash_str(str(message_id))).first()
        if not reschedule_message:
            return
        ally_role = None
        enemy_role = None
        if str(user.id) == reschedule_message.enemy_user_id:
            enemy_role = guild.get_member(reschedule_message.ally_user_id)
            ally_role = user
        elif any(reschedule_message.enemy_role_id == str(role.id) for role in user.roles):
            for role in guild.roles:
                if reschedule_message.ally_role_id == str(role.id):
                    ally_role = role
                if reschedule_message.enemy_role_id == str(role.id):
                    enemy_role = role
        if ally_role and enemy_role:
            if emoji.name == "👍":
                guild_id = str(guild.id)
                tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
                if not tournament:
                    await channel.send(self.get_string("reschedule", "no_tournament", self.client.command_prefix))
                    return
                schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == tournament.schedules_spreadsheet_id).first()
                if not schedules_spreadsheet:
                    await channel.send(self.get_string("reschedule", "no_schedule_spreadsheet", self.client.command_prefix))
                    return
                try:
                    values = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name)
                except googleapiclient.errors.HttpError:
                    await channel.send(self.get_string("reschedule", "spreadsheet_error"))
                    return
                previous_date = datetime.datetime.strptime(reschedule_message.previous_date, '%d/%m/%y %H:%M')
                new_date = datetime.datetime.strptime(reschedule_message.new_date, '%d/%m/%y %H:%M')
                tuples = schedules_spreadsheet.parse_parameters()
                for y, row in enumerate(values):
                    for x, value in enumerate(row):
                        if value == reschedule_message.match_id:
                            incr_x, incr_y = tuples[2]
                            referee_name = None
                            if y + incr_y < len(values) and x + incr_x < len(values[y + incr_y]):
                                referee_name = values[y + incr_y][x + incr_x]
                            tuples = tuples[3:]
                            for tup in tuples:
                                incr_x, incr_y, date_flag = tup
                                values[y + incr_y][x + incr_x] = new_date.strftime(date_flag)
                            referee = None
                            if referee_name:
                                referee = guild.get_member_named(referee_name)
                            staff_channel = self.client.get_channel(int(tournament.staff_channel_id))
                            try:
                                api.spreadsheet.write_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name, values)
                            except googleapiclient.errors.HttpError:
                                await channel.send(self.get_string("reschedule", "spreadsheet_error"))
                                return
                            await channel.send(self.get_string("reschedule", "accepted", ally_role.mention))
                            if staff_channel:
                                previous_date_string = previous_date.strftime("**%d %B at %H:%M UTC**")
                                new_date_string = new_date.strftime("**%d %B at %H:%M UTC**")
                                if referee:
                                    sent_message = await staff_channel.send(self.get_string("reschedule", "referee_notification", referee.mention, reschedule_message.match_id, ally_role.name, enemy_role.name, previous_date_string, new_date_string))
                                    referee_notification = RefereeNotification()
                                    referee_notification.message_id = str(sent_message.id)
                                    referee_notification.match_id = reschedule_message.match_id
                                    self.client.session.add(referee_notification)
                                    self.client.session.commit()
                                else:
                                    await staff_channel.send(self.get_string("reschedule", "no_referee_notification", reschedule_message.match_id, ally_role.name, enemy_role.name, previous_date_string, new_date_string))
                            self.client.session.delete(reschedule_message)
                            self.client.session.commit()
            elif emoji.name == "👎":
                await channel.send(self.get_string("reschedule", "refused", ally_role.mention))
                self.client.session.delete(reschedule_message)
                self.client.session.commit()

    async def reaction_on_referee_notification(self, emoji, message_id, channel, guild, user):
        """Removes the referee from the schedule spreadsheet"""
        referee_notification = self.client.session.query(RefereeNotification).filter(RefereeNotification.message_id == helpers.crypt.hash_str(str(message_id))).first()
        if not referee_notification:
            return
        if emoji.name == "❌":
            guild_id = str(guild.id)
            tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
            if not tournament:
                await channel.send(self.get_string("reschedule", "no_tournament", self.client.command_prefix))
                return
            schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == tournament.schedules_spreadsheet_id).first()
            if not schedules_spreadsheet:
                await channel.send(self.get_string("reschedule", "no_schedule_spreadsheet", self.client.command_prefix))
                return
            try:
                values = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name)
            except googleapiclient.errors.HttpError:
                await channel.send(self.get_string("reschedule", "spreadsheet_error"))
                return
            tuples = schedules_spreadsheet.parse_parameters()
            for y, row in enumerate(values):
                for x, value in enumerate(row):
                    if value == referee_notification.match_id:
                        incr_x, incr_y = tuples[2]
                        referee_name = values[y + incr_y][x + incr_x]
                        if referee_name == user.display_name:
                            values[y + incr_y][x + incr_x] = ""
                            staff_channel = self.client.get_channel(int(tournament.staff_channel_id))
                            try:
                                api.spreadsheet.write_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name, values)
                            except googleapiclient.errors.HttpError:
                                await channel.send(self.get_string("reschedule", "spreadsheet_error"))
                                return
                            if staff_channel:
                                await channel.send(self.get_string("reschedule", "removed_from_match", referee_notification.match_id))
                            self.client.session.delete(referee_notification)
                            self.client.session.commit()                            

def get_class(bot):
    """Returns the main class of the module"""
    return Tosurnament(bot)

def setup(bot):
    """Setups the cog"""
    bot.add_cog(Tosurnament(bot))
