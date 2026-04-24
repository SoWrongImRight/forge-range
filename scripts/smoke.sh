#!/usr/bin/env bash
# scripts/smoke.sh — fast local smoke tests for the forge-range lab.
# Checks service reachability and safety boundaries without full verify overhead.
set -uo pipefail

PASS=0
FAIL=0

note_pass() { printf "  \033[32m[PASS]\033[0m %s\n" "$1"; PASS=$((PASS + 1)); }
note_fail() { printf "  \033[31m[FAIL]\033[0m %s\n" "$1"; FAIL=$((FAIL + 1)); }

smoke() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        note_pass "$desc"
    else
        note_fail "$desc"
    fi
}

echo ""
echo "forge-range :: smoke tests"
echo "────────────────────────────────────────"

# Docker Compose services running
smoke "forge-web container running" \
    bash -c '[ "$(docker inspect --format "{{.State.Running}}" forge-web 2>/dev/null)" = "true" ]'
smoke "forge-internal container running" \
    bash -c '[ "$(docker inspect --format "{{.State.Running}}" forge-internal 2>/dev/null)" = "true" ]'
smoke "forge-db container running" \
    bash -c '[ "$(docker inspect --format "{{.State.Running}}" forge-db 2>/dev/null)" = "true" ]'
smoke "forge-privesc container running" \
    bash -c '[ "$(docker inspect --format "{{.State.Running}}" forge-privesc 2>/dev/null)" = "true" ]'

# Web target reachable and returns expected content
smoke "web root returns HTML" \
    curl -fsS --max-time 5 http://127.0.0.1:8080/
smoke "web /robots.txt mentions Disallow" \
    bash -c "curl -fsS --max-time 5 http://127.0.0.1:8080/robots.txt | grep -q 'Disallow'"
smoke "web /backup returns DB_URL credential (lab intentional)" \
    bash -c "curl -fsS --max-time 5 http://127.0.0.1:8080/backup | grep -q 'DB_URL='"
smoke "web /admin returns service registry (lab intentional)" \
    bash -c "curl -fsS --max-time 5 http://127.0.0.1:8080/admin | grep -q 'labpassword'"
smoke "web /flag returns a flag value" \
    bash -c "curl -fsS --max-time 5 http://127.0.0.1:8080/flag | grep -q 'FLAG{'"

# Safety boundary: internal service must NOT be directly reachable from host
if curl -fsS --max-time 2 http://127.0.0.1:9090/health >/dev/null 2>&1; then
    note_fail "SAFETY: forge-internal port 9090 is unexpectedly exposed on host"
else
    note_pass "forge-internal port 9090 correctly NOT exposed on host"
fi

# Privesc SSH port listening on localhost only
smoke "privesc SSH listening on 127.0.0.1:2222" \
    nc -z 127.0.0.1 2222

echo "────────────────────────────────────────"
echo "  Passed: $PASS   Failed: $FAIL"
echo ""

[ "$FAIL" -eq 0 ]
