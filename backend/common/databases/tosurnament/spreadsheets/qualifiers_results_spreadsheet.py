"""Qualifiers results spreadsheet table"""

from encrypted_mysqldb.fields import StrField

from .base_spreadsheet import BaseSpreadsheet
from common.api.spreadsheet import (
    find_corresponding_cell_best_effort,
    Cell,
)


class QualifiersResultsSpreadsheet(BaseSpreadsheet):
    """Qualifiers spreadsheet class"""

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._type = "qualifiers_results"

    range_osu_id = StrField()
    range_score = StrField()


class QualifiersResultInfo:
    """Contains all info about a lobby."""

    def __init__(self, osu_id_cell):
        self.osu_id = osu_id_cell
        self.score = Cell(-1, -1, "")

    def set_score(self, score_cell):
        self.score = score_cell
        self.score.value_type = str

    @staticmethod
    def get_all(qualifiers_results_spreadsheet):
        osu_id_cells = qualifiers_results_spreadsheet.spreadsheet.get_cells_with_value_in_range(
            qualifiers_results_spreadsheet.range_osu_id
        )
        results_info = []
        for osu_id_cell in osu_id_cells:
            results_info.append(QualifiersResultInfo.from_osu_id_cell(qualifiers_results_spreadsheet, osu_id_cell))
        return results_info

    @staticmethod
    def from_osu_id_cell(qualifiers_results_spreadsheet, osu_id_cell):
        result_info = QualifiersResultInfo(osu_id_cell)
        spreadsheet = qualifiers_results_spreadsheet.spreadsheet
        result_info.set_score(
            find_corresponding_cell_best_effort(
                spreadsheet.get_range(qualifiers_results_spreadsheet.range_score), osu_id_cell
            )
        )
        return result_info
