"""Base of all tosurnament modules"""

import datetime
import os
import pickle
import asyncio
import functools
from discord.ext import commands
from bot.modules.module import *
from common.databases.tournament import Tournament
from common.databases.base_spreadsheet import BaseSpreadsheet
from common.databases.schedules_spreadsheet import DuplicateMatchId, MatchIdNotFound, DateIsNotString, MatchInfo
from common.databases.players_spreadsheet import (
    TeamInfo,
    DuplicateTeam,
    TeamNotFound,
)
from common.api.spreadsheet import Spreadsheet, InvalidWorksheet, HttpError
from common.databases.base_spreadsheet import SpreadsheetHttpError
from common.api import challonge

PRETTY_DATE_FORMAT = "%A %d %B at %H:%M UTC"
DATABASE_DATE_FORMAT = "%d/%m/%y %H:%M"


class UserDetails:
    class Role:
        def __init__(self):
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
            user_details.referee = UserDetails.Role()
        if get_role(roles, tournament.streamer_role_id, "Streamer"):
            user_details.streamer = UserDetails.Role()
        if get_role(roles, tournament.commentator_role_id, "Commentator"):
            user_details.commentator = UserDetails.Role()
        if get_role(roles, tournament.player_role_id, "Player"):
            user_details.player = UserDetails.Role()
        return user_details

    @staticmethod
    def get_as_referee(bot, user):
        user_details = UserDetails(UserAbstraction.get_from_user(bot, user))
        user_details.referee = UserDetails.Role()
        return user_details

    @staticmethod
    def get_as_streamer(bot, user):
        user_details = UserDetails(UserAbstraction.get_from_user(bot, user))
        user_details.streamer = UserDetails.Role()
        return user_details

    @staticmethod
    def get_as_commentator(bot, user):
        user_details = UserDetails(UserAbstraction.get_from_user(bot, user))
        user_details.commentator = UserDetails.Role()
        return user_details

    @staticmethod
    def get_as_player(bot, user):
        user_details = UserDetails(UserAbstraction.get_from_user(bot, user))
        user_details.player = UserDetails.Role()
        return user_details

    @staticmethod
    def get_as_all(bot, user):
        user_details = UserDetails(UserAbstraction.get_from_user(bot, user))
        user_details.referee = UserDetails.Role()
        user_details.streamer = UserDetails.Role()
        user_details.commentator = UserDetails.Role()
        user_details.player = UserDetails.Role()
        return user_details

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

    def clear_matches(self):
        for value in self.get_as_dict().values():
            if value:
                value.taken_matches = []
                value.not_taken_matches = []


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

    def find_staff_to_ping(self, guild, staff_cells):
        staff_names_to_ping = set()
        for staff_cell in staff_cells:
            if staff_cell.value:
                tmp_staff_names = staff_cell.value.split("/")
                for staff_name in tmp_staff_names:
                    staff_names_to_ping.add(staff_name.strip())
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
        schedules_spreadsheet = bracket.schedules_spreadsheet
        if not schedules_spreadsheet:
            return []
        await schedules_spreadsheet.get_spreadsheet()
        match_ids_cells = schedules_spreadsheet.spreadsheet.get_cells_with_value_in_range(
            schedules_spreadsheet.range_match_id
        )
        match_infos = []
        for match_id_cell in match_ids_cells:
            if match_id_cell.value.lower() in match_ids:
                match_infos.append(MatchInfo.from_match_id_cell(schedules_spreadsheet, match_id_cell))
                match_ids.remove(match_id_cell.value.lower())
        return match_infos

    async def get_next_matches_info_for_bracket(self, tournament, bracket):
        matches_data = []
        schedules_spreadsheet = bracket.schedules_spreadsheet
        if not schedules_spreadsheet:
            return matches_data
        await schedules_spreadsheet.get_spreadsheet()
        match_ids_cells = schedules_spreadsheet.spreadsheet.get_cells_with_value_in_range(
            schedules_spreadsheet.range_match_id
        )
        now = datetime.datetime.utcnow()
        matches_to_ignore = tournament.matches_to_ignore.split("\n")
        for match_id_cell in match_ids_cells:
            if match_id_cell.value in matches_to_ignore:
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
                        spreadsheet_ids.append(spreadsheet.id)
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

    async def find_player_identification(self, ctx, bracket, user_name):
        players_spreadsheet = bracket.players_spreadsheet
        if not players_spreadsheet:
            return user_name
        await players_spreadsheet.get_spreadsheet()
        if players_spreadsheet.range_team_name:
            cells = players_spreadsheet.spreadsheet.get_cells_with_value_in_range(players_spreadsheet.range_team_name)
            for cell in cells:
                team_info = TeamInfo.from_team_name(players_spreadsheet, cell.value)
                if user_name in [cell.value for cell in team_info.players]:
                    return team_info.team_name.value
        else:
            return user_name

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
            await self.send_reply(ctx, ctx.command.name, "connection_reset_by_peer")
        elif error_code == 408:
            await self.send_reply(ctx, ctx.command.name, "request_timeout")
        else:
            await self.send_reply(ctx, ctx.command.name, "spreadsheet_error", error_type, spreadsheet_type)

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
        elif isinstance(error, DateIsNotString):
            await self.send_reply(channel, command_name, "date_is_not_string", error.type)
        elif isinstance(error, DuplicatePlayer):
            await self.send_reply(channel, command_name, "duplicate_player", error.player)
        elif isinstance(error, InvalidDateOrFormat):
            await self.send_reply(channel, command_name, "invalid_date_or_format")
        elif isinstance(error, UserAlreadyPlayer):
            await self.send_reply(channel, command_name, "already_player")
        elif isinstance(error, NotAPlayer):
            await self.send_reply(channel, command_name, "not_a_player")
        elif isinstance(error, InvalidMatchIdOrNoBracketRole):
            await self.send_reply(channel, command_name, "invalid_match_id_or_no_bracket_role")
        elif isinstance(error, InvalidMatchId):
            await self.send_reply(channel, command_name, "invalid_match_id")
        elif isinstance(error, NoChallonge):
            await self.send_reply(channel, command_name, "no_challonge", error.bracket)
        elif isinstance(error, challonge.NoRights):
            await self.send_reply(channel, command_name, "challonge_no_rights")
        elif isinstance(error, challonge.NotFound):
            await self.send_reply(channel, command_name, "challonge_not_found")
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


def retry_and_update_spreadsheet_pickle_on_false_or_exceptions(_func=None, *, exceptions=[]):
    exceptions_tuple = tuple(exceptions)

    def retry_wrapper(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = False
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                if not isinstance(e, exceptions_tuple):
                    raise e
            if not result:
                spreadsheets = []
                for arg in args:
                    if isinstance(arg, BaseSpreadsheet):
                        spreadsheets.append(arg)
                spreadsheet_ids = []
                for spreadsheet in spreadsheets:
                    if spreadsheet.id not in spreadsheet_ids:
                        if await spreadsheet.get_spreadsheet(force_sync=True):
                            spreadsheet_ids.append(spreadsheet.id)
                if spreadsheet_ids:
                    return await func(*args, **kwargs, retry=True)
            return result

        return wrapper

    if _func:
        return retry_wrapper(_func)
    else:
        return retry_wrapper
