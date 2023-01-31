import os
import importlib

from cryptography.fernet import Fernet
from encrypted_mysqldb.database import Database
from encrypted_mysqldb.errors import DatabaseInitializationError

from common.config import constants

RESOURCES_DIR = "common/databases/tosurnament"
for root, _, files in os.walk(RESOURCES_DIR):
    for filename in files:
        if filename.endswith(".py"):
            importlib.import_module(root.replace("/", ".").replace("\\", ".") + "." + filename[:-3])

try:
    db = Database(
        constants.MYSQL_USER,
        constants.MYSQL_PASSWORD,
        constants.MYSQL_DATABASE,
        Fernet(constants.ENCRYPTION_KEY),
        host=constants.MYSQL_HOST,
        pool_name="tosurnament_pool",
    )
except DatabaseInitializationError as e:
    db = None
