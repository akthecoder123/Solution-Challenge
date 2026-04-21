# 🚀 Tech Stack Overview

This project is built using a modern, scalable, and AI-driven architecture designed for high performance, geospatial intelligence, and intelligent task matching.

---

## 🧠 1. Backend (API & Core Logic)

### 🔹 Framework
- **FastAPI (Python)**
  - High-performance async framework
  - Automatic API documentation (Swagger)
  - Ideal for AI/ML integration

### 🔹 Background Processing
- **Celery**
  - Handles heavy computations asynchronously
- **Redis**
  - Message broker + caching layer

---

## 🗄️ 2. Database (Geospatial + AI Support)

### 🔹 Core Database
- **PostgreSQL**
  - Reliable relational database

### 🔹 Extensions
- **PostGIS**
  - Enables geospatial queries
  - Example:
    ```sql
    SELECT * FROM volunteers
    WHERE ST_DWithin(location, disaster_zone, radius);
    ```

- **pgvector**
  - Supports vector embeddings for AI similarity search

### 🔹 Hosting Options
- **Supabase (Recommended)**
  - Easy setup
  - Built-in PostGIS + pgvector support

- **Alternative**
  - Docker + AWS RDS (for advanced deployment)

---

## 🤖 3. AI & Matching Engine

### 🔹 Data Parsing
- **LangChain**
- **Google Gemini API / OpenAI API**
  - Converts unstructured input → structured data

### 🔹 Skill Matching (Vector Search)
- **pgvector**
  - Embedding-based similarity matching

### 🔹 Optimization Engine
- **SciPy / PuLP**
  - Solves assignment problems:
    - Optimal volunteer-task matching
    - Avoids double-booking
    - Maximizes priority coverage

---

## 💻 4. Frontend (User Interface)

### 🔹 Framework
- **Next.js (React) + TypeScript**
  - SSR + performance optimized UI

### 🔹 Styling
- **Tailwind CSS**
- **Shadcn UI**
  - Clean, modern UI components

### 🔹 Mapping
- **Mapbox GL JS / Leaflet**
  - Real-time geospatial visualization
  - Displays:
    - Volunteer locations
    - Task zones
    - Deployment tracking

---

## 🧩 5. System Architecture

```text
Frontend (Next.js)
        ↓
FastAPI Backend (REST APIs)
        ↓
--------------------------------
| PostgreSQL + PostGIS + pgvector |
--------------------------------
        ↓
Celery Workers (Async Tasks)
        ↓
AI Engine (LangChain + Embeddings + Optimization)
