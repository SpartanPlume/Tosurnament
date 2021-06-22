import mysqldb_wrapper
from common.config import constants

db = mysqldb_wrapper.Session(constants.DB_USERNAME, constants.DB_PASSWORD, constants.DB_NAME, constants.ENCRYPTION_KEY)
