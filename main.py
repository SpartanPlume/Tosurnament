"""Starts the bot"""

import sys
import logging
import selfbotclient
import constants

def main():
    """Main function"""
    client = selfbotclient.SelfBotClient()
    client.log(logging.INFO, "Tosurnament Bot started")
    client.run(constants.TOKEN)

if __name__ == '__main__':
    sys.exit(main())
