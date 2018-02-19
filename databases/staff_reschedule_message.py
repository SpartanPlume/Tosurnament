"""Staff reschedule message class"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Binary
from sqlalchemy import orm
from databases.base import Base
import helpers.crypt

class StaffRescheduleMessage(Base):
    """Staff reschedule message class"""
    __tablename__ = 'staff_reschedule_message'

    id = Column(Integer, primary_key=True)
    message_id = Column(Binary)
    match_id = Column(Binary)
    staff_id = Column(Binary)
    to_hash = ["message_id"]
    ignore = ["staff_type"]

    @orm.reconstructor
    def init(self):
        """Decrypts the object after being queried"""
        self = helpers.crypt.decrypt_obj(self)
