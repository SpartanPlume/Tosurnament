#!/usr/bin/python3

"""Main file used to start the bot"""

import sys

from bot.client import Client
from common.config import constants


def main():
    """Main function"""
    bot = Client()
    if bot.error_code == 0:
        bot.run(constants.BOT_TOKEN)
    return bot.error_code


if __name__ == "__main__":
    sys.exit(main())
