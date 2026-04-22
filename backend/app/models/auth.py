from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid

class AuthSession(Base, TimestampMixin):
    __tablename__ = "auth_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    refresh_token_hash = Column(String)
    device_info = Column(String)
    ip_address = Column(String)
    expires_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))

class PasswordResetToken(Base, TimestampMixin):
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    token_hash = Column(String)
    expires_at = Column(DateTime(timezone=True))
    used_at = Column(DateTime(timezone=True))
