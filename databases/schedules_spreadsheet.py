"""Schedules spreadsheet class"""

import re
from ast import literal_eval
from mysql_wrapper import Base
from helpers.parser import Parser

class SchedulesSpreadsheet(Base):
    """Schedules spreadsheet class"""
    __tablename__ = 'schedules_spreadsheet'

    id = int()
    spreadsheet_id = bytes()
    range_name = bytes()
    range_match_id = bytes()
    parameters = bytes()
    to_hash = []
    ignore = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse_parameters(self):
        strings = Parser.split(self.parameters, " ", ["()", "[]"])
        tuples = []
        for tup in strings:
            if tup.lower() != "none":
                tuples.append(literal_eval(tup))
            else:
                tuples.append(tup)
        if isinstance(tuples[4], tuple):
            tuples[4] = [tuples[4]]
        return tuples
