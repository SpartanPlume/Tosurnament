"""Base for all databases"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event

Base = declarative_base()
