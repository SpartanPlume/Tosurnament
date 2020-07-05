#!/usr/bin/python3

"""Starts the server"""

import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
import importlib
import signal
import MySQLdb
from http.server import HTTPServer
from server.handler import create_my_handler
from common.config import constants
from mysqldb_wrapper import Session

ROUTES_DIR = "server.routes"
ROUTER_MODULE = "server.routes.index"


def signal_handler(signal, frame):
    sys.exit(0)


def init_logging_handler():
    """Initializes the logger"""
    logging_handler = TimedRotatingFileHandler(
        filename="log/server.log", when="W1", utc=True, backupCount=4, atTime=datetime.time(hour=12),
    )
    logging_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s: %(message)s"))
    return logging_handler


def init_db(logging_handler):
    """Initializes the database"""
    try:
        session = Session(
            constants.DB_USERNAME, constants.DB_PASSWORD, constants.DB_NAME, constants.ENCRYPTION_KEY, logging_handler,
        )
    except MySQLdb._exceptions.OperationalError:
        print("ERROR: Couldn't initialize the db session. Is the mysql service started ?")
        return None
    return session


def main():
    signal.signal(signal.SIGINT, signal_handler)
    try:
        module = importlib.import_module(ROUTER_MODULE)
    except ModuleNotFoundError:
        print("routes module not found")
        return 1
    for dirpath, dirnames, filenames in os.walk(ROUTES_DIR):
        for filename in filenames:
            if filename.endswith(".py"):
                importlib.import_module(dirpath.replace("/", ".").replace("\\", ".") + "." + filename[:-3])
    logging_handler = init_logging_handler()
    session = init_db(logging_handler)
    if not session:
        return 2
    handler = create_my_handler(module, logging_handler, session)
    httpd = HTTPServer(("", 4000), handler)
    print("Started server at http://localhost:4000")
    httpd.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
