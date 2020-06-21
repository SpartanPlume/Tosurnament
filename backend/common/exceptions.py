"""All custom exceptions for the bot and backend"""

from discord.ext import commands


class NotGuildOwner(commands.CheckFailure):
    """Special exception in case the user is not guild owner."""

    pass


class NotBotAdmin(commands.CommandError):
    """Special exception in case the user is not a bot admin."""

    pass


class UnknownError(commands.CommandError):
    """Special exception in case there is an unknown error."""

    def __init__(self, message=None):
        super().__init__()
        self.message = message


class InvalidRoleName(commands.CommandError):
    """Special exception in case the role name specified during the creation in invalid."""

    def __init__(self, role_name=""):
        super().__init__()
        self.role_name = role_name


class RoleDoesNotExist(commands.CommandError):
    """Special exception in case the role does not exist."""

    def __init__(self, role):
        super().__init__()
        self.role = role


class NotRequiredRole(commands.CommandError):
    """Special exception in case the user does not have the required role."""

    def __init__(self, role):
        super().__init__()
        self.role = role


class UserNotFound(commands.CommandError):
    """Special exception in case the user is not found."""

    def __init__(self, username):
        super().__init__()
        self.username = username


class UserNotLinked(commands.CommandError):
    """Special exception in case the user is not linked."""

    pass


class UserNotVerified(commands.CommandError):
    """Special exception in case the user is not verified."""

    pass


class OsuError(commands.CommandError):  # TODO move in api
    """Special exception in case osu api returns an error or is not reachable."""

    pass


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


class DuplicatePlayer(commands.CommandError):
    """Special exception in case the player in found multiple times in the players spreadsheet."""

    def __init__(self, player):
        super().__init__()
        self.player = player


class InvalidDateOrFormat(commands.CommandError):
    """Special exception in case the date or format used in the schedules spreadsheet is wrong."""

    pass


class SpreadsheetHttpError(commands.CommandError):
    """Special exception in case there is an http error when reading or writing on the spreadsheet."""

    def __init__(self, code, operation, bracket_name, spreadsheet):
        super().__init__()
        self.code = code
        self.operation = operation
        self.bracket_name = bracket_name
        self.spreadsheet = spreadsheet
