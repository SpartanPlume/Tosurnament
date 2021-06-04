import json
from common.api.spreadsheet import Spreadsheet, Worksheet, Cell
from common.databases.spreadsheets.players_spreadsheet import PlayersSpreadsheet
from common.databases.spreadsheets.schedules_spreadsheet import SchedulesSpreadsheet

SPREADSHEET_RESOURCES_DIR = "test/resources/spreadsheets/"


class SpreadsheetMock(Spreadsheet):
    @staticmethod
    def retrieve_spreadsheet(spreadsheet_id):
        with open(SPREADSHEET_RESOURCES_DIR + spreadsheet_id + ".json", "r") as f:
            spreadsheet_data = json.loads(f.read())
        spreadsheet = SpreadsheetMock(spreadsheet_data["spreadsheet_id"])
        for index, sheet in enumerate(spreadsheet_data["worksheets"]):
            cells = []
            for y, row in enumerate(sheet["cells"]):
                cells.append([])
                for x, cell in enumerate(row):
                    cells[y].append(Cell(x, y, cell))
            spreadsheet.worksheets.append(Worksheet(index, sheet["name"], cells))
        spreadsheet._spreadsheet = spreadsheet
        return spreadsheet

    @staticmethod
    def retrieve_spreadsheet_and_update_pickle(spreadsheet_id):
        return SpreadsheetMock.retrieve_spreadsheet(spreadsheet_id)

    @staticmethod
    def get_from_id(spreadsheet_id):
        return SpreadsheetMock.retrieve_spreadsheet(spreadsheet_id)

    def get_updated_values_with_ranges(self):
        ranges_name, ranges_values = [], []
        for worksheet in self.worksheets:
            ranges, values = worksheet.get_updated_values_with_ranges()
            ranges_name = [*ranges_name, *ranges]
            ranges_values = [*ranges_values, *values]
        return ranges_name, ranges_values


class PlayersSpreadsheetSingleMock(PlayersSpreadsheet):
    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self.spreadsheet_id = "players/single"
        self.range_team = "A2:A"
        self.range_discord = "B2:B"


class PlayersSpreadsheetTeamsMock(PlayersSpreadsheet):
    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self.spreadsheet_id = "players/teams"
        self.range_team_name = "A2:A"
        self.range_team = "B2:C"
        self.range_discord = "D2:E"


class SchedulesSpreadsheetSingleMock(SchedulesSpreadsheet):
    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self.spreadsheet_id = "schedules/single"
        self.range_match_id = "A2:A"
        self.range_team1 = "B2:B"
        self.range_score_team1 = "C2:C"
        self.range_score_team2 = "D2:D"
        self.range_team2 = "E2:E"
        self.range_date = "F2:F"
        self.range_time = "G2:G"
        self.range_referee = "H2:H"
        self.range_streamer = "I2:I"
        self.range_commentator = "J2:J"
        self.range_mp_links = "K2:K"


class SchedulesSpreadsheetTeamsMock(SchedulesSpreadsheetSingleMock):
    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self.spreadsheet_id = "schedules/teams"
