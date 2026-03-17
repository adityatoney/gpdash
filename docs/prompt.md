I have multi-year GP (Guru Purnima) event data spanning 2022 to 2025 across three data sources:

1. Event Registration — attendee sign-ups, personal info, regions, arrival/departure dates, special needs flags
2. Room Allocation — hotel room bookings tied to attendees (room type, check-in/out dates, occupancy)
3. Food Preferences — per-attendee meal day selections and headcounts used by the kitchen/dining team

The data is unorganized and inconsistent across years — likely different column names, formats, and structures between files. My goal is a clean multi-year analysis and an interactive dashboard.

---

TECH STACK

Frontend: React + Vite
Backend / API: Node.js (Express)
Background Agent: Python (runs natively on server as a long-running process)
AI Models: Anthropic Claude models (primary) + open-source models (fallback or parallel tasks)
Database: Convex DB — see database strategy section below
Final Outputs: Agent writes .md report files to local device

Before writing any code, propose a full project folder structure that reflects this stack. It should separate concerns cleanly so the React frontend, Node API, Python agent, and Convex schema each live in their own directories.

---

DATABASE STRATEGY — WHAT NEEDS CONVEX DB AND WHAT DOESN'T

Think carefully about which parts of the system need persistent storage vs. which parts are better served by flat files or in-memory processing. Propose a decision before writing any schema.

RECOMMENDED SPLIT (propose this, then confirm with me before implementing):

Use Convex DB for:
- Cleaned and normalized master dataset (post-processing by the Python agent) — queryable by the dashboard in real time
- Agent job status and task logs (so the frontend can show processing progress)
- Filter/view preferences saved per user session
- Any cached aggregations or pre-computed trend summaries the dashboard needs to render fast

Do NOT use Convex DB for:
- Raw uploaded files (keep as local files)
- Intermediate processing files the agent creates during analysis (keep as temp files)
- Final markdown reports (write directly to local device as .md files)

Propose a Convex schema covering: events table (year, type, metadata), attendees table, rooms table, meals table, and agent_jobs table. Use Convex's real-time subscription model so the dashboard updates live as the Python agent writes processed data.

---

PHASE 1 — DATA DISCOVERY & INVENTORY

Before writing any analysis code, start by:
- Listing all files I provide and identifying which year and data type each belongs to
- For each file: print the shape, column names, data types, null counts, and 5 sample rows
- Identify naming inconsistencies across years (e.g. "First Name" vs "fname" vs "FirstName")
- Flag data quality issues: duplicates, missing keys, malformed dates, outlier values
- Propose a unified schema for each of the 3 data types that works across all years

Do not proceed to Phase 2 until I confirm the schema mapping.

---

PHASE 2 — DATA CLEANING & NORMALIZATION (Python Agent)

The Python agent handles all ETL work as a background process:
- Standardize column names to the confirmed unified schema
- Parse and normalize all date fields
- Deduplicate records using a defined key (e.g. email + year for registrations)
- Merge the three data sources into one master dataset per year, then combine into a single multi-year dataset with a "year" column
- Write cleaned data into Convex DB (attendees, rooms, meals tables)
- Update agent_jobs table in Convex with progress status at each step so the frontend can show a live progress indicator
- Export a local CSV/Excel backup of the merged dataset

The agent should be written as a standalone Python script that can be re-run each year when new GP data comes in. Use the Convex Python client to write data. Print a data quality summary before and after cleaning.

---

PHASE 3 — TREND ANALYSIS (Claude + Open Models)

The Python agent runs analysis using a combination of Claude and open models:

Model usage strategy:
- Use Claude (via Anthropic API) for: natural language summaries of trends, anomaly explanation, generating the final .md report narrative
- Use an open model (e.g. a local model via Ollama, or a lightweight open API) for: repetitive classification tasks, data labeling, and any batch operations where cost efficiency matters
- Make the model selection configurable via an environment variable so it can be swapped without code changes

Analyze the following across all years (2022–2025):

REGISTRATION TRENDS
- Total attendees per year and YoY growth rate
- Breakdown by region/zone
- Arrival and departure date distribution (peak arrival days, average length of stay)
- Special needs registrations over time
- New vs returning attendees (if email/ID allows tracking)

ROOM ALLOCATION TRENDS
- Room type distribution per year
- Average occupancy per room type
- Check-in/check-out date clusters
- Hotel room utilization rate
- Rooms per attendee ratio over time

FOOD / DINING TRENDS
- Total meal headcount per day per year
- Day-by-day meal demand curve (which days are highest volume)
- Food preference breakdowns if available
- Ratio of registered attendees vs meal-day opt-ins
- Average meals per attendee per event

CROSS-DATASET INSIGHTS
- Correlation between registration count and room bookings
- Attendees who registered but did not book a room
- Attendees who booked rooms but skipped certain meal days

After analysis, the Python agent should write a structured .md report file to the local device. The report should include: an executive summary (Claude-generated), key statistics tables, trend highlights, and data quality notes. Name the file GP_Analysis_Report_[timestamp].md.

---

PHASE 4 — INTERACTIVE DASHBOARD (React + Vite + Node.js API)

ARCHITECTURE

The Node.js backend (Express) serves as the API layer between the React frontend and Convex DB. It exposes REST endpoints for the dashboard to query aggregated data and also proxies requests to the Convex client. The Python agent writes directly to Convex; the Node API reads from it. The React frontend connects to the Node API and subscribes to Convex real-time updates for live data refresh.

FILTERS (sidebar):
- Year selector (multi-select: 2022–2025)
- Region/zone filter
- Room type filter
- Date range slider

DASHBOARD TABS:

1. Overview
   - KPI cards: total registrations, total room nights, average daily meals, YoY growth %
   - Agent status panel: shows whether the Python agent is idle, processing, or complete (reads from agent_jobs in Convex in real time)

2. Registration Trends
   - Line/bar charts of registrations by year and region
   - New vs returning attendee breakdown

3. Room Allocation
   - Occupancy heatmap by date
   - Room type breakdown
   - Utilization chart

4. Dining & Kitchen Planning
   - Day-by-day meal demand chart
   - Food preference breakdown
   - Kitchen headcount table exportable to CSV

5. AI Insights
   - A panel that lets the user ask plain-English questions about the data (e.g. "Which region had the highest growth from 2023 to 2024?")
   - Routes the query to Claude via the Node API, which queries Convex for relevant data and passes it as context
   - Displays the Claude response inline with supporting chart if applicable

6. Raw Data Explorer
   - Filterable table of the merged dataset from Convex
   - Export to CSV button

DESIGN NOTES:
- Dashboard must feel clean and non-technical — users are event coordinators, not data analysts
- Consistent color scheme, clear labels, hover tooltips on all charts
- Use Recharts or Chart.js for visualizations (not D3 directly)
- Dashboard should run locally (localhost)

---

NODE.JS API ENDPOINTS TO BUILD

- GET /api/summary — returns pre-aggregated KPIs from Convex
- GET /api/registrations — returns filtered registration data
- GET /api/rooms — returns filtered room allocation data
- GET /api/meals — returns filtered meal headcount data
- GET /api/agent/status — returns current agent job status from Convex
- POST /api/agent/run — triggers the Python agent as a subprocess
- POST /api/ask — takes a plain-English question, queries Convex for context, sends to Claude, returns answer

---

IMPORTANT INSTRUCTIONS

- Ask me to upload or share the files before starting Phase 1
- After Phase 1, pause and show me the proposed schema AND the Convex table structure before proceeding
- After Phase 3, pause and show me the key findings and the .md report before building the dashboard
- Propose the project folder structure at the very start before writing any code
- Write modular, well-commented code — this system should be updatable each year with minimal effort
- All environment variables (Anthropic API key, Convex URL, open model endpoint) should be in a .env file with a sample .env.example included
- If data is missing for a year in any category, note it clearly rather than silently skipping it