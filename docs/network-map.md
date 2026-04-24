# Network Map

ForgeRange uses two Docker bridge networks and one optional local `kind` cluster.

---

## Docker Networks

| Network | Subnet | Marked `internal` | Attached Services |
|---------|--------|--------------------|-------------------|
| `public_net` | `10.10.0.0/24` | No — host can reach published ports | `forge-web`, `forge-internal`, `forge-privesc` |
| `internal_net` | `10.10.1.0/24` | Yes — no direct host publishing | `forge-internal`, `forge-db`, `forge-privesc` |

`forge-internal` and `forge-privesc` both bridge the two networks. Docker's `internal: true` flag prevents host port publishing from containers on `internal_net` only — `forge-privesc` is also on `public_net` so its SSH port can be published to the host loopback.

---

## Exposed Host Ports

All ports bind to `127.0.0.1` (loopback only). None are reachable from the LAN.

| Host Bind | Container / Service | Container Port | Protocol | Purpose |
|-----------|---------------------|----------------|----------|---------|
| `127.0.0.1:8080` | `forge-web` | `8080` | HTTP | Intentionally exposed web target (attack surface) |
| `127.0.0.1:2222` | `forge-privesc` | `22` | SSH | Privilege escalation host SSH access |
| `127.0.0.1:30080` | kind NodePort | `8080` | HTTP | Optional Kubernetes scenario — requires `make kind-up` |

**Not exposed to host:**
- `forge-internal:9090` — internal API, reachable only from containers on `public_net`
- `forge-db:5432` — PostgreSQL, reachable only from containers on `internal_net`

---

## Service Relationships

| Source | Destination | Protocol / Port | Reason |
|--------|-------------|----------------|--------|
| Host (attacker) | `forge-web` | HTTP `:8080` | Attack entry point — intentionally exposed |
| Host (attacker) | `forge-privesc` | SSH `:2222` | SSH lateral movement target — loopback only |
| `forge-web` | `forge-internal` | HTTP `:9090` | Lateral movement path: web foothold → internal API |
| `forge-internal` | `forge-db` | PostgreSQL `:5432` | Internal service reads from database |
| `forge-internal` | `forge-privesc` | SSH `:22` | Internal-network pivot path (container-to-container) |
| `forge-web` | `forge-db` | — | **No route** — not on same network |
| `forge-web` | `forge-privesc` | — | **No route** — not on same network |

---

## Multi-Path Attack Matrix

Each stage of Scenario 01 offers two valid paths. The table shows which services each path touches and whether it requires container-to-container access or host access.

| Stage | Path | Services Used | Access Type |
|-------|------|---------------|-------------|
| 1A — Foothold | Command injection (`/ping`) | `forge-web` | Host → container (HTTP) |
| 1B — Foothold | SSTI (`/greet`) | `forge-web` | Host → container (HTTP) |
| 2A — Credentials | `/admin` endpoint | `forge-web` | Host → container (HTTP) |
| 2B — Credentials | `/backup` endpoint | `forge-web` | Host → container (HTTP) |
| 3A — Lateral | Web RCE → Internal API | `forge-web` → `forge-internal` | Container-to-container (HTTP) |
| 3B — Lateral | SSH → privesc host → DB | `forge-privesc` → `forge-db` | Host → container (SSH), then container-to-container (psql) |
| 4 — PrivEsc | sudo / SUID / cron | `forge-privesc` | Host → container (SSH) |

## Dual-Homing of forge-privesc

`forge-privesc` is attached to **both** networks:

- `public_net` — enables the host-published SSH port (`127.0.0.1:2222`)
- `internal_net` — gives it a route to `forge-db:5432`

This dual-homing is what makes Stage 3 Path B possible: SSH in via the published loopback port, then use `psql` to reach `forge-db` through the internal network. In a real engagement this would require an SSH tunnel or pivot; the published port simulates that access for the lab.

## Intended Scenario Paths

```
[Attacker host]
      │
      ├─ HTTP:8080 ──────────► forge-web (public_net)
      │   Stage 1A: /ping         │ Stage 1B: /greet
      │   Stage 2A: /admin        │ Stage 2B: /backup
      │                           │
      │                           │ Stage 3A: HTTP:9090 (curl from RCE)
      │                           ▼
      │                     forge-internal (public_net + internal_net)
      │                           │
      │                           └─ PostgreSQL:5432 ──► forge-db (internal_net)
      │                                                     ↑
      │                                              Stage 3B: psql from forge-privesc
      │
      └─ SSH:2222 ───────────► forge-privesc (public_net + internal_net)
           Stage 3B entry            │
           Stage 4 privesc           └─ PostgreSQL:5432 ──► forge-db (internal_net)
```

---

## Optional kind Topology

| Component | Exposure | Notes |
|-----------|----------|-------|
| `kind-forge-range` control-plane | `127.0.0.1:30080` via NodePort | Used for the Kubernetes scenario |
| `forge-web` Kubernetes Service | NodePort `30080` | Mirrors the Docker Compose web target inside the cluster |
| `forge-config` ConfigMap | cluster-internal | Intentionally stores credentials as plaintext for enumeration practice |

See [../kind/README.md](../kind/README.md) for setup and teardown instructions.
