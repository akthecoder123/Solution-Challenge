from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid

class ConsentLog(Base, TimestampMixin):
    __tablename__ = "consent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    consent_given = Column(Boolean)
    consent_type = Column(String)
    version = Column(String)

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    entity_type = Column(String)
    entity_id = Column(String)
    action = Column(String)
    before_data = Column(JSONB)
    after_data = Column(JSONB)

class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    source_type = Column(String)
    source_name = Column(String)
    status = Column(String)
    records_total = Column(Integer)
    records_success = Column(Integer)
    records_failed = Column(Integer)
    error_report = Column(JSONB)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
