# AI Implementation Plan — Smart Volunteer Coordination System
> **For AI agents (Claude Code, Cursor, Copilot, etc.)**
> Follow phases in strict order. Complete every checklist item before moving to the next phase.
> Each phase has a clear goal, exact file structure, commands, and acceptance criteria.

---

## Stack Reference (commit to this — do not deviate)

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS + Shadcn/UI |
| Backend API | FastAPI (Python 3.11+) |
| Database | PostgreSQL 15 + PostGIS + pgvector |
| Hosting (DB) | Supabase (free tier for hackathon) |
| AI / Matching | Google Gemini API + pgvector similarity + SciPy/PuLP |
| Background Jobs | Celery + Redis |
| Maps | Mapbox GL JS |
| Auth | JWT (access + refresh tokens) via FastAPI |
| Notifications | Twilio (SMS) + SendGrid (email) |
| Deployment | Vercel (frontend) + Railway or Render (backend) |

---

## Phase 0 — Project Scaffold (Day 1, ~2 hours)

**Goal:** Monorepo exists, both apps boot, env vars wired, git initialized.

### 0.1 Create monorepo structure
```
smart-volunteer/
├── frontend/          # Next.js app
├── backend/           # FastAPI app
├── docs/              # PRD, schema, flow diagrams
├── .env.example
├── docker-compose.yml
└── README.md
```

### 0.2 Initialize frontend
```bash
cd smart-volunteer
npx create-next-app@latest frontend \
  --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
cd frontend
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card badge input label select dialog sheet tabs
npm install mapbox-gl @types/mapbox-gl lucide-react axios swr date-fns
```

### 0.3 Initialize backend
```bash
cd ../backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn[standard] sqlalchemy asyncpg alembic \
  psycopg2-binary pydantic pydantic-settings python-jose[cryptography] \
  passlib[bcrypt] celery redis python-multipart langchain google-generativeai \
  pgvector scipy pulp geopy httpx pytest pytest-asyncio python-dotenv
pip freeze > requirements.txt
```

### 0.4 Create docker-compose.yml (local dev only)
```yaml
version: '3.9'
services:
  db:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_DB: volunteer_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
volumes:
  pgdata:
```

### 0.5 .env.example
```
# Backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/volunteer_db
REDIS_URL=redis://localhost:6379
JWT_SECRET=changeme_use_32_char_random_string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
GEMINI_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
SENDGRID_API_KEY=
MAPBOX_TOKEN=

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAPBOX_TOKEN=
```

### 0.6 Acceptance criteria
- [ ] `docker-compose up` starts Postgres + Redis with no errors
- [ ] `cd frontend && npm run dev` → Next.js running on :3000
- [ ] `cd backend && uvicorn main:app --reload` → FastAPI on :8000, `/docs` loads

---

## Phase 1 — Database Schema (Day 1–2, ~3 hours)

**Goal:** All tables exist in Postgres with correct indexes. Alembic migrations work.

### 1.1 Backend folder structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── volunteer.py
│   │   ├── organization.py
│   │   ├── task.py
│   │   ├── assignment.py
│   │   ├── notification.py
│   │   └── audit.py
│   ├── schemas/
│   ├── routers/
│   ├── services/
│   └── utils/
├── alembic/
├── alembic.ini
└── requirements.txt
```

### 1.2 Create app/database.py
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### 1.3 Create all models (implement each file)

**app/models/user.py** — fields: id(UUID), email(unique), password_hash, full_name, role(enum: admin/coordinator/volunteer/funder), is_active, email_verified, created_at, updated_at

**app/models/volunteer.py** — fields: user_id(FK), bio, location_id(FK), embedding(Vector(768)), reputation_score, profile_complete, created_at. Relations: skills (many-to-many via volunteer_skills), availability (one-to-many), assignments (one-to-many)

**app/models/organization.py** — fields: id(UUID), name, description, created_by_user_id(FK), created_at

**app/models/task.py** — fields: id(UUID), organization_id(FK), title, description, location_id(FK), priority(enum), status(enum: open/in_progress/completed/cancelled), embedding(Vector(768)), volunteers_needed, start_time, end_time, deadline, priority_score, created_at

**app/models/assignment.py** — fields: id(UUID), task_id(FK), volunteer_id(FK), status(enum: pending/confirmed/completed/cancelled), match_score(float), distance_km(float), assigned_at, assigned_by_user_id(FK). Unique constraint: (task_id, volunteer_id)

**app/models/notification.py** — fields: id, user_id(FK), type(enum: email/sms/push/in_app), message, status(enum: pending/sent/failed), scheduled_for, sent_at, created_at

**app/models/audit.py** — consent_logs, audit_logs, import_jobs tables

### 1.4 Additional tables to add in models
- `locations` — id, name, address, geom(PostGIS POINT 4326), created_at
- `skills` — id, name(unique), category
- `volunteer_skills` — volunteer_id, skill_id, proficiency_level(1-5), PK(both)
- `task_skills` — task_id, skill_id, required_level(1-5), PK(both)
- `availability` — id, volunteer_id, start_time, end_time, is_recurring, recurrence_rule
- `shifts` — id, assignment_id, start_time, end_time, check_in, check_out
- `feedback` — id, assignment_id, rating(1-5), comment, created_at
- `impact_logs` — id, assignment_id, hours_logged, metric_type, value, recorded_at
- `auth_sessions` — id, user_id, refresh_token_hash, device_info, ip_address, expires_at, revoked_at
- `password_reset_tokens` — id, user_id, token_hash, expires_at, used_at

### 1.5 Run Alembic
```bash
alembic init alembic
# Edit alembic/env.py to use async engine and import all models
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

### 1.6 Create PostGIS + pgvector indexes manually in migration
```sql
-- Add to migration file
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE INDEX idx_locations_geom ON locations USING GIST(geom);
CREATE INDEX idx_tasks_embedding ON tasks USING ivfflat(embedding vector_cosine_ops) WITH (lists=100);
CREATE INDEX idx_volunteers_embedding ON volunteers USING ivfflat(embedding vector_cosine_ops) WITH (lists=100);
CREATE INDEX idx_assignments_task_status ON assignments(task_id, status);
```

### 1.7 Acceptance criteria
- [ ] `alembic upgrade head` completes with zero errors
- [ ] All 20 tables visible in psql/Supabase
- [ ] PostGIS geom column exists on locations
- [ ] pgvector columns exist on volunteers and tasks
- [ ] All indexes created

---

## Phase 2 — Auth System (Day 2, ~3 hours)

**Goal:** Register, login, refresh, logout all work. JWT gates protected routes.

### 2.1 Create app/utils/auth.py
```python
# Implement:
# - hash_password(plain) -> hashed
# - verify_password(plain, hashed) -> bool
# - create_access_token(data, expires_delta) -> str
# - create_refresh_token(data) -> str
# - decode_token(token) -> payload dict
# - get_current_user(token, db) -> User  (FastAPI dependency)
# - require_role(*roles) -> FastAPI dependency factory
```

### 2.2 Create app/schemas/auth.py
```python
# Pydantic models:
# RegisterRequest: email, password, full_name, role
# LoginRequest: email, password
# TokenResponse: access_token, refresh_token, token_type
# RefreshRequest: refresh_token
# PasswordResetRequest: email
# PasswordResetConfirm: token, new_password
```

### 2.3 Create app/routers/auth.py — implement all endpoints
```
POST /auth/register      → create user + volunteer/org record + consent_log + return tokens
POST /auth/login         → verify password + issue tokens + create auth_session
POST /auth/refresh       → validate refresh token + issue new access token
POST /auth/logout        → revoke auth_session
POST /auth/forgot-password → create password_reset_token + send email
POST /auth/reset-password  → validate token + update password_hash + mark token used
GET  /auth/me            → return current user (protected)
```

### 2.4 Wire into main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth

app = FastAPI(title="Smart Volunteer API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], 
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
```

### 2.5 Frontend: Auth pages
Create these pages/components in Next.js:
```
frontend/src/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── layout.tsx
├── lib/
│   ├── api.ts          # axios instance with interceptor for token refresh
│   └── auth.ts         # useAuth hook, token storage in httpOnly cookie
├── middleware.ts        # Next.js middleware to protect routes by role
```

**middleware.ts logic:** redirect unauthenticated users to /login; redirect by role — volunteer→/volunteer, coordinator→/coordinator, funder→/funder, admin→/admin

### 2.6 Acceptance criteria
- [ ] POST /auth/register creates user + returns JWT
- [ ] POST /auth/login returns access + refresh token
- [ ] Protected route returns 401 without token, 200 with valid token
- [ ] `/login` and `/register` pages render and call API correctly
- [ ] Role-based redirect works after login

---

## Phase 3 — Volunteer Profile Module (Day 2–3, ~4 hours)

**Goal:** Volunteers can create/edit full profiles. Skills searchable. Availability set.

### 3.1 Backend — app/routers/volunteers.py
```
GET    /volunteers/me              → own profile
PUT    /volunteers/me              → update bio, location
POST   /volunteers/me/skills       → add skill with proficiency
DELETE /volunteers/me/skills/{id}  → remove skill
GET    /volunteers/me/availability → list slots
POST   /volunteers/me/availability → add availability window
DELETE /volunteers/me/availability/{id}
GET    /volunteers/                → search (coordinator only): ?skill=&lat=&lng=&radius=&available_on=
GET    /volunteers/{id}            → get volunteer profile (coordinator/admin only)
```

### 3.2 Embedding generation service — app/services/embedding.py
```python
# Called after profile update
# Uses Google Gemini embeddings API (text-embedding-004 model)
# Input: concatenate bio + skill names + languages
# Output: 768-dim float vector
# Store in volunteers.embedding
# Also embed task descriptions → tasks.embedding (same function)

async def generate_volunteer_embedding(volunteer_id: UUID, db: AsyncSession) -> None:
    # 1. Fetch volunteer with skills
    # 2. Build text: f"{bio}. Skills: {', '.join(skill_names)}"
    # 3. Call Gemini embeddings API
    # 4. UPDATE volunteers SET embedding = :vec WHERE user_id = :id
    # 5. Dispatch as Celery task so it's async
```

### 3.3 Frontend — Volunteer profile page
```
frontend/src/app/volunteer/
├── profile/
│   ├── page.tsx         # Profile view with completion %
│   └── edit/page.tsx    # Edit form: bio, skills multi-select, location picker
├── availability/page.tsx # Weekly availability grid (like Google Calendar lite)
└── layout.tsx
```

**Profile edit form components:**
- `SkillSelector` — searchable multi-select with proficiency slider (1-5) per skill
- `LocationPicker` — Mapbox geocoder input → sets lat/lng
- `AvailabilityGrid` — 7-day × time-slot grid, click to toggle available slots
- `ProfileCompletion` — progress bar showing % of fields filled

### 3.4 Acceptance criteria
- [ ] Volunteer can add/remove skills with proficiency levels
- [ ] Embedding is generated (async) after profile save
- [ ] Availability slots save and display correctly
- [ ] Coordinator can search volunteers by skill + location radius
- [ ] Profile completion % reflects actual filled fields

---

## Phase 4 — Task / Needs Management (Day 3, ~3 hours)

**Goal:** Coordinators can create, edit, prioritize tasks. System auto-scores urgency.

### 4.1 Backend — app/routers/tasks.py
```
POST   /tasks                    → create task (coordinator only)
GET    /tasks                    → list tasks: ?status=&priority=&lat=&lng=&radius=&org_id=
GET    /tasks/{id}               → get single task
PUT    /tasks/{id}               → update task
DELETE /tasks/{id}               → soft delete (set status=cancelled)
POST   /tasks/bulk-import        → accept CSV upload, parse, create tasks (runs as Celery job)
GET    /tasks/{id}/candidates    → ranked volunteer list for this task (coordinator)
POST   /tasks/{id}/match         → trigger matching engine for this task
```

### 4.2 Priority scoring service — app/services/priority.py
```python
# Called on task create/update
# Computes priority_score (0-100) using weighted formula:
#   urgency_weight = {"critical": 40, "high": 30, "medium": 20, "low": 10}
#   recency_score = max(0, 30 - days_until_deadline)   # 0-30
#   gap_score = volunteers_needed / max(1, assigned_count) * 20  # 0-20
#   vulnerability_score = from task metadata JSONB field  # 0-10
#   priority_score = urgency_weight + recency_score + gap_score + vulnerability_score
# Also generate embedding for task description (same Celery pattern)
```

### 4.3 Frontend — Task management
```
frontend/src/app/coordinator/
├── dashboard/page.tsx        # Main coordinator hub
├── tasks/
│   ├── page.tsx              # Priority queue table + map toggle
│   ├── new/page.tsx          # Create task form
│   └── [id]/
│       ├── page.tsx          # Task detail + candidate list
│       └── edit/page.tsx
└── layout.tsx
```

**Key UI components:**
- `TaskPriorityQueue` — sortable table with urgency badges, fill rate bar, quick-assign button
- `NeedsMap` — Mapbox map showing task pins colored by urgency (red=critical, amber=high, blue=medium)
- `TaskForm` — location picker + skill requirements + urgency + volunteer count
- `CSVImporter` — drag-drop upload with column mapping UI + import progress tracker

### 4.4 Acceptance criteria
- [ ] Task creation saves with auto-computed priority_score
- [ ] Task embedding is generated async via Celery
- [ ] CSV bulk import works for sample Tasks.csv format
- [ ] Priority queue shows tasks sorted by score descending
- [ ] Map shows task pins colored by urgency level

---

## Phase 5 — Matching Engine (Day 3–4, ~5 hours)

**Goal:** System suggests best-fit volunteers for any task. Three-layer pipeline working.

### 5.1 Create app/services/matching.py — implement full pipeline

```python
# STEP 1: Hard filter (SQL query)
# SELECT volunteers with:
#   - has ALL required skills at required proficiency level
#   - has availability overlapping task start/end time
#   - ST_DWithin(volunteer.location, task.location, radius_meters)
#   - not already assigned to a conflicting task at same time

# STEP 2: Vector similarity score (pgvector)
# SELECT 1 - (v.embedding <=> t.embedding) AS semantic_score
# FROM volunteers v, tasks t
# WHERE t.id = :task_id AND v.user_id IN (:filtered_ids)
# ORDER BY semantic_score DESC

# STEP 3: Composite scoring
# match_score = (
#   0.30 * skill_overlap_score +     # exact skills matched / required
#   0.25 * semantic_score +           # pgvector cosine similarity
#   0.20 * distance_score +           # 1 - (distance_km / max_radius)
#   0.15 * availability_score +       # slot fit quality
#   0.10 * reputation_score           # past performance
# )

# STEP 4: Fairness reranking
# If task already has >= 80% slots filled:
#   multiply score by 0.5 to surface other tasks
# If NGO has received 0 volunteers this week:
#   multiply score by 1.2 to boost underserved orgs

# STEP 5: Return top K candidates with scores
# Insert into assignments table with status='pending'
# Trigger notifications for top candidates
```

### 5.2 Create app/services/optimizer.py — ILP for batch mode
```python
# Uses PuLP for large-scale assignment optimization
# Variables: x[volunteer_id][task_id] ∈ {0, 1}
# Objective: maximize sum of match_score * x[v][t]
# Constraints:
#   - sum(x[v][t] for all t) <= max_tasks_per_volunteer (= 2 per day)
#   - sum(x[v][t] for all v) <= task.volunteers_needed
#   - x[v][t] = 0 if volunteer not in filtered candidates for task
# Solve with CBC solver (included in PuLP)
# Output: list of (volunteer_id, task_id) pairs to assign
```

### 5.3 Celery task — app/tasks/matching_tasks.py
```python
@celery.task
def run_batch_matching():
    # Called nightly or on-demand
    # Gets all OPEN tasks with unfilled slots
    # Runs optimizer.py across all tasks simultaneously
    # Creates assignment records
    # Queues notifications

@celery.task
def run_realtime_match(task_id: str):
    # Called when a new task is created
    # Runs matching.py for single task
    # Returns top 10 candidates to coordinator
```

### 5.4 Frontend — Matching UI
```
coordinator/tasks/[id]/page.tsx  # Add CandidateList component
```

**CandidateList component:**
- Shows ranked volunteers with match score bar
- Columns: Name, Skills match %, Distance, Availability fit, Reputation
- "Assign" button per row → POST /assignments
- "Run matching" button → POST /tasks/{id}/match
- Shows fairness indicator if task is underserved

### 5.5 Acceptance criteria
- [ ] POST /tasks/{id}/match returns ranked candidate list in < 3s
- [ ] Hard filter excludes unavailable and out-of-range volunteers
- [ ] Composite score reflects all 5 weighted components
- [ ] Fairness reranking demonstrably surfaces underserved NGOs
- [ ] ILP optimizer runs without error on 50 tasks × 200 volunteers
- [ ] Celery worker processes match job asynchronously

---

## Phase 6 — Scheduling & Assignments (Day 4, ~3 hours)

**Goal:** Coordinators assign volunteers to shifts. Calendar view works. Check-in/out tracked.

### 6.1 Backend — app/routers/assignments.py
```
POST   /assignments                     → create assignment (coordinator assigns volunteer)
GET    /assignments?task_id=&volunteer_id=&status=
PUT    /assignments/{id}/status         → confirm / cancel
POST   /assignments/{id}/shifts         → create shift (start/end time)
PUT    /assignments/{id}/shifts/{sid}/checkin   → record check_in timestamp
PUT    /assignments/{id}/shifts/{sid}/checkout  → record check_out + auto-log hours
POST   /assignments/{id}/feedback       → submit rating + comment
GET    /assignments/{id}/impact         → get impact_log entries
POST   /assignments/{id}/impact         → log impact metric (beneficiaries, meals, etc.)
```

### 6.2 Frontend — Scheduling calendar
```
frontend/src/app/coordinator/schedule/page.tsx
```

**Components:**
- `ScheduleCalendar` — week view grid. Each cell is a time slot. Drag volunteer chip onto task slot to assign
- `ShiftCard` — shows volunteer name, task, time, status badge
- `ConflictAlert` — red banner if volunteer double-booked
- `BulkAssignModal` — assign multiple volunteers to recurring event

**Volunteer side:**
```
frontend/src/app/volunteer/assignments/page.tsx
```
- List of upcoming assignments with countdown timer
- "Confirm" / "Cancel" buttons
- "Check in" button (geo-locked — only works within 500m of task location)

### 6.3 Acceptance criteria
- [ ] Coordinator can drag-assign volunteers on calendar
- [ ] Conflict detection fires when double-booking
- [ ] Volunteer can confirm / cancel their assignment
- [ ] Check-in records timestamp correctly
- [ ] Check-out auto-calculates hours and writes to impact_logs

---

## Phase 7 — Notifications System (Day 4–5, ~2 hours)

**Goal:** Email + SMS fire on assignment, reminder 24h before, cancellation.

### 7.1 Backend — app/services/notifications.py
```python
# Implement send functions:
async def send_email(to: str, subject: str, html: str) -> None:
    # Uses SendGrid API

async def send_sms(to: str, body: str) -> None:
    # Uses Twilio API

async def queue_notification(user_id, type, message, scheduled_for=None, db=...) -> None:
    # Creates notifications record with status='pending'
    # If scheduled_for is None → send immediately via Celery task
    # If scheduled_for is set → schedule Celery task with countdown
```

### 7.2 Celery tasks — app/tasks/notification_tasks.py
```python
@celery.task
def send_queued_notification(notification_id: str):
    # Fetch notification
    # Route to send_email or send_sms based on type
    # Update status to 'sent' or 'failed'

@celery.task
def send_shift_reminders():
    # Cron: runs every hour
    # Find shifts starting in 24h and 1h
    # Queue reminder notifications for assigned volunteers
```

### 7.3 Trigger points — add notification calls to:
- `POST /assignments` → "You've been matched to [task]" to volunteer
- `PUT /assignments/{id}/status` (confirmed) → "Volunteer confirmed" to coordinator
- `PUT /assignments/{id}/status` (cancelled) → "Slot opened" to waitlist
- Shift reminder → "Reminder: your shift starts in 24h at [location]"
- Task completed → "Please rate your experience" to volunteer

### 7.4 Frontend — Notification bell
- In-app notification dropdown in header (polls `/notifications?unread=true`)
- Mark all read button
- Click notification → navigate to relevant task/assignment

### 7.5 Acceptance criteria
- [ ] Email sends on assignment creation (verify in SendGrid logs)
- [ ] SMS sends for high-urgency tasks (verify in Twilio logs)
- [ ] 24-hour reminder fires via Celery beat scheduler
- [ ] In-app notification badge shows unread count
- [ ] All notifications logged in DB with sent_at timestamp

---

## Phase 8 — Analytics Dashboards (Day 5, ~4 hours)

**Goal:** Three role-specific dashboards with live KPIs. Funder report exportable.

### 8.1 Backend — app/routers/analytics.py
```
GET /analytics/dashboard         → returns all KPIs for current user's role
GET /analytics/volunteer-hours   → total + trend (by week/month) ?org_id=&date_from=&date_to=
GET /analytics/task-fill-rate    → % tasks with ≥1 volunteer, by org/region
GET /analytics/response-time     → avg hours from task creation to first assignment
GET /analytics/coverage-map      → GeoJSON of fulfilled vs unfulfilled tasks by district
GET /analytics/volunteer-retention → % volunteers with 2+ assignments
GET /analytics/ngos-served       → count + % of NGOs receiving ≥1 volunteer (fairness KPI)
GET /analytics/impact-summary    → total beneficiaries, hours, meals etc. from impact_logs
GET /analytics/export/pdf        → generate funder report PDF (uses ReportLab or WeasyPrint)
```

### 8.2 Frontend — Coordinator dashboard
```
frontend/src/app/coordinator/dashboard/page.tsx
```
**Widgets (use Recharts for charts):**
- `SupplyDemandBar` — stacked bar: open tasks vs assigned volunteers per day
- `UrgentTasksList` — top 5 tasks by priority_score with quick-assign CTA
- `VolunteerMapView` — Mapbox showing volunteer locations + task pins
- `FillRateGauge` — donut chart: % tasks filled this week
- `RecentActivity` — live feed of assignments/completions

### 8.3 Frontend — Volunteer dashboard
```
frontend/src/app/volunteer/dashboard/page.tsx
```
- Hours logged this month (stat card)
- Upcoming assignments (next 3)
- Recommended tasks (top 3 from matching engine)
- Badge collection (earned from reputation system)
- Impact statement: "You've helped X people this month"

### 8.4 Frontend — Funder dashboard
```
frontend/src/app/funder/dashboard/page.tsx
```
- KPI cards: volunteer-hours, tasks completed, beneficiaries reached, NGOs served
- `ImpactTrendChart` — line chart over 12 months
- `GeoCoverageMap` — choropleth: districts colored by fulfillment %
- `FairnessMetric` — % NGOs receiving ≥1 volunteer (vs baseline)
- "Export Report" button → download PDF

### 8.5 Acceptance criteria
- [ ] Coordinator dashboard loads in < 2s
- [ ] All 6 KPI cards show correct aggregated numbers
- [ ] Map loads with correct task/volunteer pins
- [ ] Funder PDF export generates cleanly
- [ ] Fairness KPI visible on funder dashboard

---

## Phase 9 — AI Data Ingestion Pipeline (Day 5–6, ~3 hours)

**Goal:** Unstructured NGO data (CSV, PDF, text) → clean structured tasks in DB.

### 9.1 Backend — app/routers/import.py
```
POST /import/csv            → upload CSV file → parse → create tasks/volunteers
POST /import/text           → raw text description → Gemini extracts structured data
POST /import/batch-url      → URL to Google Sheet or public CSV
GET  /import/jobs           → list import_jobs with status
GET  /import/jobs/{id}      → get single job + error_report JSONB
```

### 9.2 AI parsing service — app/services/ai_parser.py
```python
# Uses LangChain + Gemini to parse unstructured input

EXTRACTION_PROMPT = """
Extract volunteer task information from the following text.
Return ONLY valid JSON with these fields:
{
  "title": string,
  "description": string,
  "location_address": string,
  "required_skills": [string],
  "urgency": "critical|high|medium|low",
  "volunteers_needed": integer,
  "start_time": "ISO8601 or null",
  "end_time": "ISO8601 or null"
}
Text: {input_text}
"""

async def parse_unstructured_task(text: str) -> dict:
    # Call Gemini via LangChain
    # Parse JSON response
    # Validate with Pydantic
    # Return structured dict

async def process_csv_import(file_bytes: bytes, job_id: UUID, db: AsyncSession):
    # Run as Celery task
    # Parse CSV rows
    # For each row: validate → geocode address → create task record
    # Update import_job with progress
    # Write errors to error_report JSONB
```

### 9.3 Frontend — Import UI
```
frontend/src/app/coordinator/import/page.tsx
```
- Tab 1: CSV Upload — drag-drop + column mapping table + import button
- Tab 2: Paste Text — textarea → "Parse with AI" → preview extracted fields → confirm import
- Tab 3: Import History — table of import_jobs with status chips + error download

### 9.4 Acceptance criteria
- [ ] CSV import creates tasks correctly for sample Tasks.csv
- [ ] AI text parser extracts ≥ 4 correct fields from an unstructured paragraph
- [ ] Import job status updates in real-time (poll every 2s)
- [ ] Error report shows failed rows with reasons
- [ ] Geocoding converts address string to lat/lng correctly

---

## Phase 10 — GDPR & Security (Day 6, ~2 hours)

**Goal:** Consent logged, data deletion works, audit trail complete, security hardened.

### 10.1 Backend — app/routers/privacy.py
```
GET    /privacy/consent                → get my consent log
POST   /privacy/consent                → log new consent (called on register)
GET    /privacy/my-data                → export all my personal data as JSON
DELETE /privacy/my-account            → anonymize + soft-delete account
POST   /privacy/data-correction        → submit data correction request
GET    /admin/audit-logs               → paginated audit log (admin only)
GET    /admin/gdpr-requests            → pending deletion/correction requests (admin)
```

### 10.2 Audit logging middleware — app/middleware/audit.py
```python
# FastAPI middleware that:
# - Intercepts all mutating requests (POST, PUT, DELETE)
# - Captures before/after state for sensitive entities
# - Writes to audit_logs table
# Sensitive entities: users, volunteers, assignments, consent_logs
```

### 10.3 Data anonymization — app/services/privacy.py
```python
async def anonymize_user(user_id: UUID, db: AsyncSession):
    # Set email = f"deleted_{uuid4()}@deleted.invalid"
    # Set full_name = "Deleted User"
    # Set password_hash = ""
    # Set is_active = False
    # Revoke all auth_sessions
    # Keep assignment/impact records (anonymized) for reporting
    # Log in audit_logs
```

### 10.4 Security hardening checklist
- [ ] Rate limiting on auth endpoints (slowapi: 5 req/min on /auth/login)
- [ ] Input validation on all request bodies (Pydantic strict mode)
- [ ] SQL injection impossible (SQLAlchemy ORM only, no raw f-strings)
- [ ] CORS restricted to known origins in production
- [ ] JWT secret is 32+ random chars, loaded from env only
- [ ] Passwords hashed with bcrypt (cost factor ≥ 12)
- [ ] All API endpoints return 401/403 correctly for wrong roles
- [ ] File upload limited to 10MB, CSV/PDF only
- [ ] HTTPS enforced in production (Vercel/Railway handle this)

### 10.5 Acceptance criteria
- [ ] POST /auth/login rate-limited after 5 failed attempts
- [ ] DELETE /privacy/my-account anonymizes all PII fields
- [ ] Audit log records before/after on volunteer profile edit
- [ ] GDPR export returns all user data as downloadable JSON
- [ ] No raw SQL strings anywhere in codebase

---

## Phase 11 — Testing (Day 6–7, ~3 hours)

**Goal:** Core flows covered by automated tests. No critical bugs at demo.

### 11.1 Backend tests — backend/tests/
```
tests/
├── conftest.py            # async test DB setup, fixture users by role
├── test_auth.py           # register, login, refresh, logout, reset password
├── test_volunteers.py     # profile CRUD, skill add/remove, availability
├── test_tasks.py          # create, priority scoring, CSV import
├── test_matching.py       # hard filter, composite score, fairness reranking
├── test_assignments.py    # create, confirm, cancel, check-in/out
└── test_analytics.py      # KPI endpoint correctness
```

**Key test cases to implement:**
```python
# test_matching.py
async def test_hard_filter_excludes_unavailable():
    # Create volunteer with no overlap with task time → assert not in candidates

async def test_fairness_boosts_underserved_ngo():
    # NGO with 0 volunteers this week → assert match_score multiplied by 1.2

async def test_composite_score_range():
    # All returned match_scores are between 0.0 and 1.0

async def test_matching_returns_ranked_results():
    # First result has higher match_score than last result
```

### 11.2 Frontend tests
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom jest jest-environment-jsdom
```

Test files:
- `__tests__/auth/login.test.tsx` — form validation, API call, redirect
- `__tests__/volunteer/profile.test.tsx` — skill add/remove UI
- `__tests__/coordinator/matching.test.tsx` — candidate list renders correctly

### 11.3 Run all tests
```bash
# Backend
cd backend && pytest tests/ -v --asyncio-mode=auto

# Frontend
cd frontend && npm run test
```

### 11.4 Acceptance criteria
- [ ] pytest passes with ≥ 80% of tests green
- [ ] Auth flow tests all pass
- [ ] Matching engine tests all pass
- [ ] No TypeScript errors (`npm run build` succeeds)

---

## Phase 12 — Deployment (Day 7, ~2 hours)

**Goal:** Live URLs for both frontend and backend. Demo-ready.

### 12.1 Supabase setup (production DB)
```
1. Create Supabase project at supabase.com
2. Enable PostGIS: SQL editor → CREATE EXTENSION postgis;
3. Enable pgvector: SQL editor → CREATE EXTENSION vector;
4. Get connection string → update DATABASE_URL env var
5. Run: alembic upgrade head (against Supabase)
6. Seed minimal data: 2 NGOs, 10 volunteers, 20 tasks
```

### 12.2 Deploy backend to Railway
```bash
# Create railway.json in backend/
{
  "build": { "builder": "nixpacks" },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}

# Add /health endpoint to main.py
@app.get("/health")
async def health(): return {"status": "ok"}

# Set env vars in Railway dashboard (copy from .env.example)
# Add Redis plugin in Railway
# Add Celery worker as second Railway service:
#   startCommand: celery -A app.celery_app worker --loglevel=info
```

### 12.3 Deploy frontend to Vercel
```bash
cd frontend
vercel deploy --prod
# Set env vars in Vercel dashboard:
#   NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app
#   NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
```

### 12.4 CORS update
In backend/app/main.py update CORS origins to include Vercel URL:
```python
allow_origins=[
    "http://localhost:3000",
    "https://your-app.vercel.app"
]
```

### 12.5 Seed demo data script — backend/scripts/seed_demo.py
```python
# Create:
# - 1 admin user (admin@demo.com / demo1234)
# - 2 coordinator users with organizations (ReliefOrg XYZ, HealthNGO)
# - 1 funder user
# - 10 volunteers with varied skills/locations
# - 20 tasks across urgency levels and locations
# - 5 existing assignments with feedback
# - Impact logs showing 150 volunteer-hours, 500 beneficiaries
```

Run: `python scripts/seed_demo.py`

### 12.6 Acceptance criteria
- [ ] Frontend live at https://[project].vercel.app
- [ ] Backend API live at https://[project].railway.app/docs
- [ ] Login works with seeded demo accounts
- [ ] Matching engine runs against live DB
- [ ] All map features work with live Mapbox token

---

## Phase 13 — Demo Polish (Day 7–8, ~3 hours)

**Goal:** Hackathon judges can experience the full flow in 5 minutes.

### 13.1 Landing page
```
frontend/src/app/page.tsx  → public landing page
```
Content:
- Hero: "AI-Powered Volunteer Coordination for Social Impact"
- 3 role cards: NGO Coordinator / Volunteer / Funder — each with "Try Demo" button
- Feature highlights: AI matching, real-time map, GDPR-compliant
- Quick stats from seed data: "150 volunteer-hours, 500 beneficiaries, 20 tasks filled"
- "Demo Login" buttons pre-filled with demo credentials per role

### 13.2 Demo flow to make work flawlessly (prioritize these)
```
1. Coordinator logs in → sees dashboard with map + urgent tasks
2. Coordinator clicks "Run AI Matching" on a task → sees ranked candidates in 3s
3. Coordinator assigns volunteer → volunteer gets in-app notification
4. Volunteer logs in → sees assignment + can confirm
5. Funder logs in → sees impact KPIs + exports PDF report
```

### 13.3 Loading states & error handling
- Add skeleton loaders to all data-fetching components
- Add toast notifications for all API success/error states
- Add empty states with helpful CTAs when lists are empty
- Handle network errors gracefully with retry buttons

### 13.4 Mobile responsiveness
- Test all pages at 375px (iPhone SE) and 768px (iPad)
- Coordinator map should work on mobile (pinch zoom)
- Bottom navigation bar for volunteer mobile experience

### 13.5 Final checklist before demo
- [ ] All 5 demo flow steps work end-to-end without errors
- [ ] Pages load in < 2s on production URLs
- [ ] No console errors in browser devtools
- [ ] Demo data is reset and looks realistic
- [ ] README.md has clear setup instructions + demo video link
- [ ] API docs at /docs are clean and annotated
- [ ] Environment variables are NOT in git (check .gitignore)

---

## Quick Reference: Build Order Summary

```
Day 1:  Phase 0 (scaffold) → Phase 1 (schema)
Day 2:  Phase 2 (auth) → Phase 3 (volunteer profiles)
Day 3:  Phase 4 (tasks) → Phase 5 start (matching engine)
Day 4:  Phase 5 finish → Phase 6 (scheduling) → Phase 7 (notifications)
Day 5:  Phase 8 (dashboards) → Phase 9 (AI ingestion)
Day 6:  Phase 10 (GDPR/security) → Phase 11 (testing)
Day 7:  Phase 12 (deployment) → Phase 13 start (demo polish)
Day 8:  Phase 13 finish → submit
```

## If time runs short — MVP cut list (keep these, drop the rest)

| Must keep | Can cut |
|---|---|
| Auth + roles | Password reset flow |
| Volunteer profiles + skills | Recurring availability patterns |
| Task creation + priority scoring | CSV bulk import |
| Matching engine (rule-based at minimum) | ILP optimizer (keep greedy) |
| Assignment creation | Check-in GPS verification |
| Email notifications | SMS (keep email only) |
| Coordinator dashboard | Funder PDF export |
| Deployment + seed data | Mobile app (responsive web is fine) |

---

## Key File to Create First in Each Phase

| Phase | First file to create |
|---|---|
| 0 | `docker-compose.yml` |
| 1 | `backend/app/database.py` |
| 2 | `backend/app/utils/auth.py` |
| 3 | `backend/app/routers/volunteers.py` |
| 4 | `backend/app/services/priority.py` |
| 5 | `backend/app/services/matching.py` |
| 6 | `backend/app/routers/assignments.py` |
| 7 | `backend/app/services/notifications.py` |
| 8 | `backend/app/routers/analytics.py` |
| 9 | `backend/app/services/ai_parser.py` |
| 10 | `backend/app/middleware/audit.py` |
| 11 | `backend/tests/conftest.py` |
| 12 | `backend/railway.json` |
| 13 | `frontend/src/app/page.tsx` |
