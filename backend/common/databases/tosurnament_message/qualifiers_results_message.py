"""Qualifiers results message table"""

from encrypted_mysqldb.table import Table
from encrypted_mysqldb.fields import IdField, StrField, IntField


class QualifiersResultsMessage(Table):
    """Qualifiers results message class"""

    tournament_id = IdField()
    bracket_id = IdField()
    message_id = IntField()
    channel_id = StrField()
