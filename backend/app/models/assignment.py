from sqlalchemy import Column, String, ForeignKey, Float, DateTime, Boolean, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid

class Assignment(Base, TimestampMixin):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    volunteer_id = Column(UUID(as_uuid=True), ForeignKey("volunteers.user_id"))
    status = Column(String, default="pending") # pending, confirmed, completed, cancelled
    match_score = Column(Float)
    distance_km = Column(Float)
    assigned_at = Column(DateTime(timezone=True))
    assigned_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    __table_args__ = (
        UniqueConstraint('task_id', 'volunteer_id', name='uix_task_volunteer'),
    )

class Availability(Base):
    __tablename__ = "availability"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    volunteer_id = Column(UUID(as_uuid=True), ForeignKey("volunteers.user_id"))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String)

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id"))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    check_in = Column(DateTime(timezone=True))
    check_out = Column(DateTime(timezone=True))

class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id"))
    rating = Column(Integer)
    comment = Column(String)

class ImpactLog(Base):
    __tablename__ = "impact_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id"))
    hours_logged = Column(Float)
    metric_type = Column(String)
    value = Column(Float)
    recorded_at = Column(DateTime(timezone=True))
