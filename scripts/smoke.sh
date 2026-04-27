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
smoke "forge-operator container running" \
    bash -c '[ "$(docker inspect --format "{{.State.Running}}" forge-operator 2>/dev/null)" = "true" ]'
smoke "forge-proctor container running" \
    bash -c '[ "$(docker inspect --format "{{.State.Running}}" forge-proctor 2>/dev/null)" = "true" ]'

# Operator container network connectivity
smoke "forge-operator DNS resolves forge-web" \
    docker exec forge-operator getent hosts forge-web
smoke "forge-operator DNS resolves forge-internal" \
    docker exec forge-operator getent hosts forge-internal
smoke "forge-operator can reach forge-web HTTP" \
    docker exec forge-operator curl -fsS --max-time 5 http://forge-web:8080

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

# Proctor scoring UI
smoke "proctor /health returns ok" \
    bash -c "curl -fsS --max-time 5 http://127.0.0.1:8090/health | grep -q 'ok'"
smoke "proctor root reachable" \
    bash -c "curl -s --max-time 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/ | grep -qE '^(200|302|303)'"

# Safety boundary: internal service must NOT be directly reachable from host
if curl -fsS --max-time 2 http://127.0.0.1:9090/health >/dev/null 2>&1; then
    note_fail "SAFETY: forge-internal port 9090 is unexpectedly exposed on host"
else
    note_pass "forge-internal port 9090 correctly NOT exposed on host"
fi

# Privesc SSH port listening on localhost only
smoke "privesc SSH listening on 127.0.0.1:2222" \
    nc -z 127.0.0.1 2222

# Multi-path validation — Stage 1 Foothold
smoke "Stage 1A: /ping POST responds (command injection path)" \
    bash -c "curl -fsS --max-time 5 -X POST http://127.0.0.1:8080/ping -d 'host=127.0.0.1' | grep -q '<pre>'"
smoke "Stage 1B: /greet GET responds (SSTI path)" \
    bash -c "curl -fsS --max-time 5 'http://127.0.0.1:8080/greet?name=test' | grep -qi 'hello'"

# Multi-path validation — Stage 3 Lateral Movement
smoke "Stage 3A: forge-internal reachable from forge-web (lateral path A)" \
    docker exec forge-web curl -fsS --max-time 5 http://forge-internal:9090/health
smoke "Stage 3B: forge-db port reachable from forge-privesc (lateral path B)" \
    docker exec forge-privesc nc -z forge-db 5432

# Optional V2 Kubernetes scenario checks (only when kind cluster is running)
if command -v kind >/dev/null 2>&1 && kind get clusters 2>/dev/null | grep -qx "forge-range"; then
    smoke "V2 web health endpoint reachable (:18080)" \
        bash -c "curl -fsS --max-time 10 http://127.0.0.1:18080/health | grep -q 'ok'"
    smoke "V2 web root reachable (:18080)" \
        bash -c "curl -s --max-time 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:18080/ | grep -qE '^(200|302|303)'"
fi

echo "────────────────────────────────────────"
echo "  Passed: $PASS   Failed: $FAIL"
echo ""

[ "$FAIL" -eq 0 ]
