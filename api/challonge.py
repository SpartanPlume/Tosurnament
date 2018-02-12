"""challonge API wrapper"""

import requests
import constants

CHALLONGE_URL = "https://api.challonge.com/v1/"

class ServerError(Exception):
    """Special exception when the challonge servers can't be reached"""
    pass

class NoRights(Exception):
    """Special exception when the user does not have the rights to do something"""
    pass

class NotFound(Exception):
    """Special exception when the requested data can't be found"""
    pass

def get_tournament(tournament):
    try:
        r = requests.get(CHALLONGE_URL + "tournaments/" + str(tournament) + ".json", auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY))
    except requests.exceptions.RequestException:
        raise ServerError()
    t = r.json()
    if "tournament" in t:
        return t["tournament"]
    raise NotFound()

def start_tournament(tournament):
    try:
        r = requests.post(CHALLONGE_URL + "tournaments/" + str(tournament) + "/start.json", auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY))
    except requests.exceptions.RequestException:
        raise ServerError()
    t = r.json()
    if "tournament" in t:
        return t["tournament"]
    elif "errors" in t:
        if t["errors"][0] == "Invalid state transition":
            return []
    raise NoRights()

def get_matches(tournament):
    try:
        r = requests.get(CHALLONGE_URL + "tournaments/" + str(tournament) + "/matches.json", auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY))
    except requests.exceptions.RequestException:
        raise ServerError()
    m = r.json()
    if "errors" in m:
        raise NotFound()
    else:
        matches = []
        for match in m:
            matches.append(match["match"])
        return matches

def update_match(tournament, match_id, **params):
    new_params = {}
    for key, value in params.items():
        key = "match[" + key + "]"
        new_params[key] = value
    try:
        r = requests.put(CHALLONGE_URL + "tournaments/" + str(tournament) + "/matches/" + str(match_id) + ".json", auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY), data=new_params)
    except requests.exceptions.RequestException:
        raise ServerError()
    m = r.json()
    if "match" in m:
        return m["match"]
    raise NoRights()

def get_participants(tournament):
    try:
        r = requests.get(CHALLONGE_URL + "tournaments/" + str(tournament) + "/participants.json", auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY))
    except requests.exceptions.RequestException:
        raise ServerError()
    p = r.json()
    if "errors" in p:
        raise NotFound()
    else:
        participants = []
        for participant in p:
            participants.append(participant["participant"])
        return participants

def get_participant(tournament, participant_id, **params):
    try:
        r = requests.get(CHALLONGE_URL + "tournaments/" + str(tournament) + "/participants/" + str(participant_id) + ".json", auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY), params=params)
    except requests.exceptions.RequestException:
        raise ServerError()
    p = r.json()
    if "participant" in p:
        return p["participant"]
    raise NotFound()

def update_participant(tournament, participant_id, **params):
    new_params = {}
    for key, value in params.items():
        key = "participant[" + key + "]"
        new_params[key] = value
    try:
        r = requests.put(CHALLONGE_URL + "tournaments/" + str(tournament) + "/participants/" + str(participant_id) + ".json", auth=(constants.CHALLONGE_USERNAME, constants.CHALLONGE_API_KEY), data=new_params)
    except requests.exceptions.RequestException:
        raise ServerError()
    p = r.json()
    if "participant" in p:
        return p["participant"]
    raise NoRights()    

def is_match_containing_participants(match, participant1, participant2):
    participant_id = get_id_from_participant(participant1)
    if match["player1_id"] != participant_id and match["player2_id"] != participant_id:
        return None
    participant_id = get_id_from_participant(participant2)
    if match["player1_id"] == participant_id:
        return participant2, participant1
    elif match["player2_id"] == participant_id:
        return participant1, participant2
    return None, None

def get_id_from_participant(participant):
    if "group_player_ids" in participant and len(participant["group_player_ids"]) > 0:
        return participant["group_player_ids"][0]
    else:
        return participant["id"]
