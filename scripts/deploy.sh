#!/usr/bin/env bash
# deploy.sh — Build and run the full gpdash stack in Docker
#
# Usage:
#   ./scripts/deploy.sh          # Rebuild all & start
#   ./scripts/deploy.sh --down   # Stop & remove containers
#   ./scripts/deploy.sh --logs   # Tail logs for all services
#   ./scripts/deploy.sh --dev    # Start only postgres (for local dev)

set -euo pipefail
cd "$(dirname "$0")/.."

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${BLUE}▸${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }

# ── Parse flags ───────────────────────────────────────────────────────────

if [[ "${1:-}" == "--down" ]]; then
    log "Stopping all containers..."
    docker compose down
    ok "All containers stopped."
    exit 0
fi

if [[ "${1:-}" == "--logs" ]]; then
    docker compose logs -f --tail=50
    exit 0
fi

if [[ "${1:-}" == "--dev" ]]; then
    log "Starting postgres only (for local dev)..."
    docker compose up -d postgres
    echo ""
    ok "Postgres running on localhost:5434"
    echo -e "   Run ${BOLD}cd server && npm run dev${NC} and ${BOLD}cd frontend && npm run dev${NC} separately."
    exit 0
fi

# ── Full deploy ───────────────────────────────────────────────────────────

echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     gpdash — Full Stack Deploy       ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""

# Pre-flight: check for port conflicts
PORTS_IN_USE=()
for PORT in 3002 5434 8081; do
    if lsof -i :"$PORT" -sTCP:LISTEN -t > /dev/null 2>&1; then
        PORTS_IN_USE+=("$PORT")
    fi
done

if [[ ${#PORTS_IN_USE[@]} -gt 0 ]]; then
    err "Port(s) ${PORTS_IN_USE[*]} already in use!"
    echo ""
    echo -e "  Stop local dev servers first, or use ${BOLD}--dev${NC} mode instead."
    echo -e "  Quick fix: kill the processes using these ports:"
    for PORT in "${PORTS_IN_USE[@]}"; do
        PID=$(lsof -i :"$PORT" -sTCP:LISTEN -t 2>/dev/null | head -1)
        CMD=$(ps -p "$PID" -o comm= 2>/dev/null || echo "unknown")
        echo -e "    Port $PORT → PID $PID ($CMD) — run: ${BOLD}kill $PID${NC}"
    done
    echo ""
    exit 1
fi

# Step 1: Build images
log "Building Docker images (server + frontend)..."
docker compose build --parallel
ok "Images built."
echo ""

# Step 2: Start all services
log "Starting all services..."
docker compose up -d
ok "All containers started."
echo ""

# Step 3: Wait for health checks
log "Waiting for services to be healthy..."
TRIES=0
MAX_TRIES=30
until docker compose exec -T postgres pg_isready -U gpdash -q 2>/dev/null; do
    TRIES=$((TRIES + 1))
    if [[ $TRIES -ge $MAX_TRIES ]]; then
        err "Postgres failed to become ready after ${MAX_TRIES}s"
        docker compose logs postgres --tail=20
        exit 1
    fi
    sleep 1
done
ok "Postgres is ready."

TRIES=0
until curl -sf http://localhost:3002/api/health > /dev/null 2>&1; do
    TRIES=$((TRIES + 1))
    if [[ $TRIES -ge $MAX_TRIES ]]; then
        err "Server failed to become ready after ${MAX_TRIES}s"
        docker compose logs server --tail=20
        exit 1
    fi
    sleep 1
done
ok "API server is ready."

TRIES=0
until curl -sf http://localhost:8081 > /dev/null 2>&1; do
    TRIES=$((TRIES + 1))
    if [[ $TRIES -ge $MAX_TRIES ]]; then
        err "Frontend failed to become ready after ${MAX_TRIES}s"
        docker compose logs frontend --tail=20
        exit 1
    fi
    sleep 1
done
ok "Frontend is ready."

# Step 4: Summary
echo ""
echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${BOLD}║          All services up!            ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Frontend:${NC}  http://localhost:8081"
echo -e "  ${BOLD}API:${NC}       http://localhost:3002/api/health"
echo -e "  ${BOLD}Postgres:${NC}  localhost:5434"
echo ""
echo -e "  ${BOLD}Useful commands:${NC}"
echo -e "    ./scripts/deploy.sh --logs    # tail all logs"
echo -e "    ./scripts/deploy.sh --down    # stop everything"
echo -e "    docker compose ps             # check status"
echo ""
