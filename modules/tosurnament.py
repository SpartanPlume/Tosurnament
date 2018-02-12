"""Module for all Tosurnament related commands"""

import base64
import datetime
import re
import os
import requests
import urllib
from ast import literal_eval
import googleapiclient
import discord
from discord.ext import commands
import modules.module
import api.osu
import api.spreadsheet
import api.challonge
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

class UserNotFound(commands.CommandError):
    """Special exception if user not found"""
    def __init__(self, username):
        super().__init__()
        self.username = username

class UserNotLinked(commands.CommandError):
    """Special exception if user not linked"""
    pass

class UserNotVerified(commands.CommandError):
    """Special exception if user not veirfied"""
    pass

class UserAlreadyVerified(commands.CommandError):
    """Special exception if user already verified"""
    pass

class UserAlreadyRegistered(commands.CommandError):
    """Special exception if user already registered"""
    pass

class OsuError(commands.CommandError):
    """Special exception if osu error"""
    pass

class WrongCodeError(commands.CommandError):
    """Special exception if a code is wrong"""
    pass

class AcronymAlreadyUsed(commands.CommandError):
    """Special exception if a tournament acronym is already used"""
    pass

class NoTournament(commands.CommandError):
    """Special exception if a guild does not have any tournament running"""
    pass

class NotBotAdmin(commands.CommandError):
    """Special exception if user is not a bot admin"""
    pass

class NoSpreadsheet(commands.CommandError):
    """Special exception if a spreadsheet has not been set"""
    def __init__(self, spreadsheet=None):
        super().__init__()
        self.spreadsheet = spreadsheet

class SpreadsheetError(commands.CommandError):
    """Special exception if an error occur with a spreadsheet"""
    pass

class NoPlayerRole(commands.CommandError):
    """Special exception if there is no player role on the guild"""
    pass

class NotAPlayer(commands.CommandError):
    """Special exception if the user is not a player"""
    pass

class NoRefereeRole(commands.CommandError):
    """Special exception if there is no player role on the guild"""
    pass

class NotAReferee(commands.CommandError):
    """Special exception if the user is not a player"""
    pass

class InvalidMatch(commands.CommandError):
    """Special exception if the user is not in the match"""
    pass

class InvalidMatchId(commands.CommandError):
    """Special exception if the match id does not exist"""
    pass

class InvalidMpLink(commands.CommandError):
    """Special exception if the match link does not exist"""
    pass

class MatchNotFound(commands.CommandError):
    """Special exception if a match in the challonge is not found"""
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

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(self.get_string("", "not_on_a_server"))
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(self.get_string("", "disabled_command"))
        elif isinstance(error, NotGuildOwner):
            await ctx.send(self.get_string("", "not_owner"))
        elif isinstance(error, UserNotFound):
            await ctx.send(self.get_string("", "user_not_found", error.username))
        elif isinstance(error, UserNotLinked):
            await ctx.send(self.get_string("", "not_linked", ctx.prefix))
        elif isinstance(error, UserNotVerified):
            await ctx.send(self.get_string("", "not_verified", ctx.prefix))
        elif isinstance(error, UserAlreadyVerified):
            await ctx.send(self.get_string("", "already_verified", ctx.prefix))
        elif isinstance(error, UserAlreadyRegistered):
            await ctx.send(self.get_string("", "already_registered", ctx.prefix))
        elif isinstance(error, OsuError):
            await ctx.send(self.get_string("", "osu_error"))
        elif isinstance(error, NoTournament):
            await ctx.send(self.get_string("", "no_tournament", ctx.prefix))
        elif isinstance(error, NotBotAdmin):
            await ctx.send(self.get_string("", "no_rights", ctx.prefix))
        elif isinstance(error, NoPlayerRole):
            await ctx.send(self.get_string("", "no_player_role"))
        elif isinstance(error, NotAPlayer):
            await ctx.send(self.get_string("", "not_a_player"))
        elif isinstance(error, NoRefereeRole):
            await ctx.send(self.get_string("", "no_referee_role"))
        elif isinstance(error, NotAReferee):
            await ctx.send(self.get_string("", "not_a_referee"))
        elif isinstance(error, commands.BotMissingPermissions):
            for missing_permission in error.missing_perms:
                if missing_permission == "manage_nicknames":
                    await ctx.send(self.get_string("", "change_nickname_forbidden"))
                    return
                elif missing_permission == "manage_roles":
                    await ctx.send(self.get_string("", "change_role_forbidden"))
                    return
                elif missing_permission == "change_owner_nickname":
                    await ctx.send(self.get_string("", "change_nickname_forbidden"))
                    return
        elif isinstance(error, api.challonge.NoRights):
            await ctx.send(self.get_string("", "challonge_no_rights"))
        elif isinstance(error, api.challonge.NotFound):
            await ctx.send(self.get_string("", "challonge_not_found"))

    @commands.command(name='link')
    async def link(self, ctx, *, osu_name: str):
        """Sends a private message to the command runner to link his account"""
        discord_id = str(ctx.author.id)
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        if user:
            if user.verified:
                raise UserAlreadyVerified()
        osu_name = api.osu.User.get_from_string(osu_name)
        osu_users = api.osu.OsuApi.get_user(osu_name)
        if not osu_users:
            raise UserNotFound(osu_name)
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
        if isinstance(error, UserAlreadyVerified):
            await ctx.send(self.get_string("link", "already_verified", ctx.prefix))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("link", "usage", ctx.prefix))

    @commands.command(name='auth')
    async def auth(self, ctx):
        """Sends a private message to the command runner to auth his account"""
        discord_id = str(ctx.author.id)
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        if not user:
            raise UserNotLinked()
        if user.verified:
            raise UserAlreadyVerified()
        osu_id = user.osu_id
        request = requests.get("https://osu.ppy.sh/u/" + osu_id)
        if request.status_code != 200:
            raise OsuError()
        index = 0
        try:
            to_find = "<div title='Location'><i class='icon-map-marker'></i><div>"
            index = request.text.index(to_find)
            index += len(to_find)
        except ValueError:
            raise OsuError()
        location = request.text[index:]
        location = location.split("</div>", 1)[0]
        if location != user.code:
            raise WrongCodeError()
        else:
            user.verified = True
            self.client.session.commit()
        await ctx.author.send(self.get_string("auth", "success"))

    @auth.error
    async def auth_handler(self, ctx, error):
        if isinstance(error, WrongCodeError):
            await ctx.author.send(self.get_string("auth", "wrong_code", ctx.prefix))

    @commands.command(name='create_tournament')
    @commands.guild_only()
    @is_guild_owner()
    async def create_tournament(self, ctx, acronym: str, *, name: str):
        """Create a tournament"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).filter(Tournament.acronym == acronym).first()
        if tournament:
            raise AcronymAlreadyUsed()
        tournament = Tournament(server_id=guild_id, acronym=acronym, name=name, name_change_enabled=True)
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
        elif isinstance(error, AcronymAlreadyUsed):
            await ctx.send(self.get_string("create_tournament", "acronym_used"))

    @commands.command(name='set_staff_channel')
    @commands.guild_only()
    async def set_staff_channel(self, ctx, *, channel: discord.TextChannel):
        """Set the staff channel"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(role.id == tournament.admin_role_id for role in ctx.author.roles):
            raise NotBotAdmin()
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

    @commands.command(name='set_admin_role')
    @commands.guild_only()
    @is_guild_owner()
    async def set_admin_role(self, ctx, *, admin_role: discord.Role):
        """Set the admin role"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
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

    @commands.command(name='set_referee_role')
    @commands.guild_only()
    async def set_referee_role(self, ctx, *, referee_role: discord.Role):
        """Set the referee role"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            raise NotBotAdmin()
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

    @commands.command(name='set_player_role')
    @commands.guild_only()
    async def set_player_role(self, ctx, *, player_role: discord.Role):
        """Set the player role"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            raise NotBotAdmin()
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

    @commands.command(name='set_challonge')
    @commands.guild_only()
    async def set_challonge(self, ctx, challonge_tournament: str):
        """Set the player role"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            raise NotBotAdmin()
        if challonge_tournament.startswith('http'):
            if challonge_tournament.endswith('/'):
                challonge_tournament = challonge_tournament[:-1]
            challonge_tournament = challonge_tournament.split('/')[-1]
        tournament.challonge = challonge_tournament
        self.client.session.commit()
        await ctx.send(self.get_string("set_challonge", "success"))  

    @set_challonge.error
    async def set_challonge_handler(self, ctx, error):
        """Error handler of set_challonge function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_challonge", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_challonge", "usage", ctx.prefix))

    @commands.command(name='set_post_result_message')
    @commands.guild_only()
    async def set_post_result_message(self, ctx, *, message: str = ""):
        """Set the player role"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            raise NotBotAdmin()
        tournament.post_result_message = message
        self.client.session.commit()
        await ctx.send(self.get_string("set_post_result_message", "success"))  

    @set_post_result_message.error
    async def set_post_result_message_handler(self, ctx, error):
        """Error handler of set_post_result_message function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_post_result_message", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_post_result_message", "usage", ctx.prefix))

    @commands.command(name='set_players_spreadsheet')
    @commands.guild_only()
    async def set_players_spreadsheet(self, ctx, spreadsheet_id: str, range_team_name: str, range_team: str, incr_column: str, incr_row: str, n_team: int):
        """Sets the players spreadsheet"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            raise NotBotAdmin()
        if not re.match(r'^((.+!)?[A-Z]+\d*(:[A-Z]+\d*)?|[Nn][Oo][Nn][Ee])$', range_team_name):
            raise commands.UserInputError()
        if not re.match(r'^(.+!)?[A-Z]+\d*(:[A-Z]+\d*)?$', range_team):
            raise commands.UserInputError()
        regex = re.compile(re.escape("n"), re.IGNORECASE)
        try:
            eval(regex.sub("1", incr_column))
            eval(regex.sub("1", incr_row))
        except NameError:
            raise commands.UserInputError()
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
        elif isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("set_players_spreadsheet", "usage", ctx.prefix))

    @commands.command(name='register')
    @commands.guild_only()
    @commands.bot_has_permissions(manage_nicknames=True, manage_roles=True)
    async def register(self, ctx):
        """Registers a player"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        player_role_id = tournament.player_role_id
        if self.get_role(ctx.author.roles, player_role_id, "Player"):
            raise UserAlreadyRegistered()
        discord_id = str(ctx.author.id)
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        if not user:
            raise UserNotLinked()
        if not user.verified:
            raise UserNotVerified()
        osu_id = user.osu_id
        osu_users = api.osu.OsuApi.get_user(osu_id)
        if not osu_users:
            raise OsuError()
        osu_name = osu_users[0][api.osu.User.NAME]
        #try:
        #    await ctx.author.edit(nick=osu_name)
        #except discord.Forbidden:
        #    raise commands.BotMissingPermissions(["change_owner_nickname"])
        players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == tournament.players_spreadsheet_id).first()
        if not players_spreadsheet:
            raise NoSpreadsheet()
        range_names = players_spreadsheet.get_ranges()
        try:
            cells = api.spreadsheet.get_ranges(players_spreadsheet.spreadsheet_id, range_names)
        except googleapiclient.errors.HttpError:
            raise SpreadsheetError()
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
                            raise NoPlayerRole()
                        await ctx.author.add_roles(player_role)
                        if team_name:
                            team_role = None
                            for role in roles:
                                if role.name == team_name:
                                    team_role = role
                                    break
                            if not team_role:
                                team_role = await ctx.guild.create_role(name=team_name, mentionable=True)
                            await ctx.author.add_roles(team_role)
                        await ctx.send(self.get_string("register", "success"))
                        return
            i += 1
        raise NotAPlayer()

    @register.error
    async def register_handler(self, ctx, error):
        """Error handler of register function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("register", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("register", "usage", ctx.prefix))
        elif isinstance(error, NoSpreadsheet):
            await ctx.send(self.get_string("register", "no_players_spreadsheet", ctx.prefix))
        elif isinstance(error, SpreadsheetError):
            await ctx.send(self.get_string("register", "spreadsheet_error", ctx.prefix))

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
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            raise NotBotAdmin()
        if not re.match(r'^(.+!)?[A-Z]+\d*(:[A-Z]+\d*)?$', range_name):
            raise commands.UserInputError()
        if not re.match(r'^((\(\d+, ?\d+)\) ?){3}( ?\((\d+, ?){2}"(?:[^"\\]|\\.)*"\))*$', parameters):
            raise commands.UserInputError()
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
        elif isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("set_schedules_spreadsheet", "usage", ctx.prefix))

    @commands.command(name='reschedule')
    @commands.guild_only()
    async def reschedule(self, ctx, match_id: str, *, date: str):
        """Allows players to reschedule their matches"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == tournament.schedules_spreadsheet_id).first()
        if not schedules_spreadsheet:
            raise NoSpreadsheet()
        roles = ctx.guild.roles
        player_role = self.get_role(roles, tournament.player_role_id, "Player")
        if not player_role:
            raise NoPlayerRole()
        if not any(player_role.id == role.id for role in ctx.author.roles):
            raise NotAPlayer()
        date = datetime.datetime.strptime(date + "2008", '%d/%m %H:%M%Y')
        try:
            values = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name)
        except googleapiclient.errors.HttpError:
            raise SpreadsheetError()
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
                        raise InvalidMatch()
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
        raise InvalidMatchId()

    @reschedule.error
    async def reschedule_handler(self, ctx, error):
        """Error handler of reschedule function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("reschedule", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("reschedule", "usage", ctx.prefix))
        elif isinstance(error, NoSpreadsheet):
            await ctx.send(self.get_string("reschedule", "no_schedules_spreadsheet", ctx.prefix))
        elif isinstance(error, SpreadsheetError):
            await ctx.send(self.get_string("reschedule", "spreadsheet_error", ctx.prefix))
        elif isinstance(error, InvalidMatch):
            await ctx.send(self.get_string("reschedule", "invalid_match"))
        elif isinstance(error, InvalidMatchId):
            await ctx.send(self.get_string("reschedule", "invalid_match_id"))

    @commands.command(name='name_change')
    @commands.guild_only()
    @commands.bot_has_permissions(manage_nicknames=True, manage_roles=True)
    async def name_change(self, ctx):
        """Allows players to change their nickname to their osu! username"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if tournament and not tournament.name_change_enabled:
            raise commands.DisabledCommand()
        discord_id = str(ctx.author.id)
        user = self.client.session.query(User).filter(User.discord_id == helpers.crypt.hash_str(discord_id)).first()
        if not user:
            raise UserNotLinked()
        if not user.verified:
            raise UserNotVerified()
        osu_id = user.osu_id
        osu_users = api.osu.OsuApi.get_user(osu_id)
        if not osu_users:
            raise OsuError()
        previous_name = ctx.author.nick
        if not previous_name:
            previous_name = ctx.author.name
        osu_name = osu_users[0][api.osu.User.NAME]
        write_access = True
        if tournament:
            players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == tournament.players_spreadsheet_id).first()
            if players_spreadsheet:
                range_names = players_spreadsheet.get_ranges()
                try:
                    cells = api.spreadsheet.get_ranges(players_spreadsheet.spreadsheet_id, range_names)
                    i = 0
                    while i < len(cells):
                        if players_spreadsheet.range_team_name.lower() != "none":
                            i += 1
                        j, k = self.get_player_from_cells(cells[i], previous_name)
                        if j != None:
                            cells[i][j][k] = osu_name
                            api.spreadsheet.write_ranges(players_spreadsheet.spreadsheet_id, range_names, cells)
                            break
                        i += 1
                except googleapiclient.errors.HttpError:
                    write_access = False
            schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == tournament.schedules_spreadsheet_id).first()
            if schedules_spreadsheet:
                try:
                    cells = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name)
                    j, k = self.get_player_from_cells(cells, previous_name)
                    if j != None:
                        cells[j][k] = osu_name
                        api.spreadsheet.write_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name, cells)                        
                except googleapiclient.errors.HttpError:
                    write_access = False
            if tournament.challonge:
                try:
                    participants = api.challonge.get_participants(tournament.challonge)
                    for participant in participants:
                        if participant["name"] == previous_name:
                            api.challonge.update_participant(tournament.challonge, participant["id"], name=osu_name)
                except Exception:
                    write_access = False
        try:
            await ctx.author.edit(nick=osu_name)
        except discord.Forbidden:
            raise commands.BotMissingPermissions(["change_owner_nickname"])
        await ctx.send(self.get_string("name_change", "success"))
        if not write_access:
            await ctx.send(self.get_string("name_change", "no_access"))

    def get_player_from_cells(self, cells, previous_name):
        for j, player_row in enumerate(cells):
            for k, player in enumerate(player_row):
                if player == previous_name:
                    return j, k
        return None, None

    @commands.command(name='disable_name_change', aliases=['enable_name_change'])
    @commands.guild_only()
    async def disable_name_change(self, ctx):
        """Disables or enables the name_change command for a tournament"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            raise NotBotAdmin()
        tournament.name_change_enabled = not tournament.name_change_enabled
        self.client.session.commit()
        if tournament.name_change_enabled:
            await ctx.send(self.get_string("disable_name_change", "success", "enabled"))
        else:
            await ctx.send(self.get_string("disable_name_change", "success", "disabled"))

    @commands.command(name='post_result')
    @commands.guild_only()
    async def post_result(self, ctx, match_id: str, n_warmup: int, best_of: int, roll_team1: int, roll_team2: int, *, parameters: str):
        """Allows referees to post the result of a match"""
        if n_warmup < 0:
            raise commands.UserInputError()
        if (best_of < 0) or (best_of % 2 != 1):
            raise commands.UserInputError()
        parameters = parameters.split("] ", 1)
        if len(parameters) != 2:
            raise commands.UserInputError()
        mp_links = literal_eval(parameters[0] + "]")
        mp_ids = []
        for mp_link in mp_links:
            mp_ids.append(api.osu.Match.get_from_string(mp_link))
        bans = parameters[1].split("; ")
        if len(bans) % 2 != 0:
            raise commands.UserInputError()
        bans_team1 = ", ".join(bans[:int(len(bans)/2)])
        bans_team2 = ", ".join(bans[int(len(bans)/2):])
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        roles = ctx.guild.roles
        referee_role = self.get_role(roles, tournament.referee_role_id, "Referee")
        if not referee_role:
            raise NoRefereeRole()
        if not any(referee_role.id == role.id for role in ctx.author.roles):
            raise NotAReferee()
        schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == tournament.schedules_spreadsheet_id).first()
        if not schedules_spreadsheet:
            raise NoSpreadsheet("schedules_spreadsheet")
        players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == tournament.players_spreadsheet_id).first()
        if not players_spreadsheet:
            raise NoSpreadsheet("players_spreadsheet")
        range_names = players_spreadsheet.get_ranges()
        try:
            cells = api.spreadsheet.get_ranges(players_spreadsheet.spreadsheet_id, range_names)
        except googleapiclient.errors.HttpError:
            raise SpreadsheetError()
        try:
            values = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name)
        except googleapiclient.errors.HttpError:
            raise SpreadsheetError()
        tuples = schedules_spreadsheet.parse_parameters()
        for y, row in enumerate(values):
            for x, value in enumerate(row):
                if value == match_id:
                    incr_x, incr_y = tuples[0]
                    team_name1 = values[y + incr_y][x + incr_x]
                    incr_x, incr_y = tuples[1]
                    team_name2 = values[y + incr_y][x + incr_x]
                    if roll_team1 > roll_team2:
                        winner_roll = team_name1
                        bans_winner_roll = bans_team1
                        loser_roll = team_name2
                        bans_loser_roll = bans_team2
                    else:
                        winner_roll = team_name2
                        bans_winner_roll = bans_team2
                        loser_roll = team_name1
                        bans_loser_roll = bans_team1
                    players_team1 = []
                    players_team2 = []
                    if range_team_name.lower() != "none":
                        i = 0
                        while i < len(cells):
                            for row in cells[i]:
                                for cell in row:
                                    if cell == team_name1:
                                        for player_row in cells[i + 1]:
                                            for player in player_row:
                                                players_team1.append(player)
                                    elif cell == team_name2:
                                        for player_row in cells[i + 1]:
                                            for player in player_row:
                                                players_team2.append(player)
                            i += 1
                    else:
                        players_team1.append(team_name1)
                        players_team2.append(team_name2)
                    i = 0
                    players_team1 = api.osu.User.names_to_ids(players_team1)
                    players_team2 = api.osu.User.names_to_ids(players_team2)
                    score_team1 = 0
                    score_team2 = 0
                    for mp_id in mp_ids:
                        matches = api.osu.OsuApi.get_match(mp_id)
                        if not matches:
                            raise InvalidMpLink()
                        games = matches["games"]
                        i = 0
                        while i < len(games):
                            if n_warmup > 0:
                                n_warmup -= 1
                            else:
                                if i + 1 < len(games):
                                    beatmap_id = games[i][api.osu.Game.BEATMAP_ID]
                                    if games[i + 1][api.osu.Game.BEATMAP_ID] == beatmap_id:
                                        i += 1
                                        pass
                                total_team1 = 0
                                total_team2 = 0
                                for score in games[i][api.osu.Game.SCORES]:
                                    if score[api.osu.Game.Score.PASS] == "1":
                                        if score[api.osu.Game.Score.USER_ID] in players_team1:
                                            total_team1 += int(score[api.osu.Game.Score.SCORE])
                                        elif score[api.osu.Game.Score.USER_ID] in players_team2:
                                            total_team2 += int(score[api.osu.Game.Score.SCORE])
                                if total_team1 > total_team2:
                                    if score_team1 < int(best_of / 2) + 1:
                                        score_team1 += 1
                                elif total_team1 < total_team2:
                                    if score_team2 < int(best_of / 2) + 1:
                                        score_team2 += 1
                            i += 1
                        mp_links = ""
                        for mp_id in mp_ids:
                            mp_links += "https://osu.ppy.sh/community/matches/" + mp_id + "; "
                        mp_links = mp_links[:-2]
                        if tournament.post_result_message:
                            result_string = tournament.post_result_message
                        else:
                            result_string = self.get_string("post_result", "success")
                        result_string = result_string.replace("%match_id", match_id)
                        result_string = result_string.replace("%mp_link", mp_links)
                        result_string = result_string.replace("%team1", team_name1)
                        result_string = result_string.replace("%team2", team_name2)
                        result_string = result_string.replace("%score_team1", str(score_team1))
                        result_string = result_string.replace("%score_team2", str(score_team2))
                        result_string = result_string.replace("%bans_team1", bans_team1)
                        result_string = result_string.replace("%bans_team2", bans_team2)                           
                        result_string = result_string.replace("%winner_roll", winner_roll)
                        result_string = result_string.replace("%loser_roll", loser_roll)
                        result_string = result_string.replace("%bans_winner_roll", bans_winner_roll)
                        result_string = result_string.replace("%bans_loser_roll", bans_loser_roll)
                        if tournament.challonge:
                            t_id = 0
                            try:
                                t = api.challonge.get_tournament(tournament.challonge)
                                t_id = t["id"]
                                if not t["started_at"]:
                                    api.challonge.start_tournament(t_id)
                                participants = api.challonge.get_participants(t_id)
                                for participant in participants:
                                    if participant["name"] == team_name1:
                                        participant1 = participant
                                    elif participant["name"] == team_name2:
                                        participant2 = participant
                                participant_matches = api.challonge.get_participant(t_id, participant1["id"], include_matches=1)["matches"]
                            except api.challonge.ServerError:
                                if tournament.staff_channel_id:
                                    channel = self.client.get_channel(int(tournament.staff_channel_id))
                                else:
                                    channel = ctx
                                await channel.send(self.get_string("", "challonge_server_error"))
                                await ctx.send(result_string)
                                return
                            for match in participant_matches:
                                match = match["match"]
                                player1, player2 = api.challonge.is_match_containing_participants(match, participant1, participant2)
                                if player1:
                                    if player1["name"] == participant1["name"]:
                                        match_score = str(score_team1) + "-" + str(score_team2)
                                    else:
                                        match_score = str(score_team2) + "-" + str(score_team1)
                                    if score_team1 > score_team2:
                                        match_winner = api.challonge.get_id_from_participant(player1)
                                    else:
                                        match_winner = api.challonge.get_id_from_participant(player2)
                                    api.challonge.update_match(t_id, match["id"], scores_csv=match_score, winner_id=match_winner)
                                    await ctx.send(result_string)
                                    return
                            raise MatchNotFound()
                        await ctx.send(result_string)
                        return
        raise InvalidMatchId()

    @post_result.error
    async def post_result_handler(self, ctx, error):
        """Error handler of post_result function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("post_result", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("post_result", "usage", ctx.prefix))
        elif isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("post_result", "usage", ctx.prefix))
        elif isinstance(error, NoSpreadsheet):
            if error.spreadsheet == "schedules_spreadsheet":
                await ctx.send(self.get_string("post_result", "no_schedules_spreadsheet", ctx.prefix))
            elif error.spreadsheet == "players_spreadsheet":
                await ctx.send(self.get_string("post_result", "no_players_spreadsheet", ctx.prefix))
        elif isinstance(error, SpreadsheetError):
            await ctx.send(self.get_string("post_result", "spreadsheet_error", ctx.prefix))
        elif isinstance(error, InvalidMatchId):
            await ctx.send(self.get_string("post_result", "invalid_match_id"))
        elif isinstance(error, InvalidMpLink):
            await ctx.send(self.get_string("post_result", "invalid_mp_link"))
        elif isinstance(error, MatchNotFound):
            await ctx.send(self.get_string("post_result", "match_not_found"))

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
