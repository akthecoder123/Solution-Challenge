from sqlalchemy import Column, String, ForeignKey, Float, Integer, Boolean, Table
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid

volunteer_skills = Table(
    'volunteer_skills',
    Base.metadata,
    Column('volunteer_id', UUID(as_uuid=True), ForeignKey('volunteers.user_id'), primary_key=True),
    Column('skill_id', UUID(as_uuid=True), ForeignKey('skills.id'), primary_key=True),
    Column('proficiency_level', Integer, default=1)
)

class Volunteer(Base, TimestampMixin):
    __tablename__ = "volunteers"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    bio = Column(String)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))
    embedding = Column(Vector(768))
    reputation_score = Column(Float, default=0.0)
    profile_complete = Column(Boolean, default=False)
