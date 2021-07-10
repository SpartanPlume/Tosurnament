"""Base of all tosurnament modules"""

import datetime
import os
import pickle
import asyncio
import functools
from discord.ext import commands
from bot.modules.module import *
from common.databases.tournament import Tournament
from common.databases.spreadsheets.base_spreadsheet import BaseSpreadsheet, SpreadsheetHttpError
from common.databases.spreadsheets.schedules_spreadsheet import (
    DuplicateMatchId,
    MatchIdNotFound,
    DateIsNotString,
    MatchInfo,
)
from common.databases.spreadsheets.players_spreadsheet import (
    TeamInfo,
    DuplicateTeam,
    TeamNotFound,
)
from common.api.spreadsheet import Spreadsheet, InvalidWorksheet, HttpError
from common.api import challonge

PRETTY_DATE_FORMAT = "%A %d %B at %H:%M UTC"
DATABASE_DATE_FORMAT = "%d/%m/%y %H:%M"


class UserDetails:
    class Role:
        def __init__(self, name):
            self.name = name
            self.taken_matches = []
            self.not_taken_matches = []

    def __init__(self, user):
        self.user = user
        self.referee = None
        self.streamer = None
        self.commentator = None
        self.player = None

    @property
    def name(self):
        return self.user.name

    @staticmethod
    def get_from_ctx(ctx):
        tournament = ctx.bot.session.query(Tournament).where(Tournament.guild_id == ctx.guild.id).first()
        if not tournament:
            raise NoTournament()
        return UserDetails.get_from_user(ctx.bot, ctx.author, tournament)

    @staticmethod
    def get_from_user(bot, user, tournament):
        user_details = UserDetails(UserAbstraction.get_from_user(bot, user))
        roles = user.roles
        if get_role(roles, tournament.referee_role_id, "Referee"):
            user_details.referee = UserDetails.Role("Referee")
        if get_role(roles, tournament.streamer_role_id, "Streamer"):
            user_details.streamer = UserDetails.Role("Streamer")
        if get_role(roles, tournament.commentator_role_id, "Commentator"):
            user_details.commentator = UserDetails.Role("Commentator")
        if get_role(roles, tournament.player_role_id, "Player"):
            user_details.player = UserDetails.Role("Player")
        return user_details

    @staticmethod
    def get_as_referee(bot, user):
        user_details = UserDetails(UserAbstraction.get_from_user(bot, user))
        user_details.referee = UserDetails.Role("Referee")
        return user_details

    @staticmethod
    def get_as_streamer(bot, user):
        user_details = UserDetails(UserAbstraction.get_from_user(bot, user))
        user_details.streamer = UserDetails.Role("Streamer")
        return user_details

    @staticmethod
    def get_as_commentator(bot, user):
        user_details = UserDetails(UserAbstraction.get_from_user(bot, user))
        user_details.commentator = UserDetails.Role("Commentator")
        return user_details

    @staticmethod
    def get_as_player(bot, user):
        user_details = UserDetails(UserAbstraction.get_from_user(bot, user))
        user_details.player = UserDetails.Role("Player")
        return user_details

    @staticmethod
    def get_as_all(bot, user):
        user_details = UserDetails(UserAbstraction.get_from_user(bot, user))
        user_details.referee = UserDetails.Role("Referee")
        user_details.streamer = UserDetails.Role("Streamer")
        user_details.commentator = UserDetails.Role("Commentator")
        user_details.player = UserDetails.Role("Player")
        return user_details

    def is_staff(self):
        return bool(self.referee) | bool(self.streamer) | bool(self.commentator)

    def is_user(self):
        return self.is_staff() | bool(self.player)

    def get_staff_roles(self):
        return list(
            filter(
                None,
                [
                    self.referee,
                    self.streamer,
                    self.commentator,
                ],
            )
        )

    def get_all_roles(self):
        roles = self.get_staff_roles()
        if self.player:
            roles.append(self.player)
        return roles

    def clear_matches(self):
        for role_store in self.get_all_roles():
            if role_store:
                role_store.taken_matches = []
                role_store.not_taken_matches = []


class TosurnamentBaseModule(BaseModule):
    """Contains utility functions used by Tosurnament modules."""

    def __init__(self, bot):
        super().__init__(bot)

    def get_tournament(self, guild_id):
        """
        Gets the tournament linked to the guild.
        If there is no tournament, throws NoTournament.
        """
        tournament = self.bot.session.query(Tournament).where(Tournament.guild_id == guild_id).first()
        if not tournament:
            raise NoTournament()
        return tournament

    def get_player_in_team(self, member, team_info):
        user = UserAbstraction.get_from_user(self.bot, member)
        user_name = user.name if user.verified else ""
        return team_info.find_player(user_name, member.id, str(member))

    def find_staff_to_ping(self, guild, staff_cells):
        staff_names_to_ping = set()
        for staff_cell in staff_cells:
            for staff_name in staff_cell.split("/"):
                staff_name = staff_name.strip()
                if staff_name:
                    staff_names_to_ping.add(staff_name)
        staffs = []
        staffs_not_found = []
        for staff_name in staff_names_to_ping:
            user = UserAbstraction.get_from_osu_name(self.bot, staff_name, staff_name)
            member = user.get_member(guild)
            if member:
                staffs.append(member)
            else:
                staffs_not_found.append(user.name)
        return staffs, staffs_not_found

    async def get_match_infos_from_id(self, bracket, match_ids):
        schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
        if not schedules_spreadsheet:
            return []
        match_ids_cells = schedules_spreadsheet.spreadsheet.get_cells_with_value_in_range(
            schedules_spreadsheet.range_match_id
        )
        match_infos = []
        for match_id_cell in match_ids_cells:
            if match_id_cell.casefold() in match_ids:
                match_infos.append(MatchInfo.from_match_id_cell(schedules_spreadsheet, match_id_cell))
        return match_infos

    async def get_next_matches_info_for_bracket(self, tournament, bracket):
        matches_data = []
        schedules_spreadsheet = await bracket.get_schedules_spreadsheet()
        if not schedules_spreadsheet:
            return matches_data
        match_ids_cells = schedules_spreadsheet.spreadsheet.get_cells_with_value_in_range(
            schedules_spreadsheet.range_match_id
        )
        now = datetime.datetime.now(datetime.timezone.utc)
        matches_to_ignore = [match.casefold() for match in tournament.matches_to_ignore.split("\n")]
        for match_id_cell in match_ids_cells:
            if match_id_cell.casefold() in matches_to_ignore:
                continue
            match_info = MatchInfo.from_match_id_cell(schedules_spreadsheet, match_id_cell)
            date_format = "%d %B"
            if schedules_spreadsheet.date_format:
                date_format = schedules_spreadsheet.date_format
            match_date = tournament.parse_date(
                match_info.get_datetime(), date_formats=list(filter(None, [date_format + " %H:%M"]))
            )
            if not match_date or match_date < now:
                continue
            matches_data.append((match_info, match_date))
        return matches_data

    async def get_all_teams_infos_and_roles(self, guild, players_spreadsheet):
        teams_info = []
        teams_roles = []
        if players_spreadsheet:
            if players_spreadsheet.range_team_name:
                team_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    players_spreadsheet.range_team_name
                )
            else:
                team_cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(
                    players_spreadsheet.range_team
                )
            for team_cell in team_cells:
                try:
                    team_info = TeamInfo.from_team_name(players_spreadsheet, str(team_cell))
                except Exception:
                    continue
                if players_spreadsheet.range_team_name and (
                    team_role := get_role(guild.roles, None, team_info.team_name)
                ):
                    teams_roles.append(team_role)
                else:
                    teams_roles.append(None)
                teams_info.append(team_info)
        return teams_info, teams_roles

    def get_spreadsheet_ids_to_update_pickle(self):
        if not os.path.exists("pickles"):
            os.mkdir("pickles")
            return []
        try:
            with open("pickles/spreadsheet_ids_to_update", "rb") as pfile:
                spreadsheet_ids = pickle.load(pfile)
                return spreadsheet_ids
        except IOError:
            return []

    def update_spreadsheet_ids_to_update_pickle(self, spreadsheet_ids):
        if not os.path.exists("pickles"):
            os.mkdir("pickles")
        with open("pickles/spreadsheet_ids_to_update", "w+b") as pfile:
            pickle.dump(spreadsheet_ids, pfile)

    async def update_spreadsheet_background_task(self, spreadsheet_id):
        try:
            await asyncio.sleep(2)  # To prioritize finishing the executed command
            while True:
                self.bot.info("Trying to update online spreadsheet...")
                Spreadsheet.pickle_from_id.cache_clear()
                spreadsheet = Spreadsheet.pickle_from_id(spreadsheet_id)
                spreadsheet_ids = self.get_spreadsheet_ids_to_update_pickle()
                spreadsheet_ids.remove(spreadsheet.id)
                self.update_spreadsheet_ids_to_update_pickle(spreadsheet_ids)
                if not spreadsheet:
                    self.bot.error("Spreadsheet pickle not found")
                    return
                try:
                    spreadsheet.update()
                except HttpError as e:
                    self.bot.info("Exception raised while trying to update online spreadsheet")
                    self.bot.info_exception(e)
                    spreadsheet_ids = self.get_spreadsheet_ids_to_update_pickle()
                    if spreadsheet.id not in spreadsheet_ids:
                        spreadsheet_ids.add(spreadsheet.id)
                        self.update_spreadsheet_ids_to_update_pickle(spreadsheet_ids)
                    await asyncio.sleep(10)
                    continue
                self.bot.info("Updated online spreadsheet successfully")
                return
        except asyncio.CancelledError:
            return

    def add_update_spreadsheet_background_task(self, spreadsheet):
        spreadsheet.spreadsheet.update_pickle()
        spreadsheet_id = spreadsheet.spreadsheet.id
        spreadsheet_ids = self.get_spreadsheet_ids_to_update_pickle()
        if spreadsheet_ids:
            if spreadsheet_id in spreadsheet_ids:
                return
            spreadsheet_ids.add(spreadsheet_id)
        else:
            spreadsheet_ids = set([spreadsheet_id])
        self.update_spreadsheet_ids_to_update_pickle(spreadsheet_ids)
        self.bot.tasks.append(self.bot.loop.create_task(self.update_spreadsheet_background_task(spreadsheet_id)))

    def get_bracket_from_index(self, brackets, shown_index):
        """Gets the bracket corresponding to the shown index (shown index starts at 1)."""
        if len(brackets) != 1:
            if shown_index is None:
                return None
            elif shown_index <= 0 or shown_index > len(brackets):
                raise commands.UserInputError()
            shown_index -= 1
        else:
            shown_index = 0
        return brackets[shown_index]

    def get_spreadsheet_error(self, error_code):  # TODO
        if error_code == 499:
            return "connection_reset_by_peer"
        elif error_code == 408:
            return "request_timeout"
        else:
            return "spreadsheet_rights"

    async def handle_spreadsheet_error(self, ctx, error_code, error_type, spreadsheet_type):  # TODO
        """Sends an appropriate error message in case of error with the spreadsheet api."""
        if error_code == 499:
            await self.send_reply(ctx, "connection_reset_by_peer")
        elif error_code == 408:
            await self.send_reply(ctx, "request_timeout")
        else:
            await self.send_reply(ctx, "spreadsheet_error", error_type, spreadsheet_type)

    async def show_spreadsheet_settings(self, ctx, spreadsheet_type):
        """Shows the spreadsheet settings."""
        tournament = self.get_tournament(ctx.guild.id)
        spreadsheet = tournament.current_bracket.get_spreadsheet_from_type(spreadsheet_type)
        if not spreadsheet:
            raise NoSpreadsheet(spreadsheet_type)
        await self.show_object_settings(ctx, spreadsheet, stack_depth=3)

    async def on_cog_command_error(self, ctx, error, channel=None):
        if not channel:
            channel = ctx.channel
        error_found = await super().on_cog_command_error(ctx, error, channel=channel)
        if error_found:
            return True
        if isinstance(error, NoTournament):
            await self.send_reply(ctx, "no_tournament", channel=channel)
        elif isinstance(error, NoBracket):
            await self.send_reply(ctx, "no_bracket", channel=channel)
        elif isinstance(error, NoSpreadsheet):
            await self.send_reply(ctx, "no_spreadsheet", error.spreadsheet, channel=channel)
        elif isinstance(error, InvalidWorksheet):
            await self.send_reply(ctx, "invalid_worksheet", error.worksheet, channel=channel)
        elif isinstance(error, SpreadsheetError):
            await self.send_reply(ctx, "spreadsheet_error", channel=channel)
        elif isinstance(error, OpponentNotFound):
            await self.send_reply(ctx, "opponent_not_found", error.mention, channel=channel)
        elif isinstance(error, SpreadsheetHttpError):
            await self.send_reply(
                ctx,
                self.get_spreadsheet_error(error.code),
                error.operation,
                error.bracket_name,
                error.spreadsheet,
                channel=channel,
            )
        elif isinstance(error, DuplicateTeam):
            await self.send_reply(ctx, "duplicate_team", error.team, channel=channel)
        elif isinstance(error, TeamNotFound):
            await self.send_reply(ctx, "team_not_found", error.team, channel=channel)
        elif isinstance(error, DuplicateMatchId):
            await self.send_reply(ctx, "duplicate_match_id", error.match_id, channel=channel)
        elif isinstance(error, MatchIdNotFound):
            await self.send_reply(ctx, "match_id_not_found", error.match_id, channel=channel)
        elif isinstance(error, DateIsNotString):
            await self.send_reply(ctx, "date_is_not_string", error.type, channel=channel)
        elif isinstance(error, DuplicatePlayer):
            await self.send_reply(ctx, "duplicate_player", error.player, channel=channel)
        elif isinstance(error, InvalidDateOrFormat):
            await self.send_reply(ctx, "invalid_date_or_format", channel=channel)
        elif isinstance(error, UserAlreadyPlayer):
            await self.send_reply(ctx, "already_player", channel=channel)
        elif isinstance(error, NotAPlayer):
            await self.send_reply(ctx, "not_a_player", channel=channel)
        elif isinstance(error, InvalidMatchIdOrNoBracketRole):
            await self.send_reply(ctx, "invalid_match_id_or_no_bracket_role", channel=channel)
        elif isinstance(error, InvalidMatchId):
            await self.send_reply(ctx, "invalid_match_id", channel=channel)
        elif isinstance(error, NoChallonge):
            await self.send_reply(ctx, "no_challonge", error.bracket, channel=channel)
        elif isinstance(error, challonge.NoRights):
            await self.send_reply(ctx, "challonge_no_rights", channel=channel)
        elif isinstance(error, challonge.NotFound):
            await self.send_reply(ctx, "challonge_not_found", channel=channel)
        else:
            return False
        return True


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
        raise NotRequiredRole(role.name)

    return commands.check(predicate)


def get_pretty_date(tournament, date):
    utc = ""
    if tournament:
        utc = tournament.utc
        if utc:
            hour = utc[1:3]
            minute = utc[4:6]
            if int(hour) == 0 and int(minute) == 0:
                utc = ""
            else:
                utc = utc[0] + hour.lstrip("0")
                if int(minute) > 0:
                    utc += ":" + minute
    return "**" + date.strftime(PRETTY_DATE_FORMAT) + utc + "**"


def retry_and_update_spreadsheet_pickle_on_exceptions(_func=None, *, exceptions=[]):
    exceptions_tuple = tuple(exceptions)

    def retry_wrapper(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                invalid_match_ids = await func(*args, **kwargs)
            except Exception as e:
                if not isinstance(e, exceptions_tuple):
                    raise e
                spreadsheet_ids = set()
                for arg in args:
                    if isinstance(arg, BaseSpreadsheet):
                        if await arg.get_spreadsheet(force_sync=True):
                            spreadsheet_ids.add(arg.id)
                if spreadsheet_ids:
                    return await func(*args, **kwargs, retry=True)
            return invalid_match_ids

        return wrapper

    if _func:
        return retry_wrapper(_func)
    else:
        return retry_wrapper
