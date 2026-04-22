# Backend Schema Blueprint — Smart Volunteer Allocation & Coordination

## 1) Purpose
This database supports an AI-driven volunteer coordination platform for NGOs, volunteers, funders, and admins.  
It is designed for:

- role-based authentication
- volunteer profile management
- community need / task intake
- AI matching using embeddings
- geospatial search with PostGIS
- scheduling and shift tracking
- notifications and feedback
- consent, audit, and analytics

---

## 2) Tech stack alignment

- **Backend API:** FastAPI
- **Database:** PostgreSQL
- **Geospatial:** PostGIS
- **Vector search:** pgvector
- **Background jobs:** Celery + Redis
- **Auth:** JWT + refresh tokens
- **Storage pattern:** normalized relational schema + JSONB for flexible metadata

---

## 3) Auth flow blueprint

### A. Registration
1. User signs up with email, password, full name, and role.
2. System creates a record in `users`.
3. If role = `volunteer`, create a linked record in `volunteers`.
4. If role = `coordinator`, create or link an `organizations` record.
5. Create `consent_logs` entry for privacy consent.
6. Issue JWT access token + refresh token.

### B. Login
1. User submits email + password.
2. Backend verifies password hash.
3. If valid, issue:
   - access token (short-lived)
   - refresh token (long-lived)
4. Store refresh token hash in `auth_sessions` or `refresh_tokens`.

### C. Token refresh
1. Client sends refresh token.
2. Backend validates token hash, expiry, and revocation status.
3. Issue new access token.
4. Optionally rotate refresh token.

### D. Logout
1. Revoke refresh token/session.
2. Access token expires naturally.

### E. Password reset
1. User requests password reset.
2. Create `password_reset_tokens` record.
3. Send reset link via email.
4. User submits new password.
5. Token is marked used/revoked.

### F. Role-based access
- `admin`: full access
- `coordinator`: create tasks, manage assignments, view NGO dashboard
- `volunteer`: manage profile, availability, accept assignments
- `funder`: read-only analytics and reporting

---

## 4) Core tables

### `users`
Central identity table for authentication and authorization.

Fields:
- `id` UUID PK
- `email` unique
- `password_hash`
- `full_name`
- `role`
- `is_active`
- `email_verified`
- `created_at`
- `updated_at`

### `auth_sessions`
Tracks active login sessions / refresh tokens.

Fields:
- `id` UUID PK
- `user_id` FK -> users.id
- `refresh_token_hash`
- `device_info`
- `ip_address`
- `expires_at`
- `revoked_at`
- `created_at`

### `password_reset_tokens`
One-time password reset records.

Fields:
- `id` UUID PK
- `user_id` FK -> users.id
- `token_hash`
- `expires_at`
- `used_at`
- `created_at`

### `organizations`
NGOs or community groups.

Fields:
- `id` UUID PK
- `name`
- `description`
- `created_by_user_id` FK -> users.id
- `created_at`

### `locations`
Shared location table for volunteers, tasks, and organizations.

Fields:
- `id` UUID PK
- `name`
- `address`
- `geom` PostGIS Point(4326)
- `created_at`

### `volunteers`
Volunteer-specific profile data.

Fields:
- `user_id` UUID PK, FK -> users.id
- `bio`
- `location_id` FK -> locations.id
- `embedding` pgvector(768)
- `reputation_score`
- `profile_complete`
- `created_at`

### `skills`
Global skill dictionary.

Fields:
- `id` UUID PK
- `name` unique
- `category`

### `volunteer_skills`
Many-to-many mapping between volunteers and skills.

Fields:
- `volunteer_id` FK -> volunteers.user_id
- `skill_id` FK -> skills.id
- `proficiency_level` 1..5

Primary key:
- (`volunteer_id`, `skill_id`)

### `availability`
Volunteer availability windows.

Fields:
- `id` UUID PK
- `volunteer_id` FK -> volunteers.user_id
- `start_time`
- `end_time`
- `is_recurring`
- `recurrence_rule`

### `tasks`
Community requests / volunteer opportunities.

Fields:
- `id` UUID PK
- `organization_id` FK -> organizations.id
- `title`
- `description`
- `location_id` FK -> locations.id
- `priority`
- `status`
- `embedding` pgvector(768)
- `volunteers_needed`
- `start_time`
- `end_time`
- `deadline`
- `priority_score`
- `created_at`

### `task_skills`
Required skills for each task.

Fields:
- `task_id` FK -> tasks.id
- `skill_id` FK -> skills.id
- `required_level` 1..5

Primary key:
- (`task_id`, `skill_id`)

### `assignments`
Core match table linking volunteers to tasks.

Fields:
- `id` UUID PK
- `task_id` FK -> tasks.id
- `volunteer_id` FK -> volunteers.user_id
- `status`
- `match_score`
- `distance_km`
- `assigned_at`
- `assigned_by_user_id` FK -> users.id

Constraints:
- unique (`task_id`, `volunteer_id`)

### `shifts`
Actual scheduled work periods for assignments.

Fields:
- `id` UUID PK
- `assignment_id` FK -> assignments.id
- `start_time`
- `end_time`
- `check_in`
- `check_out`

### `feedback`
Post-task feedback and ratings.

Fields:
- `id` UUID PK
- `assignment_id` FK -> assignments.id
- `rating`
- `comment`
- `created_at`

### `impact_logs`
Tracks outcomes and volunteer hours.

Fields:
- `id` UUID PK
- `assignment_id` FK -> assignments.id
- `hours_logged`
- `metric_type`
- `value`
- `recorded_at`

### `notifications`
Stores queued/sent alerts.

Fields:
- `id` UUID PK
- `user_id` FK -> users.id
- `type` email/sms/push/in_app
- `message`
- `status`
- `scheduled_for`
- `sent_at`
- `created_at`

### `consent_logs`
GDPR-style consent and privacy tracking.

Fields:
- `id` UUID PK
- `user_id` FK -> users.id
- `consent_given`
- `consent_type`
- `version`
- `created_at`

### `audit_logs`
Records sensitive actions for accountability.

Fields:
- `id` UUID PK
- `actor_user_id` FK -> users.id
- `entity_type`
- `entity_id`
- `action`
- `before_data` JSONB
- `after_data` JSONB
- `created_at`

### `import_jobs`
Tracks data ingestion from CSV/API/OCR/manual sources.

Fields:
- `id` UUID PK
- `source_type`
- `source_name`
- `status`
- `records_total`
- `records_success`
- `records_failed`
- `error_report` JSONB
- `started_at`
- `finished_at`

---

## 5) Relationships

### Identity and auth
- One `user` can have zero or one `volunteer` profile.
- One `user` can belong to many `auth_sessions`.
- One `user` can have many `notifications`, `consent_logs`, and `audit_logs`.

### Organization and tasks
- One `organization` creates many `tasks`.
- One `user` can create many `organizations` if allowed by role.

### Volunteer graph
- One `volunteer` can have many `availability` rows.
- One `volunteer` can have many skills through `volunteer_skills`.
- One `volunteer` can have many `assignments`.

### Task graph
- One `task` belongs to one `organization`.
- One `task` can have many required skills through `task_skills`.
- One `task` can have many `assignments`.

### Assignment graph
- One `assignment` links one `task` and one `volunteer`.
- One `assignment` can have many `shifts`.
- One `assignment` can have many `feedback` rows.
- One `assignment` can have many `impact_logs`.

### Location graph
- One `location` can be linked to many volunteers and tasks.

---

## 6) Matching and scheduling logic

### Matching pipeline
1. Filter volunteers by:
   - required skills
   - availability window
   - location radius
2. Score candidates using:
   - pgvector similarity
   - geospatial distance
   - priority boost
   - fairness rules
3. Insert top matches into `assignments`
4. Create `notifications` for selected volunteers

### Scheduling pipeline
1. Assignment is accepted.
2. Create `shifts`.
3. Send reminder notifications.
4. Mark check-in / check-out during event.
5. Store hours in `impact_logs`.

---

## 7) Indexing plan

- `locations.geom` → GIST index
- `tasks.embedding` → IVFFlat vector index
- `volunteers.embedding` → IVFFlat vector index
- `assignments(task_id, status)` → composite index
- `users.email` → unique index
- `(task_id, volunteer_id)` in `assignments` → unique constraint

---

## 8) Recommended API groups

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`

- `GET/POST /volunteers`
- `GET/POST /tasks`
- `POST /tasks/{id}/match`
- `POST /assignments`
- `POST /shifts`
- `POST /feedback`
- `POST /impact`
- `GET /analytics/dashboard`

---

## 9) Presentation-ready summary

This schema gives the platform a clean backbone:
- secure authentication
- role-based access control
- volunteer and NGO profiles
- skill and availability matching
- geospatial task allocation
- AI embeddings for semantic matching
- compliance, audit, and reporting

It is built to scale from an MVP into a production-ready coordination system.
