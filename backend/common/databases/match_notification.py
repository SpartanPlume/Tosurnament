"""Match notification table"""

from mysqldb_wrapper import Base, Id


class MatchNotification(Base):
    """MatchNotification class"""

    __tablename__ = "match_notification"

    id = Id()
    tournament_id = Id()
    bracket_id = Id()
    message_id_hash = bytes()
    message_id = int()
    match_id = str()
    teams_mentions = str()
    team1_mention = str()
    team2_mention = str()
    date_info = str()
    notification_type = int()
    in_use = bool()
