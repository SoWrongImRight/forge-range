# Reset Guide

Use these commands to return the lab to a known-good state after exercises. Always reset before starting a new scenario run to ensure repeatable results.

---

## Stopping vs. Resetting

| Command | What it does | When to use |
|---------|-------------|-------------|
| `make down` | Stops containers, removes them and the default network. Volumes are preserved. | Quick pause — you want to restart without losing DB state |
| `make reset` | Full teardown (`-v --remove-orphans`) + rebuild. Wipes volumes. | Before a new scenario run; after you modify target source files |
| `make reset-docker` | Same as `make reset` | Alias — identical behavior |
| `make reset-all` | Runs `make reset-docker` then `make reset-kind` | When both Docker Compose and kind need a clean slate |

---

## Docker Compose Reset

### Stop without wiping state

```bash
make down
# Equivalent: docker compose down
```

Containers stop and are removed. The `db_data` PostgreSQL volume is preserved. Run `make up` to restart.

### Full reset (recommended before each scenario)

```bash
make reset
# Equivalent: docker compose down -v --remove-orphans && docker compose up -d --build
```

This destroys all containers, anonymous networks, and the PostgreSQL data volume, then rebuilds and restarts everything from scratch.

Run `make verify` after reset to confirm a clean state:

```bash
make reset
make verify
```

---

## Optional kind Reset

Delete the cluster:

```bash
make kind-down
# Equivalent: kind delete cluster --name forge-range
```

Recreate and redeploy:

```bash
make kind-up
make kind-load
kubectl apply -f kind/manifests/web.yaml
```

---

## Full Reset (Docker + kind)

```bash
make reset-all
make verify
```

---

## If Verification Fails After Reset

1. Confirm Docker Desktop or the Docker daemon is running.
2. Run `make ps` to see container status (`docker compose ps`).
3. Run `make logs` to inspect container output for errors.
4. If containers exited immediately, rebuild: `make reset`.
5. If the kind scenario is involved, run `make kind-down && make kind-up`.
6. Re-run `make verify` to confirm all checks pass.

---

## Manual Teardown

If make commands are unavailable:

```bash
# Stop and wipe Docker Compose lab
docker compose down -v --remove-orphans

# Delete kind cluster (if it exists)
kind delete cluster --name forge-range
```
