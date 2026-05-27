
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class OperatorRole(str, enum.Enum):
    ADMIN      = "ADMIN"      
    DISPATCHER = "DISPATCHER"  
    VIEWER     = "VIEWER"      


class Operator(Base):
    __tablename__ = "operators"

    id            = Column(Integer,    primary_key=True, autoincrement=True)
    username      = Column(String(60), nullable=False, unique=True, index=True)
    # bcrypt hash — use passlib.hash.bcrypt.hash(password) to generate
    password_hash = Column(String(128),nullable=False)
    full_name     = Column(String(100),nullable=True)
    role          = Column(
        Enum(OperatorRole, name="operator_role"),
        nullable=False,
        default=OperatorRole.DISPATCHER,
    )
    is_active     = Column(Boolean,    nullable=False, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Operator {self.username} [{self.role}]>"
