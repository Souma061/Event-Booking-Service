#!/usr/bin/env bash
# =============================================================================
# run_load_tests.sh — Pre-configured spike test profiles
# Usage: bash scripts/run_load_tests.sh [profile]
#
# Profiles:
#   smoke        — quick sanity check   (10 users, 20 s)
#   normal       — steady-state load    (100 users, 60 s)
#   spike        — sudden user surge    (500 users ramp in 10 s, 90 s total)
#   soak         — sustained pressure   (150 users, 5 min)
#   race         — booking contention   (200 users, 60 s)
#   ratelimit    — brute-force hammer   (100 users, 30 s)
#   breakpoint   — stepped torture test (500→1000→2500→5000 users, 8 min)
#   ui           — interactive dashboard
# =============================================================================
set -euo pipefail

HOST="${BACKEND_HOST:-http://localhost:8000}"
LOCUSTFILE="tests/load/locustfile.py"
REPORTS_DIR="tests/load/reports"
PROFILE="${1:-smoke}"

# Workers to start the backend with (optional; only used in the startup hint).
# Rule of thumb: (2 × nproc) + 1
WORKERS="${WORKERS:-$(( $(nproc) * 2 + 1 ))}"

mkdir -p "$REPORTS_DIR"

echo ""
echo "============================================================"
echo "  Event Booking Service — Spike Test Runner"
echo "  Profile : $PROFILE"
echo "  Host    : $HOST"
echo "============================================================"
echo ""

# Activate venv if present
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

run_headless() {
  local users=$1 spawn_rate=$2 runtime=$3 tags="${4:-}" extra="${5:-}"
  local report="$REPORTS_DIR/${PROFILE}_$(date +%Y%m%d_%H%M%S).html"

  TAG_FLAG=""
  if [ -n "$tags" ]; then
    TAG_FLAG="--tags $tags"
  fi

  # shellcheck disable=SC2086
  locust \
    -f "$LOCUSTFILE" \
    --host="$HOST" \
    --headless \
    -u "$users" \
    -r "$spawn_rate" \
    --run-time "$runtime" \
    --html "$report" \
    $TAG_FLAG \
    $extra

  echo ""
  echo "Report saved → $report"
}

case "$PROFILE" in

  smoke)
    echo "Smoke test — 10 users, 2/s ramp, 20 s"
    run_headless 10 2 20s
    ;;

  normal)
    echo "Normal load — 100 users, 10/s ramp, 60 s"
    run_headless 100 10 60s
    ;;

  spike)
    echo "SPIKE test — 500 users, 50/s ramp, 90 s"
    echo "This is the 'can we handle sudden viral traffic?' test."
    run_headless 500 50 90s
    ;;

  soak)
    echo "Soak test — 150 users, 5/s ramp, 5 min (memory leak / drift check)"
    run_headless 150 5 5m
    ;;

  race)
    echo "Booking race — 200 users targeting same show (tests DB locking)"
    run_headless 200 100 60s "booking_race"
    ;;

  ratelimit)
    echo "Rate-limit hammer — 100 users, bad logins (tests 429 throttle)"
    run_headless 100 50 30s "rate_limit"
    ;;

  breakpoint)
    echo "Breakpoint torture test — stepped staircase: 500→1000→2500→5000 users"
    echo "Stages (2 min each): baseline → knee → saturation → collapse"
    echo "Total runtime: ~8 min. Watch for the knee in the HTML chart."
    echo ""
    REPORT="$REPORTS_DIR/breakpoint_$(date +%Y%m%d_%H%M%S).html"
    # --shape-class activates BreakpointShape; -u/-r are overridden by the shape.
    locust \
      -f "$LOCUSTFILE" \
      --host="$HOST" \
      --headless \
      --shape-class BreakpointShape \
      --html "$REPORT"
    echo ""
    echo "Report saved → $REPORT"
    echo "Open the HTML report and look at the 'Response Times' chart:"
    echo "  Knee       — where p95 first bends upward sharply"
    echo "  Saturation — where req/s plateaus despite more users"
    echo "  Collapse   — where status-0 timeouts begin appearing"
    ;;

  ui)
    echo "Opening Locust web UI at http://localhost:8089"
    locust -f "$LOCUSTFILE" --host="$HOST"
    ;;

  *)
    echo "Unknown profile: '$PROFILE'"
    echo "Available: smoke | normal | spike | soak | race | ratelimit | breakpoint | ui"
    exit 1
    ;;
esac
