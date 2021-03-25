"""Players spreadsheet table"""

import re
from discord.ext import commands
from .base_spreadsheet import BaseSpreadsheet
from common.api.spreadsheet import (
    find_corresponding_cell_best_effort_from_range,
    find_corresponding_cells_best_effort_from_range,
    Cell,
    from_letter_base,
)


class PlayersSpreadsheet(BaseSpreadsheet):
    """Players spreadsheet class"""

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._type = "players"

    __tablename__ = "players_spreadsheet"

    range_team_name = str()
    range_team = str()
    range_discord = str()
    range_discord_id = str()
    range_rank = str()
    range_bws_rank = str()
    range_osu_id = str()
    range_pp = str()
    range_country = str()
    range_timezone = str()
    max_range_for_teams = int(0)


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
            self.discord = discord if discord else Cell(-1, -1, "")
            self.discord.value_type = str
            self.discord_id = discord_id if discord_id else Cell(-1, -1, 0)
            self.discord_id.value_type = int
            self.rank = rank if rank else Cell(-1, -1, "")
            self.rank.value_type = str
            self.bws_rank = bws_rank if bws_rank else Cell(-1, -1, "")
            self.bws_rank.value_type = str
            self.osu_id = osu_id if osu_id else Cell(-1, -1, "")
            self.osu_id.value_type = str
            self.pp = pp if pp else Cell(-1, -1, "")
            self.pp.value_type = str
            self.country = country if country else Cell(-1, -1, "")
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

    def find_player(self, name, discord, discord_id):
        for player in self.players:
            if discord_id and discord_id == player.discord_id:
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
        team_info.timezone = find_corresponding_cell_best_effort_from_range(
            players_spreadsheet.spreadsheet,
            players_spreadsheet.range_timezone,
            player_cell,
            max_difference_with_base=players_spreadsheet.max_range_for_teams,
        )
        team_info.add_player(TeamInfo.PlayerInfo(player_cell, discord, discord_id, rank, bws_rank, osu_id, pp, country))
        return team_info

    @staticmethod
    def from_discord_id(players_spreadsheet, discord_id):
        discord_id = str(discord_id)
        discord_id_cells = players_spreadsheet.spreadsheet.find_cells(players_spreadsheet.range_discord_id, discord_id)
        if not discord_id_cells:
            raise TeamNotFound(discord_id)
        discord_id_cell = discord_id_cells[0]
        return TeamInfo.from_discord_id_cell(players_spreadsheet, discord_id_cell)

    @staticmethod
    def from_discord_id_cell(players_spreadsheet, discord_id_cell):
        if players_spreadsheet.range_team_name:
            team_name_cell = find_corresponding_cell_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_team_name,
                discord_id_cell,
            )
            if team_name_cell.x == -1:
                raise TeamNotFound(discord_id_cell.get())
            return TeamInfo.from_team_name_cell(players_spreadsheet, team_name_cell)
        else:
            player_cell = find_corresponding_cell_best_effort_from_range(
                players_spreadsheet.spreadsheet,
                players_spreadsheet.range_team,
                discord_id_cell,
            )
            if player_cell.x == -1:
                raise TeamNotFound(discord_id_cell.get())
            return TeamInfo.from_player_cell(players_spreadsheet, player_cell)

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
                to_string=True,
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
        team_info.timezone = find_corresponding_cells_best_effort_from_range(
            players_spreadsheet.spreadsheet,
            players_spreadsheet.range_timezone,
            team_name_cell,
            max_difference_with_base=players_spreadsheet.max_range_for_teams,
        )[0]
        for name, discord, discord_id, rank, bws_rank, osu_id, pp, country in zip(players_data):
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
