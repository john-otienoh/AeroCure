import enum
from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base

class CaseStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    DISPATCHED = "DISPATCHED"
    AIRBORNE = "AIRBORNE"
    LANDED = "LANDED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Case(Base):
    __tablename__ = 'cases'
    id = Column(String(20), primary_key=True)
    condition_code = Column(String(2), nullable=False, index=True)
    condition_name = Column(String(100), nullable=False)
    airstrip_code = Column(
        String(30),
        nullable=False,
        index=True,
    )
    airstrip_name = Column(String(100), nullable=False)
    initiating_phone = Column(String(20), nullable=False)

    status = Column(
        Enum(CaseStatus, name="case_status"),
        default=CaseStatus.RECEIVED,
        nullable=False,
        index=True,
    )
    eta_minutes = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Case id={self.id} status={self.status} airstrip={self.airstrip_code}>"