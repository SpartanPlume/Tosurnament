"""Allowed reschedule table"""

from encrypted_mysqldb.table import Table
from encrypted_mysqldb.fields import IdField, StrField, IntField, DatetimeField


class AllowedReschedule(Table):
    """AllowedReschedule class"""

    tournament_id = IdField()
    match_id = StrField()
    allowed_hours = IntField(24)
    created_at = DatetimeField()
