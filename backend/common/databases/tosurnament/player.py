"""Team table"""

from encrypted_mysqldb.table import Table
from encrypted_mysqldb.fields import IdField, BoolField


class Player(Table):
    """Player class"""

    team_id = IdField()
    user_id = IdField()
    is_captain = BoolField()
    has_validated_participation = BoolField()
