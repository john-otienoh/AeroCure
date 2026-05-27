
import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class NotifChannel(str, enum.Enum):
    SMS  = "SMS"
    USSD = "USSD"


class NotifStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT    = "SENT"
    FAILED  = "FAILED"


class NotifRole(str, enum.Enum):
    NURSE       = "NURSE"
    AGENT       = "AGENT"
    HOSPITAL    = "HOSPITAL"
    NEXT_OF_KIN = "NEXT_OF_KIN"


class Notification(Base):
    __tablename__ = "notifications"

    id              = Column(Integer,    primary_key=True, autoincrement=True)
    case_id         = Column(String(20), nullable=True, index=True)
    recipient_phone = Column(String(20), nullable=False)
    recipient_role  = Column(Enum(NotifRole,    name="notif_role"),    nullable=False)
    channel         = Column(Enum(NotifChannel, name="notif_channel"), nullable=False,
                             default=NotifChannel.SMS)
    message_preview = Column(String(100),nullable=True)
    at_message_id   = Column(String(60), nullable=True)
    status = Column(Enum(NotifStatus, name="notif_status"), nullable=False,
                             default=NotifStatus.PENDING)
    cost            = Column(String(20), nullable=True)
    error_detail    = Column(Text,       nullable=True)
    sent_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Notification {self.case_id} {self.channel} {self.status}>"
