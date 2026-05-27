from sqlalchemy import Boolean, Column, Integer, String, Text

from app.database import Base


class Condition(Base):
    __tablename__ = "conditions"

    code = Column(String(2), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, nullable=False, default=3)
    is_active = Column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Condition {self.code} [{self.priority}] — {self.name}>"
