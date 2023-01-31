"""File loading all the constants used by the bot and the server"""

import argparse
import os

constants = argparse.Namespace(**os.environ)
