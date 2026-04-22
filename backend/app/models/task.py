from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Table
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid

task_skills = Table(
    'task_skills',
    Base.metadata,
    Column('task_id', UUID(as_uuid=True), ForeignKey('tasks.id'), primary_key=True),
    Column('skill_id', UUID(as_uuid=True), ForeignKey('skills.id'), primary_key=True),
    Column('required_level', Integer, default=1)
)

class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    title = Column(String, nullable=False)
    description = Column(String)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))
    priority = Column(String) # critical, high, medium, low
    status = Column(String, default="open") # open, in_progress, completed, cancelled
    embedding = Column(Vector(768))
    volunteers_needed = Column(Integer, default=1)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    deadline = Column(DateTime(timezone=True))
    priority_score = Column(Integer, default=0)
