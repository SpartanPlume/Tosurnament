"""challonge API wrapper"""

import requests
from common.config import constants

CHALLONGE_URL = "https://api.challonge.com/v1/"


class ChallongeException(Exception):
    """Base exception of the challonge api wrapper"""

    pass


class ServerError(ChallongeException):
    """Special exception when the challonge servers can't be reached"""

    pass


class StartTournamentError(ChallongeException):
    """Special exception when the tournament couldn't be started"""

    pass


class NoRights(ChallongeException):
    """Special exception when the user does not have the rights to do something"""

    pass


class NotFound(ChallongeException):
    """Special exception when the requested data can't be found"""

    pass


class Base:
    """Base class"""

    def __repr__(self):
        return str(self.__dict__)

    def __init__(self, data={}):
        for key, value in data.items():
            object.__setattr__(self, key, value)


class Tournament(Base):
    """Contains fields of a Tournament"""

    def __init__(self, data={}):
        super().__init__(data=data)
        self._matches = None
        self._participants = None

    def start(self):
        try:
            r = requests.post(
                CHALLONGE_URL + "tournaments/" + str(self.id) + "/start.json",
                auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY),
            )
        except requests.exceptions.RequestException:
            raise ServerError()
        t = r.json()
        if "errors" in t:
            if t["errors"][0] == "Invalid state transition":
                raise StartTournamentError()
        if "tournament" not in t:
            raise NoRights()
        new_object = Tournament(t["tournament"])
        self.__dict__.update(new_object.__dict__)

    @property
    def matches(self):
        if self._matches is None:
            try:
                r = requests.get(
                    CHALLONGE_URL + "tournaments/" + str(self.id) + "/matches.json",
                    auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY),
                )
            except requests.exceptions.RequestException:
                raise ServerError()
            m = r.json()
            if "errors" in m:
                raise NotFound()
            else:
                self._matches = []
                for match in m:
                    self._matches.append(Match(match["match"]))
        return self._matches

    @property
    def participants(self):
        if self._participants is None:
            self._participants = get_participants(self.id)
        return self._participants


class Match(Base):
    """Contains fields of a Match"""

    def update_score(self, score_player1, score_player2):
        score = str(score_player1) + "-" + str(score_player2)
        if score_player1 > score_player2:
            winner_id = self.player1_id
        else:
            winner_id = self.player2_id

        try:
            r = requests.put(
                CHALLONGE_URL + "tournaments/" + str(self.tournament_id) + "/matches/" + str(self.id) + ".json",
                auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY),
                data={"match[scores_csv]": score, "match[winner_id]": winner_id},
            )
        except requests.exceptions.RequestException:
            raise ServerError()
        m = r.json()
        if "match" not in m:
            raise NoRights()
        new_object = Match(m["match"])
        self.__dict__.update(new_object.__dict__)


class Participant(Base):
    """Contains fields of a Participant"""

    def __init__(self, data={}):
        super().__init__(data=data)
        self._matches = None

    def has_id(self, participant_id):
        if self.id == participant_id:
            return True
        if participant_id in self.group_player_ids:
            return True
        return False

    def update_name(self, new_name):
        try:
            r = requests.put(
                CHALLONGE_URL + "tournaments/" + str(self.tournament_id) + "/participants/" + str(self.id) + ".json",
                auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY),
                data={"participant[name]": new_name},
            )
        except requests.exceptions.RequestException:
            raise ServerError()
        p = r.json()
        if "participant" not in p:
            raise NoRights()
        new_object = Participant(p["participant"])
        self.__dict__.update(new_object.__dict__)

    @property
    def matches(self):
        if self._matches is None:
            self._matches = get_participant_with_matches(self.tournament_id, self.id)
        return self._matches


def get_tournament(tournament_id):
    try:
        r = requests.get(
            CHALLONGE_URL + "tournaments/" + str(tournament_id) + ".json",
            auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY),
        )
    except requests.exceptions.RequestException:
        raise ServerError()
    t = r.json()
    if "tournament" in t:
        return Tournament(t["tournament"])
    raise NotFound()


def get_participants(tournament_id):
    try:
        r = requests.get(
            CHALLONGE_URL + "tournaments/" + str(tournament_id) + "/participants.json",
            auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY),
        )
    except requests.exceptions.RequestException:
        raise ServerError()
    p = r.json()
    if "errors" in p:
        raise NotFound()
    participants = []
    for participant in p:
        participants.append(Participant(participant["participant"]))
    return participants


def get_participant_with_matches(tournament_id, participant_id):
    try:
        r = requests.get(
            CHALLONGE_URL + "tournaments/" + str(tournament_id) + "/participants/" + str(participant_id) + ".json",
            auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY),
            params={"include_matches": "1"},
        )
    except requests.exceptions.RequestException:
        raise ServerError()
    p = r.json()
    if "participant" not in p:
        raise NotFound()
    matches = []
    if "matches" in p["participant"]:
        for m in p["participant"]["matches"]:
            matches.append(Match(m["match"]))
    return matches
