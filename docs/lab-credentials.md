# Lab Credentials

**These are fake credentials intentionally embedded in the lab environment. Do not reuse them outside this repository. They have no value beyond this local lab.**

---

## Docker Compose Service Credentials

### Web App (`forge-web`)

| Item | Value | Where It Appears | Used For | Scenario |
|------|-------|-----------------|---------|---------|
| DB_USER | `app` | `docker-compose.yml`, `/backup` endpoint | Web app database connection | Scenario 01 — Phase 2 |
| DB_PASSWORD | `SuperSecret1!` | `docker-compose.yml`, `/backup` endpoint | Web app database connection; also in DB seeded users | Scenario 01 — Phase 2 |
| FLAG_01 | `FLAG{enum_the_web}` | `docker-compose.yml`, `/flag` endpoint | Enumeration flag | Scenario 01 — Phase 3 |

### Internal API (`forge-internal`)

| Item | Value | Where It Appears | Used For | Scenario |
|------|-------|-----------------|---------|---------|
| SECRET_KEY | `internal_lab_secret_do_not_reuse` | `docker-compose.yml`, `/admin` on web app, `/secret` response | Internal API token | Scenario 01 — Phase 4 |
| Auth bypass | `lab-bypass` | Source code (`targets/internal/app.py`) | Hard-coded bypass for the `X-Internal-Token` header | Scenario 01 — Phase 4 |
| FLAG_02 | `FLAG{lateral_move_success}` | `docker-compose.yml`, `/secret` response | Lateral movement flag | Scenario 01 — Phase 4 |

### Database (`forge-db`)

| Item | Value | Where It Appears | Used For | Scenario |
|------|-------|-----------------|---------|---------|
| POSTGRES_USER | `app` | `docker-compose.yml`, `targets/db/init.sql` | Database owner / app user | Scenario 01 — Phase 5 |
| POSTGRES_PASSWORD | `SuperSecret1!` | `docker-compose.yml`, `/backup` endpoint | PostgreSQL authentication | Scenario 01 — Phase 5 |
| POSTGRES_DB | `appdb` | `docker-compose.yml` | Database name | Scenario 01 — Phase 5 |
| FLAG_03 | `FLAG{db_creds_found}` | `docker-compose.yml`, `flags` table in `appdb` | Database access flag | Scenario 01 — Phase 5 |

### Privilege Escalation Host (`forge-privesc`)

| Item | Value | Where It Appears | Used For | Scenario |
|------|-------|-----------------|---------|---------|
| SSH user | `labuser` | `targets/privesc/Dockerfile`, `/admin` on web app | Low-privilege SSH login | Scenario 01 — Phase 6 |
| SSH password | `labpassword` | `targets/privesc/Dockerfile`, `/admin` on web app | SSH authentication to `127.0.0.1:2222` | Scenario 01 — Phase 6 |
| FLAG_04 | `FLAG{root_privesc_complete}` | `docker-compose.yml`, `/root/flag.txt` | Root privesc flag | Scenario 01 — Phase 7 |

---

## Seeded Database Users (`appdb.users` table)

These users are inserted by `targets/db/init.sql`. Passwords are stored in plaintext — an intentional lab misconfiguration for practice.

| Username | Password | Role | Notes |
|----------|----------|------|-------|
| `admin` | `admin123` | `admin` | Simulates a weak admin account |
| `alice` | `password1` | `user` | Common weak password |
| `bob` | `letmein` | `user` | Common weak password |
| `svc_acct` | `Serv1ce!Pass` | `service` | Service account with slightly stronger password |

---

## Optional kind Cluster

| Item | Value | Where It Appears | Used For |
|------|-------|-----------------|---------|
| `db_password` in ConfigMap | `SuperSecret1!` | `kind/manifests/web.yaml` | Intentional bad practice: credentials in ConfigMap instead of Secret |

---

## Credential Discovery Paths (Scenario 01)

### Path A — Admin Panel (`/admin`)

Provides the full service registry in one request. Enables all lateral movement and privesc paths.

| Credential | Enables |
|------------|---------|
| `app:SuperSecret1!` (DB) | Stage 3 Path B (psql from forge-privesc) |
| `internal_lab_secret_do_not_reuse` (API token) | Stage 3 Path A alternative token |
| `labuser:labpassword` (SSH) | Stage 3 Path B SSH login; Stage 4 entry point |

### Path B — Backup Endpoint (`/backup`)

Provides only the database connection string. Sufficient for Stage 3 Path B but does not give SSH or API credentials.

| Credential | Enables |
|------------|---------|
| `app:SuperSecret1!` (DB) | Stage 3 Path B (psql from forge-privesc) |

You will still need `/admin` to obtain `labuser:labpassword` before Stage 4.

---

## Multi-Path Attack Chains (Scenario 01)

```
GET /robots.txt → finds /admin and /backup
        │
        ├─ Path A: GET /admin → full service registry
        │     labuser:labpassword  ──────────────────────► SSH 127.0.0.1:2222
        │     internal_lab_secret  ──► Stage 3A alt token    │
        │     app:SuperSecret1!    ──► Stage 3B psql          │ (on forge-privesc)
        │                                                      ▼
        └─ Path B: GET /backup → DB_URL                  forge-db psql
              app:SuperSecret1!  ──► Stage 3B psql        → FLAG_03
                                                               │
                                                               ▼
Stage 1 (either path): RCE in forge-web                  Stage 4 privesc
        │                                                 → FLAG_04
        └─ Stage 3A: curl forge-internal:9090/secret
              X-Internal-Token: lab-bypass
              → FLAG_02
```
