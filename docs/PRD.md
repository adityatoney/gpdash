# Product Requirements Document — gpdash

**Guru Purnima Event Analytics Dashboard**

| Field | Value |
|---|---|
| Version | 1.0 |
| Date | 2026-03-16 |
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

gpdash is a local-first analytics dashboard for multi-year Guru Purnima (GP) event data spanning 2022–2025. The project ingests unstructured Excel files covering attendee registrations, room allocations, and food/dining preferences, normalizes them through a Python ETL agent, stores the cleaned data in Convex DB, and surfaces interactive visualizations and AI-powered insights through a React + Vite frontend backed by a Node.js/Express API.

### Key Deliverables

- **Python ETL Agent** — standalone, re-runnable pipeline that discovers, cleans, normalizes, and loads multi-year event data into Convex DB while reporting progress in real time.
- **Convex Database** — real-time queryable store of normalized attendee, room, and meal records plus agent job status and cached aggregations.
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
| G1 | Unify 4 years of GP data into a single, clean, queryable dataset | All 6 source files ingested; unified schema covers registrations, rooms, and meals with a `year` column |
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

| # | File Name | Year | Data Type(s) | Size | Notes |
|---|-----------|------|-------------|------|-------|
| 1 | `gp2022_registrations_and_room_pickups.xlsx` | 2022 | Registrations + Rooms | 835 KB | Combined file — may need split during ETL |
| 2 | `gp2022_food_preferences.xlsx` | 2022 | Food/Dining | 912 KB | |
| 3 | `gp2023_event_registrations_and_room_pickups.xlsx` | 2023 | Registrations + Rooms | 1.3 MB | Largest registration file |
| 4 | `Gp2024_event_dashboard.xlsx` | 2024 | Unknown (likely combined) | 301 KB | **Caution:** filename suggests a dashboard export, not raw data. Structure must be inspected in Phase 1. May contain registrations, rooms, meals, or aggregated summaries. |
| 5 | `gp2025_food_preferences.xlsx` | 2025 | Food/Dining | 5.1 MB | Largest file overall — may contain multiple sheets or embedded images |
| 6 | `gp2025_room_analysis.xlsx` | 2025 | Rooms | 511 KB | Named "analysis" — may contain derived data, not just raw allocations |

### Year × Data-Type Coverage Matrix

| Year | Registrations | Rooms | Food/Dining |
|------|:------------:|:-----:|:-----------:|
| 2022 | ✅ (file 1) | ✅ (file 1) | ✅ (file 2) |
| 2023 | ✅ (file 3) | ✅ (file 3) | ❌ **GAP** |
| 2024 | ❓ (file 4 — unknown) | ❓ (file 4 — unknown) | ❓ (file 4 — unknown) |
| 2025 | ❌ **GAP** | ✅ (file 6) | ✅ (file 5) |

### Known Data Gaps

1. **2023 Food Preferences** — No food file exists for 2023. Dining trend analysis for 2023 will show "Data Not Available." The ETL agent must handle this gracefully and the dashboard must display a clear "No data" indicator rather than an empty chart.
2. **2025 Registrations** — No registration file exists for 2025. Attendance trends will only cover 2022–2024 (or 2022–2023 if 2024 is unusable). Cross-dataset analysis (registrations vs rooms) cannot be performed for 2025.
3. **2024 Unknown Structure** — The `Gp2024_event_dashboard.xlsx` file may not contain raw data. Phase 1 must inspect this file and determine: (a) which data types it covers, (b) whether data is raw or aggregated, (c) whether it can be mapped to the unified schema.

### Data Quality Risks

- **Inconsistent column naming** — the prompt explicitly warns that column names vary across years (e.g., "First Name" vs "fname" vs "FirstName"). Phase 1 must catalog all column names and propose a mapping.
- **Date format variance** — arrival/departure, check-in/check-out dates likely use different formats across files.
- **Duplicate records** — attendees may appear multiple times within a file; deduplication key (e.g., email + year) must be defined in Phase 1.
- **Combined files** — files 1 and 3 combine registrations and rooms; the ETL agent must split them into separate logical tables.
- **Filename casing** — file 4 uses `Gp` (capitalized) while others use `gp`. The agent must handle case-insensitive file matching.

---

## 5. System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          LOCAL MACHINE                              │
│                                                                     │
│  ┌──────────────┐     HTTP      ┌──────────────┐    Convex SDK     │
│  │              │  ──────────▶  │              │  ──────────────▶   │
│  │   React +    │               │  Express.js  │               ┌───┴───┐
│  │   Vite       │  ◀──────────  │  API Server  │  ◀────────────│Convex │
│  │   Frontend   │     JSON      │              │    Real-time   │  DB   │
│  │              │               │              │    Queries     │(cloud)│
│  └──────┬───────┘               └──────┬───────┘               └───┬───┘
│         │                              │                           │
│         │  Convex real-time            │  POST /api/agent/run      │
│         │  subscriptions               │  (spawn subprocess)       │
│         │         ┌────────────────────┘                           │
│         │         ▼                                                │
│         │   ┌──────────────┐    Convex Python SDK                 │
│         │   │   Python     │  ─────────────────────────────────▶  │
│         │   │   ETL Agent  │                                      │
│         │   │              │  ──▶  Anthropic API (Claude)         │
│         │   │              │  ──▶  Open Model (Ollama / API)      │
│         │   └──────┬───────┘                                      │
│         │          │                                               │
│         │          ▼                                               │
│         │   ┌──────────────┐                                      │
│         │   │  Local Files │                                      │
│         │   │  - raw xlsx  │                                      │
│         │   │  - tmp/      │                                      │
│         │   │  - reports/  │                                      │
│         │   │  - exports/  │                                      │
│         │   └──────────────┘                                      │
│         │                                                          │
└─────────┴──────────────────────────────────────────────────────────┘
```

### Data Flow (6 Steps)

| Step | From | To | Action |
|------|------|----|--------|
| 1 | User | Local filesystem | Places `.xlsx` files in `docs/event_docs/` |
| 2 | React UI | Express API | User clicks "Run Agent" → `POST /api/agent/run` |
| 3 | Express API | Python Agent | Express spawns Python agent as a child process |
| 4 | Python Agent | Convex DB | Agent reads `.xlsx` files, cleans data, writes normalized records to Convex tables; updates `agent_jobs` status at each step |
| 5 | Convex DB | React UI | Dashboard subscribes to Convex real-time updates; agent progress and data appear live |
| 6 | Python Agent | Local disk | Agent writes `.md` report to `reports/` and CSV backup to `exports/` |

### Communication Protocol Table

| Connection | Protocol | Library / Method |
|------------|----------|-----------------|
| React → Express | HTTP REST | `fetch` / Axios |
| React → Convex | WebSocket (real-time subscriptions) | `convex/react` client |
| Express → Convex | HTTP | `convex` Node SDK |
| Express → Python Agent | Child process (`spawn`) | Node `child_process` |
| Python Agent → Convex | HTTP | `convex` Python SDK |
| Python Agent → Claude | HTTPS | `anthropic` Python SDK |
| Python Agent → Open Model | HTTP | Ollama REST API or compatible |
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
| Runtime | Node.js | 20.x LTS | Required for Express and Convex Node SDK | Use LTS for stability |
| Database | Convex | Latest | Real-time subscriptions for live agent progress; managed cloud backend; schema validation | Requires internet connection; free tier limits may apply at scale |
| ETL Agent | Python | 3.11+ | Best ecosystem for data wrangling (pandas, openpyxl) | Must be installed separately from Node |
| Excel parsing | openpyxl / pandas | Latest | Handles `.xlsx` reading, multi-sheet support | Large files (5 MB) may be slow to parse |
| AI (primary) | Anthropic Claude | claude-sonnet-4-6 / claude-haiku-4-5 | Natural language summaries, Q&A, report generation | Requires API key; cost per token |
| AI (fallback) | Ollama (local) or open API | Latest | Batch classification, data labeling — cost-efficient | Requires local GPU or external endpoint |
| Reports | Markdown | N/A | Human-readable, version-controllable output format | None |

---

## 7. Database Design

### Storage Decision Matrix

| Data Category | Storage | Rationale |
|---------------|---------|-----------|
| Cleaned, normalized attendee/room/meal records | **Convex DB** | Queryable by dashboard in real time; supports filters and aggregations |
| Agent job status and task logs | **Convex DB** | Frontend subscribes to live progress updates |
| Filter/view preferences per user session | **Convex DB** | Persists across page refreshes |
| Cached aggregations and trend summaries | **Convex DB** | Fast dashboard rendering without re-computing on every load |
| Raw uploaded `.xlsx` files | **Local filesystem** (`docs/event_docs/`) | No need to store binary blobs in DB |
| Intermediate processing files | **Local filesystem** (`tmp/`) | Disposable; agent creates and deletes during ETL |
| Final markdown reports | **Local filesystem** (`reports/`) | Written by agent; user reads/shares directly |
| CSV/Excel backups | **Local filesystem** (`exports/`) | Offline backup of cleaned data |

### Convex Schema — 7 Tables

#### `events`

Stores metadata for each GP event year.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `year` | `number` | yes | Event year (2022, 2023, 2024, 2025) |
| `name` | `string` | yes | Event display name, e.g., "Guru Purnima 2023" |
| `startDate` | `string` | no | Event start date (ISO 8601) — derived from earliest arrival |
| `endDate` | `string` | no | Event end date (ISO 8601) — derived from latest departure |
| `totalRegistrations` | `number` | no | Cached count of attendees for this year |
| `totalRoomNights` | `number` | no | Cached sum of room-nights for this year |
| `dataGaps` | `array<string>` | no | List of missing data types, e.g., `["food"]` for 2023 |
| `metadata` | `object` | no | Flexible field for additional event-level info |
| `createdAt` | `number` | yes | Timestamp of record creation |

#### `attendees`

One record per attendee per year.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eventYear` | `number` | yes | FK to `events.year` |
| `firstName` | `string` | yes | Normalized first name |
| `lastName` | `string` | yes | Normalized last name |
| `email` | `string` | no | Used as dedup key (with year) |
| `phone` | `string` | no | Contact number |
| `region` | `string` | no | Region/zone — normalized to consistent values |
| `city` | `string` | no | City of origin |
| `arrivalDate` | `string` | no | ISO 8601 date |
| `departureDate` | `string` | no | ISO 8601 date |
| `lengthOfStay` | `number` | no | Computed: departure − arrival in days |
| `specialNeeds` | `string` | no | Accessibility or dietary notes |
| `isReturning` | `boolean` | no | True if email appears in a prior year |
| `rawSourceFile` | `string` | yes | Original filename for traceability |
| `createdAt` | `number` | yes | Timestamp |

#### `rooms`

One record per room assignment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eventYear` | `number` | yes | FK to `events.year` |
| `attendeeEmail` | `string` | no | FK to `attendees.email` (may be absent) |
| `attendeeName` | `string` | no | Fallback identifier if email is missing |
| `roomType` | `string` | yes | Normalized room type (e.g., "Single", "Double", "Suite") |
| `roomNumber` | `string` | no | Room number or identifier |
| `hotelName` | `string` | no | Hotel/venue name |
| `checkInDate` | `string` | no | ISO 8601 date |
| `checkOutDate` | `string` | no | ISO 8601 date |
| `nightCount` | `number` | no | Computed: checkout − checkin in days |
| `occupancy` | `number` | no | Number of guests in this room |
| `rawSourceFile` | `string` | yes | Original filename |
| `createdAt` | `number` | yes | Timestamp |

#### `meals`

One record per attendee per meal-day.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eventYear` | `number` | yes | FK to `events.year` |
| `attendeeEmail` | `string` | no | FK to `attendees.email` |
| `attendeeName` | `string` | no | Fallback identifier |
| `mealDate` | `string` | yes | ISO 8601 date |
| `mealType` | `string` | no | "Breakfast", "Lunch", "Dinner", or "All" |
| `preference` | `string` | no | Food preference (e.g., "Vegetarian", "Vegan") |
| `optedIn` | `boolean` | yes | Whether the attendee opted in for this meal-day |
| `rawSourceFile` | `string` | yes | Original filename |
| `createdAt` | `number` | yes | Timestamp |

#### `agent_jobs`

Tracks ETL agent runs and their progress.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `jobId` | `string` | yes | Unique identifier (UUID) |
| `status` | `string` | yes | One of: `"queued"`, `"running"`, `"completed"`, `"failed"` |
| `phase` | `string` | no | Current phase: `"discovery"`, `"cleaning"`, `"analysis"`, `"reporting"` |
| `progress` | `number` | no | 0–100 percentage |
| `currentStep` | `string` | no | Human-readable description of current action |
| `filesProcessed` | `array<string>` | no | List of files processed so far |
| `errors` | `array<string>` | no | Error messages encountered |
| `startedAt` | `number` | yes | Timestamp |
| `completedAt` | `number` | no | Timestamp (set when done) |
| `reportPath` | `string` | no | Local path to the generated `.md` report |

#### `aggregations`

Pre-computed summaries for fast dashboard rendering.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `key` | `string` | yes | Aggregation identifier, e.g., `"kpi_summary"`, `"registrations_by_year"`, `"meals_by_day_2023"` |
| `eventYear` | `number` | no | Null for cross-year aggregations |
| `dataType` | `string` | yes | `"registration"`, `"room"`, `"meal"`, `"cross"`, `"kpi"` |
| `payload` | `object` | yes | The aggregated data (flexible JSON structure) |
| `computedAt` | `number` | yes | Timestamp of last computation |

#### `user_preferences`

Stores per-session filter/view state.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sessionId` | `string` | yes | Browser session identifier |
| `selectedYears` | `array<number>` | no | Active year filters |
| `selectedRegions` | `array<string>` | no | Active region filters |
| `selectedRoomTypes` | `array<string>` | no | Active room type filters |
| `dateRange` | `object` | no | `{ start: string, end: string }` |
| `activeTab` | `string` | no | Last active dashboard tab |
| `updatedAt` | `number` | yes | Timestamp |

### Recommended Indexes

| Table | Index Fields | Purpose |
|-------|-------------|---------|
| `attendees` | `eventYear` | Filter attendees by year |
| `attendees` | `email, eventYear` | Dedup lookups; returning attendee detection |
| `attendees` | `region, eventYear` | Region breakdown queries |
| `rooms` | `eventYear` | Filter rooms by year |
| `rooms` | `roomType, eventYear` | Room type breakdown |
| `rooms` | `checkInDate` | Occupancy heatmap queries |
| `meals` | `eventYear` | Filter meals by year |
| `meals` | `mealDate, eventYear` | Day-by-day demand queries |
| `agent_jobs` | `status` | Find active/running jobs |
| `aggregations` | `key` | Fast lookup by aggregation type |
| `aggregations` | `dataType, eventYear` | Filter aggregations by scope |
| `user_preferences` | `sessionId` | Session lookup |

---

## 8. Proposed Project Folder Structure

```
gpdash/
├── frontend/                      # React + Vite application
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx          # Year, region, room type, date range filters
│   │   │   │   ├── Header.tsx           # App title, agent status badge
│   │   │   │   └── TabNav.tsx           # 6-tab navigation
│   │   │   ├── charts/
│   │   │   │   ├── LineChart.tsx         # Reusable line chart wrapper
│   │   │   │   ├── BarChart.tsx          # Reusable bar chart wrapper
│   │   │   │   ├── HeatmapChart.tsx      # Occupancy heatmap
│   │   │   │   └── KpiCard.tsx           # Single KPI display card
│   │   │   ├── tabs/
│   │   │   │   ├── OverviewTab.tsx       # KPI cards + agent status
│   │   │   │   ├── RegistrationTab.tsx   # Registration trend charts
│   │   │   │   ├── RoomTab.tsx           # Room allocation visuals
│   │   │   │   ├── DiningTab.tsx         # Meal demand charts + export
│   │   │   │   ├── AiInsightsTab.tsx     # Q&A panel
│   │   │   │   └── RawDataTab.tsx        # Filterable table + CSV export
│   │   │   ├── agent/
│   │   │   │   ├── AgentStatusPanel.tsx   # Real-time progress display
│   │   │   │   └── AgentRunButton.tsx     # Trigger agent run
│   │   │   └── common/
│   │   │       ├── DataGapBanner.tsx      # "No data available" indicator
│   │   │       ├── ExportButton.tsx       # CSV export utility
│   │   │       └── LoadingSpinner.tsx
│   │   ├── hooks/
│   │   │   ├── useConvex.ts              # Convex real-time subscription hooks
│   │   │   ├── useFilters.ts             # Filter state management
│   │   │   └── useApi.ts                 # Express API fetch hooks
│   │   ├── lib/
│   │   │   ├── api.ts                    # API client (base URL, error handling)
│   │   │   ├── formatters.ts             # Date, number, percentage formatters
│   │   │   └── constants.ts              # Color palette, tab names, etc.
│   │   ├── convex/
│   │   │   └── _generated/               # Convex codegen output
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── server/                        # Node.js Express API
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
│   │   │   ├── convex.ts          # Convex client wrapper
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
├── agent/                         # Python ETL + analysis agent
│   ├── main.py                    # Entry point — orchestrates all phases
│   ├── discovery.py               # Phase 1: file inventory, schema inspection
│   ├── cleaning.py                # Phase 2: normalize, deduplicate, merge
│   ├── analysis.py                # Phase 3: trend analysis, cross-dataset insights
│   ├── reporting.py               # Phase 3: generate markdown report via Claude
│   ├── convex_client.py           # Convex Python SDK wrapper (read/write)
│   ├── models.py                  # AI model abstraction (Claude + open model)
│   ├── schema_mapping.py          # Column name mappings per year/file
│   ├── utils.py                   # Date parsing, dedup, validation helpers
│   ├── requirements.txt           # Python dependencies
│   └── .python-version            # Python version pin (3.11+)
│
├── convex/                        # Convex schema and functions
│   ├── schema.ts                  # Table definitions (7 tables)
│   ├── events.ts                  # Query/mutation functions for events
│   ├── attendees.ts               # Query/mutation functions for attendees
│   ├── rooms.ts                   # Query/mutation functions for rooms
│   ├── meals.ts                   # Query/mutation functions for meals
│   ├── agentJobs.ts               # Query/mutation functions for agent_jobs
│   ├── aggregations.ts            # Query/mutation functions for aggregations
│   ├── userPreferences.ts         # Query/mutation functions for user_preferences
│   ├── convex.json                # Convex project config
│   └── tsconfig.json
│
├── reports/                       # Agent-generated markdown reports (gitignored)
├── exports/                       # CSV/Excel backups (gitignored)
├── tmp/                           # Intermediate processing files (gitignored)
│
├── docs/
│   ├── prompt.md                  # Original project prompt
│   ├── PRD.md                     # This document
│   └── event_docs/                # Raw source Excel files
│       ├── gp2022_registrations_and_room_pickups.xlsx
│       ├── gp2022_food_preferences.xlsx
│       ├── gp2023_event_registrations_and_room_pickups.xlsx
│       ├── Gp2024_event_dashboard.xlsx
│       ├── gp2025_food_preferences.xlsx
│       └── gp2025_room_analysis.xlsx
│
├── .env.example                   # Environment variable template
├── .gitignore
├── package.json                   # Root workspace config (if monorepo)
└── README.md
```

---

## 9. Phase-by-Phase Requirements

### Phase 1 — Data Discovery & Inventory

**Goal:** Understand every file before writing any transformation code.

| # | Requirement | Acceptance Criteria |
|---|------------|-------------------|
| P1.1 | List all files in `docs/event_docs/` and classify by year and data type | Output table matches the 6-file inventory in Section 4 |
| P1.2 | For each file, print shape, column names, data types, null counts, and 5 sample rows | Report generated for all 6 files with no crashes |
| P1.3 | Identify column naming inconsistencies across years | Mapping table produced showing source column → unified column for each file |
| P1.4 | Flag data quality issues: duplicates, missing keys, malformed dates, outlier values | Quality report lists all issues with counts and examples |
| P1.5 | Inspect `Gp2024_event_dashboard.xlsx` to determine its structure and usability | Written assessment: which data types it covers, raw vs aggregated, schema-mappable or not |
| P1.6 | Propose unified schema for registrations, rooms, and meals | Schema document with field names, types, and required/optional status |
| P1.7 | Propose Convex table structure | Schema matches Section 7 of this PRD (after user confirmation) |

> **⏸ CHECKPOINT:** Pause after Phase 1. Show the user the proposed schema mapping AND Convex table structure. Do not proceed until confirmed.

### Phase 2 — Data Cleaning & Normalization

**Goal:** Transform raw data into clean, queryable records in Convex DB.

| # | Requirement | Acceptance Criteria |
|---|------------|-------------------|
| P2.1 | Standardize column names to confirmed unified schema | All columns match the mapping from P1.3 |
| P2.2 | Parse and normalize all date fields to ISO 8601 | Zero malformed dates in output; `arrivalDate`, `departureDate`, `checkInDate`, `checkOutDate`, `mealDate` all in `YYYY-MM-DD` format |
| P2.3 | Deduplicate records using defined composite key | Dedup key documented; duplicate count before/after reported |
| P2.4 | Split combined files (2022, 2023) into separate registration and room records | `attendees` and `rooms` tables populated from files 1 and 3 |
| P2.5 | Merge into single multi-year dataset with `year` column | Each record has `eventYear` field; all years represented |
| P2.6 | Write cleaned data to Convex DB | Records appear in `attendees`, `rooms`, `meals` tables; counts match expected totals |
| P2.7 | Update `agent_jobs` in Convex with progress at each step | Frontend shows live progress: phase name, current step, percentage |
| P2.8 | Export local CSV/Excel backup of merged dataset | Files written to `exports/` directory; openable in Excel |
| P2.9 | Print data quality summary (before and after) | Console output shows record counts, null rates, and issue counts pre- and post-cleaning |
| P2.10 | Handle missing years gracefully | 2023 meals and 2025 registrations produce no records but log a clear warning; `events.dataGaps` populated |
| P2.11 | Populate `events` table | One record per year (2022–2025) with cached counts and `dataGaps` |
| P2.12 | Agent is re-runnable | Running the agent a second time clears and re-populates tables without duplicating data |

### Phase 3 — Trend Analysis

**Goal:** Produce analytical insights and a narrative report.

| # | Requirement | Acceptance Criteria |
|---|------------|-------------------|
| P3.1 | Registration trends: total per year, YoY growth, region breakdown, arrival/departure distribution, special needs, new vs returning | Charts or tables for each metric; missing years noted |
| P3.2 | Room allocation trends: type distribution, occupancy, check-in/out clusters, utilization rate, rooms-per-attendee ratio | Charts or tables for each metric |
| P3.3 | Food/dining trends: daily headcount, demand curve, preference breakdown, registered-vs-opted ratio, meals-per-attendee | Charts or tables for each metric; 2023 gap explicitly noted |
| P3.4 | Cross-dataset insights: registration–room correlation, registered-but-no-room, booked-but-skipped-meals | At least 3 cross-dataset findings documented |
| P3.5 | Pre-compute aggregations and write to `aggregations` table | Dashboard can render all charts from `aggregations` without re-querying raw data |
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
| P4.9 | Data gap indicators | Tabs and charts for missing data (2023 food, 2025 registrations) show a clear "Data Not Available" banner, not empty/broken charts |
| P4.10 | Design: clean, non-technical | Consistent color scheme, clear labels, hover tooltips on all charts; usable by event coordinators |
| P4.11 | Convex real-time subscriptions | Dashboard auto-updates when agent writes new data — no manual refresh needed |

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
| Region filter | Multi-select dropdown | Options populated from `attendees.region` distinct values. Default: all. |
| Room type filter | Multi-select dropdown | Options populated from `rooms.roomType` distinct values. Default: all. |
| Date range slider | Dual-handle range slider | Range spans earliest to latest date across all data. Filters arrival/check-in/meal dates. |
| Reset filters button | Button | Resets all filters to defaults. |

#### Header (persistent, top)

| Element | Type | Behavior |
|---------|------|----------|
| App title | Text | "GP Event Analytics Dashboard" |
| Agent status badge | Colored badge | Green = idle/completed, Yellow = running, Red = failed. Clicking navigates to Overview tab agent panel. Real-time via Convex subscription. |

---

### Tab 1: Overview

| Element | Type | Data Source | Behavior |
|---------|------|-------------|----------|
| Total Registrations KPI | Card | `GET /api/summary` → `totalRegistrations` | Large number with sparkline showing YoY trend |
| Total Room Nights KPI | Card | `GET /api/summary` → `totalRoomNights` | Large number with sparkline |
| Average Daily Meals KPI | Card | `GET /api/summary` → `averageDailyMeals` | Large number; shows "Partial data" footnote if 2023 food missing |
| YoY Growth % KPI | Card | `GET /api/summary` → `yoyGrowthPercent` | Percentage with up/down arrow indicator |
| Agent Status Panel | Panel | Convex real-time subscription to `agent_jobs` | Shows: current status, phase, progress bar, current step, files processed list, errors. Includes "Run Agent" button. |
| Data Gaps Summary | Banner | `GET /api/summary` → `byYear[].dataGaps` | Amber banner listing: "2023: Food data missing. 2025: Registration data missing." |

### Tab 2: Registration Trends

| Element | Type | Data Source | Behavior |
|---------|------|-------------|----------|
| Registrations by Year | Bar chart (Recharts `BarChart`) | `aggregations` table, key `registrations_by_year` | One bar per year. Color-coded. Hover tooltip shows exact count. |
| Registrations by Region | Stacked bar chart | `aggregations` table, key `registrations_by_region` | Stacked by region within each year. Legend shows region colors. |
| New vs Returning Attendees | Grouped bar chart | `aggregations` table, key `new_vs_returning` | Two bars per year: new (blue) and returning (green). |
| Arrival Date Distribution | Line chart | `aggregations` table, key `arrival_distribution` | X-axis: event-relative day; Y-axis: arrivals. One line per year. |
| Length of Stay Histogram | Bar chart | Computed from `attendees.lengthOfStay` | X-axis: days (1–10+); Y-axis: count. |
| Special Needs Trend | Small line chart | `aggregations` table | Count of `specialNeeds IS NOT NULL` per year. |
| Missing Year Banner | `DataGapBanner` | n/a | If 2025 registrations gap active: "2025 registration data is not available." |

### Tab 3: Room Allocation

| Element | Type | Data Source | Behavior |
|---------|------|-------------|----------|
| Occupancy Heatmap | Heatmap (custom Recharts or Chart.js matrix) | `rooms` table, grouped by date × room type | X-axis: dates; Y-axis: room types; color intensity = occupancy count. Hover shows exact numbers. |
| Room Type Distribution | Pie/donut chart | `aggregations` table, key `room_type_distribution` | One chart per selected year, or combined. |
| Utilization Rate by Year | Line chart | `aggregations` table, key `room_utilization` | Y-axis: utilization % (rooms used / rooms available). One point per year. |
| Rooms per Attendee Ratio | Line chart | Computed: `COUNT(rooms) / COUNT(attendees)` per year | Shows trend of room density. |
| Check-in/Check-out Clusters | Dual bar chart | `rooms` grouped by date | Two series: check-ins and check-outs by date. Peak days highlighted. |

### Tab 4: Dining & Kitchen Planning

| Element | Type | Data Source | Behavior |
|---------|------|-------------|----------|
| Daily Meal Headcount | Line chart | `aggregations` table, key `daily_meal_headcount` | One line per year. X-axis: event day; Y-axis: total headcount. |
| Meal Demand Curve | Area chart | Same data, smoothed | Highlights peak-demand days. |
| Food Preference Breakdown | Horizontal bar chart | `aggregations` table, key `meal_preferences` | Bars for each preference (Vegetarian, Vegan, etc.) by count. |
| Registered vs Opted-In Ratio | Grouped bar chart | Cross-query: `attendees.count` vs `meals.count(distinct attendeeEmail)` per year | Shows drop-off between registration and meal opt-in. |
| Kitchen Headcount Table | Sortable table | `meals` grouped by `mealDate, mealType` | Columns: Date, Meal Type, Headcount, Year. |
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

1. **Query Convex** — The Express server queries relevant data from Convex based on the question and optional year filter. It pulls from `aggregations` first (fast), then from raw tables if needed.
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
| Agent full pipeline (6 files) | < 5 minutes |
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
- If Convex is unreachable, the Express API returns a clear error rather than hanging.
- Frontend handles API errors gracefully with user-friendly messages.

### Maintainability

- Modular, well-commented code (per prompt requirement).
- Each concern (frontend, API, agent, database) in its own directory.
- Adding a new year's data requires only placing files in `docs/event_docs/` and re-running the agent — no code changes needed.
- Column mapping defined in a single file (`agent/schema_mapping.py`) for easy updates.

---

## 14. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| R1 | 2024 file (`Gp2024_event_dashboard.xlsx`) is aggregated/unusable as raw data | Medium | High — lose an entire year of data | Phase 1 inspects the file first. If aggregated, document what is available and adjust trend analysis to show 3 years instead of 4. Dashboard shows "2024: Limited data" banner. |
| R2 | Column naming is so inconsistent that automated mapping fails | Medium | Medium — delays Phase 2 | Phase 1 produces a full column inventory. Mapping is confirmed by user before Phase 2. Fallback: manual mapping in `schema_mapping.py`. |
| R3 | Duplicate records inflate counts | Medium | Medium — incorrect KPIs | Define dedup key (email + year) in Phase 1. Report duplicate counts before and after cleaning. |
| R4 | Large file (5.1 MB `gp2025_food_preferences.xlsx`) causes memory issues | Low | Medium — agent crashes | Use pandas chunked reading. Monitor memory. Set a file size warning threshold (10 MB). |
| R5 | Convex free-tier limits exceeded | Low | High — data write failures | Monitor record counts during Phase 2. If approaching limits, implement batched writes. Document Convex tier limits. |
| R6 | Claude API rate limits or downtime during Phase 3 / Q&A | Low | Medium — delayed analysis or Q&A unavailable | Implement retry with exponential backoff. Cache report output locally so it only needs to be generated once. Q&A shows "Service temporarily unavailable" message. |
| R7 | No returning-attendee tracking possible (emails missing or inconsistent) | Medium | Low — one analysis feature unavailable | If email coverage is < 50%, disable "New vs Returning" chart and note in data quality report. |
| R8 | Date formats are unparseable across files | Low | High — date-dependent analysis broken | Phase 1 samples and catalogs all date formats. Use `dateutil.parser` with multiple fallback formats. Log unparseable dates rather than crashing. |
| R9 | Open model (Ollama) not available on user's machine | Medium | Low — batch tasks fall back to Claude | Make open model optional. If `OPEN_MODEL_ENDPOINT` is unset or unreachable, fall back to Claude Haiku for batch tasks. Log a warning. |

---

## 15. Success Metrics

### Technical Metrics

| # | Metric | Target | Measurement |
|---|--------|--------|-------------|
| T1 | Data coverage | All 6 files ingested; all mappable years present in Convex | Count records per year per table after Phase 2 |
| T2 | Data quality | < 1% null rate on required fields after cleaning | Agent quality report (Phase 2) |
| T3 | API reliability | All 7 endpoints return valid JSON with no 500 errors under normal use | Manual testing of each endpoint |
| T4 | Dashboard completeness | All 6 tabs render with correct data | Visual inspection against Section 11 specs |
| T5 | Agent re-runnability | Agent can be triggered twice with identical output | Run agent, check DB; re-run agent, verify DB matches |
| T6 | Real-time updates | Dashboard reflects agent-written data within 2 seconds | Observe dashboard during agent run |

### User-Facing Metrics

| # | Metric | Target | Measurement |
|---|--------|--------|-------------|
| U1 | Time to first insight | User sees populated dashboard < 10 minutes after initial setup | End-to-end timing: install → agent run → dashboard loads |
| U2 | Data gap transparency | Every missing data point has a visible indicator | Review all tabs for 2023 food and 2025 registration gaps |
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
# ── Convex ─────────────────────────────────────────────
CONVEX_URL=https://your-project.convex.cloud
CONVEX_DEPLOY_KEY=prod:your-deploy-key

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
VITE_CONVEX_URL=https://your-project.convex.cloud

# ── Agent ──────────────────────────────────────────────
DATA_DIR=./docs/event_docs
REPORTS_DIR=./reports
EXPORTS_DIR=./exports
TMP_DIR=./tmp
```

---

## Appendix B: File-to-Table Mapping

This table maps each source file to the Convex tables it populates after ETL.

| Source File | Year | → `events` | → `attendees` | → `rooms` | → `meals` |
|-------------|------|:----------:|:--------------:|:---------:|:---------:|
| `gp2022_registrations_and_room_pickups.xlsx` | 2022 | ✅ | ✅ | ✅ | — |
| `gp2022_food_preferences.xlsx` | 2022 | — | — | — | ✅ |
| `gp2023_event_registrations_and_room_pickups.xlsx` | 2023 | ✅ | ✅ | ✅ | — |
| `Gp2024_event_dashboard.xlsx` | 2024 | ✅ | ❓ | ❓ | ❓ |
| `gp2025_food_preferences.xlsx` | 2025 | — | — | — | ✅ |
| `gp2025_room_analysis.xlsx` | 2025 | ✅ | — | ✅ | — |

**Legend:** ✅ = populates this table, — = does not contribute, ❓ = depends on Phase 1 inspection of file structure.

**Gaps by table:**
- `attendees`: Missing 2025 registrations. 2024 uncertain.
- `rooms`: 2024 uncertain.
- `meals`: Missing 2023 food. 2024 uncertain.

---

## Appendix C: Glossary

| Term | Definition |
|------|-----------|
| **GP** | Guru Purnima — an annual spiritual/cultural event. The subject of all data in this project. |
| **ETL** | Extract, Transform, Load — the process of reading raw data files, cleaning/normalizing them, and writing to the database. Performed by the Python agent. |
| **Agent** | The Python background process (`agent/main.py`) that handles data discovery, cleaning, analysis, and report generation. Spawned by the Express API as a subprocess. |
| **Convex** | A real-time backend-as-a-service database. Used for storing cleaned data, agent status, aggregations, and user preferences. Supports real-time subscriptions via WebSocket. |
| **KPI** | Key Performance Indicator — a high-level summary metric (e.g., total registrations, YoY growth %). Displayed on the Overview tab. |
| **YoY** | Year-over-Year — comparison of a metric between consecutive years (e.g., 2023 vs 2024). |
| **Data gap** | A year × data-type combination for which no source file exists (e.g., 2023 food, 2025 registrations). Must be displayed as "Data Not Available" in the dashboard, never as an empty chart. |
| **Room night** | One room occupied for one night. A 3-night stay = 3 room nights. Used as a standard measure of accommodation demand. |
| **Headcount** | The number of people expected for a specific meal on a specific day. Used by the kitchen/dining team for planning. |
| **Ollama** | A local runtime for open-source LLMs. Used as the open model provider for batch classification and labeling tasks. |
| **Recharts** | A React-native charting library built on D3. The primary visualization library for the dashboard (as specified in the prompt). |
| **Real-time subscription** | A Convex feature where the frontend receives live updates when database records change, without polling. Used for agent progress display. |
| **Unified schema** | The standardized field names and types that all years' data is mapped to during Phase 2 (e.g., "First Name" / "fname" / "FirstName" all become `firstName`). |

---

*End of PRD*
