"""Base spreadsheet table"""

import asyncio
import copy
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

    def copy_to(self, new_obj):
        keys_to_ignore = ["id", "sheet_name"]
        for key, value in vars(self).items():
            if not key.startswith("_") and key not in keys_to_ignore:
                setattr(new_obj, key, value)

    async def get_spreadsheet(self, retry=False, force_sync=False):
        if self._spreadsheet is None or force_sync:
            loop = asyncio.get_running_loop()
            if not loop:
                return None
            n_retry = 0
            while True:
                try:
                    await loop.run_in_executor(None, _get_spreadsheet_worksheet, self, force_sync)
                except SpreadsheetHttpError as e:
                    if e.code != 403 and retry and n_retry < 5:
                        n_retry += 1
                        await asyncio.sleep(10)
                        continue
                    else:
                        raise e
                break
        return self._spreadsheet

    @property
    def spreadsheet(self):
        return self._spreadsheet


def _get_spreadsheet_worksheet(self, force_sync):
    """Retrieves the spreadsheet and its main worksheet."""
    try:
        if force_sync:
            self._spreadsheet = copy.copy(Spreadsheet.retrieve_spreadsheet_and_update_pickle(self.spreadsheet_id))
        else:
            self._spreadsheet = copy.copy(Spreadsheet.get_from_id(self.spreadsheet_id))
        if self.sheet_name:
            for i, worksheet in enumerate(self._spreadsheet.worksheets):
                if worksheet.name == self.sheet_name:
                    self._spreadsheet.main_worksheet_index = i
    except HttpError as e:
        try:
            bracket = (
                self._session.query(common.databases.bracket.Bracket)
                .where(getattr(common.databases.bracket.Bracket, self._type + "_spreadsheet_id") == self.id)
                .first()
            )
        except Exception:
            bracket = None
        if bracket:
            raise SpreadsheetHttpError(e.code, e.operation, bracket.name, self._type, e.error)
        else:
            raise SpreadsheetHttpError(e.code, e.operation, "Unknown bracket", self._type, e.error)
