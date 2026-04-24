#!/usr/bin/env bash
# scripts/verify.sh — validate that the forge-range lab is available only on
# local machine boundaries and that the core services are reachable.
set -uo pipefail

PASS=0
FAIL=0
WARN=0

note_pass() {
    printf "  \033[32m[PASS]\033[0m %s\n" "$1"
    PASS=$((PASS + 1))
}

note_fail() {
    printf "  \033[31m[FAIL]\033[0m %s\n" "$1"
    FAIL=$((FAIL + 1))
}

note_warn() {
    printf "  \033[33m[WARN]\033[0m %s\n" "$1"
    WARN=$((WARN + 1))
}

check_cmd() {
    local cmd="$1"
    if command -v "$cmd" >/dev/null 2>&1; then
        note_pass "required tool present: $cmd"
    else
        note_fail "required tool missing: $cmd"
    fi
}

run_check() {
    local desc="$1"
    shift
    if "$@" >/dev/null 2>&1; then
        note_pass "$desc"
    else
        note_fail "$desc"
    fi
}

docker_running() {
    docker info >/dev/null 2>&1
}

container_running() {
    local name="$1"
    [ "$(docker inspect --format '{{.State.Running}}' "$name" 2>/dev/null)" = "true" ]
}

container_on_network() {
    local name="$1"
    local network="$2"
    docker inspect --format '{{range $name, $_ := .NetworkSettings.Networks}}{{println $name}}{{end}}' "$name" 2>/dev/null | grep -Eq "(^|_)${network}$"
}

port_binding_is_localhost() {
    local name="$1"
    local private_port="$2"
    docker inspect --format '{{range $p, $bindings := .NetworkSettings.Ports}}{{if eq $p "'"$private_port"'"}}{{range $bindings}}{{println .HostIp}}{{end}}{{end}}{{end}}' "$name" 2>/dev/null | grep -qx "127.0.0.1"
}

kind_cluster_exists() {
    kind get clusters 2>/dev/null | grep -qx "forge-range"
}

echo ""
echo "forge-range :: verification"
echo "────────────────────────────────────────"

for tool in bash docker curl; do
    check_cmd "$tool"
done

if ! docker_running; then
    note_fail "docker daemon reachable"
    echo "────────────────────────────────────────"
    echo "  Passed: $PASS   Failed: $FAIL   Warnings: $WARN"
    echo ""
    exit 1
fi
note_pass "docker daemon reachable"

run_check "docker compose configuration parses" docker compose config -q

for container in forge-web forge-internal forge-db forge-privesc; do
    run_check "$container container running" container_running "$container"
done

run_check "forge-web published port bound to localhost" port_binding_is_localhost forge-web "8080/tcp"
run_check "forge-privesc SSH port bound to localhost" port_binding_is_localhost forge-privesc "22/tcp"
run_check "forge-web attached to public_net" container_on_network forge-web public_net
run_check "forge-internal attached to public_net" container_on_network forge-internal public_net
run_check "forge-internal attached to internal_net" container_on_network forge-internal internal_net
run_check "forge-db attached to internal_net" container_on_network forge-db internal_net
run_check "forge-privesc attached to internal_net" container_on_network forge-privesc internal_net

run_check "web target reachable from localhost" curl -fsS --max-time 5 http://127.0.0.1:8080/
run_check "web /flag returns FLAG{" bash -lc "curl -fsS --max-time 5 http://127.0.0.1:8080/flag | grep -q 'FLAG{'"
run_check "web /robots.txt present" bash -lc "curl -fsS --max-time 5 http://127.0.0.1:8080/robots.txt | grep -q 'Disallow'"
run_check "web /backup leaks credentials as expected for the lab" bash -lc "curl -fsS --max-time 5 http://127.0.0.1:8080/backup | grep -q 'DB_URL='"
run_check "web /admin leaks service registry as expected for the lab" bash -lc "curl -fsS --max-time 5 http://127.0.0.1:8080/admin | grep -q 'labpassword'"
run_check "internal service reachable from web container" docker exec forge-web python -c "import urllib.request; urllib.request.urlopen('http://forge-internal:9090/health', timeout=5).read()"
run_check "database accepts local lab connections" docker exec forge-db pg_isready -U app -d appdb
run_check "privesc SSH listening on localhost:2222" bash -c "nc -z 127.0.0.1 2222"

if command -v kind >/dev/null 2>&1; then
    note_pass "optional tool present: kind"
    if kind_cluster_exists; then
        note_pass "kind cluster forge-range exists"
        if command -v kubectl >/dev/null 2>&1; then
            note_pass "optional tool present: kubectl"
            run_check "kubectl can reach kind-forge-range context" kubectl cluster-info --context kind-forge-range
        else
            note_warn "kubectl not installed; skipping cluster reachability checks"
        fi
    else
        note_warn "kind cluster forge-range not present; skipping cluster checks"
    fi
else
    note_warn "kind not installed; skipping optional cluster checks"
fi

echo "────────────────────────────────────────"
echo "  Passed: $PASS   Failed: $FAIL   Warnings: $WARN"
echo ""

[ "$FAIL" -eq 0 ]
