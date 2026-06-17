from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from datetime import datetime
from database import Base


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    filename = Column(String(255))

    total_rows = Column(Integer)
    valid_rows = Column(Integer)
    invalid_rows = Column(Integer)

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow
    )