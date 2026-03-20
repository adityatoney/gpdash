# Product Requirements Document — gpdash

**Guru Purnima Event Analytics Dashboard**

| Field | Value |
|---|---|
| Version | 2.0 |
| Date | 2026-03-19 |
| Status | Draft |
| Source | `docs/prompt.md` |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Goals](#2-problem-statement--goals)
3. [Target Users / Personas](#3-target-users--personas)
4. [Data Sources & Inventory](#4-data-sources--inventory)
5. [System Architecture](#5-system-architecture)
6. [Tech Stack & Justification](#6-tech-stack--justification)
7. [Database Design](#7-database-design)
8. [Proposed Project Folder Structure](#8-proposed-project-folder-structure)
9. [Phase-by-Phase Requirements](#9-phase-by-phase-requirements)
10. [API Specification](#10-api-specification)
11. [Dashboard UI Requirements](#11-dashboard-ui-requirements)
12. [AI Integration Strategy](#12-ai-integration-strategy)
13. [Non-Functional Requirements](#13-non-functional-requirements)
14. [Risks & Mitigations](#14-risks--mitigations)
15. [Success Metrics](#15-success-metrics)
16. [Future Considerations](#16-future-considerations)
17. [Appendix A: `.env.example` Template](#appendix-a-envexample-template)
18. [Appendix B: File-to-Table Mapping](#appendix-b-file-to-table-mapping)
19. [Appendix C: Glossary](#appendix-c-glossary)

---

## 1. Executive Summary

gpdash is a local-first analytics dashboard for multi-year Guru Purnima (GP) event data spanning 2022–2025. The project ingests 9 Excel files covering attendee registrations, room allocations, food/dining scans, and event dashboards, normalizes them through a Python ETL pipeline, stores the cleaned data in a local PostgreSQL database (26 normalized tables), and surfaces interactive visualizations and AI-powered insights through a React + Vite frontend backed by a Node.js/Express API.

### Key Deliverables

- **PostgreSQL Database** — normalized relational schema with 26 tables (6 reference, 7 core, 8 auxiliary, 5 system) storing ~170K rows across 4 event years. Runs locally via Docker.
- **Python ETL Pipeline** — re-runnable pipeline (`etl/`) that reads xlsx files, normalizes columns across years, resolves person identity, and loads into PostgreSQL. CLI-driven with per-year and full-load modes.
- **Node.js API** — Express server exposing REST endpoints for dashboard queries, agent orchestration, and AI-powered Q&A.
- **React Dashboard** — 6-tab interactive UI with filters, charts, exportable tables, and a natural-language AI Insights panel.
- **Markdown Analysis Report** — Claude-generated narrative report with key statistics, trend highlights, and data quality notes, written to local disk.

The system is designed to be updated each year with minimal effort when new GP data arrives.

---

## 2. Problem Statement & Goals

### Problem Statement

GP event data is scattered across multiple Excel files with inconsistent column names, formats, and coverage gaps between years. There is no unified view of attendance trends, room utilization, or dining demand over time, making year-over-year planning difficult and reactive rather than data-driven.

### Goals

| # | Goal | Success Indicator |
|---|------|-------------------|
| G1 | Unify 4 years of GP data into a single, clean, queryable dataset | All 9 source files ingested into 26 PostgreSQL tables; unified schema covers registrations, rooms, meals, and auxiliary data with `event_year` column |
| G2 | Surface year-over-year trends in registration, rooms, and dining | Dashboard shows line/bar charts for all three data types across 2022–2025; YoY growth rates calculated |
| G3 | Provide AI-powered natural-language Q&A over the data | User can type a plain-English question and receive a contextual answer from Claude within the dashboard |
| G4 | Enable data export for offline planning | Every data table and chart is exportable to CSV; markdown analysis report written to local disk |
| G5 | Make the pipeline re-runnable for future years | Agent can be re-triggered from the UI; adding a 2026 file requires no code changes, only data |

### Non-Goals

- **Multi-user authentication / authorization** — the dashboard runs locally; there is no login system.
- **Cloud deployment** — the system runs on localhost only. No hosting, CI/CD, or infrastructure provisioning.
- **Real-time event streaming** — data is batch-loaded from static Excel files, not streamed from a live event system.
- **Mobile-responsive design** — optimized for desktop/laptop screens used during planning sessions.
- **Automated data collection** — files are manually placed in the `docs/event_docs/` directory.

---

## 3. Target Users / Personas

### Persona 1: Event Coordinator (Primary)

| Attribute | Detail |
|---|---|
| Role | Plans logistics for the annual GP event |
| Technical skill | Low — comfortable with Excel, not with code or databases |
| Key tasks | Compare attendance across years, estimate room and meal demand for next year, export headcount data for vendors |
| Pain points | Data is in separate files with different formats; manual comparison is tedious and error-prone |
| Needs from gpdash | Clean dashboard with clear charts, hover tooltips, CSV export, plain-English AI Q&A |

### Persona 2: Technical Operator

| Attribute | Detail |
|---|---|
| Role | Sets up and maintains the local gpdash instance |
| Technical skill | Moderate — can run `npm` / `python` commands, edit `.env` files |
| Key tasks | Start the system, trigger the agent, monitor processing progress, troubleshoot errors |
| Pain points | Needs clear status feedback; agent failures should be visible, not silent |
| Needs from gpdash | Agent status panel, clear error messages, simple startup instructions |

### Persona 3: Decision Maker

| Attribute | Detail |
|---|---|
| Role | Senior organizer making budget and capacity decisions |
| Technical skill | Low |
| Key tasks | Review high-level KPIs, read AI-generated summaries, compare growth trends |
| Pain points | Needs concise insights, not raw data |
| Needs from gpdash | KPI cards, executive summary in markdown report, AI Insights panel |

---

## 4. Data Sources & Inventory

### File Inventory

| # | File Name | Year | Data Type(s) | Size | Sheets | Notes |
|---|-----------|------|-------------|------|--------|-------|
| 1 | `gp2022_registrations_and_room_pickups.xlsx` | 2022 | Registrations + Rooms | 835 KB | 2 | `Registration-CheckIn-RoomAcc by` (2,657 rows, 54 cols) + `Room Stats - Booked vs Pickedup` |
| 2 | `gp2022_food_preferences.xlsx` | 2022 | Food/Dining | 912 KB | 10 | `Pivot Data - ALL` (6,015 rows), `Pivot Data - Gurupujan` (404 rows), + trend/chart sheets |
| 3 | `gp2023_event_registrations_and_room_pickups.xlsx` | 2023 | Registrations + Rooms | 1.3 MB | 3 | Identical structure to 2022; 3,574 rows |
| 4 | `gp2024_event_dashboard.xlsx` | 2024 | Dashboard (aggregated) | 301 KB | 6 | **No raw data** — contains pre-aggregated dashboard summaries, hotel pickup stats, food pref charts |
| 5 | `gp2024_scanning_analysis.xlsx` | 2024 | Food scanning (aggregated) | 16 KB | 2 | Daily meal counts + meal conflict matrices |
| 6 | `gp2025_registrations.xlsx` | 2025 | Registrations + Youth + Bhakti + Rooms + Exceptions | 8.5 MB | 15 | `Data` (7,229 rows, 70 cols), `Rooms` (1,742), `BMHT+LMHT` (172), `YMHT` (155), `Bhakti` (170), `Special Needs` (133), `Translation` (535), `Exceptions` (1,419), + more |
| 7 | `gp2025_food_preferences.xlsx` | 2025 | Food/Dining (individual scans) | 5.1 MB | 5 | `All Data` (46,755 individual scans with person link), + summarized sheets |
| 8 | `gp2025_room_analysis.xlsx` | 2025 | Rooms (detailed) | 511 KB | 3 | `Data` (1,344 rows, 40 cols) — room details with financial data, accessibility flags |
| 9 | `gp2025_event_dashboard.xlsx` | 2025 | Dashboard | 657 KB | 2 | `Report` + `Date wise Attendees` |

### Year × Data-Type Coverage Matrix

| Year | Registrations | Rooms | Food/Dining | Dashboard |
|------|:------------:|:-----:|:-----------:|:---------:|
| 2022 | ✅ Individual (2,657) | ✅ Individual (2,187) | ✅ Aggregated (6,015 pivot) | — |
| 2023 | ✅ Individual (3,574) | ✅ Individual (2,442) | ❌ **NONE** | — |
| 2024 | ❌ Summary only | ❌ Summary only | ✅ Aggregated (216 daily) | ✅ (6 sheets) |
| 2025 | ✅ Individual (4,396 + 327 youth) | ✅ Individual (1,558) | ✅ Individual (46,755 scans) | ✅ (2 sheets) |

### Known Data Gaps & Imputation Strategy

| Gap | Impact | Strategy |
|-----|--------|----------|
| 2023 food data | No meal analysis for 2023 | `data_availability` marks as `data_level = 'none'`. Dashboard shows "Not Available" banner. Cannot impute. |
| 2024 registration/room raw data | No individual records for 2024 | Use `dashboard_snapshots` for aggregate totals. Individual queries return empty with explanation. |
| 2022/2023 missing MahatmaID | Cannot link to 2025 person records by MahatmaID | Cross-reference by `FamilyID + LOWER(first_name) + LOWER(last_name)` to backfill where possible |
| 2025 missing BirthMonth/BirthYear | Cannot compute exact age for 2025 attendees | Only `AgeAtEvent` available. Store age, leave birth fields NULL |
| 2025 missing FamilyEmailAddress | Cannot use email for dedup in 2025 | Not collected in 2025 registration system. Leave NULL |
| 2022/2023 missing Address fields | No street-level address for early years | Not collected. Leave NULL |
| 2025 arrival/departure dates | Stored as one-hot boolean columns, not date fields | Parse one-hot columns (e.g., "First Day at GP - 2025-07-05") to derive dates |

### Data Quality Risks

- **Inconsistent column naming** — Column names vary across years (e.g., `Gender` vs `GenderMF`, `Zipcode` vs `PostalCode`, `regionID` (numeric) vs `Region` (string)). All mappings are encoded in `etl/load_*.py` loaders.
- **Date format variance** — Dates appear as Excel datetime objects, `MM/DD/YYYY` strings, and `YYYY-MM-DD` strings. The ETL `safe_date()` handles all formats.
- **Duplicate records** — Attendees may appear across years; deduplication uses `MahatmaID` (2025) or `FamilyID + name` (2022/2023). 1,766 returning attendees detected across years.
- **Combined files** — 2022 and 2023 files combine registrations + rooms in 54-column rows; ETL splits cols 1–44 → person+registration, cols 45–54 → rooms.
- **Room data overlap** — 2025 has room data in both `gp2025_registrations.xlsx` Rooms sheet and `gp2025_room_analysis.xlsx`. ETL uses room_analysis as primary, supplements with registration Rooms sheet.

---

## 5. System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          LOCAL MACHINE                              │
│                                                                     │
│  ┌──────────────┐     HTTP      ┌──────────────┐    SQL (pg)      │
│  │              │  ──────────▶  │              │  ──────────────▶  │
│  │   React +    │               │  Express.js  │               ┌───┴────┐
│  │   Vite       │  ◀──────────  │  API Server  │  ◀────────────│Postgres│
│  │   Frontend   │     JSON      │              │    Queries     │(Docker)│
│  │              │               │              │                │:5433   │
│  └──────────────┘               └──────┬───────┘               └───┬────┘
│                                        │                           │
│                                        │  POST /api/agent/run      │
│                                        │  (spawn subprocess)       │
│                          ┌─────────────┘                           │
│                          ▼                                         │
│                    ┌──────────────┐    SQL (psycopg2)             │
│                    │   Python     │  ─────────────────────────▶   │
│                    │   ETL Agent  │                                │
│                    │              │  ──▶  Anthropic API (Claude)   │
│                    │              │  ──▶  Open Model (Ollama)      │
│                    └──────┬───────┘                                │
│                           │                                        │
│                           ▼                                        │
│                    ┌──────────────┐                                │
│                    │  Local Files │                                │
│                    │  - raw xlsx  │                                │
│                    │  - tmp/      │                                │
│                    │  - reports/  │                                │
│                    │  - exports/  │                                │
│                    └──────────────┘                                │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Data Flow (6 Steps)

| Step | From | To | Action |
|------|------|----|--------|
| 1 | User | Local filesystem | Places `.xlsx` files in `docs/event_docs/` |
| 2 | User | CLI | Runs `python -m etl.run` to execute ETL pipeline (or triggers via Express API) |
| 3 | Python ETL | PostgreSQL | ETL reads xlsx files, normalizes data, writes to 26 tables; seeds reference data, loads per-year records, tracks progress in `agent_jobs` |
| 4 | React UI | Express API | Dashboard queries data via REST endpoints |
| 5 | Express API | PostgreSQL | Express queries PostgreSQL with SQL, returns JSON to frontend |
| 6 | Python ETL | Local disk | ETL can write `.md` reports to `reports/` and CSV exports to `exports/` |

### Communication Protocol Table

| Connection | Protocol | Library / Method |
|------------|----------|-----------------|
| React → Express | HTTP REST | `fetch` / Axios |
| Express → PostgreSQL | TCP (SQL) | `pg` / `node-postgres` |
| Express → Python ETL | Child process (`spawn`) | Node `child_process` |
| Python ETL → PostgreSQL | TCP (SQL) | `psycopg2` |
| Python ETL → xlsx files | File I/O | `openpyxl` |
| Python ETL → Claude | HTTPS | `anthropic` Python SDK |
| Python ETL → Open Model | HTTP | Ollama REST API or compatible |
| Express → Claude (Q&A) | HTTPS | `@anthropic-ai/sdk` Node SDK |

---

## 6. Tech Stack & Justification

| Layer | Technology | Version | Justification | Risk Notes |
|-------|-----------|---------|---------------|------------|
| Frontend | React | 18.x or 19.x | Component model fits dashboard tabs; large ecosystem for charting | None |
| Build tool | Vite | 5.x+ | Fast HMR for development; simple config | None |
| Charting | Recharts (primary) or Chart.js | Recharts 2.x / Chart.js 4.x | Prompt specifies Recharts or Chart.js — not D3 directly. Recharts is React-native and simpler for declarative charts. | Chart.js requires a React wrapper (`react-chartjs-2`) |
| UI Components | Tailwind CSS + shadcn/ui | Tailwind 3.x+ | Utility-first CSS for clean, non-technical look; shadcn provides accessible components | None |
| Backend API | Express.js | 4.x | Lightweight, well-known; sufficient for local REST API | None |
| Runtime | Node.js | 20.x LTS | Required for Express | Use LTS for stability |
| Database | PostgreSQL | 16.x (Docker) | Normalized relational schema; powerful SQL for analytics; runs locally via Docker Compose on port 5433; no cloud dependency | Requires Docker Desktop |
| DB Client (Python) | psycopg2-binary | 2.9+ | PostgreSQL adapter for Python ETL pipeline | None |
| DB Client (Node) | pg (node-postgres) | 8.x | PostgreSQL client for Express API | None |
| ETL Pipeline | Python | 3.9+ | Data wrangling with openpyxl; CLI-driven with per-year and full-load modes | Must be installed separately from Node |
| Excel parsing | openpyxl | 3.1+ | Handles `.xlsx` reading, multi-sheet support, read-only mode for performance | Large files (8.5 MB) take ~10s to parse |
| Config | python-dotenv | 1.0+ | Environment variable management for database URL | None |
| AI (primary) | Anthropic Claude | claude-sonnet-4-6 / claude-haiku-4-5 | Natural language summaries, Q&A, report generation | Requires API key; cost per token |
| AI (fallback) | Ollama (local) or open API | Latest | Batch classification, data labeling — cost-efficient | Requires local GPU or external endpoint |
| Reports | Markdown | N/A | Human-readable, version-controllable output format | None |

---

## 7. Database Design

### Storage Decision Matrix

| Data Category | Storage | Rationale |
|---------------|---------|-----------|
| Cleaned, normalized attendee/room/meal records | **PostgreSQL** (7 core tables) | Fully normalized relational schema; powerful SQL for analytics; local-only, no cloud dependency |
| Reference data (regions, centers, hotels, etc.) | **PostgreSQL** (6 `ref_*` tables) | Normalized lookup tables populated from xlsx data during ETL seeding |
| Auxiliary data (youth, bhakti, special needs, etc.) | **PostgreSQL** (8 aux tables) | Year-specific or entity-specific extensions linked to core tables |
| Agent job status and task logs | **PostgreSQL** (`agent_jobs`, `agent_job_steps`) | Queryable from both Python ETL and Express API |
| Filter/view preferences per user session | **PostgreSQL** (`user_preferences`) | Persists across page refreshes |
| Cached aggregations and trend summaries | **PostgreSQL** (`aggregation_cache`, `dashboard_snapshots`, `meal_aggregates`) | Fast dashboard rendering; pre-computed summaries |
| Data gap tracking | **PostgreSQL** (`data_availability`) | Documents what data exists per year per entity type |
| Raw uploaded `.xlsx` files | **Local filesystem** (`docs/event_docs/`) | No need to store binary blobs in DB |
| Final markdown reports | **Local filesystem** (`reports/`) | Written by agent; user reads/shares directly |
| CSV/Excel backups | **Local filesystem** (`exports/`) | Offline backup of cleaned data |

### PostgreSQL Schema — 26 Tables

The full DDL is in `db/schema.sql`. The detailed design document with entity mapping, discrepancy matrix, and ER diagram is in `docs/db_design.md`.

#### Table Classification

| Category | Count | Tables |
|----------|-------|--------|
| **Reference** | 6 | `ref_regions`, `ref_centers`, `ref_food_preferences`, `ref_room_types`, `ref_age_groups`, `ref_hotels` |
| **Core** | 7 | `events`, `persons`, `person_contacts`, `registrations`, `rooms`, `room_occupants`, `meal_scans` |
| **Auxiliary** | 8 | `registration_youth`, `registration_lmht`, `registration_bhakti`, `special_needs_requests`, `translation_requests`, `registration_exceptions`, `dashboard_snapshots`, `meal_aggregates` |
| **System** | 5 | `data_availability`, `agent_jobs`, `agent_job_steps`, `aggregation_cache`, `user_preferences` |

#### Core Tables (Summary)

##### `events`

Stores metadata for each GP event year. Auto-populated with totals after ETL run.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | `SERIAL` | PK | Auto-incrementing primary key |
| `event_year` | `SMALLINT` | UK, yes | Event year (2022, 2023, 2024, 2025) |
| `event_name` | `VARCHAR(100)` | yes | Event display name, e.g., "Guru Purnima 2023" |
| `start_date` | `DATE` | no | Event start date |
| `end_date` | `DATE` | no | Event end date |
| `total_registrations` | `INTEGER` | no | Cached count of registrations (auto-updated after ETL) |
| `total_room_bookings` | `INTEGER` | no | Cached count of room records |
| `total_meal_scans` | `INTEGER` | no | Cached count of meal scan records |
| `has_registration_data` | `BOOLEAN` | no | Whether individual registration data exists |
| `has_room_data` | `BOOLEAN` | no | Whether individual room data exists |
| `has_food_data` | `BOOLEAN` | no | Whether food/meal data exists |
| `has_dashboard_data` | `BOOLEAN` | no | Whether dashboard snapshot data exists |

##### `persons`

Central person table with deduplication across years. 2025 uses `MahatmaID` as the unique key; 2022/2023 use `FamilyID + LOWER(first_name) + LOWER(last_name)`.

| Key Fields | Type | Description |
|------------|------|-------------|
| `person_id` | `SERIAL PK` | Auto-incrementing primary key |
| `mahatma_id` | `VARCHAR(50) UNIQUE` | Unique identifier from 2025 data |
| `family_id` | `VARCHAR(50)` | Family grouping identifier |
| `first_name`, `last_name` | `VARCHAR(100)` | Name fields (required) |
| `gender` | `CHAR(1)` | Normalized to M/F |
| `center_id` | `FK → ref_centers` | Attendee's center |
| `region_id` | `FK → ref_regions` | Attendee's region |

##### `registrations`

One record per person per event year. Links to `persons` and `events`.

| Key Fields | Type | Description |
|------------|------|-------------|
| `registration_id` | `SERIAL PK` | Auto-incrementing primary key |
| `event_id` | `FK → events` | Which event |
| `person_id` | `FK → persons` | Who registered |
| `event_year` | `SMALLINT` | Denormalized for fast filtering |
| `age_at_event` | `SMALLINT` | Age at time of event |
| `age_group_id` | `FK → ref_age_groups` | Age group classification |
| `food_pref_id` | `FK → ref_food_preferences` | Food preference |
| `arrival_date`, `departure_date` | `DATE` | Stay dates (parsed from one-hot columns in 2025) |
| `source_file` | `VARCHAR(200)` | Traceability |
| Constraint | `UNIQUE (event_id, person_id)` | One registration per person per event |

##### `rooms`

One record per room booking. Links to `events`, `persons`, reference tables.

| Key Fields | Type | Description |
|------------|------|-------------|
| `room_id` | `SERIAL PK` | Auto-incrementing primary key |
| `event_id` | `FK → events` | Which event |
| `primary_room_holder_id` | `FK → persons` | Primary occupant |
| `room_type_requested_id`, `room_type_assigned_id` | `FK → ref_room_types` | Requested vs assigned type |
| `hotel_id` | `FK → ref_hotels` | Hotel assignment |
| `check_in_date`, `check_out_date` | `DATE` | Stay dates |
| `invoiced_amount`, `paid_amount` | `NUMERIC(10,2)` | Financial data (2025 only) |
| `source_file` | `VARCHAR(200)` | Traceability |

##### `meal_scans`

Individual meal scan records (2025: per-person; 2022: aggregated with `food_count`).

| Key Fields | Type | Description |
|------------|------|-------------|
| `meal_scan_id` | `SERIAL PK` | Auto-incrementing primary key |
| `event_id` | `FK → events` | Which event |
| `person_id` | `FK → persons` | Who was scanned (NULL for aggregated 2022 data) |
| `session_title` | `VARCHAR(200)` | Meal session name (Breakfast, Lunch, Dinner, etc.) |
| `session_date` | `DATE` | Date of meal |
| `food_consumed` | `VARCHAR(50)` | What was consumed (Regular, Jain, Western) |
| `food_count` | `INTEGER` | Count (1 for individual scans, >1 for aggregated) |

#### Auxiliary Tables (Summary)

| Table | Purpose | Linked To |
|-------|---------|-----------|
| `registration_youth` | YMHT (13-17) program data | `registrations` |
| `registration_lmht` | BMHT/LMHT (4-12) program data | `registrations` |
| `registration_bhakti` | Bhakti performance sign-ups | `registrations`, `persons` |
| `special_needs_requests` | Accessibility/mobility requests | `registrations`, `persons` |
| `translation_requests` | Language translation needs | `registrations`, `persons` |
| `registration_exceptions` | Data quality exceptions (AC-no-GP, GP-no-12) | `persons` |
| `dashboard_snapshots` | Pre-aggregated dashboard data (2024, 2025) | — |
| `meal_aggregates` | Daily meal totals (2024) with conflict matrices | `events` |

#### System Tables (Summary)

| Table | Purpose |
|-------|---------|
| `data_availability` | Documents what data exists per year per entity type |
| `agent_jobs` | Tracks ETL pipeline runs (UUID PK, status, phase, progress, errors) |
| `agent_job_steps` | Per-step tracking within a job |
| `aggregation_cache` | Pre-computed JSONB payloads keyed by `cache_key` |
| `user_preferences` | Per-session filter/view state (selected years, regions, active tab) |

#### Reference Tables (Summary)

| Table | Key Field | Seeded From |
|-------|-----------|-------------|
| `ref_regions` | `region_code` | Hardcoded mapping (7 US regions + India + ROW) |
| `ref_centers` | `center_name` | Scanned from xlsx data across all years |
| `ref_food_preferences` | `code` (R/J/RW/JW/W) | Hardcoded mapping |
| `ref_room_types` | `type_code` | Scanned from xlsx data across all years |
| `ref_age_groups` | `group_code` | Hardcoded mapping (2025 ranges + 2022 pivot codes) |
| `ref_hotels` | `hotel_name` | Scanned from xlsx data across all years |

### Indexes

All indexes are defined in `db/schema.sql`. Key indexes include:

| Table | Index | Purpose |
|-------|-------|---------|
| `persons` | `mahatma_id`, `family_id`, `(last_name, first_name)`, `center_id`, `region_id` | Person lookup and deduplication |
| `registrations` | `event_year`, `(event_id, person_id)`, `arrival_date`, `(age_group_id, event_year)`, `(food_pref_id, event_year)` | Registration queries and filtering |
| `rooms` | `event_year`, `check_in_date`, `(hotel_id, event_year)`, `(family_id, event_year)`, `(room_type_assigned_id, event_year)` | Room queries |
| `meal_scans` | `event_year`, `(session_date, event_year)`, `person_id`, `(session_title, event_year)` | Meal scan queries |
| System | `agent_jobs(status)`, `aggregation_cache(cache_key)`, `dashboard_snapshots(event_year, snapshot_type)` | System table lookups |

---

## 8. Proposed Project Folder Structure

```
gpdash/
├── db/                            # Database schema (auto-executed by Docker initdb)
│   └── schema.sql                 # Full PostgreSQL DDL (26 tables + indexes)
│
├── etl/                           # Python ETL pipeline
│   ├── __init__.py
│   ├── run.py                     # CLI entry point (argparse: --year, --seed-only, --reset, --verify)
│   ├── db.py                      # DB connection, get_cursor(), get_or_create_person(), bulk_insert()
│   ├── xlsx_utils.py              # open_workbook(), safe_str/int/float/date(), normalize_gender/food_pref()
│   ├── seed.py                    # Reference table seeding (regions, centers, hotels, room types, etc.)
│   ├── load_2022_2023.py          # Loader for 2022+2023 (identical 54-col structure)
│   ├── load_2024.py               # Loader for 2024 (dashboard snapshots + scanning analysis)
│   └── load_2025.py               # Loader for 2025 (10 sub-loaders: registrations, youth, bhakti, rooms, food, etc.)
│
├── frontend/                      # React + Vite application (to be built)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/            # Sidebar, Header, TabNav
│   │   │   ├── charts/            # LineChart, BarChart, HeatmapChart, KpiCard
│   │   │   ├── tabs/              # OverviewTab, RegistrationTab, RoomTab, DiningTab, AiInsightsTab, RawDataTab
│   │   │   ├── agent/             # AgentStatusPanel, AgentRunButton
│   │   │   └── common/            # DataGapBanner, ExportButton, LoadingSpinner
│   │   ├── hooks/
│   │   │   ├── useFilters.ts      # Filter state management
│   │   │   └── useApi.ts          # Express API fetch hooks
│   │   ├── lib/
│   │   │   ├── api.ts             # API client (base URL, error handling)
│   │   │   ├── formatters.ts      # Date, number, percentage formatters
│   │   │   └── constants.ts       # Color palette, tab names, etc.
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── server/                        # Node.js Express API (to be built)
│   ├── src/
│   │   ├── index.ts               # Express app entry point
│   │   ├── routes/
│   │   │   ├── summary.ts         # GET /api/summary
│   │   │   ├── registrations.ts   # GET /api/registrations
│   │   │   ├── rooms.ts           # GET /api/rooms
│   │   │   ├── meals.ts           # GET /api/meals
│   │   │   ├── agent.ts           # GET /api/agent/status, POST /api/agent/run
│   │   │   └── ask.ts             # POST /api/ask
│   │   ├── services/
│   │   │   ├── db.ts              # PostgreSQL connection pool (node-postgres)
│   │   │   ├── agent.ts           # Python subprocess management
│   │   │   └── claude.ts          # Anthropic SDK wrapper for Q&A
│   │   ├── middleware/
│   │   │   ├── errorHandler.ts    # Centralized error handling
│   │   │   └── cors.ts            # CORS config for local dev
│   │   └── types/
│   │       └── index.ts           # Shared TypeScript types
│   ├── tsconfig.json
│   └── package.json
│
├── reports/                       # Agent-generated markdown reports (gitignored)
├── exports/                       # CSV/Excel backups (gitignored)
├── tmp/                           # Intermediate processing files (gitignored)
│
├── docs/
│   ├── prompt.md                  # Original project prompt
│   ├── PRD.md                     # This document
│   ├── db_design.md               # Detailed database design (entity mapping, discrepancy matrix, ER diagram)
│   └── event_docs/                # Raw source Excel files (9 files, gitignored)
│       ├── gp2022_registrations_and_room_pickups.xlsx
│       ├── gp2022_food_preferences.xlsx
│       ├── gp2023_event_registrations_and_room_pickups.xlsx
│       ├── gp2024_event_dashboard.xlsx
│       ├── gp2024_scanning_analysis.xlsx
│       ├── gp2025_registrations.xlsx
│       ├── gp2025_food_preferences.xlsx
│       ├── gp2025_room_analysis.xlsx
│       └── gp2025_event_dashboard.xlsx
│
├── docker-compose.yml             # PostgreSQL 16-alpine container (port 5433)
├── requirements.txt               # Python dependencies (openpyxl, psycopg2-binary, python-dotenv)
├── .env.example                   # Environment variable template
├── .gitignore
└── README.md
```

---

## 9. Phase-by-Phase Requirements

### Phase 1 — Data Discovery & Schema Design ✅ COMPLETE

**Goal:** Understand every file, design normalized schema, and document data gaps.

| # | Requirement | Status | Notes |
|---|------------|--------|-------|
| P1.1 | Inventory all 9 files in `docs/event_docs/` by year and data type | ✅ | See Section 4 file inventory |
| P1.2 | For each file, document shape, columns, data types, null counts | ✅ | Column mappings encoded in `etl/load_*.py` |
| P1.3 | Identify column naming inconsistencies across years | ✅ | Full mapping in `docs/db_design.md` Section 1 |
| P1.4 | Flag data quality issues: duplicates, missing keys, format variance | ✅ | Documented in `docs/db_design.md` Section 3 |
| P1.5 | Inspect 2024 files to determine structure and usability | ✅ | 2024 is dashboard-only — no individual records |
| P1.6 | Design normalized PostgreSQL schema (26 tables) | ✅ | DDL in `db/schema.sql`, design in `docs/db_design.md` |
| P1.7 | Document data availability per year per entity type | ✅ | Discrepancy matrix in `docs/db_design.md` Section 3 |

### Phase 2 — ETL Pipeline & Data Loading ✅ COMPLETE

**Goal:** Build re-runnable Python ETL pipeline that normalizes and loads all data into PostgreSQL.

| # | Requirement | Status | Notes |
|---|------------|--------|-------|
| P2.1 | Standardize column names to unified schema per year | ✅ | Mappings in `etl/load_2022_2023.py`, `etl/load_2025.py` |
| P2.2 | Parse and normalize all date fields | ✅ | `etl/xlsx_utils.py` `safe_date()` handles multiple formats |
| P2.3 | Deduplicate persons across years | ✅ | `MahatmaID` (2025) or `FamilyID+name` (2022/2023); 1,766 returning attendees detected |
| P2.4 | Split combined 2022/2023 files into person + registration + room records | ✅ | Cols 1–44 → person+registration, cols 45–54 → rooms |
| P2.5 | Seed reference tables from xlsx data | ✅ | `etl/seed.py` seeds regions, centers, hotels, room types, age groups, food prefs |
| P2.6 | Write cleaned data to PostgreSQL (26 tables) | ✅ | ~170K total rows across all tables |
| P2.7 | Track ETL progress in `agent_jobs` table | ✅ | Job steps tracked in `agent_job_steps` |
| P2.8 | Handle 2024 as dashboard-only year (no individual data) | ✅ | Loads `dashboard_snapshots` + `meal_aggregates` only |
| P2.9 | Handle 2023 food gap gracefully | ✅ | `data_availability` marks as `data_level = 'none'` |
| P2.10 | Populate `events` table with cached totals | ✅ | Auto-updated after ETL run |
| P2.11 | Merge room data from two overlapping 2025 sources | ✅ | `room_analysis` as primary, registrations Rooms sheet supplements |
| P2.12 | Pipeline is re-runnable (`--reset` flag) | ✅ | `python -m etl.run --reset` clears and re-populates |

### Phase 3 — Trend Analysis

**Goal:** Produce analytical insights and a narrative report.

| # | Requirement | Acceptance Criteria |
|---|------------|-------------------|
| P3.1 | Registration trends: total per year, YoY growth, region breakdown, arrival/departure distribution, special needs, new vs returning | Charts or tables for each metric; missing years noted |
| P3.2 | Room allocation trends: type distribution, occupancy, check-in/out clusters, utilization rate, rooms-per-attendee ratio | Charts or tables for each metric |
| P3.3 | Food/dining trends: daily headcount, demand curve, preference breakdown, registered-vs-opted ratio, meals-per-attendee | Charts or tables for each metric; 2023 gap explicitly noted |
| P3.4 | Cross-dataset insights: registration–room correlation, registered-but-no-room, booked-but-skipped-meals | At least 3 cross-dataset findings documented |
| P3.5 | Pre-compute aggregations and write to `aggregation_cache` table | Dashboard can render all charts from cached aggregations without re-querying raw data |
| P3.6 | Generate Claude-powered narrative report | `.md` file in `reports/` with: executive summary, stats tables, trend highlights, data quality notes |
| P3.7 | Report file naming | File named `GP_Analysis_Report_[YYYYMMDD_HHMMSS].md` |

> **⏸ CHECKPOINT:** Pause after Phase 3. Show the user key findings and the `.md` report before building the dashboard.

### Phase 4 — Interactive Dashboard

**Goal:** Build the React frontend and Express API.

| # | Requirement | Acceptance Criteria |
|---|------------|-------------------|
| P4.1 | Express API: all 7 endpoints functional | Each endpoint returns valid JSON per Section 10 spec |
| P4.2 | Dashboard: sidebar filters (year, region, room type, date range) | Filters update all charts in real time; multi-select for years |
| P4.3 | Dashboard: Overview tab with KPI cards and agent status | 4 KPI cards rendered; agent status panel shows real-time state |
| P4.4 | Dashboard: Registration Trends tab | Line/bar charts of registrations by year and region; new vs returning breakdown |
| P4.5 | Dashboard: Room Allocation tab | Occupancy heatmap, room type breakdown, utilization chart |
| P4.6 | Dashboard: Dining & Kitchen Planning tab | Day-by-day meal demand chart, preference breakdown, exportable headcount table |
| P4.7 | Dashboard: AI Insights tab | User types question → Claude responds with contextual answer inline |
| P4.8 | Dashboard: Raw Data Explorer tab | Filterable table showing merged dataset; CSV export button |
| P4.9 | Data gap indicators | Tabs and charts for missing data (2023 food, 2024 individual records) show a clear "Data Not Available" banner, not empty/broken charts |
| P4.10 | Design: clean, non-technical | Consistent color scheme, clear labels, hover tooltips on all charts; usable by event coordinators |
| P4.11 | Agent status polling | Dashboard polls `GET /api/agent/status` during active runs; refreshes data after completion |

---

## 10. API Specification

### Base URL

```
http://localhost:3001/api
```

### Common Error Response

All endpoints return errors in this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable error description",
    "details": {}
  }
}
```

Error codes: `VALIDATION_ERROR`, `NOT_FOUND`, `AGENT_BUSY`, `AI_ERROR`, `INTERNAL_ERROR`.

---

### GET `/api/summary`

Returns pre-aggregated KPIs for the dashboard Overview tab.

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `years` | `string` | no | Comma-separated year filter, e.g., `"2022,2023"`. Default: all years. |

**Response (200):**

```json
{
  "data": {
    "totalRegistrations": 4500,
    "totalRoomNights": 3200,
    "averageDailyMeals": 1800,
    "yoyGrowthPercent": 12.5,
    "byYear": [
      {
        "year": 2022,
        "registrations": 1000,
        "roomNights": 700,
        "avgDailyMeals": 800,
        "dataGaps": []
      },
      {
        "year": 2023,
        "registrations": 1200,
        "roomNights": 850,
        "avgDailyMeals": null,
        "dataGaps": ["food"]
      }
    ]
  }
}
```

---

### GET `/api/registrations`

Returns filtered registration data for charts and tables.

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `years` | `string` | no | Comma-separated year filter |
| `regions` | `string` | no | Comma-separated region filter |
| `dateFrom` | `string` | no | ISO 8601 date — filter by arrival date |
| `dateTo` | `string` | no | ISO 8601 date — filter by arrival date |
| `page` | `number` | no | Pagination (default: 1) |
| `pageSize` | `number` | no | Records per page (default: 100, max: 1000) |

**Response (200):**

```json
{
  "data": {
    "records": [
      {
        "eventYear": 2022,
        "firstName": "Jane",
        "lastName": "Doe",
        "email": "jane@example.com",
        "region": "North",
        "arrivalDate": "2022-07-12",
        "departureDate": "2022-07-15",
        "lengthOfStay": 3,
        "specialNeeds": null,
        "isReturning": false
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 100,
      "totalRecords": 4500,
      "totalPages": 45
    },
    "aggregations": {
      "byYear": [
        { "year": 2022, "count": 1000 },
        { "year": 2023, "count": 1200 }
      ],
      "byRegion": [
        { "region": "North", "count": 800 },
        { "region": "South", "count": 650 }
      ],
      "newVsReturning": {
        "new": 3000,
        "returning": 1500
      }
    }
  }
}
```

---

### GET `/api/rooms`

Returns filtered room allocation data.

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `years` | `string` | no | Comma-separated year filter |
| `roomTypes` | `string` | no | Comma-separated room type filter |
| `dateFrom` | `string` | no | ISO 8601 — filter by check-in date |
| `dateTo` | `string` | no | ISO 8601 — filter by check-in date |
| `page` | `number` | no | Default: 1 |
| `pageSize` | `number` | no | Default: 100, max: 1000 |

**Response (200):**

```json
{
  "data": {
    "records": [
      {
        "eventYear": 2022,
        "attendeeName": "Jane Doe",
        "roomType": "Double",
        "hotelName": "Grand Hotel",
        "checkInDate": "2022-07-12",
        "checkOutDate": "2022-07-15",
        "nightCount": 3,
        "occupancy": 2
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 100,
      "totalRecords": 3200,
      "totalPages": 32
    },
    "aggregations": {
      "byRoomType": [
        { "roomType": "Single", "count": 500, "avgOccupancy": 1.0 },
        { "roomType": "Double", "count": 1200, "avgOccupancy": 1.8 }
      ],
      "utilizationByYear": [
        { "year": 2022, "utilizationPercent": 85.2 }
      ]
    }
  }
}
```

---

### GET `/api/meals`

Returns filtered meal headcount data.

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `years` | `string` | no | Comma-separated year filter |
| `mealTypes` | `string` | no | Comma-separated: "Breakfast", "Lunch", "Dinner" |
| `dateFrom` | `string` | no | ISO 8601 — filter by meal date |
| `dateTo` | `string` | no | ISO 8601 — filter by meal date |
| `page` | `number` | no | Default: 1 |
| `pageSize` | `number` | no | Default: 100, max: 1000 |

**Response (200):**

```json
{
  "data": {
    "records": [
      {
        "eventYear": 2022,
        "mealDate": "2022-07-13",
        "mealType": "Lunch",
        "attendeeName": "Jane Doe",
        "preference": "Vegetarian",
        "optedIn": true
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 100,
      "totalRecords": 12000,
      "totalPages": 120
    },
    "aggregations": {
      "dailyHeadcount": [
        { "date": "2022-07-12", "count": 950 },
        { "date": "2022-07-13", "count": 1100 }
      ],
      "byPreference": [
        { "preference": "Vegetarian", "count": 8000 },
        { "preference": "Vegan", "count": 1200 }
      ]
    }
  }
}
```

---

### GET `/api/agent/status`

Returns the current (or most recent) agent job status.

**Response (200):**

```json
{
  "data": {
    "jobId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "running",
    "phase": "cleaning",
    "progress": 45,
    "currentStep": "Normalizing date fields for 2023 registrations",
    "filesProcessed": [
      "gp2022_registrations_and_room_pickups.xlsx",
      "gp2022_food_preferences.xlsx"
    ],
    "errors": [],
    "startedAt": 1710600000000,
    "completedAt": null,
    "reportPath": null
  }
}
```

When no job has ever run:

```json
{
  "data": {
    "status": "idle",
    "message": "No agent jobs found. Click 'Run Agent' to start."
  }
}
```

---

### POST `/api/agent/run`

Triggers the Python ETL agent as a subprocess.

**Request Body:**

```json
{
  "forceRerun": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `forceRerun` | `boolean` | no | If true, clears existing data before re-running. Default: false. |

**Response (202 Accepted):**

```json
{
  "data": {
    "jobId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "queued",
    "message": "Agent job started. Monitor progress via GET /api/agent/status."
  }
}
```

**Error (409 Conflict):**

```json
{
  "error": {
    "code": "AGENT_BUSY",
    "message": "An agent job is already running. Wait for it to complete or check status."
  }
}
```

---

### POST `/api/ask`

Sends a natural-language question about the data to Claude.

**Request Body:**

```json
{
  "question": "Which region had the highest growth from 2023 to 2024?",
  "years": [2023, 2024]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | `string` | yes | Plain-English question (max 500 characters) |
| `years` | `array<number>` | no | Scope the query to specific years |

**Response (200):**

```json
{
  "data": {
    "answer": "The North region had the highest growth from 2023 to 2024, increasing by 28% (from 320 to 410 registrations). The South region grew by 15%, while the West region declined by 3%.",
    "supportingData": {
      "chartType": "bar",
      "labels": ["North", "South", "West", "East"],
      "datasets": [
        { "label": "2023", "data": [320, 280, 190, 210] },
        { "label": "2024", "data": [410, 322, 184, 234] }
      ]
    },
    "model": "claude-sonnet-4-6",
    "tokensUsed": 1250
  }
}
```

When the question cannot be answered due to missing data:

```json
{
  "data": {
    "answer": "I cannot answer this question because food preference data is not available for 2023. Data is available for 2022 and 2025 only.",
    "supportingData": null,
    "model": "claude-sonnet-4-6",
    "tokensUsed": 320
  }
}
```

---

## 11. Dashboard UI Requirements

### Global Elements

#### Sidebar (persistent, left-side)

| Element | Type | Behavior |
|---------|------|----------|
| Year selector | Multi-select checkboxes | Options: 2022, 2023, 2024, 2025. Default: all selected. Updating filters re-fetches data for all visible charts. |
| Region filter | Multi-select dropdown | Options populated from `ref_regions` table. Default: all. |
| Room type filter | Multi-select dropdown | Options populated from `ref_room_types` table. Default: all. |
| Date range slider | Dual-handle range slider | Range spans earliest to latest date across all data. Filters arrival/check-in/meal dates. |
| Reset filters button | Button | Resets all filters to defaults. |

#### Header (persistent, top)

| Element | Type | Behavior |
|---------|------|----------|
| App title | Text | "GP Event Analytics Dashboard" |
| Agent status badge | Colored badge | Green = idle/completed, Yellow = running, Red = failed. Clicking navigates to Overview tab agent panel. Polled via `GET /api/agent/status`. |

---

### Tab 1: Overview

| Element | Type | Data Source | Behavior |
|---------|------|-------------|----------|
| Total Registrations KPI | Card | `GET /api/summary` → `totalRegistrations` | Large number with sparkline showing YoY trend |
| Total Room Nights KPI | Card | `GET /api/summary` → `totalRoomNights` | Large number with sparkline |
| Average Daily Meals KPI | Card | `GET /api/summary` → `averageDailyMeals` | Large number; shows "Partial data" footnote if 2023 food missing |
| YoY Growth % KPI | Card | `GET /api/summary` → `yoyGrowthPercent` | Percentage with up/down arrow indicator |
| Agent Status Panel | Panel | Polled via `GET /api/agent/status` | Shows: current status, phase, progress bar, current step, files processed list, errors. Includes "Run Agent" button. |
| Data Gaps Summary | Banner | `GET /api/summary` → `byYear[].dataGaps` | Amber banner listing: "2023: Food data missing. 2024: Individual records unavailable (dashboard aggregates only)." |

### Tab 2: Registration Trends

| Element | Type | Data Source | Behavior |
|---------|------|-------------|----------|
| Registrations by Year | Bar chart (Recharts `BarChart`) | `aggregation_cache` table, key `registrations_by_year` | One bar per year. Color-coded. Hover tooltip shows exact count. |
| Registrations by Region | Stacked bar chart | `aggregation_cache` table, key `registrations_by_region` | Stacked by region within each year. Legend shows region colors. |
| New vs Returning Attendees | Grouped bar chart | `aggregation_cache` table, key `new_vs_returning` | Two bars per year: new (blue) and returning (green). |
| Arrival Date Distribution | Line chart | `aggregation_cache` table, key `arrival_distribution` | X-axis: event-relative day; Y-axis: arrivals. One line per year. |
| Length of Stay Histogram | Bar chart | Computed from `registrations.length_of_stay` | X-axis: days (1–10+); Y-axis: count. |
| Special Needs Trend | Small line chart | `aggregation_cache` table | Count of `specialNeeds IS NOT NULL` per year. |
| Missing Year Banner | `DataGapBanner` | n/a | If 2024 individual data gap active: "2024 individual registration data is not available — only aggregate totals." |

### Tab 3: Room Allocation

| Element | Type | Data Source | Behavior |
|---------|------|-------------|----------|
| Occupancy Heatmap | Heatmap (custom Recharts or Chart.js matrix) | `rooms` table, grouped by date × room type | X-axis: dates; Y-axis: room types; color intensity = occupancy count. Hover shows exact numbers. |
| Room Type Distribution | Pie/donut chart | `aggregation_cache` table, key `room_type_distribution` | One chart per selected year, or combined. |
| Utilization Rate by Year | Line chart | `aggregation_cache` table, key `room_utilization` | Y-axis: utilization % (rooms used / rooms available). One point per year. |
| Rooms per Attendee Ratio | Line chart | Computed: `COUNT(rooms) / COUNT(attendees)` per year | Shows trend of room density. |
| Check-in/Check-out Clusters | Dual bar chart | `rooms` grouped by date | Two series: check-ins and check-outs by date. Peak days highlighted. |

### Tab 4: Dining & Kitchen Planning

| Element | Type | Data Source | Behavior |
|---------|------|-------------|----------|
| Daily Meal Headcount | Line chart | `aggregation_cache` table, key `daily_meal_headcount` | One line per year. X-axis: event day; Y-axis: total headcount. |
| Meal Demand Curve | Area chart | Same data, smoothed | Highlights peak-demand days. |
| Food Preference Breakdown | Horizontal bar chart | `aggregation_cache` table, key `meal_preferences` | Bars for each preference (Vegetarian, Vegan, etc.) by count. |
| Registered vs Opted-In Ratio | Grouped bar chart | Cross-query: `registrations` count vs `meal_scans` distinct persons per year | Shows drop-off between registration and meal opt-in. |
| Kitchen Headcount Table | Sortable table | `meal_scans` / `meal_aggregates` grouped by date and session | Columns: Date, Meal Type, Headcount, Year. |
| Export Headcount Button | Button | Above table data | Exports the table to CSV. Filename: `kitchen_headcount_[date].csv`. |
| Missing Year Banner | `DataGapBanner` | n/a | "2023 food preference data is not available." |

### Tab 5: AI Insights

| Element | Type | Data Source | Behavior |
|---------|------|-------------|----------|
| Question Input | Text input + submit button | n/a | Placeholder: "Ask a question about the event data..." Max 500 chars. Submit on Enter or click. |
| Answer Display | Rendered text panel | `POST /api/ask` response → `answer` | Claude's response displayed with markdown rendering. |
| Supporting Chart | Dynamic chart | `POST /api/ask` response → `supportingData` | If `supportingData` is non-null, render a chart using the provided `chartType`, `labels`, and `datasets`. |
| Conversation History | Scrollable list | Local state (session only) | Previous Q&A pairs shown above the input. Not persisted to DB. |
| Model Attribution | Small text | Response → `model` | "Answered by claude-sonnet-4-6" below the answer. |
| Loading State | Spinner + "Thinking..." | While awaiting response | Disable input while loading. |
| Error State | Error banner | On API error | "Unable to answer. Please try rephrasing your question." |

### Tab 6: Raw Data Explorer

| Element | Type | Data Source | Behavior |
|---------|------|-------------|----------|
| Data Type Selector | Segmented control | n/a | Toggle between: Registrations, Rooms, Meals. Changes the table below. |
| Data Table | Paginated, sortable, filterable table | `GET /api/registrations`, `/api/rooms`, or `/api/meals` | Columns match the API response record fields. Sortable by clicking headers. Filterable via sidebar. Pagination: 100 rows per page. |
| Row Count | Text | API response → `pagination.totalRecords` | "Showing 1–100 of 4,500 records" |
| Export to CSV | Button | Current filtered dataset | Downloads full filtered dataset (not just current page) as CSV. |
| Column Visibility Toggle | Dropdown | n/a | User can show/hide columns. Preference saved to `user_preferences`. |

---

## 12. AI Integration Strategy

### Model Usage Matrix

| Task | Model | Justification |
|------|-------|---------------|
| Natural language trend summaries | Claude (Sonnet 4.6) | High-quality narrative generation |
| Anomaly explanation | Claude (Sonnet 4.6) | Requires reasoning about data patterns |
| Final `.md` report narrative | Claude (Sonnet 4.6) | Long-form, coherent writing |
| Dashboard Q&A (`POST /api/ask`) | Claude (Sonnet 4.6) | Interactive, context-aware responses |
| Repetitive classification (e.g., region normalization) | Open model (Ollama or compatible) | High volume, low complexity — cost-efficient |
| Data labeling (e.g., categorizing special needs) | Open model | Batch operation, cost-efficient |
| Quick validation tasks | Claude (Haiku 4.5) | Fast, cheap for simple checks |

### Environment Configuration

```bash
# Model selection (see Appendix A for full .env.example)
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-6         # Primary model for summaries/Q&A
CLAUDE_FAST_MODEL=claude-haiku-4-5     # Fast model for validation
OPEN_MODEL_PROVIDER=ollama             # "ollama" or "openai-compatible"
OPEN_MODEL_ENDPOINT=http://localhost:11434
OPEN_MODEL_NAME=llama3                 # Model name for open model provider
```

Model selection is configurable via environment variables so it can be swapped without code changes (per prompt requirement).

### Context Management for Q&A

When a user submits a question via `POST /api/ask`:

1. **Query PostgreSQL** — The Express server queries relevant data from PostgreSQL based on the question and optional year filter. It pulls from `aggregation_cache` first (fast), then from core/aux tables if needed.
2. **Build context** — Construct a context block containing:
   - Summary statistics for the scoped years
   - Relevant aggregation payloads
   - Data gap information (so Claude can say "data not available" rather than hallucinate)
   - Sample raw records if the question requires detail
3. **Limit context size** — Cap the context at ~4,000 tokens. Prioritize aggregations over raw records.
4. **Send to Claude** — System prompt instructs Claude to answer based only on the provided data, cite specific numbers, and flag any data gaps. If supporting data can be visualized, Claude returns a `supportingData` object with chart configuration.
5. **Return response** — The Express server returns Claude's answer, supporting data, model used, and token count.

### Prompt Templates

**Report generation (Phase 3):**

```
You are analyzing multi-year Guru Purnima event data (2022–2025).
Given the following statistics and trend data, write an executive summary
covering: attendance trends, room utilization, dining demand, and notable
cross-dataset insights. Flag any data quality concerns.

Data:
{aggregated_statistics}

Data gaps:
{data_gaps}

Write in a professional but accessible tone suitable for event coordinators.
Structure with headers: Executive Summary, Registration Trends, Room Allocation,
Dining Analysis, Cross-Dataset Insights, Data Quality Notes.
```

**Q&A (Dashboard AI Insights):**

```
You are a data analyst for the Guru Purnima event series (2022–2025).
Answer the user's question based ONLY on the data provided below.
If the data is insufficient to answer, say so and explain which data is missing.
If your answer can be visualized as a chart, include a "supportingData" JSON
object with fields: chartType ("bar"|"line"|"pie"), labels, datasets.

Event Data Context:
{context_block}

Known Data Gaps:
{data_gaps}

User Question: {question}
```

---

## 13. Non-Functional Requirements

### Performance

| Metric | Target |
|--------|--------|
| Dashboard initial load (cold) | < 3 seconds |
| Chart re-render after filter change | < 500 ms |
| API response time (summary, aggregations) | < 200 ms |
| API response time (paginated raw data) | < 500 ms |
| AI Q&A response time | < 10 seconds (depends on Claude API latency) |
| ETL full pipeline (9 files) | < 2 minutes (measured: ~78 seconds) |
| CSV export (full dataset) | < 3 seconds |

### Security

| Concern | Mitigation |
|---------|-----------|
| API keys in source code | All secrets stored in `.env`; `.env` added to `.gitignore`; `.env.example` provided with placeholder values |
| Input injection via Q&A | Sanitize user question input; Claude system prompt restricts to data-only answers; no code execution from user input |
| Local-only access | Server binds to `localhost` only; no external-facing ports |
| File path traversal | Agent only reads from `docs/event_docs/`; Express does not serve arbitrary files |

### Usability

- Dashboard must feel clean and non-technical (per prompt requirement).
- Consistent color scheme across all charts. Suggested palette: a muted, professional 4-color set — one color per year (e.g., blue, teal, amber, coral).
- Clear labels on all axes and chart elements.
- Hover tooltips on every chart data point showing exact values.
- "Data Not Available" banners instead of empty/broken charts for missing years.
- All tables sortable and filterable.

### Reliability

- Agent failures are captured and surfaced in `agent_jobs.errors`, not silently swallowed.
- Agent is idempotent — re-running clears previous data and re-processes.
- If PostgreSQL is unreachable, the Express API returns a clear error rather than hanging.
- Frontend handles API errors gracefully with user-friendly messages.

### Maintainability

- Modular, well-commented code (per prompt requirement).
- Each concern (frontend, API, agent, database) in its own directory.
- Adding a new year's data requires only placing files in `docs/event_docs/` and re-running the agent — no code changes needed.
- Column mappings are defined in per-year loader files (`etl/load_2022_2023.py`, `etl/load_2025.py`) with shared utilities in `etl/xlsx_utils.py`.

---

## 14. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| R1 | 2024 file (`Gp2024_event_dashboard.xlsx`) is aggregated/unusable as raw data | Medium | High — lose an entire year of data | Phase 1 inspects the file first. If aggregated, document what is available and adjust trend analysis to show 3 years instead of 4. Dashboard shows "2024: Limited data" banner. |
| R2 | Column naming is so inconsistent that automated mapping fails | Medium | Medium — delays Phase 2 | Phase 1 produces a full column inventory. Mapping is confirmed by user before Phase 2. Fallback: manual mapping in `schema_mapping.py`. |
| R3 | Duplicate records inflate counts | Medium | Medium — incorrect KPIs | Define dedup key (email + year) in Phase 1. Report duplicate counts before and after cleaning. |
| R4 | Large file (5.1 MB `gp2025_food_preferences.xlsx`) causes memory issues | Low | Medium — agent crashes | Use pandas chunked reading. Monitor memory. Set a file size warning threshold (10 MB). |
| R5 | Docker Desktop not available on user's machine | Low | High — no database | Provide clear Docker install instructions in README. Alternative: user installs PostgreSQL natively and runs `db/schema.sql` manually. |
| R6 | Claude API rate limits or downtime during Phase 3 / Q&A | Low | Medium — delayed analysis or Q&A unavailable | Implement retry with exponential backoff. Cache report output locally so it only needs to be generated once. Q&A shows "Service temporarily unavailable" message. |
| R7 | No returning-attendee tracking possible (emails missing or inconsistent) | Medium | Low — one analysis feature unavailable | If email coverage is < 50%, disable "New vs Returning" chart and note in data quality report. |
| R8 | Date formats are unparseable across files | Low | High — date-dependent analysis broken | Phase 1 samples and catalogs all date formats. Use `dateutil.parser` with multiple fallback formats. Log unparseable dates rather than crashing. |
| R9 | Open model (Ollama) not available on user's machine | Medium | Low — batch tasks fall back to Claude | Make open model optional. If `OPEN_MODEL_ENDPOINT` is unset or unreachable, fall back to Claude Haiku for batch tasks. Log a warning. |

---

## 15. Success Metrics

### Technical Metrics

| # | Metric | Target | Measurement |
|---|--------|--------|-------------|
| T1 | Data coverage | All 9 files ingested; all mappable years present in PostgreSQL | Count records per year per table after ETL run |
| T2 | Data quality | < 1% null rate on required fields after cleaning | Agent quality report (Phase 2) |
| T3 | API reliability | All 7 endpoints return valid JSON with no 500 errors under normal use | Manual testing of each endpoint |
| T4 | Dashboard completeness | All 6 tabs render with correct data | Visual inspection against Section 11 specs |
| T5 | Agent re-runnability | Agent can be triggered twice with identical output | Run agent, check DB; re-run agent, verify DB matches |
| T6 | Agent status polling | Dashboard reflects agent status updates within 5 seconds via polling | Observe dashboard during agent run |

### User-Facing Metrics

| # | Metric | Target | Measurement |
|---|--------|--------|-------------|
| U1 | Time to first insight | User sees populated dashboard < 10 minutes after initial setup | End-to-end timing: install → agent run → dashboard loads |
| U2 | Data gap transparency | Every missing data point has a visible indicator | Review all tabs for 2023 food and 2024 individual data gaps |
| U3 | Export usability | Exported CSV opens correctly in Excel with proper formatting | Open exports in Excel; verify columns, dates, special characters |
| U4 | AI Q&A accuracy | Claude answers are factually grounded in the data — no hallucinated numbers | Test 10 questions; verify each answer against raw data |

---

## 16. Future Considerations

The following items are explicitly **out of scope** for the initial build but documented for future planning:

| # | Item | Notes |
|---|------|-------|
| F1 | Multi-user auth | Add login if the dashboard is ever hosted on a shared server |
| F2 | Cloud deployment | Containerize with Docker; deploy frontend to Vercel, API to Railway/Fly.io |
| F3 | Automated file ingestion | Watch `docs/event_docs/` for new files and auto-trigger agent |
| F4 | Mobile-responsive UI | Adapt layouts for tablet/phone use during events |
| F5 | Historical comparison presets | One-click "Compare 2023 vs 2024" that auto-sets filters |
| F6 | Notification system | Alert when agent completes or encounters errors (email, Slack) |
| F7 | Data versioning | Track changes to cleaned data over time; allow rollback |
| F8 | Budget/cost analysis | Integrate room costs, meal costs for financial planning |
| F9 | Predictive analytics | Use historical trends to forecast 2026 attendance, room, and meal demand |
| F10 | Multi-event support | Generalize beyond GP to other annual events with similar data structures |

---

## Appendix A: `.env.example` Template

```bash
# ── PostgreSQL ─────────────────────────────────────────
DATABASE_URL=postgresql://gpdash:gpdash_dev@localhost:5433/gpdash

# ── Data ───────────────────────────────────────────────
DATA_DIR=./docs/event_docs

# ── Anthropic (Claude) ────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx
CLAUDE_MODEL=claude-sonnet-4-6
CLAUDE_FAST_MODEL=claude-haiku-4-5
CLAUDE_MAX_TOKENS=4096

# ── Open Model (Ollama or compatible) ─────────────────
OPEN_MODEL_PROVIDER=ollama
OPEN_MODEL_ENDPOINT=http://localhost:11434
OPEN_MODEL_NAME=llama3

# ── Server ─────────────────────────────────────────────
API_PORT=3001
API_HOST=localhost

# ── Frontend ───────────────────────────────────────────
VITE_API_URL=http://localhost:3001/api

# ── Agent ──────────────────────────────────────────────
REPORTS_DIR=./reports
EXPORTS_DIR=./exports
TMP_DIR=./tmp
```

---

## Appendix B: File-to-Table Mapping

This table maps each source file to the PostgreSQL tables it populates after ETL.

| Source File | Year | → `persons` / `registrations` | → `rooms` | → `meal_scans` / `meal_aggregates` | → `dashboard_snapshots` | → Aux Tables |
|-------------|------|:---:|:---:|:---:|:---:|:---:|
| `gp2022_registrations_and_room_pickups.xlsx` | 2022 | ✅ | ✅ | — | — | — |
| `gp2022_food_preferences.xlsx` | 2022 | — | — | ✅ `meal_scans` | — | — |
| `gp2023_event_registrations_and_room_pickups.xlsx` | 2023 | ✅ | ✅ | — | — | — |
| `gp2024_event_dashboard.xlsx` | 2024 | — | — | — | ✅ | — |
| `gp2024_scanning_analysis.xlsx` | 2024 | — | — | ✅ `meal_aggregates` | — | — |
| `gp2025_registrations.xlsx` | 2025 | ✅ | ✅ | — | — | ✅ youth, LMHT, bhakti, special needs, translation, exceptions |
| `gp2025_food_preferences.xlsx` | 2025 | — | — | ✅ `meal_scans` | — | — |
| `gp2025_room_analysis.xlsx` | 2025 | — | ✅ | — | — | — |
| `gp2025_event_dashboard.xlsx` | 2025 | — | — | — | ✅ | — |

**Known gaps:**
- `persons` / `registrations`: No individual data for 2024 (dashboard aggregates only)
- `meal_scans`: No food data for 2023 at all
- `rooms`: No individual data for 2024

---

## Appendix C: Glossary

| Term | Definition |
|------|-----------|
| **GP** | Guru Purnima — an annual spiritual/cultural event. The subject of all data in this project. |
| **ETL** | Extract, Transform, Load — the process of reading raw data files, cleaning/normalizing them, and writing to the database. Performed by the Python agent. |
| **Agent / ETL Pipeline** | The Python ETL pipeline (`etl/run.py`) that reads xlsx files, normalizes data, and loads into PostgreSQL. Can be run via CLI or spawned by the Express API as a subprocess. |
| **PostgreSQL** | An open-source relational database. Used locally via Docker (port 5433) to store all cleaned data across 26 normalized tables. |
| **KPI** | Key Performance Indicator — a high-level summary metric (e.g., total registrations, YoY growth %). Displayed on the Overview tab. |
| **YoY** | Year-over-Year — comparison of a metric between consecutive years (e.g., 2023 vs 2024). |
| **Data gap** | A year × data-type combination for which no source data exists (e.g., 2023 food, 2024 individual records). Tracked in `data_availability` table. Must be displayed as "Data Not Available" in the dashboard, never as an empty chart. |
| **Room night** | One room occupied for one night. A 3-night stay = 3 room nights. Used as a standard measure of accommodation demand. |
| **Headcount** | The number of people expected for a specific meal on a specific day. Used by the kitchen/dining team for planning. |
| **Ollama** | A local runtime for open-source LLMs. Used as the open model provider for batch classification and labeling tasks. |
| **Recharts** | A React-native charting library built on D3. The primary visualization library for the dashboard (as specified in the prompt). |
| **Normalized schema** | The standardized 26-table PostgreSQL schema that all years' data is mapped to during ETL. Column name variations across years (e.g., `Gender` / `GenderMF`, `regionID` / `Region`) are resolved to consistent fields. |
| **Docker Compose** | Container orchestration tool used to run PostgreSQL locally. Configuration in `docker-compose.yml`. |

---

*End of PRD*
