"""Base of all tosurnament modules"""

from discord.ext import commands
from bot.modules.module import *
from common.databases.tournament import Tournament
from common.databases.bracket import Bracket
from common.databases.schedules_spreadsheet import (
    SchedulesSpreadsheet,
    DuplicateMatchId,
    MatchIdNotFound,
)
from common.databases.players_spreadsheet import (
    PlayersSpreadsheet,
    TeamInfo,
    DuplicateTeam,
    TeamNotFound,
)
from common.api.spreadsheet import Spreadsheet, InvalidWorksheet, HttpError


class UserAlreadyPlayer(commands.CommandError):
    """Special exception in case the user is already a player."""

    pass


class NoTournament(commands.CommandError):
    """Special exception in case a guild does not have any tournament running."""

    pass


class TournamentAlreadyCreated(commands.CommandError):
    """Special exception in case a guild already has a tournament running."""

    pass


class NoBracket(commands.CommandError):
    """Special exception in case a guild does not have the requested bracket."""

    pass


class NoSpreadsheet(commands.CommandError):
    """Special exception in case a spreadsheet has not been set."""

    def __init__(self, spreadsheet=None):
        super().__init__()
        self.spreadsheet = spreadsheet


class SpreadsheetError(commands.CommandError):
    """Special exception in case an error occurs with a spreadsheet."""

    pass


class InvalidMatch(commands.CommandError):
    """Special exception in case the user is not in the match."""

    pass


class InvalidMatchId(commands.CommandError):
    """Special exception in case the match id does not exist."""

    pass


class InvalidMpLink(commands.CommandError):
    """Special exception in case the match link does not exist."""

    pass


class MatchNotFound(commands.CommandError):
    """Special exception in case a match in the challonge is not found."""

    pass


class PastDeadline(commands.CommandError):
    """Special exception in case the deadline is passed."""

    pass


class ImpossibleReschedule(commands.CommandError):
    """Special exception in case the rescheduled time is not acceptable."""

    pass


class SameDate(commands.CommandError):
    """Special exception in case the rescheduled time
    is the same date than the previous one."""

    pass


class NotAPlayer(commands.CommandError):
    """Special exception in case the player is not found in the player spreadsheets."""

    pass


class OpponentNotFound(commands.CommandError):
    """Special exception in case the opponent in not found in the guild."""

    def __init__(self, mention):
        super().__init__()
        self.mention = mention


class SpreadsheetHttpError(commands.CommandError):
    """Special exception in case there is an http error when reading or writing on the spreadsheet."""

    def __init__(self, code, operation, bracket_name, spreadsheet):
        super().__init__()
        self.code = code
        self.operation = operation
        self.bracket_name = bracket_name
        self.spreadsheet = spreadsheet


class DuplicatePlayer(commands.CommandError):
    """Special exception in case the player in found multiple times in the players spreadsheet."""

    def __init__(self, player):
        super().__init__()
        self.player = player


class InvalidDateOrFormat(commands.CommandError):
    """Special exception in case the date or format used in the schedules spreadsheet is wrong."""

    pass


class UserRoles:
    class Role:
        def __init__(self):
            self.taken_matches = []
            self.not_taken_matches = []

    def __init__(self):
        self.referee = None
        self.streamer = None
        self.commentator = None
        self.player = None

    @staticmethod
    def get_from_context(ctx):
        tournament = ctx.bot.session.query(Tournament).where(Tournament.guild_id == ctx.guild.id).first()
        if not tournament:
            raise NoTournament()
        roles = ctx.author.roles
        return UserRoles.get_from_roles(roles, tournament)

    @staticmethod
    def get_from_roles(roles, tournament):
        user_roles = UserRoles()
        if get_role(roles, tournament.referee_role_id, "Referee"):
            user_roles.referee = UserRoles.Role()
        if get_role(roles, tournament.streamer_role_id, "Streamer"):
            user_roles.streamer = UserRoles.Role()
        if get_role(roles, tournament.commentator_role_id, "Commentator"):
            user_roles.commentator = UserRoles.Role()
        if get_role(roles, tournament.player_role_id, "Player"):
            user_roles.player = UserRoles.Role()
        return user_roles

    @staticmethod
    def get_as_referee():
        user_roles = UserRoles()
        user_roles.referee = UserRoles.Role()
        return user_roles

    @staticmethod
    def get_as_streamer():
        user_roles = UserRoles()
        user_roles.streamer = UserRoles.Role()
        return user_roles

    @staticmethod
    def get_as_commentator():
        user_roles = UserRoles()
        user_roles.commentator = UserRoles.Role()
        return user_roles

    @staticmethod
    def get_as_player():
        user_roles = UserRoles()
        user_roles.player = UserRoles.Role()
        return user_roles

    @staticmethod
    def get_as_all():
        user_roles = UserRoles()
        user_roles.referee = UserRoles.Role()
        user_roles.streamer = UserRoles.Role()
        user_roles.commentator = UserRoles.Role()
        user_roles.player = UserRoles.Role()
        return user_roles

    def is_staff(self):
        return bool(self.referee) | bool(self.streamer) | bool(self.commentator)

    def is_user(self):
        return self.is_staff() | bool(self.player)

    def get_staff_roles_as_dict(self):
        return {
            "Referee": self.referee,
            "Streamer": self.streamer,
            "Commentator": self.commentator,
        }

    def get_as_dict(self):
        roles = self.get_staff_roles_as_dict()
        roles["Player"] = self.player
        return roles


class TosurnamentBaseModule(BaseModule):
    """Contains utility functions used by Tosurnament modules."""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def get_tournament(self, guild_id):
        """
        Gets the tournament linked to the guild.
        If there is no tournament, throws NoTournament.
        """
        tournament = self.bot.session.query(Tournament).where(Tournament.guild_id == guild_id).first()
        if not tournament:
            raise NoTournament()
        return tournament

    def get_current_bracket(self, tournament):
        """Gets the current bracket of the tournament."""
        bracket = self.bot.session.query(Bracket).where(Bracket.id == tournament.current_bracket_id).first()
        if not bracket:
            raise UnknownError("No bracket found")
        return bracket

    def get_all_brackets(self, tournament):
        """Gets all brackets of the tournament."""
        brackets = self.bot.session.query(Bracket).where(Bracket.tournament_id == tournament.id).all()
        if not brackets:
            raise UnknownError("No brackets found")
        return brackets

    def get_players_spreadsheet(self, bracket):
        """Gets the bracket's players spreadsheet."""
        return (
            self.bot.session.query(PlayersSpreadsheet)
            .where(PlayersSpreadsheet.id == bracket.players_spreadsheet_id)
            .first()
        )

    def get_schedules_spreadsheet(self, bracket):
        """Gets the bracket's schedules spreadsheet."""
        return (
            self.bot.session.query(SchedulesSpreadsheet)
            .where(SchedulesSpreadsheet.id == bracket.schedules_spreadsheet_id)
            .first()
        )

    def get_spreadsheet_worksheet(self, spreadsheet):
        """Retrieves the spreadsheet and its main worksheet."""
        sp = Spreadsheet.get_from_id(spreadsheet.spreadsheet_id)
        worksheet = sp.get_worksheet(spreadsheet.sheet_name)
        return sp, worksheet

    def find_player_identification(self, ctx, bracket, user_name):
        players_spreadsheet = self.get_players_spreadsheet(bracket)
        if not players_spreadsheet:
            return user_name
        if players_spreadsheet.range_team_name:
            try:
                _, worksheet = self.get_spreadsheet_worksheet(ctx, players_spreadsheet)
            except HttpError as e:
                raise SpreadsheetHttpError(e.code, e.operation, bracket.name, "players")
            cells = worksheet.get_cells_with_value_in_range(players_spreadsheet.range_team_name)
            for cell in cells:
                team_info = TeamInfo.get_from_team_name(cell.value)
                if user_name in [cell.value for cell in team_info.players]:
                    return team_info.team_name.value
        else:
            return user_name

    def get_spreadsheet_error(self, error_code):  # TODO
        return "spreadsheet_rights"

    async def handle_spreadsheet_error(self, ctx, error_code, error_type, spreadsheet_type):  # TODO
        """Sends an appropriate error message in case of error with the spreadsheet api."""
        await self.send_reply(ctx, ctx.command.name, "spreadsheet_error", error_type, spreadsheet_type)

    async def cog_command_error(self, ctx, error):  # ? To Remove ?
        await self.on_cog_command_error(ctx, ctx.command.name, error)

    async def on_cog_command_error(self, channel, command_name, error):
        error_found = await super().on_cog_command_error(channel, command_name, error)
        if error_found:
            return True
        if isinstance(error, NoTournament):
            await self.send_reply(channel, command_name, "no_tournament")
        elif isinstance(error, NoBracket):
            await self.send_reply(channel, command_name, "no_bracket")
        elif isinstance(error, NoSpreadsheet):
            await self.send_reply(channel, command_name, "no_spreadsheet", error.spreadsheet)
        elif isinstance(error, InvalidWorksheet):
            await self.send_reply(channel, command_name, "invalid_worksheet", error.worksheet)
        elif isinstance(error, SpreadsheetError):
            await self.send_reply(channel, command_name, "spreadsheet_error")
        elif isinstance(error, OpponentNotFound):
            await self.send_reply(channel, command_name, "opponent_not_found", error.mention)
        elif isinstance(error, SpreadsheetHttpError):
            await self.send_reply(
                channel,
                command_name,
                self.get_spreadsheet_error(error.code),
                error.operation,
                error.bracket_name,
                error.spreadsheet,
            )
        elif isinstance(error, DuplicateTeam):
            await self.send_reply(channel, command_name, "duplicate_team", error.team)
        elif isinstance(error, TeamNotFound):
            await self.send_reply(channel, command_name, "team_not_found", error.team)
        elif isinstance(error, DuplicateMatchId):
            await self.send_reply(channel, command_name, "duplicate_match_id", error.match_id)
        elif isinstance(error, MatchIdNotFound):
            await self.send_reply(channel, command_name, "match_id_not_found", error.match_id)
        elif isinstance(error, DuplicatePlayer):
            await self.send_reply(channel, command_name, "duplicate_player", error.player)
        elif isinstance(error, InvalidDateOrFormat):
            await self.send_reply(channel, command_name, "invalid_date_or_format")
        elif isinstance(error, UserAlreadyPlayer):
            await self.send_reply(channel, command_name, "already_player")
        elif isinstance(error, NotAPlayer):
            await self.send_reply(channel, command_name, "not_a_player")
        elif isinstance(error, InvalidMatchId):
            await self.send_reply(channel, command_name, "invalid_match_id")
        else:
            return False
        return True
        # elif isinstance(error, api.challonge.NoRights):
        #    await self.send_reply(channel, command_name, "challonge_no_rights")
        # elif isinstance(error, api.challonge.NotFound):
        #    await self.send_reply(channel, command_name, "challonge_not_found")


def has_tournament_role(role_name):
    """Check function to know if the user has a tournament role."""

    async def predicate(ctx):
        tournament = ctx.bot.session.query(Tournament).where(Tournament.guild_id == ctx.guild.id).first()
        if not tournament:
            raise NoTournament()
        role_id = tournament.get_role_id(role_name)
        role = get_role(ctx.guild.roles, role_id, role_name)
        if not role:
            raise RoleDoesNotExist(role_name)
        if role in ctx.author.roles:
            return True
        raise NotRequiredRole(role_name)

    return commands.check(predicate)


def is_bot_admin():
    """Check function to know if the user is a bot admin."""

    async def predicate(ctx):
        guild = ctx.bot.session.query(Guild).where(Guild.guild_id == ctx.guild.id).first()
        if not guild:
            raise NotBotAdmin()
        if not guild.admin_role_id and ctx.guild.owner != ctx.author:
            raise NotBotAdmin()
        if ctx.guild.owner != ctx.author and not get_role(ctx.author.roles, guild.admin_role_id):
            raise NotBotAdmin()
        return True

    return commands.check(predicate)
