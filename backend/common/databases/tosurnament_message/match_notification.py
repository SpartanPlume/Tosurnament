"""Match notification table"""

from encrypted_mysqldb.fields import IdField, StrField, IntField
from .base_message import BaseLockMessage


class MatchNotification(BaseLockMessage):
    """MatchNotification class"""

    tournament_id = IdField()
    bracket_id = IdField()
    message_id_int = IntField()
    match_id = StrField()
    teams_mentions = StrField()
    team1_mention = StrField()
    team2_mention = StrField()
    date_info = StrField()
    notification_type = IntField()
