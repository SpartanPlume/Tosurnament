"""Starts the bot"""

import sys
import logging
import client
import constants

def main():
    """Main function"""
    client = client.Client()
    client.log(logging.INFO, "Tosurnament Bot started")
    client.run(constants.TOKEN)

if __name__ == '__main__':
    sys.exit(main())
