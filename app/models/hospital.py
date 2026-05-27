
from sqlalchemy import Boolean, Column, Float, Integer, String

from app.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False)
    county = Column(String(80), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Hospital {self.name} default={self.is_default}>"
