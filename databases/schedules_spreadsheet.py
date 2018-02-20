"""Schedules spreadsheet class"""

import re
from ast import literal_eval
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary
from sqlalchemy import orm
from databases.base import Base
import helpers.crypt
from helpers.parser import Parser

class SchedulesSpreadsheet(Base):
    """Schedules spreadsheet class"""
    __tablename__ = 'schedules_spreadsheet'

    id = Column(Integer, primary_key=True)
    spreadsheet_id = Column(Binary)
    range_name = Column(Binary)
    parameters = Column(Binary)
    to_hash = []
    ignore = []

    @orm.reconstructor
    def init(self):
        """Decrypts the object after being queried"""
        self = helpers.crypt.decrypt_obj(self)

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