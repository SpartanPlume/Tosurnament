"""Base spreadsheet table"""

from mysqldb_wrapper import Base, Id
from common.api.spreadsheet import Spreadsheet, HttpError
from common.exceptions import SpreadsheetHttpError
import common.databases.bracket


class BaseSpreadsheet(Base):
    """Base spreadsheet class"""

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._spreadsheet = None
        self._type = ""

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.id = Id()
        cls.spreadsheet_id = str()
        cls.sheet_name = str("")

    @property
    def spreadsheet(self):
        if self._spreadsheet is None:
            self._get_spreadsheet_worksheet()
        return self._spreadsheet

    def _get_spreadsheet_worksheet(self):
        """Retrieves the spreadsheet and its main worksheet."""
        try:
            self._spreadsheet = Spreadsheet.get_from_id(self.spreadsheet_id)
            if self.sheet_name:
                for i, worksheet in enumerate(self._spreadsheet.worksheets):
                    if worksheet.name == self.sheet_name:
                        self._spreadsheet.main_worksheet_index = i
        except HttpError as e:
            bracket = (
                self._session.query(common.databases.bracket.Bracket)
                .where(getattr(common.databases.bracket.Bracket, self._type + "_spreadsheet_id") == self.id)
                .first()
            )
            if bracket:
                raise SpreadsheetHttpError(e.code, e.operation, bracket.name, self._type, e.error)
            else:
                raise SpreadsheetHttpError(e.code, e.operation, "Unknown bracket", self._type, e.error)
