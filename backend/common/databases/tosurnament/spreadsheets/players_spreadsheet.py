"""Players spreadsheet table"""

import re

from discord.ext import commands
from encrypted_mysqldb.fields import StrField, IntField

from .base_spreadsheet import BaseSpreadsheet
from common.api.spreadsheet import (
    find_corresponding_cell_best_effort_from_range,
    find_corresponding_cells_best_effort_from_range,
    Cell,
    from_letter_base,
)


class PlayersSpreadsheet(BaseSpreadsheet):
    """Players spreadsheet class"""

    range_team_name = StrField()
    range_team = StrField()
    range_discord = StrField()
    range_discord_id = StrField()
    range_rank = StrField()
    range_bws_rank = StrField()
    range_osu_id = StrField()
    range_pp = StrField()
    range_country = StrField()
    range_timezone = StrField()
    max_range_for_teams = IntField()

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._type = "players"


class TeamNotFound(commands.CommandError):
    """Thrown when a match id is not found."""

    def __init__(self, team):
        self.team = team


class DuplicateTeam(commands.CommandError):
    """Thrown when a match id is found multiple times."""

    def __init__(self, team):
        self.team = team


class TeamInfo:
    """Contains all info about a team."""

    class PlayerInfo:
        def __init__(
            self,
            name,
            discord=None,
            discord_id=None,
            rank=None,
            bws_rank=None,
            osu_id=None,
            pp=None,
            country=None,
            is_captain=False,
        ):
            self.name = name
            self.name.value_type = str
            self.discord = discord if isinstance(discord, Cell) else Cell(-1, -1, "")
            self.discord.value_type = str
            self.discord_id = discord_id if isinstance(discord_id, Cell) else Cell(-1, -1, 0)
            self.discord_id.value_type = int
            self.rank = rank if isinstance(rank, Cell) else Cell(-1, -1, "")
            self.rank.value_type = str
            self.bws_rank = bws_rank if isinstance(bws_rank, Cell) else Cell(-1, -1, "")
            self.bws_rank.value_type = str
            self.osu_id = osu_id if isinstance(osu_id, Cell) else Cell(-1, -1, "")
            self.osu_id.value_type = str
            self.pp = pp if isinstance(pp, Cell) else Cell(-1, -1, "")
            self.pp.value_type = str
            self.country = country if isinstance(country, Cell) else Cell(-1, -1, "")
            self.country.value_type = str
            self.is_captain = is_captain

    def __init__(self, team_name_cell):
        self.team_name = team_name_cell
        self.team_name.value_type = str
        self.players = []
        self.timezone = Cell(-1, -1, "")

    def add_player(self, player_info):
        if not self.players:
            player_info.is_captain = True
        self.players.append(player_info)

    def set_timezone(self, timezone_cell):
        self.timezone = timezone_cell
        self.timezone.value_type = str

    def find_player(self, name, discord_id, discord):
        for player in self.players:
            if discord_id and str(discord_id) == str(player.discord_id):
                return player
            elif discord and discord == player.discord:
                return player
            elif name and name.casefold() == player.name.casefold():
                return player
        return None

    def get_team_captain(self):
        for player in self.players:
            if player.is_captain:
                return player
        return self.players[0]

    @staticmethod
    def from_player_name(players_spreadsheet, player_name):
        player_name = str(player_name)
        player_cells = players_spreadsheet.spreadsheet.find_cells(players_spreadsheet.range_team, player_name)
        if not player_cells:
            raise TeamNotFound(player_name)
        # ? To keep ?
        # if len(player_cells) > 1:
        #    raise DuplicateTeam(player_name)
        player_cell = player_cells[0]
        return TeamInfo.from_player_cell(players_spreadsheet, player_cell)

    @staticmethod
    def from_player_cell(players_spreadsheet, player_cell):
        team_info = TeamInfo(player_cell)
        discord = find_corresponding_cell_best_effort_from_range(
            players_spreadsheet.spreadsheet,
            players_spreadsheet.range_discord,
            player_cell,
            max_difference_with_base=players_spreadsheet.max_range_for_teams,
        )
        discord_id = find_corresponding_cell_best_effort_from_range(
            players_spreadsheet.spreadsheet,
            players_spreadsheet.range_discord_id,
            player_cell,
            max_difference_with_base=players_spreadsheet.max_range_for_teams,
        )
        rank = find_corresponding_cell_best_effort_from_range(
            players_spreadsheet.spreadsheet,
            players_spreadsheet.range_rank,
            player_cell,
            max_difference_with_base=players_spreadsheet.max_range_for_teams,
        )
        bws_rank = find_corresponding_cell_best_effort_from_range(
            players_spreadsheet.spreadsheet,
            players_spreadsheet.range_bws_rank,
            player_cell,
            max_difference_with_base=players_spreadsheet.max_range_for_teams,
        )
        osu_id = find_corresponding_cell_best_effort_from_range(
            players_spreadsheet.spreadsheet,
            players_spreadsheet.range_osu_id,
            player_cell,
            max_difference_with_base=players_spreadsheet.max_range_for_teams,
        )
        pp = find_corresponding_cell_best_effort_from_range(
            players_spreadsheet.spreadsheet,
            players_spreadsheet.range_pp,
            player_cell,
            max_difference_with_base=players_spreadsheet.max_range_for_teams,
        )
        country = find_corresponding_cell_best_effort_from_range(
            players_spreadsheet.spreadsheet,
            players_spreadsheet.range_country,
            player_cell,
            max_difference_with_base=players_spreadsheet.max_range_for_teams,
        )
        team_info.set_timezone(
            find_corresponding_cell_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_timezone,
                player_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams,
            )
        )
        team_info.add_player(TeamInfo.PlayerInfo(player_cell, discord, discord_id, rank, bws_rank, osu_id, pp, country))
        return team_info

    @staticmethod
    def from_team_name(players_spreadsheet, team_name):
        team_name = str(team_name)
        if not players_spreadsheet.range_team_name:
            return TeamInfo.from_player_name(players_spreadsheet, team_name)
        team_name_cells = players_spreadsheet.spreadsheet.find_cells(players_spreadsheet.range_team_name, team_name)
        if not team_name_cells:
            raise TeamNotFound(team_name)
        # ? To keep ?
        # if len(team_name_cells) > 1:
        #    raise DuplicateTeam(team_name)
        team_name_cell = team_name_cells[0]
        return TeamInfo.from_team_name_cell(players_spreadsheet, team_name_cell)

    @staticmethod
    def from_team_name_cell(players_spreadsheet, team_name_cell):
        team_info = TeamInfo(team_name_cell)
        players_data = []
        players_data.append(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_team,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams,
            )
        )
        players_data.append(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_discord,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams,
            )
        )
        players_data.append(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_discord_id,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams,
            )
        )
        players_data.append(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_rank,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams,
            )
        )
        players_data.append(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_bws_rank,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams,
            )
        )
        players_data.append(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_osu_id,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams,
            )
        )
        players_data.append(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_pp,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams,
            )
        )
        players_data.append(
            find_corresponding_cells_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_country,
                team_name_cell,
                max_difference_with_base=players_spreadsheet.max_range_for_teams,
            )
        )
        # TODO: only one cell needed / maybe a new function needed ?
        timezone_cells = find_corresponding_cells_best_effort_from_range(
            players_spreadsheet.spreadsheet,
            players_spreadsheet.range_timezone,
            team_name_cell,
            max_difference_with_base=players_spreadsheet.max_range_for_teams,
        )
        if timezone_cells:
            team_info.timezone = timezone_cells[0]
        max_len = len(players_data[0])
        for player_data in players_data:
            while len(player_data) < max_len:
                player_data.append(Cell(-1, -1, ""))
        for name, discord, discord_id, rank, bws_rank, osu_id, pp, country in zip(*players_data):
            team_info.add_player(TeamInfo.PlayerInfo(name, discord, discord_id, rank, bws_rank, osu_id, pp, country))
        return team_info

    @staticmethod
    def get_first_blank_fields(players_spreadsheet):
        range_to_use = None
        if players_spreadsheet.range_team_name:
            range_to_use = players_spreadsheet.range_team_name
        else:
            range_to_use = players_spreadsheet.range_team
        cells = players_spreadsheet.spreadsheet.get_range(range_to_use)
        if not cells:
            worksheet, range_to_use = players_spreadsheet.spreadsheet.get_worksheet_and_range(range_to_use)
            splitted_range = range_to_use.split(":")[0]
            column, row, _ = re.split(r"(\d+)", splitted_range)  # TODO: handle all kind of ranges
            cells = [[Cell(from_letter_base(column), int(row) - 1, "")]]
            worksheet.cells = cells
        used = False
        for row in cells:
            used = False
            for cell in row:
                if cell:
                    used = True
                    break
            if not used:
                break
        if used:
            worksheet, _ = players_spreadsheet.spreadsheet.get_worksheet_and_range(range_to_use)
            cells = worksheet.cells
            row = [Cell(row[0].x, row[0].y + 1, "")]
            cells.append(row)
        if players_spreadsheet.range_team_name:
            return TeamInfo.from_team_name_cell(players_spreadsheet, row[0])
        else:
            return TeamInfo.from_player_cell(players_spreadsheet, row[0])
