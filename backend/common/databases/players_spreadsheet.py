"""Players spreadsheet table"""

from discord.ext import commands
from common.databases.base_spreadsheet import BaseSpreadsheet
from common.api.spreadsheet import find_corresponding_cell_best_effort, find_corresponding_cells_best_effort, Cell


class PlayersSpreadsheet(BaseSpreadsheet):
    """Players spreadsheet class"""

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._type = "players"

    __tablename__ = "players_spreadsheet"

    range_team_name = str("")
    range_team = str("B2:B")
    range_discord = str("")


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

    def __init__(self, team_name_cell):
        self.team_name = team_name_cell
        self.players = [team_name_cell]
        self.discord = [""]

    def set_players(self, players_cells):
        if players_cells:
            self.players = players_cells
        else:
            self.players = [self.team_name]

    def set_discord(self, discord_ids):
        while len(discord_ids) < len(self.players):
            discord_ids.append(Cell(-1, -1, None))
        self.discord = discord_ids

    @staticmethod
    def from_player_name(players_spreadsheet, player_name):
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
        team_best_effort_y = player_cell.y
        team_info.set_discord(
            [
                find_corresponding_cell_best_effort(
                    players_spreadsheet.spreadsheet.get_range(players_spreadsheet.range_discord),
                    [team_best_effort_y],
                    team_best_effort_y,
                )
            ]
        )
        return team_info

    @staticmethod
    def from_team_name(players_spreadsheet, team_name):
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
        team_name_best_effort_ys = team_name_cell.y_merge_range
        team_info = TeamInfo(team_name_cell)
        team_info.set_players(
            [
                str(cell.value).lower()
                for cell in find_corresponding_cells_best_effort(
                    players_spreadsheet.spreadsheet.get_range(players_spreadsheet.range_team),
                    team_name_best_effort_ys,
                    team_name_cell.y,
                )
            ]
        )
        team_info.set_discord(
            find_corresponding_cells_best_effort(
                players_spreadsheet.spreadsheet.get_range(players_spreadsheet.range_discord),
                team_name_best_effort_ys,
                team_name_cell.y,
            )
        )
        return team_info
