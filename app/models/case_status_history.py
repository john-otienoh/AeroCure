from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class CaseStatusHistory(Base):
    __tablename__ = "case_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(20), nullable=False, index=True)
    from_status = Column(String(20), nullable=True)
    to_status = Column(String(20), nullable=False)
    changed_by = Column(String(60), nullable=False, default="SYSTEM")
    notes = Column(Text, nullable=True)
    eta_minutes = Column(Integer, nullable=True)
    changed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<StatusHistory {self.case_id}: {self.from_status} → {self.to_status}>"
