# Phase 4: Interactive Dashboard — Implementation Plan

## Context

The PostgreSQL database (26 tables, ~170K rows) and Python ETL pipeline are complete. No frontend or server code exists yet. This plan builds the full interactive dashboard (Express API + React frontend) in 7 incremental milestones, each producing a working, testable deliverable. Phase 3 (trend analysis/reports) is deferred — the dashboard will query PostgreSQL directly.

**Connection:** `postgresql://gpdash:gpdash_dev@localhost:5433/gpdash`
**Server:** Express on `localhost:3001`
**Frontend:** Vite dev server on `localhost:5173`

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Monorepo? | **No** — separate `package.json` in `server/` and `frontend/` | Project root already has Python `requirements.txt`; no shared JS code needed |
| DB connection | **`pg.Pool` singleton** in `server/src/services/db.ts` | Lazy-init, max 10 connections, read `DATABASE_URL` from `.env` |
| Error handling | **`AppError` class + centralized middleware** | Matches PRD error envelope `{ error: { code, message, details } }` |
| Filter state | **Zustand store + URL search param sync** | Tiny, surgical re-renders, survives page refresh |
| Data fetching | **TanStack Query (react-query)** | Caching, dedup, auto-refetch on filter change |
| UI components | **shadcn/ui** (via CLI, copies source into project) | Full control, accessible, Tailwind-native |
| Agent management | **`child_process.spawn`** of `python -m etl.run` | ETL already has CLI with `--reset`, `--year` flags |

---

## Milestone 1: End-to-End Stack — Express + PostgreSQL + React

**Goal:** Working vertical slice — Express serves real KPIs from PostgreSQL, React renders them.

### Files to Create

**Server:**
```
server/
  package.json               # express, pg, dotenv, cors, typescript, ts-node-dev
  tsconfig.json
  src/
    index.ts                 # Express app: CORS, routes, error handler, listen :3001
    services/db.ts           # pg.Pool singleton, query(), healthCheck()
    routes/summary.ts        # GET /api/summary
    middleware/errorHandler.ts
    middleware/cors.ts
    types/index.ts           # ApiResponse<T>, ApiError, SummaryResponse
    utils/catchAsync.ts      # Async route wrapper
```

**Frontend:**
```
frontend/
  package.json               # react, react-dom, vite, typescript, tailwindcss, @tanstack/react-query
  index.html
  vite.config.ts
  tailwind.config.ts
  tsconfig.json
  postcss.config.js
  src/
    main.tsx                 # React root + QueryClientProvider
    App.tsx                  # Renders 4 KPI cards
    index.css                # Tailwind directives
    lib/api.ts               # fetch wrapper, base URL from VITE_API_URL
```

**Root:**
```
.env                         # DATABASE_URL, API_PORT, VITE_API_URL (from .env.example)
```

### Key SQL — `GET /api/summary`
```sql
-- Per-year stats + data gaps
SELECT e.event_year, e.total_registrations, e.total_room_bookings, e.total_meal_scans,
       e.has_registration_data, e.has_room_data, e.has_food_data
FROM events e WHERE e.event_year = ANY($1)
ORDER BY e.event_year;

-- Data gaps
SELECT event_year, entity_type FROM data_availability
WHERE data_level IN ('none', 'summary');
```

### Verify
1. `cd server && npm run dev` → Express on :3001
2. `curl localhost:3001/api/summary` → JSON with real numbers
3. `cd frontend && npm run dev` → Vite on :5173
4. Browser shows 4 KPI cards with real data, no CORS errors

---

## Milestone 2: Layout Shell + Sidebar Filters + Tab Navigation

**Goal:** Full dashboard chrome — sidebar with working filters, header, 6-tab navigation. Only Overview tab has content (KPI cards from M1).

### Files to Create

**Server:**
```
server/src/routes/filters.ts     # GET /api/filters — years, regions, room types, date range
```

**Frontend:**
```
frontend/src/
  stores/filterStore.ts          # Zustand: { years, regions, roomTypes, dateRange, activeTab }
  hooks/useFilters.ts            # Selector hooks + URL sync
  hooks/useApi.ts                # Generic query hook wrapping TanStack Query
  components/
    layout/AppLayout.tsx         # CSS Grid: sidebar | header + content
    layout/Sidebar.tsx           # Filter controls
    layout/Header.tsx            # Title + agent status badge
    layout/TabNav.tsx            # 6 tabs
    common/LoadingSpinner.tsx
    common/DataGapBanner.tsx     # Reusable amber banner
    tabs/OverviewTab.tsx         # KPI cards (refactored from App.tsx)
    tabs/RegistrationTab.tsx     # Placeholder
    tabs/RoomTab.tsx             # Placeholder
    tabs/DiningTab.tsx           # Placeholder
    tabs/AiInsightsTab.tsx       # Placeholder
    tabs/RawDataTab.tsx          # Placeholder
  lib/constants.ts               # Color palette, tab config
  lib/formatters.ts              # Number/date/percent formatters
```

### Key SQL — `GET /api/filters`
```sql
SELECT event_year FROM events ORDER BY event_year;
SELECT region_id, region_code, region_name FROM ref_regions ORDER BY region_name;
SELECT room_type_id, type_code, type_name FROM ref_room_types ORDER BY type_name;
SELECT MIN(start_date), MAX(end_date) FROM events;
```

### Verify
1. Sidebar shows year checkboxes, region/room-type dropdowns populated from DB
2. Selecting filters updates URL params; page refresh restores them
3. Tab navigation switches content; Overview shows KPIs
4. Reset button clears all filters

---

## Milestone 3: Registration Trends + Room Allocation Tabs

**Goal:** Two data-heavy tabs with full charting. Builds reusable Recharts wrappers and the shared query-builder pattern.

### Files to Create

**Server:**
```
server/src/
  services/queryBuilder.ts       # Shared filter→SQL builder (parameterized)
  routes/registrations.ts        # GET /api/registrations — paginated + aggregations
  routes/rooms.ts                # GET /api/rooms — paginated + aggregations
```

**Frontend:**
```
frontend/src/components/
  charts/
    ChartContainer.tsx           # Wrapper: title, loading skeleton, data gap check
    BarChart.tsx                  # Recharts BarChart with consistent styling
    StackedBarChart.tsx
    GroupedBarChart.tsx
    LineChart.tsx
    PieDonutChart.tsx
    HeatmapChart.tsx             # Custom heatmap (Recharts cells or CSS grid)
    KpiCard.tsx                  # KPI card with optional sparkline
  tabs/
    RegistrationTab.tsx          # 6 charts: by year, by region, new/returning, arrival dist, LOS histogram, special needs
    RoomTab.tsx                  # 5 charts: heatmap, type dist, utilization, rooms/attendee, check-in/out clusters
```

### Key SQL — `/api/registrations` aggregations
```sql
-- By year
SELECT r.event_year, COUNT(*) FROM registrations r
WHERE r.event_year = ANY($1) GROUP BY r.event_year;

-- By region (stacked)
SELECT rr.region_name, r.event_year, COUNT(*)
FROM registrations r JOIN persons p ON r.person_id = p.person_id
LEFT JOIN ref_regions rr ON p.region_id = rr.region_id
WHERE r.event_year = ANY($1) GROUP BY rr.region_name, r.event_year;

-- New vs returning
SELECT r.event_year,
  COUNT(*) FILTER (WHERE r.is_returning = true) as returning,
  COUNT(*) FILTER (WHERE r.is_returning IS NOT true) as new
FROM registrations r WHERE r.event_year = ANY($1) GROUP BY r.event_year;

-- Arrival distribution
SELECT r.event_year, r.arrival_date, COUNT(*)
FROM registrations r WHERE r.event_year = ANY($1) AND r.arrival_date IS NOT NULL
GROUP BY r.event_year, r.arrival_date;

-- Length of stay histogram
SELECT r.length_of_stay, COUNT(*) FROM registrations r
WHERE r.event_year = ANY($1) AND r.length_of_stay IS NOT NULL
GROUP BY r.length_of_stay;
```

### Key SQL — `/api/rooms` aggregations
```sql
-- Room type distribution
SELECT rt.type_name, rm.event_year, COUNT(*), AVG(rm.room_occupancy)
FROM rooms rm LEFT JOIN ref_room_types rt ON rm.room_type_assigned_id = rt.room_type_id
WHERE rm.event_year = ANY($1) GROUP BY rt.type_name, rm.event_year;

-- Check-in/out clusters
SELECT rm.check_in_date, COUNT(*) as check_ins FROM rooms rm
WHERE rm.event_year = ANY($1) AND rm.check_in_date IS NOT NULL
GROUP BY rm.check_in_date;
```

### Verify
1. Registration tab: 6 charts with real data, respond to year/region filters
2. Room tab: 5 charts with real data
3. All charts have hover tooltips
4. 2024 shows "Individual data not available" banner
5. API returns correct pagination metadata

---

## Milestone 4: Dining Tab + Overview Polish

**Goal:** Dining tab (complex — merges `meal_scans` + `meal_aggregates` across years) and Overview polish (sparklines, agent status panel).

### Files to Create

**Server:**
```
server/src/routes/meals.ts       # GET /api/meals — merges individual + aggregated data
server/src/routes/agent.ts       # GET /api/agent/status
```

**Frontend:**
```
frontend/src/components/
  charts/AreaChart.tsx           # Meal demand curve
  charts/SortableTable.tsx       # Reusable sortable/paginated table
  common/ExportButton.tsx        # CSV download
  common/AgentStatusPanel.tsx    # Status display + progress bar
  tabs/DiningTab.tsx             # 5 charts + headcount table + CSV export
  tabs/OverviewTab.tsx           # Polish: sparklines, agent panel, data gap summary
  lib/csv.ts                     # CSV generation utility
```

### Key SQL — `/api/meals`
```sql
-- Daily headcount from individual scans (2022, 2025)
SELECT ms.event_year, ms.session_date, SUM(ms.food_count) as total
FROM meal_scans ms WHERE ms.event_year = ANY($1)
GROUP BY ms.event_year, ms.session_date;

-- Daily headcount from aggregates (2024)
SELECT ma.meal_date, ma.total_count FROM meal_aggregates ma
WHERE ma.event_year = 2024;

-- Food preference breakdown
SELECT ms.food_consumed, ms.event_year, SUM(ms.food_count)
FROM meal_scans ms WHERE ms.event_year = ANY($1) AND ms.food_consumed IS NOT NULL
GROUP BY ms.food_consumed, ms.event_year;

-- Kitchen headcount table
SELECT ms.session_date, ms.session_title, ms.event_year, SUM(ms.food_count)
FROM meal_scans ms WHERE ms.event_year = ANY($1)
GROUP BY ms.session_date, ms.session_title, ms.event_year;
```

### Verify
1. Dining tab: charts show 2022 + 2024 + 2025 data (not 2023)
2. "2023 food data not available" banner
3. Kitchen headcount table is sortable, CSV export works
4. Overview: KPI sparklines, agent status shows "idle" or last run
5. Header badge color matches agent status

---

## Milestone 5: Raw Data Explorer

**Goal:** Tab 6 — segmented control (Registrations/Rooms/Meals), paginated sortable table, column visibility, full CSV export.

### Files to Create

**Server:**
```
server/src/routes/export.ts      # GET /api/export/:type — streams full CSV
```

**Frontend:**
```
frontend/src/components/
  tabs/RawDataTab.tsx
  common/DataTable.tsx           # Full-featured: pagination, sort, column toggle
  common/ColumnToggle.tsx
  common/SegmentedControl.tsx
```

### Verify
1. Segmented control switches Registrations/Rooms/Meals
2. Table paginated at 100/page, clickable column headers sort
3. Column toggle hides/shows columns (persists in localStorage)
4. CSV export downloads full filtered dataset
5. All sidebar filters apply

---

## Milestone 6: Agent Management + AI Insights

**Goal:** `POST /api/agent/run` (spawn ETL), `POST /api/ask` (Claude Q&A), and the AI Insights tab.

### Files to Create

**Server:**
```
server/src/
  services/agent.ts              # spawn('python', ['-m', 'etl.run', ...]), track progress
  services/claude.ts             # Anthropic SDK: buildContext(), askQuestion()
  routes/agent.ts                # Add POST /api/agent/run
  routes/ask.ts                  # POST /api/ask
```

**Frontend:**
```
frontend/src/components/
  tabs/AiInsightsTab.tsx         # Q&A input, markdown answer, dynamic chart, history
  agent/AgentRunButton.tsx
```

### Agent Subprocess Pattern
1. Check `agent_jobs` for `status='running'` → 409 if busy
2. INSERT new job row with `status='running'`
3. `spawn('python', ['-m', 'etl.run', ...(forceRerun ? ['--reset'] : [])])` with `cwd: projectRoot`
4. Parse stdout for progress; UPDATE job row
5. On exit: set `completed` or `failed`
6. Return job_id immediately (202)

### Claude Q&A Pattern
1. Query `data_availability` + `events` for context
2. Query aggregations for selected years (cap ~4K tokens)
3. System prompt: "Answer ONLY from provided data, cite numbers, flag gaps"
4. Parse response for optional `supportingData` chart config
5. Return `{ answer, supportingData, model, tokensUsed }`

### Verify
1. "Run Agent" triggers ETL; status panel polls every 3s
2. Header badge turns yellow→green
3. Dashboard data refreshes after agent completes
4. AI: question → Claude answer with markdown rendering
5. Supporting chart renders if returned
6. Error states: missing API key, timeout, agent busy

---

## Milestone 7: Polish + Production Readiness

**Goal:** Data gap banners everywhere, consistent colors, tooltips, loading states, error boundaries, README.

### Files to Create/Modify

```
frontend/src/
  components/common/ErrorBoundary.tsx
  components/common/ChartSkeleton.tsx
  components/common/EmptyState.tsx
  lib/colors.ts              # { 2022: '#3B82F6', 2023: '#14B8A6', 2024: '#F59E0B', 2025: '#F97316' }
server/src/routes/preferences.ts  # GET/PUT /api/preferences (optional)
README.md
```

### Verify
1. Every tab shows data gap banners for missing years
2. Same color per year across all charts
3. Tooltips on every data point
4. Loading skeletons while fetching
5. README setup instructions work end-to-end
6. No browser console errors

---

## Critical Files Reference

| File | Role in Dashboard |
|------|-------------------|
| `db/schema.sql` | All SQL queries reference this schema |
| `docs/PRD.md` §10-11 | API contracts + UI specs (source of truth) |
| `etl/run.py` | CLI interface for agent subprocess (`--reset`, `--year`) |
| `etl/db.py` | Connection pattern to mirror in `server/src/services/db.ts` |
| `etl/seed.py` | Reference data mappings (regions, food prefs, age groups) |
| `.env.example` | Environment variable template |
