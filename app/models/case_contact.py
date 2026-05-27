import enum
from sqlalchemy import Column, DateTime, Enum, Integer, String

from app.database import Base


class ContactRole(str, enum.Enum):
    NURSE       = "NURSE"
    NEXT_OF_KIN = "NEXT_OF_KIN"
    AGENT       = "AGENT"
    HOSPITAL    = "HOSPITAL"


class CaseContact(Base):
    __tablename__ = "case_contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(20), nullable=False, index=True)
    role = Column(Enum(ContactRole, name="contact_role"), nullable=False)
    phone_raw = Column(String(20), nullable=False)
    phone_masked = Column(String(20), nullable=False)
    name = Column(String(100),nullable=True)
    notified_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<CaseContact {self.case_id} {self.role} {self.phone_masked}>"
