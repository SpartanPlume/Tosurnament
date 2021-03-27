"""Match notification table"""

from mysqldb_wrapper import Id
from .base_message import BaseLockMessage


class MatchNotification(BaseLockMessage):
    """MatchNotification class"""

    __tablename__ = "match_notification"

    tournament_id = Id()
    bracket_id = Id()
    message_id_int = int()
    match_id = str()
    teams_mentions = str()
    team1_mention = str()
    team2_mention = str()
    date_info = str()
    notification_type = int()
