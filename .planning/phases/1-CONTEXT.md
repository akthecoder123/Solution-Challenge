# Phase 1: Database Schema

## Decisions
- **Handling Enums**: Use Python Enums stored as `VARCHAR` in PostgreSQL for easier Alembic migrations and code flexibility.
- **Geospatial Integration**: Use `GeoAlchemy2` to map PostGIS geometry types cleanly within SQLAlchemy models.
- **Primary Key Generation**: Generate UUIDs in Python (`uuid.uuid4`) as the default for primary keys.
- **Timestamp Tracking**: Use a shared `TimestampMixin` to automatically handle `created_at` and `updated_at` across all models.

## Specifics
- Database schema and folder structure as outlined in `AI_IMPLEMENTATION_PLAN.md` and `backend_schema_blueprint.md`.
- Ensure migrations apply PostGIS and pgvector extensions manually before creating related indexes.

## Canonical refs
- `AI_IMPLEMENTATION_PLAN.md`
- `backend_schema_blueprint.md`
