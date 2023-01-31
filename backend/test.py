from encrypted_mysqldb.database import Database
from cryptography.fernet import Fernet
from common.config import constants
from common.databases.tosurnament.tournament import Tournament
from common.databases.tosurnament.bracket import Bracket
from common.databases.tosurnament.user import User

db = Database("spartanplume", "^9dNs3%s&5KyV5", "tosurnament", Fernet("tPfa-QbunB3PdvFuZQKrkoz7FZFsSUSbrdJ4fEEA_WY="))
tournament_id_to_current_bracket_id = {
    1: 3,
    2: 4,
    3: 5,
    4: 7,
    5: 8,
    6: 9,
    7: 10,
    8: 12,
    9: 13,
    10: 15,
    11: 16,
    12: 17,
    13: 18,
    14: 19,
    15: 21,
    16: 22,
    17: 23,
    18: 24,
    19: 25,
    20: 26,
    21: 28,
    22: 31,
    23: 32,
    24: 33,
    25: 34,
    26: 35,
    27: 36,
    28: 37,
}
for tournament_id, current_bracket_id in tournament_id_to_current_bracket_id.items():
    tournament = db.query(Tournament).where(Tournament.id == tournament_id).first()
    tournament.current_bracket_id = current_bracket_id
    print(tournament.get_api_dict())
    # db.update(tournament)
