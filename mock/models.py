import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float,
    Integer, String, Text
)
from sqlalchemy.sql import func

from database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class CaseStatus(str, enum.Enum):
    RECEIVED   = "RECEIVED"
    DISPATCHED = "DISPATCHED"
    AIRBORNE   = "AIRBORNE"
    LANDED     = "LANDED"
    COMPLETED  = "COMPLETED"
    CANCELLED  = "CANCELLED"


class NotifStatus(str, enum.Enum):
    SENT   = "SENT"
    FAILED = "FAILED"


# ── Tables ────────────────────────────────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"

    id               = Column(String(20),  primary_key=True)
    condition_code   = Column(String(2),   nullable=False)
    condition_name   = Column(String(100), nullable=False)
    airstrip_code    = Column(String(20),  nullable=False)
    airstrip_name    = Column(String(200), nullable=False)
    airstrip_lat     = Column(Float,       nullable=True)
    airstrip_lng     = Column(Float,       nullable=True)
    distance_km      = Column(Float,       nullable=True)
    eta_minutes      = Column(Integer,     nullable=True)
    # Stored masked
    nurse_phone      = Column(String(20),  nullable=False)
    status           = Column(
        Enum(CaseStatus, name="case_status"),
        default=CaseStatus.RECEIVED,
        nullable=False,
    )
    notes            = Column(Text,        nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id":             self.id,
            "condition_code": self.condition_code,
            "condition_name": self.condition_name,
            "airstrip_code":  self.airstrip_code,
            "airstrip_name":  self.airstrip_name,
            "airstrip_lat":   self.airstrip_lat,
            "airstrip_lng":   self.airstrip_lng,
            "distance_km":    round(self.distance_km, 1) if self.distance_km else None,
            "eta_minutes":    self.eta_minutes,
            "nurse_phone":    self.nurse_phone,
            "status":         self.status.value if isinstance(self.status, CaseStatus) else self.status,
            "notes":          self.notes,
            "created_at":     self.created_at.isoformat() if self.created_at else None,
            "updated_at":     self.updated_at.isoformat() if self.updated_at else None,
        }


class Notification(Base):
    __tablename__ = "notifications"

    id              = Column(Integer,     primary_key=True, autoincrement=True)
    case_id         = Column(String(20),  nullable=False)
    recipient_phone = Column(String(20),  nullable=False)
    recipient_role  = Column(String(20),  nullable=False)  # NURSE|DISPATCH|AGENT|HOSPITAL|KIN
    message_text    = Column(Text,        nullable=False)
    status          = Column(Enum(NotifStatus, name="notif_status"), default=NotifStatus.SENT)
    at_message_id   = Column(String(60),  nullable=True)
    cost            = Column(String(20),  nullable=True)
    sent_at         = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id":              self.id,
            "case_id":         self.case_id,
            "recipient_phone": self.recipient_phone,
            "recipient_role":  self.recipient_role,
            "message_text":    self.message_text,
            "status":          self.status.value if isinstance(self.status, NotifStatus) else self.status,
            "sent_at":         self.sent_at.isoformat() if self.sent_at else None,
        }


class CaseStatusHistory(Base):
    __tablename__ = "case_status_history"

    id          = Column(Integer,    primary_key=True, autoincrement=True)
    case_id     = Column(String(20), nullable=False)
    from_status = Column(String(20), nullable=True)
    to_status   = Column(String(20), nullable=False)
    changed_by  = Column(String(60), default="SYSTEM")
    notes       = Column(Text,       nullable=True)
    changed_at  = Column(DateTime(timezone=True), server_default=func.now())
