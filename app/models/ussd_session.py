import enum

from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.sql import func

from app.database import Base


class USSDOutcome(str, enum.Enum):
    CASE_CREATED   = "CASE_CREATED"    # User completed emergency report
    STATUS_CHECKED = "STATUS_CHECKED"  # User queried a case
    ABANDONED      = "ABANDONED"       # Session ended without completing
    CANCELLED      = "CANCELLED"       # User explicitly cancelled


class USSDSession(Base):
    __tablename__ = "ussd_sessions"

    # AT-provided session ID — unique per USSD dial
    session_id   = Column(String(60),  primary_key=True)
    phone        = Column(String(20),  nullable=False, index=True)
    service_code = Column(String(20),  nullable=True)
    # Full input path at session end e.g. "1*2*3*1"
    final_text   = Column(String(200), nullable=True)
    # Case ID created during this session, or NULL
    case_created = Column(String(20),  nullable=True)
    outcome      = Column(Enum(USSDOutcome, name="ussd_outcome"), nullable=True)
    started_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # Written when the session returns an END response
    ended_at     = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<USSDSession {self.session_id} {self.outcome}>"
