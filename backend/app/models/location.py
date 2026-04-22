from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid

class Location(Base, TimestampMixin):
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String)
    address = Column(String)
    geom = Column(Geometry('POINT', srid=4326))
