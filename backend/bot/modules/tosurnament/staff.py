"""Staff commands"""

from discord.ext import commands
from bot.modules.tosurnament import module as tosurnament
from common.databases.schedules_spreadsheet import MatchInfo, MatchIdNotFound
from common.api.spreadsheet import HttpError


class TosurnamentStaffCog(tosurnament.TosurnamentBaseModule, name="staff"):
    """Tosurnament staff commands"""

    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot

    def cog_check(self, ctx):
        """Check function called before any command of the cog."""
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @commands.command(aliases=["take_matches", "tm"])
    async def take_match(self, ctx, *args):
        """Allows staffs to take matches"""
        user_roles = tosurnament.UserRoles.get_from_context(ctx)
        if not user_roles.is_staff():
            await self.send_reply(ctx, ctx.command.name, "not_staff")
        else:
            await self.take_or_drop_match(ctx, args, True, user_roles)

    @commands.command(aliases=["take_matches_as_referee", "tmar"])
    @tosurnament.has_tournament_role("Referee")
    async def take_match_as_referee(self, ctx, *args):
        """Allows referees to take matches"""
        await self.take_or_drop_match(ctx, args, True, tosurnament.UserRoles.get_as_referee())

    @commands.command(aliases=["take_matches_as_streamer", "tmas"])
    @tosurnament.has_tournament_role("Streamer")
    async def take_match_as_streamer(self, ctx, *args):
        """Allows streamers to take matches"""
        await self.take_or_drop_match(ctx, args, True, tosurnament.UserRoles.get_as_streamer())

    @commands.command(aliases=["take_matches_as_commentator", "tmac"])
    @tosurnament.has_tournament_role("Commentator")
    async def take_match_as_commentator(self, ctx, *args):
        """Allows commentators to take matches"""
        await self.take_or_drop_match(ctx, args, True, tosurnament.UserRoles.get_as_commentator())

    @commands.command(aliases=["drop_matches", "dm"])
    async def drop_match(self, ctx, *args):
        """Allows staffs to drop matches"""
        user_roles = tosurnament.UserRoles.get_from_context(ctx)
        if not user_roles.is_staff():
            await self.send_reply(ctx, ctx.command.name, "not_staff")
        else:
            await self.take_or_drop_match(ctx, args, False, user_roles)

    @commands.command(aliases=["drop_matches_as_referee", "dmar"])
    @tosurnament.has_tournament_role("Referee")
    async def drop_match_as_referee(self, ctx, *args):
        """Allows referees to drop matches"""
        await self.take_or_drop_match(ctx, args, False, tosurnament.UserRoles.get_as_referee())

    @commands.command(aliases=["drop_matches_as_streamer", "dmas"])
    @tosurnament.has_tournament_role("Streamer")
    async def drop_match_as_streamer(self, ctx, *args):
        """Allows streamers to drop matches"""
        await self.take_or_drop_match(ctx, args, False, tosurnament.UserRoles.get_as_streamer())

    @commands.command(aliases=["drop_matches_as_commentator", "dmac"])
    @tosurnament.has_tournament_role("Commentator")
    async def drop_match_as_commentator(self, ctx, *args):
        """Allows commentators to drop matches"""
        await self.take_or_drop_match(ctx, args, False, tosurnament.UserRoles.get_as_commentator())

    def take_match_for_roles(self, schedules_spreadsheet, match_id, match_info, staff_name, user_roles, take):
        """Takes or drops a match of a bracket for specified roles, if possible."""
        write_cells = False
        for role_name, role_store in user_roles.get_staff_roles_as_dict().items():
            if not role_store:
                continue
            take_match = False
            role_cells = getattr(match_info, role_name.lower() + "s")
            if schedules_spreadsheet.use_range:
                for role_cell in role_cells:
                    if take and not role_cell.value:  # TODO check if not already in range
                        role_cell.value = staff_name
                        take_match = True
                        break
                    elif not take and role_cell.value == staff_name:
                        role_cell.value = ""
                        take_match = True
                        break
            elif len(role_cells) > 0:
                role_cell = role_cells[0]
                if take and not role_cell.value:
                    role_cell.value = staff_name
                    take_match = True
                elif take:
                    staffs = role_cell.value.split("/")
                    if len(staffs) == 1 and staffs[0].strip() != staff_name:
                        role_cell.value = staffs[0].strip() + " / " + staff_name
                        take_match = True
                elif not take and role_cell.value:
                    staffs = role_cell.value.split("/")
                    if len(staffs) == 1 and staffs[0].strip() == staff_name:
                        role_cell.value = ""
                        take_match = True
                    elif len(staffs) == 2 and staffs[0].strip() == staff_name:
                        role_cell.value = staffs[1].strip()
                        take_match = True
                    elif len(staffs) == 2 and staffs[1].strip() == staff_name:
                        role_cell.value = staffs[0].strip()
                        take_match = True
            if take_match:
                role_store.taken_matches.append(match_id)
                write_cells = True
            if not take_match:
                role_store.not_taken_matches.append(match_id)
        return write_cells

    def take_matches(self, bracket, match_ids, staff_name, user_roles, take, invalid_match_ids):
        """Takes or drops matches of a bracket, if possible."""
        schedules_spreadsheet = bracket.schedules_spreadsheet
        if not schedules_spreadsheet:
            return
        write_cells = False
        for match_id in match_ids:
            try:
                match_info = MatchInfo.from_id(schedules_spreadsheet, match_id, False)
            except MatchIdNotFound:
                invalid_match_ids.append(match_id)
                continue
            write_cells |= self.take_match_for_roles(
                schedules_spreadsheet, match_id, match_info, staff_name, user_roles, take,
            )
        return write_cells

    def format_take_match_string(self, string, match_ids):
        """Appends the match ids separated by a comma to the string."""
        if match_ids:
            for i, match_id in enumerate(match_ids):
                string += match_id
                if i + 1 < len(match_ids):
                    string += ", "
                else:
                    string += "\n"
            return string
        return ""

    def build_take_match_reply(self, ctx, user_roles, invalid_match_ids):
        """Builds the reply depending on matches taken or not and invalid matches."""
        reply = ""
        for staff_title, staff in user_roles.get_staff_roles_as_dict().items():
            if staff:
                reply += self.format_take_match_string(
                    self.get_string(ctx.command.name, "taken_match_ids", staff_title), staff.taken_matches,
                )
                reply += self.format_take_match_string(
                    self.get_string(ctx.command.name, "not_taken_match_ids", staff_title), staff.not_taken_matches,
                )
        reply += self.format_take_match_string(
            self.get_string(ctx.command.name, "invalid_match_ids"), invalid_match_ids
        )
        return reply

    async def take_or_drop_match(self, ctx, match_ids, take, user_roles):
        if not match_ids:
            raise commands.UserInputError()
        tournament = self.get_tournament(ctx.guild.id)
        try:
            tosurnament_user = self.get_verified_user(ctx.author.id)
            staff_name = tosurnament_user.osu_name
        except (tosurnament.UserNotLinked, tosurnament.UserNotVerified):  # ! Temporary for nik's tournament
            staff_name = ctx.author.display_name
        invalid_match_ids = []
        for bracket in tournament.brackets:
            if self.take_matches(bracket, match_ids, staff_name, user_roles, take, invalid_match_ids):
                try:
                    bracket.schedules_spreadsheet.spreadsheet.update()
                except HttpError as e:
                    raise tosurnament.SpreadsheetHttpError(e.code, e.operation, bracket.name, "schedules")
        await ctx.send(self.build_take_match_reply(ctx, user_roles, invalid_match_ids))


def get_class(bot):
    """Returns the main class of the module"""
    return TosurnamentStaffCog(bot)


def setup(bot):
    """Setups the cog"""
    bot.add_cog(TosurnamentStaffCog(bot))
