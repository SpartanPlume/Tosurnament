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


class InvalidMinute(commands.CommandError):
    """Special exception in case the minutes are not multiple of a quarter of an hour."""

    pass


class InvalidMatch(commands.CommandError):
    """Special exception in case the user is not in the match."""

    pass


class InvalidMatchId(commands.CommandError):
    """Special exception in case the match id does not exist."""

    pass


class InvalidMatchIdOrNoBracketRole(InvalidMatchId):
    """Special exception in case the match id does not exist, in case of multiple brackets tournament."""

    pass


class InvalidMpLink(commands.CommandError):
    """Special exception in case the match link does not exist."""

    pass


class TimeInThePast(commands.CommandError):
    """Special exception in case the proposed time is in the past."""

    pass


class PastDeadline(commands.CommandError):
    """Special exception in case the deadline is passed."""

    def __init__(self, reschedule_deadline_hours, referees_mentions, match_id):
        self.reschedule_deadline_hours = reschedule_deadline_hours
        self.referees_mentions = referees_mentions
        self.match_id = match_id


class ImpossibleReschedule(commands.CommandError):
    """Special exception in case the rescheduled time is not acceptable."""

    def __init__(self, reschedule_deadline_hours, referees_mentions, match_id):
        self.reschedule_deadline_hours = reschedule_deadline_hours
        self.referees_mentions = referees_mentions
        self.match_id = match_id


class PastDeadlineEnd(commands.CommandError):
    """Special exception in case the deadline is passed."""

    pass


class PastAllowedDate(commands.CommandError):
    """Special exception in case the reschedule is asked after the allowed date."""

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

    def __init__(self, code, operation, spreadsheet, google_error):
        super().__init__()
        self.code = code
        self.operation = operation
        self.spreadsheet = spreadsheet
        self.google_error = google_error

    def __str__(self):
        return (
            "Error "
            + str(self.code)
            + ": Couldn't "
            + self.operation
            + " in the "
            + self.spreadsheet
            + " spreadsheet of a bracket. Error from google api: "
            + str(self.google_error)
        )


class NotRefereeOfMatch(commands.CommandError):
    """Special exception in case someone who is not the referee of a match try to allow its reschedule."""

    pass


class NoChallonge(commands.CommandError):
    """Special exception in case no challonge is set."""

    def __init__(self, bracket):
        super().__init__()
        self.bracket = bracket


class RegistrationEnded(commands.CommandError):
    """Special exception in case someone tries to register while the registration phase ended."""

    pass


class AlreadyInLobby(commands.CommandError):
    """Special exception in case someone tries to register to a lobby he's already in."""

    pass


class LobbyNotFound(commands.CommandError):
    """Special exception in case someone tries to register to a lobby that does not exist."""

    def __init__(self, lobby_id):
        super().__init__()
        self.lobby_id = lobby_id


class LobbyIsFull(commands.CommandError):
    """Special exception in case someone tries to register to a lobby that is full."""

    pass


class InvalidTimezone(commands.CommandError):
    """Special exception in case the timezone provided is invalid."""

    def __init__(self, timezone):
        self.timezone = timezone


class NotInRankRange(commands.CommandError):
    """Special exception in case the rank of the player is not in the rank range of the tournament."""

    pass
