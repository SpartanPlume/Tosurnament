"""File loading all the constants used by the bot and the server"""

import argparse
import json

CONSTANTS_PATH = "../constants.json"

with open(CONSTANTS_PATH) as f:
    data = json.load(f)

constants = argparse.Namespace(**data)
