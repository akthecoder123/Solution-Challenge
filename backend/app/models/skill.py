from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.models.base import generate_uuid

class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)
    category = Column(String)
