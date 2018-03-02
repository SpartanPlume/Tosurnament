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
from databases.bracket import Bracket
from databases.players_spreadsheet import PlayersSpreadsheet
from databases.schedules_spreadsheet import SchedulesSpreadsheet
from databases.reschedule_message import RescheduleMessage
from databases.staff_reschedule_message import StaffRescheduleMessage
from databases.end_tournament_message import EndTournamentMessage

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

class NoTournament(commands.CommandError):
    """Special exception if a guild does not have any tournament running"""
    pass

class TournamentAlreadyCreated(commands.CommandError):
    """Special exception if a guild already have a tournament running"""
    pass

class NoBracket(commands.CommandError):
    """Special exception if a guild does not have the requested bracket"""
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
    """Special exception if there is no referee role on the guild"""
    pass

class NotAReferee(commands.CommandError):
    """Special exception if the user is not a referee"""
    pass

class NotAStreamer(commands.CommandError):
    """Special exception if the user is not a streamer"""
    pass

class NotACommentator(commands.CommandError):
    """Special exception if the user is not a commentator"""
    pass

class NotAStaff(commands.CommandError):
    """Special exception if the user is not a staff member"""
    pass

class NotTeamCaptain(commands.CommandError):
    """Special exception if the user is not a team captain"""
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

class UnknownError(commands.CommandError):
    """Special exception if unknown error"""
    def __init__(self, message=None):
        super().__init__()
        self.message = message

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
        print(error)
        if isinstance(error, UnknownError):
            await ctx.send(self.get_string("", "unknown_error"))
        elif isinstance(error, commands.NoPrivateMessage):
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
        elif isinstance(error, NoBracket):
            await ctx.send(self.get_string("", "no_bracket", ctx.prefix))
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
        elif isinstance(error, NotAStreamer):
            await ctx.send(self.get_string("", "not_a_streamer"))
        elif isinstance(error, NotACommentator):
            await ctx.send(self.get_string("", "not_a_commmentator"))
        elif isinstance(error, NotAStaff):
            await ctx.send(self.get_string("", "not_a_staff"))
        elif isinstance(error, NotTeamCaptain):
            await ctx.send(self.get_string("", "not_team_captain"))
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
    async def create_tournament(self, ctx, acronym: str, name: str, bracket_name: str = ""):
        """Creates a tournament"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if tournament:
            raise TournamentAlreadyCreated()
        tournament = Tournament(server_id=guild_id, acronym=acronym, name=name, name_change_enabled=True, ping_team=True)
        self.client.session.add(tournament)
        self.client.session.commit()
        if not bracket_name:
            bracket = Bracket(tournament_id=tournament.id, name=name, name_hash=name)
        else:
            bracket = Bracket(tournament_id=tournament.id, name=bracket_name, name_hash=bracket_name)
        self.client.session.add(bracket)
        self.client.session.commit()
        tournament.current_bracket_id = bracket.id
        self.client.session.commit()
        await ctx.send(self.get_string("create_tournament", "success"))

    @create_tournament.error
    async def create_tournament_handler(self, ctx, error):
        """Error handler of create_tournament function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("create_tournament", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("create_tournament", "usage", ctx.prefix))
        elif isinstance(error, TournamentAlreadyCreated):
            await ctx.send(self.get_string("create_tournament", "tournament_already_created", ctx.prefix))

    @commands.command(name='end_tournament')
    @commands.guild_only()
    @is_guild_owner()
    async def end_tournament(self, ctx):
        """Ends a tournament"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        message = await ctx.send(self.get_string("end_tournament", "are_you_sure"))
        end_tournament_message = EndTournamentMessage(message_id=helpers.crypt.hash_str(str(message.id)))
        self.client.session.add(end_tournament_message)
        self.client.session.commit()

    @end_tournament.error
    async def end_tournament_handler(self, ctx, error):
        """Error handler of end_tournament function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("end_tournament", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("end_tournament", "usage", ctx.prefix))

    @commands.command(name='create_bracket')
    @commands.guild_only()
    async def create_bracket(self, ctx, *, name: str):
        """Create a bracket"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(role.id == tournament.admin_role_id for role in ctx.author.roles):
            raise NotBotAdmin()
        bracket = Bracket(tournament_id=tournament.id, name=name, name_hash=name)
        self.client.session.add(bracket)
        self.client.session.commit()
        tournament.current_bracket_id = bracket.id
        self.client.session.commit()
        await ctx.send(self.get_string("create_bracket", "success"))

    @create_bracket.error
    async def create_bracket_handler(self, ctx, error):
        """Error handler of create_bracket function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("create_bracket", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("create_bracket", "usage", ctx.prefix))

    @commands.command(name='get_bracket', aliases=["get_brackets"])
    @commands.guild_only()
    async def get_bracket(self, ctx, *, name: str = ""):
        """Sets a bracket as current bracket or shows them all"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(role.id == tournament.admin_role_id for role in ctx.author.roles):
            raise NotBotAdmin()
        if name:
            bracket = self.client.session.query(Bracket).filter(Tournament.id == tournament.id).filter(Bracket.name_hash == helpers.crypt.hash_str(name)).first()
            if not bracket:
                raise NoBracket()
            tournament.current_bracket_id = bracket.id
            self.client.session.commit()
            await ctx.send(self.get_string("get_bracket", "success"))
        else:
            brackets = self.client.session.query(Bracket).filter(Tournament.id == tournament.id).all()
            if not brackets:
                raise UnknownError("get_bracket: query on brackets returned nothing.")
            brackets_string = ""
            for bracket in brackets:
                brackets_string += "`" + bracket.name + "`"
                if bracket.id == tournament.current_bracket_id:
                    brackets_string += " (current bracket)"
                brackets_string += "\n"
            await ctx.send(self.get_string("get_bracket", "default", ctx.prefix, brackets_string))

    @commands.command(name='set_bracket_name', aliases=["modify_bracket_name"])
    @commands.guild_only()
    async def set_bracket_name(self, ctx, *, name: str = ""):
        """Modifies the current bracket's name"""
        self.set_bracket_values(ctx, {"name": name, "name_hash": name})
        await ctx.send(self.get_string("set_bracket_name", "success"))

    @commands.command(name='set_bracket_role', aliases=["modify_bracket_role"])
    @commands.guild_only()
    async def set_bracket_role(self, ctx, *, role: discord.Role):
        """Modifies the current bracket's role"""
        self.set_bracket_values(ctx, {"bracket_role_id": str(role.id)})
        await ctx.send(self.get_string("set_bracket_role", "success"))

    @set_bracket_role.error
    async def set_bracket_role_handler(self, ctx, error):
        """Error handler of set_bracket_role function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_bracket_role", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_bracket_role", "usage", ctx.prefix))

    @commands.command(name='set_staff_channel')
    @commands.guild_only()
    async def set_staff_channel(self, ctx, *, channel: discord.TextChannel):
        """Sets the staff channel"""
        self.set_tournament_values(ctx, {"staff_channel_id": str(channel.id)})
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
    async def set_admin_role(self, ctx, *, role: discord.Role):
        """Sets the admin role"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        tournament.admin_role_id = str(role.id)
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
    async def set_referee_role(self, ctx, *, role: discord.Role):
        """Sets the referee role"""
        self.set_tournament_values(ctx, {"referee_role_id": str(role.id)})
        await ctx.send(self.get_string("set_referee_role", "success"))

    @set_referee_role.error
    async def set_referee_role_handler(self, ctx, error):
        """Error handler of set_referee_role function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_referee_role", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_referee_role", "usage", ctx.prefix))

    @commands.command(name='set_streamer_role')
    @commands.guild_only()
    async def set_streamer_role(self, ctx, *, role: discord.Role):
        """Sets the streamer role"""
        self.set_tournament_values(ctx, {"streamer_role_id": str(role.id)})
        await ctx.send(self.get_string("set_streamer_role", "success"))

    @set_streamer_role.error
    async def set_streamer_role_handler(self, ctx, error):
        """Error handler of set_streamer_role function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_streamer_role", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_streamer_role", "usage", ctx.prefix))

    @commands.command(name='set_commentator_role')
    @commands.guild_only()
    async def set_commentator_role(self, ctx, *, role: discord.Role):
        """Sets the commentator role"""
        self.set_tournament_values(ctx, {"commentator_role_id": str(role.id)})
        await ctx.send(self.get_string("set_commentator_role", "success"))

    @set_commentator_role.error
    async def set_commentator_role_handler(self, ctx, error):
        """Error handler of set_commentator_role function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_commentator_role", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_commentator_role", "usage", ctx.prefix))

    @commands.command(name='set_player_role')
    @commands.guild_only()
    async def set_player_role(self, ctx, *, role: discord.Role):
        """Sets the player role"""
        self.set_tournament_values(ctx, {"player_role_id": str(role.id)})
        await ctx.send(self.get_string("set_player_role", "success"))

    @set_player_role.error
    async def set_player_role_handler(self, ctx, error):
        """Error handler of set_player_role function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_player_role", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_player_role", "usage", ctx.prefix))

    @commands.command(name='set_team_captain_role')
    @commands.guild_only()
    async def set_team_captain_role(self, ctx, *, role: discord.Role = None):
        """Sets the team captain role"""
        if not role:
            self.set_tournament_values(ctx, {"team_captain_role_id": ""})
        else:
            self.set_tournament_values(ctx, {"team_captain_role_id": str(role.id)})
        await ctx.send(self.get_string("set_team_captain_role", "success"))

    @set_team_captain_role.error
    async def set_team_captain_role_handler(self, ctx, error):
        """Error handler of set_team_captain_role function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_team_captain_role", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_team_captain_role", "usage", ctx.prefix))

    @commands.command(name='set_ping_team')
    @commands.guild_only()
    async def set_ping_team(self, ctx, yes: bool):
        """Sets if team should be pinged or team captain shouldbe pinged"""
        self.set_tournament_values(ctx, {"ping_team": yes})
        await ctx.send(self.get_string("set_ping_team", "success"))

    @set_ping_team.error
    async def set_ping_team_handler(self, ctx, error):
        """Error handler of set_ping_team function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_ping_team", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_ping_team", "usage", ctx.prefix))

    @commands.command(name='set_challonge')
    @commands.guild_only()
    async def set_challonge(self, ctx, challonge_tournament: str):
        """Sets the challonge"""
        if challonge_tournament.startswith('http'):
            if challonge_tournament.endswith('/'):
                challonge_tournament = challonge_tournament[:-1]
            challonge_tournament = challonge_tournament.split('/')[-1]
        self.set_tournament_values(ctx, {"challonge": challonge_tournament})
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
        """Sets the post result message"""
        self.set_tournament_values(ctx, {"post_result_message": message})
        await ctx.send(self.get_string("set_post_result_message", "success"))  

    @set_post_result_message.error
    async def set_post_result_message_handler(self, ctx, error):
        """Error handler of set_post_result_message function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("set_post_result_message", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("set_post_result_message", "usage", ctx.prefix))

    def set_tournament_values(self, ctx, values):
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            raise NotBotAdmin()
        for key, value in values.items():
            setattr(tournament, key, value)
        self.client.session.commit()

    def set_bracket_values(self, ctx, values):
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            raise NotBotAdmin()
        bracket = self.client.session.query(Bracket).filter(Bracket.id == tournament.current_bracket_id).first()
        if not bracket:
            raise NoBracket()
        for key, value in values.items():
            setattr(bracket, key, value)
        self.client.session.commit()

    @commands.command(name='set_players_spreadsheet')
    @commands.guild_only()
    async def set_players_spreadsheet(self, ctx, spreadsheet_id: str, range_team_name: str, range_team: str, incr_column: str, incr_row: str, n_team: int):
        """Sets the players spreadsheet"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        bracket = self.client.session.query(Bracket).filter(Bracket.id == tournament.current_bracket_id).first()
        if not bracket:
            raise NoBracket()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            raise NotBotAdmin()
        if not re.match(r'^((.+!)?[A-Z]+\d*(:[A-Z]+\d*)?|[Nn][Oo][Nn][Ee])$', range_team_name):
            raise commands.UserInputError()
        if not re.match(r'^\[((, )?(.+!)?[A-Z]+\d*(:[A-Z]+\d*)?)+\]$', range_team):
            if not re.match(r'^(.+!)?[A-Z]+\d*(:[A-Z]+\d*)?$', range_team):
                raise commands.UserInputError()
        regex = re.compile(re.escape("n"), re.IGNORECASE)
        try:
            eval(regex.sub("1", incr_column))
            eval(regex.sub("1", incr_row))
        except NameError:
            raise commands.UserInputError()
        if bracket.players_spreadsheet_id:
            players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == bracket.players_spreadsheet_id).first()
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
        bracket.players_spreadsheet_id = players_spreadsheet.id
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
        brackets = self.client.session.query(Bracket).filter(Bracket.tournament_id == tournament.id).all()
        if not brackets:
            raise UnknownError("register: query on brackets returned nothing.")
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
        for bracket in brackets:
            players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == bracket.players_spreadsheet_id).first()
            if not players_spreadsheet:
                raise NoSpreadsheet()
            range_names = players_spreadsheet.get_ranges()
            n_range_team = players_spreadsheet.get_total_range_team()
            try:
                cells = api.spreadsheet.get_ranges(players_spreadsheet.spreadsheet_id, range_names)
            except googleapiclient.errors.HttpError:
                raise SpreadsheetError()
            i = 0
            while i < len(cells):
                team_name = ""
                if players_spreadsheet.range_team_name.lower() != "none":
                    team_name = self.get_team_name(cells[i])
                    i += 1
                team_captain = self.get_team_captain_name(cells[i])
                for _ in range(n_range_team):
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
                                bracket_role = self.get_role(roles, bracket.bracket_role_id)
                                if bracket_role:
                                    await ctx.author.add_roles(bracket_role)
                                if team_captain == osu_name:
                                    team_captain_role = self.get_role(roles, tournament.team_captain_role_id)
                                    if team_captain_role:
                                        await ctx.author.add_roles(team_captain_role)
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

    def get_team_name(self, cells):
        for row in cells:
            for cell in row:
                if cell:
                    return cell
        return ""

    def get_team_captain_name(self, cells):
        for player_row in cells:
            for player in player_row:
                if player:
                    return player
        return ""

    def get_role(self, roles, role_id=None, role_name=""):
        """Gets a role from its id or name"""
        wanted_role = None
        if not role_id and not role_name:
            return wanted_role
        elif not role_id:
            for role in roles:
                if role.name == role_name:
                    wanted_role = role
                    break
        else:
            for role in roles:
                if str(role.id) == role_id:
                    wanted_role = role
                    break
        return wanted_role

    @commands.command(name='set_schedules_spreadsheet')
    @commands.guild_only()
    async def set_schedules_spreadsheet(self, ctx, spreadsheet_id: str, range_name: str, range_match_id: str, *, parameters: str):
        """Sets the schedules spreadsheet"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        bracket = self.client.session.query(Bracket).filter(Bracket.id == tournament.current_bracket_id).first()
        if not bracket:
            raise NoBracket()
        if not tournament.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not any(tournament.admin_role_id == role.id for role in ctx.author.roles):
            raise NotBotAdmin()
        if not re.match(r'^((.+!)?[A-Z]+\d*(:[A-Z]+\d*)?|[Nn][Oo][Nn][Ee]|[Aa][Ll][Ll])$', range_name):
            raise commands.UserInputError()
        if not re.match(r'^((.+!)?[A-Z]+\d*:[A-Z]+\d*)$', range_match_id):
            raise commands.UserInputError()
        if not re.match(r'^(\(\d+, ?\d+\) ?){3}(\(\d+, ?\d+\) ?|[Nn][Oo][Nn][Ee] ?)(\(\d+, ?\d+\) ?|[Nn][Oo][Nn][Ee] ?|\[(\(\d+, ?\d+\)(, )?)+\] ?)( ?\((\d+, ?){2}"(?:[^"\\]|\\.)*"\))*$', parameters):
            raise commands.UserInputError()
        if bracket.schedules_spreadsheet_id:
            schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == bracket.schedules_spreadsheet_id).first()
        else:
            schedules_spreadsheet = SchedulesSpreadsheet()
            self.client.session.add(schedules_spreadsheet)
        schedules_spreadsheet.spreadsheet_id = spreadsheet_id
        schedules_spreadsheet.range_name = range_name
        schedules_spreadsheet.range_match_id = range_match_id
        schedules_spreadsheet.parameters = parameters
        self.client.session.commit()
        bracket.schedules_spreadsheet_id = schedules_spreadsheet.id
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
        brackets = self.client.session.query(Bracket).filter(Bracket.tournament_id == tournament.id).all()
        if not brackets:
            raise UnknownError("reschedule: query on brackets returned nothing.")
        roles = ctx.guild.roles
        player_role = self.get_role(roles, tournament.player_role_id, "Player")
        if not player_role:
            raise NoPlayerRole()
        if not any(player_role.id == role.id for role in ctx.author.roles):
            raise NotAPlayer()
        date = datetime.datetime.strptime(date + "2008", '%d/%m %H:%M%Y')
        for bracket in brackets:
            schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == bracket.schedules_spreadsheet_id).first()
            if not schedules_spreadsheet:
                raise NoSpreadsheet()
            all_sheets = False
            if not "!" in schedules_spreadsheet.range_name:
                all_sheets = True
            try:
                if all_sheets:
                    sheets = api.spreadsheet.get_spreadsheet_with_values(schedules_spreadsheet.spreadsheet_id)
                else:
                    values = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name)
                    sheet_range = schedules_spreadsheet.range_name.split("!")
                    sheets = [{"name": sheet_range[0], "range": sheet_range[1], "values": values}]
            except googleapiclient.errors.HttpError:
                raise SpreadsheetError()
            tuples = schedules_spreadsheet.parse_parameters()
            for sheet in sheets:
                values = sheet["values"]
                for y, row in enumerate(values):
                    for x, value in enumerate(row):
                        if value == match_id:
                            incr_x, incr_y = tuples[0]
                            team_name1 = values[y + incr_y][x + incr_x]
                            incr_x, incr_y = tuples[1]
                            team_name2 = values[y + incr_y][x + incr_x]
                            tuples = tuples[5:]
                            ally_team_captain = None
                            enemy_team_captain = None
                            is_team_captain = False
                            players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == bracket.players_spreadsheet_id).first()
                            if not players_spreadsheet:
                                raise NoSpreadsheet("players_spreadsheet")
                            if players_spreadsheet.range_team_name.lower() != "none":
                                range_names = players_spreadsheet.get_ranges()
                                n_range_team = players_spreadsheet.get_total_range_team()
                                try:
                                    cells = api.spreadsheet.get_ranges(players_spreadsheet.spreadsheet_id, range_names)
                                except googleapiclient.errors.HttpError:
                                    raise SpreadsheetError()
                                i = 0
                                while i < len(cells):
                                    team_name = self.get_team_name(cells[i])
                                    i += 1
                                    team_captain = self.get_team_captain_name(cells[i])
                                    if team_name == team_name1 or team_name == team_name2:
                                        if team_captain == ctx.author.display_name:
                                            ally_team_captain = ctx.author
                                            is_team_captain = True
                                        elif team_captain:
                                            enemy_team_captain = ctx.guild.get_member_named(team_captain)
                                    i += n_range_team
                            else:
                                is_team_captain = True
                            if not is_team_captain:
                                raise NotTeamCaptain()
                            date_string = ""
                            date_flags = ""
                            for tup in tuples:
                                incr_x, incr_y, date_flag = tup
                                if y + incr_y < len(values) and x + incr_x < len(values[y + incr_y]):
                                    date_flags += date_flag
                                    date_string += values[y + incr_y][x + incr_x]
                            previous_date = datetime.datetime.strptime(date_string, date_flags)
                            player_name = ctx.author.display_name
                            role_team1 = self.get_role(roles, role_name=team_name1)
                            role_team2 = self.get_role(roles, role_name=team_name2)
                            reschedule_message = RescheduleMessage(tournament_id=tournament.id)
                            reschedule_message.match_id = match_id
                            reschedule_message.ally_user_id = bytes('', 'utf-8')
                            reschedule_message.ally_role_id = bytes('', 'utf-8')
                            reschedule_message.enemy_user_id = bytes('', 'utf-8')
                            reschedule_message.enemy_role_id = bytes('', 'utf-8')
                            if not tournament.ping_team and ally_team_captain and enemy_team_captain:
                                ally_name = ctx.author.display_name
                                enemy_mention = enemy_team_captain.mention
                                reschedule_message.ally_user_id = str(ally_team_captain.id)
                                reschedule_message.enemy_user_id = str(enemy_team_captain.id)
                            elif role_team1 and role_team2 and any(role_team1.id == role.id for role in ctx.author.roles):
                                ally_name = role_team1.name
                                enemy_mention = role_team2.mention
                                reschedule_message.ally_role_id = str(role_team1.id)
                                reschedule_message.enemy_role_id = str(role_team2.id)
                            elif role_team1 and role_team2 and any(role_team2.id == role.id for role in ctx.author.roles):
                                ally_name = role_team2.name
                                enemy_mention = role_team1.mention
                                reschedule_message.ally_role_id = str(role_team2.id)
                                reschedule_message.enemy_role_id = str(role_team1.id)
                            elif team_name1 == player_name:
                                ally_name = player_name
                                enemy = ctx.guild.get_member_named(team_name2)
                                enemy_mention = enemy.mention
                                reschedule_message.ally_user_id = str(ctx.author.id)
                                reschedule_message.enemy_user_id = str(enemy.id)
                            elif team_name2 == player_name:
                                ally_name = player_name
                                enemy = ctx.guild.get_member_named(team_name1)
                                enemy_mention = enemy.mention
                                reschedule_message.ally_user_id = str(ctx.author.id)
                                reschedule_message.enemy_user_id = str(enemy.id)
                            else:
                                raise InvalidMatch()
                            previous_date_string = previous_date.strftime("**%d %B at %H:%M UTC**")
                            new_date_string = date.strftime("**%d %B at %H:%M UTC**")
                            reschedule_message.previous_date = previous_date.strftime("%d/%m/%y %H:%M")
                            reschedule_message.new_date = date.strftime("%d/%m/%y %H:%M")
                            sent_message = await ctx.send(self.get_string("reschedule", "success", enemy_mention, ally_name, match_id, previous_date_string, new_date_string))
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

    @commands.command(name='name_change', aliases=["change_name"])
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
        previous_name = ctx.author.display_name
        osu_name = osu_users[0][api.osu.User.NAME]
        write_access = True
        name_changed_players_spreadsheet = True
        name_changed_schedules_spreadsheet = True
        if tournament:
            brackets = self.client.session.query(Bracket).filter(Bracket.tournament_id == tournament.id).all()
            if not brackets:
                raise UnknownError("name_change: query on brackets returned nothing.")
            if self.get_role(ctx.author.roles, tournament.player_role_id, "Player"):
                name_changed_players_spreadsheet = False
                for bracket in brackets:
                    players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == bracket.players_spreadsheet_id).first()
                    if players_spreadsheet:
                        range_names = players_spreadsheet.get_ranges()
                        n_range_team = players_spreadsheet.get_total_range_team()
                        try:
                            cells = api.spreadsheet.get_ranges(players_spreadsheet.spreadsheet_id, range_names, "ROWS", "FORMULA")
                            i = 0
                            while i < len(cells):
                                if players_spreadsheet.range_team_name.lower() != "none":
                                    i += 1
                                for _ in range(n_range_team):
                                    j, k = self.get_player_from_cells(cells[i], previous_name)
                                    if j != None:
                                        cells[i][j][k] = osu_name
                                        api.spreadsheet.write_ranges(players_spreadsheet.spreadsheet_id, range_names, cells)
                                        name_changed_players_spreadsheet = True
                                        i = len(cells)
                                        break
                                    i += 1
                        except googleapiclient.errors.HttpError:
                            write_access = False
                    if bracket.challonge:
                        try:
                            participants = api.challonge.get_participants(bracket.challonge)
                            for participant in participants:
                                if participant["name"] == previous_name:
                                    api.challonge.update_participant(bracket.challonge, participant["id"], name=osu_name)
                        except Exception:
                            write_access = False
            if self.get_role(ctx.author.roles, tournament.player_role_id, "Player") or self.get_role(ctx.author.roles, tournament.referee_role_id, "Referee"):
                name_changed_schedules_spreadsheet = False
                for bracket in brackets:
                    schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == bracket.schedules_spreadsheet_id).first()
                    if schedules_spreadsheet:
                        all_sheets = False
                        if not "!" in schedules_spreadsheet.range_name:
                            all_sheets = True
                        try:
                            if all_sheets:
                                sheets = api.spreadsheet.get_spreadsheet_with_values(schedules_spreadsheet.spreadsheet_id)
                            else:
                                cells = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name)
                                sheet_range = schedules_spreadsheet.range_name.split("!")
                                sheets = [{"name": sheet_range[0], "range": sheet_range[1], "values": cells}]
                            for sheet in sheets:
                                cells = sheet["values"]
                                j, k = self.get_player_from_cells(cells, previous_name)
                                if j != None:
                                    cells[j][k] = osu_name
                                    api.spreadsheet.write_range(schedules_spreadsheet.spreadsheet_id, sheet["name"] + "!" + sheet["range"], cells)
                                    name_changed_schedules_spreadsheet = True
                                    break
                        except googleapiclient.errors.HttpError:
                            write_access = False
        try:
            await ctx.author.edit(nick=osu_name)
        except discord.Forbidden:
            raise commands.BotMissingPermissions(["change_owner_nickname"])
        await ctx.send(self.get_string("name_change", "success"))
        if not write_access or not name_changed_players_spreadsheet or not name_changed_schedules_spreadsheet:
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

    @commands.command(name='take_match', aliases=["take_matches"])
    @commands.guild_only()
    async def take_match(self, ctx, *args):
        """Allows staffs to take matches"""
        await self.take_or_drop_match(ctx, args)

    @take_match.error
    async def take_match_handler(self, ctx, error):
        """Error handler of take_match function"""
        if isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("take_match", "usage", ctx.prefix))
        elif isinstance(error, NoSpreadsheet):
            await ctx.send(self.get_string("take_match", "no_schedules_spreadsheet", ctx.prefix))
        elif isinstance(error, SpreadsheetError):
            await ctx.send(self.get_string("take_match", "spreadsheet_error", ctx.prefix))

    @commands.command(name='take_match_as_referee', aliases=["take_matches_as_referee"])
    @commands.guild_only()
    async def take_match_as_referee(self, ctx, *args):
        """Allows referees to take matches"""
        await self.take_or_drop_match(ctx, args, True, True, False, False)

    @take_match_as_referee.error
    async def take_match_as_referee_handler(self, ctx, error):
        """Error handler of take_match_as_referee function"""
        if isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("take_match_as_referee", "usage", ctx.prefix))
        elif isinstance(error, NoSpreadsheet):
            await ctx.send(self.get_string("take_match", "no_schedules_spreadsheet", ctx.prefix))
        elif isinstance(error, SpreadsheetError):
            await ctx.send(self.get_string("take_match", "spreadsheet_error", ctx.prefix))

    @commands.command(name='take_match_as_streamer', aliases=["take_matches_as_streamer"])
    @commands.guild_only()
    async def take_match_as_streamer(self, ctx, *args):
        """Allows streamers to take matches"""
        await self.take_or_drop_match(ctx, args, True, False, True, False)

    @take_match_as_streamer.error
    async def take_match_as_streamer_handler(self, ctx, error):
        """Error handler of take_match_as_streamer function"""
        if isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("take_match_as_streamer", "usage", ctx.prefix))
        elif isinstance(error, NoSpreadsheet):
            await ctx.send(self.get_string("take_match", "no_schedules_spreadsheet", ctx.prefix))
        elif isinstance(error, SpreadsheetError):
            await ctx.send(self.get_string("take_match", "spreadsheet_error", ctx.prefix))

    @commands.command(name='take_match_as_commentator', aliases=["take_matches_as_commentator"])
    @commands.guild_only()
    async def take_match_as_commentator(self, ctx, *args):
        """Allows commentators to take matches"""
        await self.take_or_drop_match(ctx, args, True, False, False, True)

    @take_match_as_commentator.error
    async def take_match_as_commentator_handler(self, ctx, error):
        """Error handler of take_match_as_commentator function"""
        if isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("take_match_as_commentator", "usage", ctx.prefix))
        elif isinstance(error, NoSpreadsheet):
            await ctx.send(self.get_string("take_match", "no_schedules_spreadsheet", ctx.prefix))
        elif isinstance(error, SpreadsheetError):
            await ctx.send(self.get_string("take_match", "spreadsheet_error", ctx.prefix))

    @commands.command(name='drop_match', aliases=["drop_matches"])
    @commands.guild_only()
    async def drop_match(self, ctx, *args):
        """Allows staffs to drop matches"""
        await self.take_or_drop_match(ctx, args, False)

    @drop_match.error
    async def drop_match_handler(self, ctx, error):
        """Error handler of drop_match function"""
        if isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("drop_match", "usage", ctx.prefix))
        elif isinstance(error, NoSpreadsheet):
            await ctx.send(self.get_string("drop_match", "no_schedules_spreadsheet", ctx.prefix))
        elif isinstance(error, SpreadsheetError):
            await ctx.send(self.get_string("drop_match", "spreadsheet_error", ctx.prefix))

    @commands.command(name='drop_match_as_referee', aliases=["drop_matches_as_referee"])
    @commands.guild_only()
    async def drop_match_as_referee(self, ctx, *args):
        """Allows referees to drop matches"""
        await self.take_or_drop_match(ctx, args, False, True, False, False)

    @drop_match_as_referee.error
    async def drop_match_as_referee_handler(self, ctx, error):
        """Error handler of drop_match_as_referee function"""
        if isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("drop_match_as_referee", "usage", ctx.prefix))
        elif isinstance(error, NoSpreadsheet):
            await ctx.send(self.get_string("drop_match", "no_schedules_spreadsheet", ctx.prefix))
        elif isinstance(error, SpreadsheetError):
            await ctx.send(self.get_string("drop_match", "spreadsheet_error", ctx.prefix))

    @commands.command(name='drop_match_as_streamer', aliases=["drop_matches_as_streamer"])
    @commands.guild_only()
    async def drop_match_as_streamer(self, ctx, *args):
        """Allows streamers to drop matches"""
        await self.take_or_drop_match(ctx, args, False, False, True, False)

    @drop_match_as_streamer.error
    async def drop_match_as_streamer_handler(self, ctx, error):
        """Error handler of drop_match_as_streamer function"""
        if isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("drop_match_as_streamer", "usage", ctx.prefix))
        elif isinstance(error, NoSpreadsheet):
            await ctx.send(self.get_string("drop_match", "no_schedules_spreadsheet", ctx.prefix))
        elif isinstance(error, SpreadsheetError):
            await ctx.send(self.get_string("drop_match", "spreadsheet_error", ctx.prefix))

    @commands.command(name='drop_match_as_commentator', aliases=["drop_matches_as_commentator"])
    @commands.guild_only()
    async def drop_match_as_commentator(self, ctx, *args):
        """Allows commentators to drop matches"""
        await self.take_or_drop_match(ctx, args, False, False, False, True)

    @drop_match_as_commentator.error
    async def drop_match_as_commentator_handler(self, ctx, error):
        """Error handler of drop_match_as_commentator function"""
        if isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("drop_match_as_commentator", "usage", ctx.prefix))
        elif isinstance(error, NoSpreadsheet):
            await ctx.send(self.get_string("drop_match", "no_schedules_spreadsheet", ctx.prefix))
        elif isinstance(error, SpreadsheetError):
            await ctx.send(self.get_string("drop_match", "spreadsheet_error", ctx.prefix))

    async def take_or_drop_match(self, ctx, match_ids, take=True, as_referee=True, as_streamer=True, as_commentator=True):
        if not match_ids:
            raise commands.UserInputError()
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        brackets = self.client.session.query(Bracket).filter(Bracket.tournament_id == tournament.id).all()
        if not brackets:
            raise UnknownError("take_match: query on brackets returned nothing.")
        roles = ctx.author.roles
        is_referee = bool(self.get_role(roles, tournament.referee_role_id, "Referee"))
        is_streamer = bool(self.get_role(roles, tournament.streamer_role_id, "Streamer"))
        is_commentator = bool(self.get_role(roles, tournament.streamer_role_id, "Commentator"))
        if not is_referee and not is_streamer and not is_commentator:
            raise NotAStaff()
        if as_referee and not as_streamer and not as_commentator and not is_referee:
            raise NotAReferee()
        if not as_referee and as_streamer and not as_commentator and not is_streamer:
            raise NotAStreamer()
        if not as_referee and not as_streamer and as_commentator and not is_commentator:
            raise NotACommentator()
        staff_name = ctx.author.display_name
        referee_successfully_taken_matches_id = []
        referee_already_taken_matches_id = []
        streamer_successfully_taken_matches_id = []
        streamer_already_taken_matches_id = []
        commentator_successfully_taken_matches_id = []
        commentator_already_taken_matches_id = []
        for bracket in brackets:
            schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == bracket.schedules_spreadsheet_id).first()
            if not schedules_spreadsheet:
                raise NoSpreadsheet("schedules_spreadsheet")
            all_sheets = False
            if not "!" in schedules_spreadsheet.range_name:
                all_sheets = True
            try:
                if all_sheets:
                    sheets = api.spreadsheet.get_spreadsheet_with_values(schedules_spreadsheet.spreadsheet_id)
                else:
                    values = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name, "ROWS", "FORMULA")
                    sheet_range = schedules_spreadsheet.range_name.split("!")
                    sheets = [{"name": sheet_range[0], "range": sheet_range[1], "values": values}]
            except googleapiclient.errors.HttpError:
                raise SpreadsheetError()
            tuples = schedules_spreadsheet.parse_parameters()
            for sheet in sheets:
                values = sheet["values"]
                write_values = False
                for match_id in match_ids:
                    for y, row in enumerate(values):
                        for x, value in enumerate(row):
                            if value == match_id:
                                if as_referee and is_referee:
                                    incr_x, incr_y = tuples[2]
                                    while y + incr_y >= len(values):
                                        values.append([])
                                    while x + incr_x >= len(values[y + incr_y]):
                                        values[y + incr_y].append("")
                                    if (take and not values[y + incr_y][x + incr_x]) or (not take and values[y + incr_y][x + incr_x] == staff_name):
                                        if take:
                                            values[y + incr_y][x + incr_x] = staff_name
                                        else:
                                            values[y + incr_y][x + incr_x] = ""
                                        write_values = True
                                        referee_successfully_taken_matches_id.append(match_id)
                                    else:
                                        referee_already_taken_matches_id.append(match_id)
                                if as_streamer and is_streamer and not isinstance(tuples[3], str):
                                    incr_x, incr_y = tuples[3]
                                    while y + incr_y >= len(values):
                                        values.append([])
                                    while x + incr_x >= len(values[y + incr_y]):
                                        values[y + incr_y].append("")
                                    if (take and not values[y + incr_y][x + incr_x]) or (not take and values[y + incr_y][x + incr_x] == staff_name):
                                        if take:
                                            values[y + incr_y][x + incr_x] = staff_name
                                        else:
                                            values[y + incr_y][x + incr_x] = ""
                                        write_values = True
                                        streamer_successfully_taken_matches_id.append(match_id)
                                    else:
                                        streamer_already_taken_matches_id.append(match_id)
                                if as_commentator and is_commentator and not isinstance(tuples[4], str):
                                    add_commentator = False
                                    for incr_x, incr_y in tuples[4]:
                                        while y + incr_y >= len(values):
                                            values.append([])
                                        while x + incr_x >= len(values[y + incr_y]):
                                            values[y + incr_y].append("")
                                        if take and values[y + incr_y][x + incr_x] == staff_name:
                                            break
                                        if (take and not values[y + incr_y][x + incr_x]) or (not take and values[y + incr_y][x + incr_x] == staff_name):
                                            if take:
                                                values[y + incr_y][x + incr_x] = staff_name
                                            else:
                                                values[y + incr_y][x + incr_x] = ""
                                            write_values = True
                                            add_commentator = True
                                            commentator_successfully_taken_matches_id.append(match_id)
                                            break
                                    if not add_commentator:
                                        commentator_already_taken_matches_id.append(match_id)
                if write_values:
                    try:
                        api.spreadsheet.write_range(schedules_spreadsheet.spreadsheet_id, sheet["name"] + "!" + sheet["range"], values)
                    except googleapiclient.errors.HttpError:
                        raise SpreadsheetError()
        invalid_matches_id = list(set(match_ids) - set(referee_successfully_taken_matches_id) - set(streamer_successfully_taken_matches_id) - set(commentator_successfully_taken_matches_id) - set(referee_already_taken_matches_id) - set(streamer_already_taken_matches_id) - set(commentator_already_taken_matches_id))
        if take:
            string = self.format_take_match_string(self.get_string("take_match", "successfully_taken_matches_id", "Referee"), referee_successfully_taken_matches_id)
            string += self.format_take_match_string(self.get_string("take_match", "successfully_taken_matches_id", "Streamer"), streamer_successfully_taken_matches_id)
            string += self.format_take_match_string(self.get_string("take_match", "successfully_taken_matches_id", "Commentator"), commentator_successfully_taken_matches_id)
            string += self.format_take_match_string(self.get_string("take_match", "already_taken_matches_id", "Referee"), referee_already_taken_matches_id)
            string += self.format_take_match_string(self.get_string("take_match", "already_taken_matches_id", "Streamer"), streamer_already_taken_matches_id)
            string += self.format_take_match_string(self.get_string("take_match", "already_taken_matches_id", "Commentator"), commentator_already_taken_matches_id)
        else:
            string = self.format_take_match_string(self.get_string("drop_match", "successfully_dropped_matches_id", "Referee"), referee_successfully_taken_matches_id)
            string += self.format_take_match_string(self.get_string("drop_match", "successfully_dropped_matches_id", "Streamer"), streamer_successfully_taken_matches_id)
            string += self.format_take_match_string(self.get_string("drop_match", "successfully_dropped_matches_id", "Commentator"), commentator_successfully_taken_matches_id)
            string += self.format_take_match_string(self.get_string("drop_match", "already_dropped_matches_id", "Referee"), referee_already_taken_matches_id)
            string += self.format_take_match_string(self.get_string("drop_match", "already_dropped_matches_id", "Streamer"), streamer_already_taken_matches_id)
            string += self.format_take_match_string(self.get_string("drop_match", "already_dropped_matches_id", "Commentator"), commentator_already_taken_matches_id)
        string += self.format_take_match_string(self.get_string("take_match", "invalid_matches_id"), invalid_matches_id)
        await ctx.send(string)

    def format_take_match_string(self, string, matches_id):
        if matches_id:
            for i, match_id in enumerate(matches_id):
                string += match_id
                if i + 1 < len(matches_id):
                    string += ", "
                else:
                    string += "\n"
            return string
        return ""

    @commands.command(name='get_matches', aliases=['get_match', 'list_matches', 'list_match', 'see_matches', 'see_match'])
    @commands.guild_only()
    async def get_matches(self, ctx):
        """Allows to see your matches"""
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        player_matches = []
        referee_matches = []
        streamer_matches = []
        commentator_matches = []
        brackets = self.client.session.query(Bracket).filter(Bracket.tournament_id == tournament.id).all()
        if not brackets:
            raise UnknownError("post_result: query on brackets returned nothing.")
        for bracket in brackets:
            bracket_name = bracket.name
            if bracket_name == tournament.name:
                bracket_name = ""
            players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == bracket.players_spreadsheet_id).first()
            if not players_spreadsheet:
                raise NoSpreadsheet("players_spreadsheet")
            if players_spreadsheet.range_team_name.lower() == "none":
                team_name = ctx.author.display_name
            else:
                range_names = players_spreadsheet.get_ranges()
                n_range_team = players_spreadsheet.get_total_range_team()
                try:
                    cells = api.spreadsheet.get_ranges(players_spreadsheet.spreadsheet_id, range_names)
                except googleapiclient.errors.HttpError:
                    raise SpreadsheetError()
                team_name = self.get_team_name_of_player(cells, n_range_team, ctx.author.display_name)
            schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == bracket.schedules_spreadsheet_id).first()
            if not schedules_spreadsheet:
                raise NoSpreadsheet("schedules_spreadsheet")
            all_sheets = False
            if not "!" in schedules_spreadsheet.range_name:
                all_sheets = True
            try:
                if all_sheets:
                    sheets = api.spreadsheet.get_spreadsheet_with_values(schedules_spreadsheet.spreadsheet_id)
                else:
                    values = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name)
                    sheet_range = schedules_spreadsheet.range_name.split("!")
                    sheets = [{"name": sheet_range[0], "range": sheet_range[1], "values": values}]
            except googleapiclient.errors.HttpError:
                raise SpreadsheetError()
            tuples = schedules_spreadsheet.parse_parameters()
            for sheet in sheets:
                values = sheet["values"]
                match_ids = self.get_match_ids_from_cells(schedules_spreadsheet, values)
                if match_ids:
                    for match_id, x, y in match_ids:
                        incr_x, incr_y = tuples[0]
                        if y + incr_y >= len(values) or x + incr_x >= len(values[y + incr_y]):
                            continue
                        team_name1 = values[y + incr_y][x + incr_x]
                        incr_x, incr_y = tuples[1]
                        if y + incr_y >= len(values) or x + incr_x >= len(values[y + incr_y]):
                            continue
                        team_name2 = values[y + incr_y][x + incr_x]
                        date_string = ""
                        date_flags = ""
                        times = tuples[5:]
                        for tup in times:
                            incr_x, incr_y, date_flag = tup
                            if y + incr_y < len(values) and x + incr_x < len(values[y + incr_y]):
                                date_flags += date_flag
                                date_string += values[y + incr_y][x + incr_x]
                        try:
                            match_date = datetime.datetime.strptime(date_string, date_flags)
                        except ValueError:
                            continue
                        if team_name == team_name1:
                            player_matches.append((match_id, team_name1, team_name2, match_date, bracket_name))                       
                        if team_name == team_name2:
                            player_matches.append((match_id, team_name1, team_name2, match_date, bracket_name))
                        incr_x, incr_y = tuples[2]
                        if y + incr_y < len(values) and x + incr_x < len(values[y + incr_y]):
                            if values[y + incr_y][x + incr_x] == ctx.author.display_name:
                                referee_matches.append((match_id, team_name1, team_name2, match_date, bracket_name))
                        incr_x, incr_y = tuples[3]
                        if y + incr_y < len(values) and x + incr_x < len(values[y + incr_y]):
                            if values[y + incr_y][x + incr_x] == ctx.author.display_name:
                                streamer_matches.append((match_id, team_name1, team_name2, match_date, bracket_name))
                        if not isinstance(tuples[4], str):
                            for incr_x, incr_y in tuples[4]:
                                if y + incr_y < len(values) and x + incr_x < len(values[y + incr_y]):
                                    if values[y + incr_y][x + incr_x] == ctx.author.display_name:
                                        commentator_matches.append((match_id, team_name1, team_name2, match_date, bracket_name))
                                        break
        string = self.get_string("get_matches", "success", tournament.acronym, tournament.name)
        string += self.get_matches_as_string(player_matches, "Player")
        string += self.get_matches_as_string(referee_matches, "Referee")
        string += self.get_matches_as_string(streamer_matches, "Streamer")
        string += self.get_matches_as_string(commentator_matches, "Commentator")
        await ctx.send(string)
        
    def get_team_name_of_player(self, cells, n_range_team, player_name):
        i = 0
        while i < len(cells):
            team_name = self.get_team_name(cells[i])
            i += 1
            for _ in range(n_range_team):
                for player_row in cells[i]:
                    for player in player_row:
                        if player == player_name:
                            return team_name
            i += 1
        return ""

    def get_matches_as_string(self, matches, role_name):
        string = ""
        if matches:
            matches.sort(key=lambda tup: tup[3])
            string = self.get_string("get_matches", "matches", role_name)
            for match_id, team_name1, team_name2, match_date, bracket_name in matches:
                string += match_date.strftime("**%d %B at %H:%M UTC**") + " | "
                if bracket_name:
                    string += bracket_name + " | "
                string += "**" + match_id + "**:\n" + team_name1 + " vs " + team_name2 + "\n"
            string += "\n"
        return string

    def get_match_ids_from_cells(self, schedules_spreadsheet, cells):
        """Returns an array with the match ids and their position in cells"""
        splitted_range_name = (schedules_spreadsheet.range_name.split("!")[-1]).split(":")
        if len(splitted_range_name) == 1:
            begin_x = 0
            begin_y = 0
        else:
            begin_x, begin_y = api.spreadsheet.from_cell(splitted_range_name[0])
        splitted_range_match_id = (schedules_spreadsheet.range_match_id.split("!")[-1]).split(":")
        end_x, end_y = api.spreadsheet.from_cell(splitted_range_match_id[1])
        x, y = api.spreadsheet.from_cell(splitted_range_match_id[0])
        if begin_x < 0:
            begin_x = 0
        if begin_y < 0:
            begin_y = 0
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        end_x = end_x - begin_x
        end_y = end_y - begin_y
        x = x - begin_x
        y = y - begin_y
        tmp_x = x
        match_ids = []
        if end_y < 0:
            end_y = len(cells)
        while y <= end_y:
            if end_x < 0:
                end_x = len(cells[y]) - 1
            while x <= end_x:
                if y < len(cells) and x < len(cells[y]):
                    match_ids.append((cells[y][x], x, y))
                x += 1
            x = tmp_x
            y += 1
        return match_ids

    @commands.command(name='post_result')
    @commands.guild_only()
    async def post_result(self, ctx, match_id: str, n_warmup: int, best_of: int, roll_team1: int, roll_team2: int, mp_links: str, *, parameters: str):
        """Allows referees to post the result of a match"""
        await self.post_result_(ctx, match_id, 0, 0, n_warmup, best_of, roll_team1, roll_team2, mp_links, parameters)

    @commands.command(name='post_result_with_scores')
    @commands.guild_only()
    async def post_result_with_scores(self, ctx, match_id: str, score_team1: int, score_team2: int, n_warmup: int, best_of: int, roll_team1: int, roll_team2: int, mp_links: str, *, parameters: str):
        """Allows referees to post the result of a match"""
        await self.post_result_(ctx, match_id, score_team1, score_team2, n_warmup, best_of, roll_team1, roll_team2, mp_links, parameters)

    async def post_result_(self, ctx, match_id, score_team1, score_team2, n_warmup, best_of, roll_team1, roll_team2, mp_links, parameters):
        """Allows referees to post the result of a match"""
        if n_warmup < 0:
            raise commands.UserInputError()
        if (best_of < 0) or (best_of % 2 != 1):
            raise commands.UserInputError()
        if mp_links.startswith("["):
            mp_links = mp_links[1:]
            mp_links = mp_links[:-1]
            mp_links = mp_links.split(", ")
        else:
            mp_links = [mp_links]
        mp_ids = []
        for mp_link in mp_links:
            mp_ids.append(api.osu.Match.get_from_string(mp_link))
        bans = parameters.split("; ")
        if len(bans) % 2 != 0:
            raise commands.UserInputError()
        bans_team1 = ", ".join(bans[:int(len(bans)/2)])
        bans_team2 = ", ".join(bans[int(len(bans)/2):])
        guild_id = str(ctx.guild.id)
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
        if not tournament:
            raise NoTournament()
        brackets = self.client.session.query(Bracket).filter(Bracket.tournament_id == tournament.id).all()
        if not brackets:
            raise UnknownError("post_result: query on brackets returned nothing.")
        roles = ctx.guild.roles
        referee_role = self.get_role(roles, tournament.referee_role_id, "Referee")
        if not referee_role:
            raise NoRefereeRole()
        if not any(referee_role.id == role.id for role in ctx.author.roles):
            raise NotAReferee()
        for bracket in brackets:
            schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == bracket.schedules_spreadsheet_id).first()
            if not schedules_spreadsheet:
                raise NoSpreadsheet("schedules_spreadsheet")
            players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == bracket.players_spreadsheet_id).first()
            if not players_spreadsheet:
                raise NoSpreadsheet("players_spreadsheet")
            range_names = players_spreadsheet.get_ranges()
            n_range_team = players_spreadsheet.get_total_range_team()
            try:
                cells = api.spreadsheet.get_ranges(players_spreadsheet.spreadsheet_id, range_names)
            except googleapiclient.errors.HttpError:
                raise SpreadsheetError()
            all_sheets = False
            if not "!" in schedules_spreadsheet.range_name:
                all_sheets = True
            try:
                if all_sheets:
                    sheets = api.spreadsheet.get_spreadsheet_with_values(schedules_spreadsheet.spreadsheet_id)
                else:
                    values = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name)
                    sheet_range = schedules_spreadsheet.range_name.split("!")
                    sheets = [{"name": sheet_range[0], "range": sheet_range[1], "values": values}]
            except googleapiclient.errors.HttpError:
                raise SpreadsheetError()
            tuples = schedules_spreadsheet.parse_parameters()
            for sheet in sheets:
                values = sheet["values"]
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
                            if players_spreadsheet.range_team_name.lower() != "none":
                                i = 0
                                while i < len(cells):
                                    for row in cells[i]:
                                        for cell in row:
                                            if cell == team_name1:
                                                for j in range(n_range_team):
                                                    for player_row in cells[i + j + 1]:
                                                        for player in player_row:
                                                            players_team1.append(player)
                                            elif cell == team_name2:
                                                for j in range(n_range_team):
                                                    for player_row in cells[i + j + 1]:
                                                        for player in player_row:
                                                            players_team2.append(player)
                                    i += 1
                            else:
                                players_team1.append(team_name1)
                                players_team2.append(team_name2)
                            i = 0
                            players_team1 = api.osu.User.names_to_ids(players_team1)
                            players_team2 = api.osu.User.names_to_ids(players_team2)
                            if score_team1 == 0 and score_team2 == 0:
                                score_team1 = 0
                                score_team2 = 0
                                games = []
                                for mp_id in mp_ids:
                                    matches = api.osu.OsuApi.get_match(mp_id)
                                    if not matches:
                                        raise InvalidMpLink()
                                    games += matches["games"]
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
                            if score_team1 < 0:
                                score_team1_string = "FF"
                            else:
                                score_team1_string = str(score_team1)
                            if score_team2 < 0:
                                score_team2_string = "FF"
                            else:
                                score_team2_string = str(score_team2)
                            if tournament.post_result_message:
                                result_string = tournament.post_result_message
                            else:
                                result_string = self.get_string("post_result", "success")
                            result_string = result_string.replace("%match_id", match_id)
                            result_string = result_string.replace("%mp_link", mp_links)
                            result_string = result_string.replace("%team1", team_name1)
                            result_string = result_string.replace("%team2", team_name2)
                            result_string = result_string.replace("%score_team1", score_team1_string)
                            result_string = result_string.replace("%score_team2", score_team2_string)
                            result_string = result_string.replace("%bans_team1", bans_team1)
                            result_string = result_string.replace("%bans_team2", bans_team2)                           
                            result_string = result_string.replace("%winner_roll", winner_roll)
                            result_string = result_string.replace("%loser_roll", loser_roll)
                            result_string = result_string.replace("%bans_winner_roll", bans_winner_roll)
                            result_string = result_string.replace("%bans_loser_roll", bans_loser_roll)
                            if bracket.challonge:
                                t_id = 0
                                try:
                                    t = api.challonge.get_tournament(bracket.challonge)
                                    t_id = t["id"]
                                    if not t["started_at"]:
                                        api.challonge.start_tournament(t_id)
                                    participants = api.challonge.get_participants(t_id)
                                    participant1 = None
                                    participant2 = None
                                    for participant in participants:
                                        if participant["name"] == team_name1:
                                            participant1 = participant
                                        elif participant["name"] == team_name2:
                                            participant2 = participant
                                    if not participant1 or not participant2:
                                        if tournament.staff_channel_id:
                                            channel = self.client.get_channel(int(tournament.staff_channel_id))
                                        else:
                                            channel = ctx
                                        await channel.send(self.get_string("post_result", "participant_not_found", match_id))
                                        await ctx.send(result_string)
                                        return
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
                                            if score_team1 > score_team2:
                                                match_winner = api.challonge.get_id_from_participant(player1)
                                            else:
                                                match_winner = api.challonge.get_id_from_participant(player2)
                                        else:
                                            match_score = str(score_team2) + "-" + str(score_team1)
                                            if score_team1 < score_team2:
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

    @post_result_with_scores.error
    async def post_result_with_scores_handler(self, ctx, error):
        """Error handler of post_result_with_scores function"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(self.get_string("post_result_with_scores", "usage", ctx.prefix))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(self.get_string("post_result_with_scores", "usage", ctx.prefix))
        elif isinstance(error, commands.UserInputError):
            await ctx.send(self.get_string("post_result_with_scores", "usage", ctx.prefix))
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
        await self.reaction_on_staff_reschedule_message(emoji, message_id, channel, guild, user)
        await self.reaction_on_end_tournament_message(emoji, message_id, channel, guild, user)

    async def reaction_on_reschedule_message(self, emoji, message_id, channel, guild, user):
        """Reschedules a match or denies the reschedule"""
        reschedule_message = self.client.session.query(RescheduleMessage).filter(RescheduleMessage.message_id == helpers.crypt.hash_str(str(message_id))).first()
        if not reschedule_message:
            return
        ally_role = None
        enemy_role = None
        if str(user.id) == reschedule_message.enemy_user_id:
            ally_role = guild.get_member(int(reschedule_message.ally_user_id))
            enemy_role = user
        elif any(reschedule_message.enemy_role_id == str(role.id) for role in user.roles):
            for role in guild.roles:
                if reschedule_message.ally_role_id == str(role.id):
                    ally_role = role
                if reschedule_message.enemy_role_id == str(role.id):
                    enemy_role = role
        if ally_role and enemy_role:
            guild_id = str(guild.id)
            tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
            if not tournament:
                await channel.send(self.get_string("reschedule", "no_tournament", self.client.command_prefix))
                return
            brackets = self.client.session.query(Bracket).filter(Bracket.tournament_id == tournament.id).all()
            if not brackets:
                await channel.send(self.get_string("", "unknown_error"))
                return
            is_team_captain = False
            if tournament.ping_team:
                team_captain_role = self.get_role(user.roles, tournament.team_captain_role_id)
                if team_captain_role:
                    is_team_captain = True
                else:
                    for bracket in brackets:
                        players_spreadsheet = self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == bracket.players_spreadsheet_id).first()
                        if players_spreadsheet:
                            range_names = players_spreadsheet.get_ranges()
                            n_range_team = players_spreadsheet.get_total_range_team()
                            try:
                                cells = api.spreadsheet.get_ranges(players_spreadsheet.spreadsheet_id, range_names)
                            except googleapiclient.errors.HttpError:
                                raise SpreadsheetError()
                            i = 0
                            while i < len(cells):
                                if players_spreadsheet.range_team_name.lower() == "none":
                                    break
                                i += 1
                                team_captain = self.get_team_captain_name(cells[i])
                                if team_captain == user.display_name:
                                    is_team_captain = True
                                    break
                                i += n_range_team
                            if is_team_captain:
                                break
            if not tournament.ping_team or is_team_captain:
                if emoji.name == "👍":
                    for bracket in brackets:
                        schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == bracket.schedules_spreadsheet_id).first()
                        if not schedules_spreadsheet:
                            await channel.send(self.get_string("reschedule", "no_schedule_spreadsheet", self.client.command_prefix))
                            return
                        previous_date = datetime.datetime.strptime(reschedule_message.previous_date, '%d/%m/%y %H:%M')
                        new_date = datetime.datetime.strptime(reschedule_message.new_date, '%d/%m/%y %H:%M')
                        all_sheets = False
                        if not "!" in schedules_spreadsheet.range_name:
                            all_sheets = True
                        try:
                            if all_sheets:
                                sheets = api.spreadsheet.get_spreadsheet_with_values(schedules_spreadsheet.spreadsheet_id)
                            else:
                                values = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name, "ROWS", "FORMULA")
                                sheet_range = schedules_spreadsheet.range_name.split("!")
                                sheets = [{"name": sheet_range[0], "range": sheet_range[1], "values": values}]
                        except googleapiclient.errors.HttpError:
                            await channel.send(self.get_string("reschedule", "spreadsheet_error"))
                            return
                        tuples = schedules_spreadsheet.parse_parameters()
                        for sheet in sheets:
                            values = sheet["values"]
                            for y, row in enumerate(values):
                                for x, value in enumerate(row):
                                    if value == reschedule_message.match_id:
                                        referee_name = None
                                        incr_x, incr_y = tuples[2]
                                        if y + incr_y < len(values) and x + incr_x < len(values[y + incr_y]):
                                            referee_name = values[y + incr_y][x + incr_x]
                                        streamer_name = None
                                        if not isinstance(tuples[3], str):
                                            incr_x, incr_y = tuples[3]
                                            if y + incr_y < len(values) and x + incr_x < len(values[y + incr_y]):
                                                streamer_name = values[y + incr_y][x + incr_x]
                                        commentators_name = []
                                        if not isinstance(tuples[4], str):
                                            for incr_x, incr_y in tuples[4]:
                                                if y + incr_y < len(values) and x + incr_x < len(values[y + incr_y]):
                                                    commentators_name.append(values[y + incr_y][x + incr_x])
                                        tuples = tuples[5:]
                                        for tup in tuples:
                                            incr_x, incr_y, date_flag = tup
                                            while y + incr_y >= len(values):
                                                values.append([])
                                            while x + incr_x >= len(values[y + incr_y]):
                                                values[y + incr_y].append("")
                                            values[y + incr_y][x + incr_x] = new_date.strftime(date_flag)
                                        staff_to_ping = []
                                        if referee_name:
                                            staff_to_ping.append(guild.get_member_named(referee_name))
                                        if streamer_name and streamer_name != referee_name:
                                            staff_to_ping.append(guild.get_member_named(streamer_name))
                                        for commentator_name in commentators_name:
                                            if commentator_name and commentator_name != streamer_name and commentator_name != referee_name:
                                                staff_to_ping.append(guild.get_member_named(commentator_name))
                                        try:
                                            api.spreadsheet.write_range(schedules_spreadsheet.spreadsheet_id, sheet["name"] + "!" + sheet["range"], values)
                                        except googleapiclient.errors.HttpError:
                                            await channel.send(self.get_string("reschedule", "spreadsheet_error"))
                                            return
                                        await channel.send(self.get_string("reschedule", "accepted", ally_role.mention, reschedule_message.match_id))
                                        if tournament.staff_channel_id:
                                            staff_channel = self.client.get_channel(int(tournament.staff_channel_id))
                                            if staff_channel:
                                                previous_date_string = previous_date.strftime("**%d %B at %H:%M UTC**")
                                                new_date_string = new_date.strftime("**%d %B at %H:%M UTC**")
                                                if staff_to_ping:
                                                    for staff in staff_to_ping:
                                                        sent_message = await staff_channel.send(self.get_string("reschedule", "staff_notification", staff.mention, reschedule_message.match_id, ally_role.name, enemy_role.name, previous_date_string, new_date_string))
                                                        staff_reschedule_message = StaffRescheduleMessage(tournament_id=tournament.id, message_id=str(sent_message.id), match_id=reschedule_message.match_id, staff_id=str(staff.id))
                                                        self.client.session.add(staff_reschedule_message)
                                                        self.client.session.commit()
                                                else:
                                                    await staff_channel.send(self.get_string("reschedule", "no_staff_notification", reschedule_message.match_id, ally_role.name, enemy_role.name, previous_date_string, new_date_string))
                                        self.client.session.delete(reschedule_message)
                                        self.client.session.commit()
                                        return
                elif emoji.name == "👎":
                    await channel.send(self.get_string("reschedule", "refused", ally_role.mention, reschedule_message.match_id))
                    self.client.session.delete(reschedule_message)
                    self.client.session.commit()
            else:
                await user.send(self.get_string("reschedule", "not_team_captain"))

    async def reaction_on_staff_reschedule_message(self, emoji, message_id, channel, guild, user):
        """Removes the referee from the schedule spreadsheet"""
        staff_reschedule_message = self.client.session.query(StaffRescheduleMessage).filter(StaffRescheduleMessage.message_id == helpers.crypt.hash_str(str(message_id))).first()
        if not staff_reschedule_message:
            return
        if str(user.id) != staff_reschedule_message.staff_id:
            return
        if emoji.name == "❌":
            guild_id = str(guild.id)
            tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(guild_id)).first()
            if not tournament:
                await channel.send(self.get_string("reschedule", "no_tournament", self.client.command_prefix))
                return
            brackets = self.client.session.query(Bracket).filter(Bracket.tournament_id == tournament.id).all()
            if not brackets:
                await channel.send(self.get_string("", "unknown_error"))
                return
            for bracket in brackets:
                schedules_spreadsheet = self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == bracket.schedules_spreadsheet_id).first()
                if not schedules_spreadsheet:
                    await channel.send(self.get_string("reschedule", "no_schedule_spreadsheet", self.client.command_prefix))
                    return
                all_sheets = False
                if not "!" in schedules_spreadsheet.range_name:
                    all_sheets = True
                try:
                    if all_sheets:
                        sheets = api.spreadsheet.get_spreadsheet_with_values(schedules_spreadsheet.spreadsheet_id)
                    else:
                        values = api.spreadsheet.get_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name, "ROWS", "FORMULA")
                        sheet_range = schedules_spreadsheet.range_name.split("!")
                        sheets = [{"name": sheet_range[0], "range": sheet_range[1], "values": values}]
                except googleapiclient.errors.HttpError:
                    await channel.send(self.get_string("reschedule", "spreadsheet_error"))
                    return
                tuples = schedules_spreadsheet.parse_parameters()
                for sheet in sheets:
                    values = sheet["values"]
                    for y, row in enumerate(values):
                        for x, value in enumerate(row):
                            if value == staff_reschedule_message.match_id:
                                cells_to_check = [tuples[2]]
                                if not isinstance(tuples[3], str):
                                    cells_to_check.append(tuples[3])
                                if not isinstance(tuples[4], str):
                                    cells_to_check += tuples[4]
                                write = False
                                for incr_x, incr_y in cells_to_check:
                                    if y + incr_y < len(values) and x + incr_x < len(values[y + incr_y]):
                                        if values[y + incr_y][x + incr_x] == user.display_name:
                                            values[y + incr_y][x + incr_x] = ""
                                            write = True
                                if write:
                                    try:
                                        api.spreadsheet.write_range(schedules_spreadsheet.spreadsheet_id, schedules_spreadsheet.range_name, values)
                                    except googleapiclient.errors.HttpError:
                                        await channel.send(self.get_string("reschedule", "spreadsheet_error"))
                                        return
                                staff_channel = self.client.get_channel(int(tournament.staff_channel_id))
                                if staff_channel:
                                    await staff_channel.send(self.get_string("reschedule", "removed_from_match", staff_reschedule_message.match_id))
                                self.client.session.delete(staff_reschedule_message)
                                self.client.session.commit()
                                return

    async def reaction_on_end_tournament_message(self, emoji, message_id, channel, guild, user):
        """Ends a tournament"""
        end_tournament_message = self.client.session.query(EndTournamentMessage).filter(EndTournamentMessage.message_id == helpers.crypt.hash_str(str(message_id))).first()
        if not end_tournament_message:
            return
        if user.id != guild.owner.id:
            return
        tournament = self.client.session.query(Tournament).filter(Tournament.server_id == helpers.crypt.hash_str(str(guild.id))).first()
        if not tournament:
            self.client.session.delete(end_tournament_message)
            self.client.session.commit()
            return
        if emoji.name == "✅":
            brackets = self.client.session.query(Bracket).filter(Bracket.tournament_id == tournament.id).all()
            if brackets:
                for bracket in brackets:
                    self.client.session.query(SchedulesSpreadsheet).filter(SchedulesSpreadsheet.id == bracket.schedules_spreadsheet_id).delete()
                    self.client.session.query(PlayersSpreadsheet).filter(PlayersSpreadsheet.id == bracket.players_spreadsheet_id).delete()
                    self.client.session.delete(bracket)
            self.client.session.query(RescheduleMessage).filter(RescheduleMessage.tournament_id == tournament.id).delete()
            self.client.session.query(StaffRescheduleMessage).filter(StaffRescheduleMessage.tournament_id == tournament.id).delete()
            self.client.session.delete(tournament)
            self.client.session.delete(end_tournament_message)
            self.client.session.commit()
            await channel.send(self.get_string("end_tournament", "success"))
        elif emoji.name == "❎":
            self.client.session.delete(end_tournament_message)
            self.client.session.commit()
            await channel.send(self.get_string("end_tournament", "refused"))

def get_class(bot):
    """Returns the main class of the module"""
    return Tosurnament(bot)

def setup(bot):
    """Setups the cog"""
    bot.add_cog(Tosurnament(bot))
