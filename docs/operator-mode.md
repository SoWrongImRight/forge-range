# Operator Mode — Internal Enumeration Container

`forge-operator` is a `nicolaka/netshoot` container attached to both lab networks. It gives you an **internal** vantage point: you can address every service by container name, reach ports that are never published to the host, and practice the kind of clean enumeration you would do after obtaining a foothold inside a real network.

---

## The Two Perspectives

### External (host or Kali VM)

You scan `127.0.0.1` and see only what the lab deliberately exposes:

| Visible port | Service |
|--------------|---------|
| `127.0.0.1:8080` | `forge-web` |
| `127.0.0.1:2222` | `forge-privesc` SSH |

Everything else (`forge-internal:9090`, `forge-db:5432`, container-to-container SSH) is invisible from here. This is the attacker perspective before any foothold.

### Internal (operator container)

You exec into `forge-operator` and address services by name across both networks:

| Reachable target | Address |
|-----------------|---------|
| `forge-web` | `http://forge-web:8080` |
| `forge-internal` | `http://forge-internal:9090` |
| `forge-db` | `forge-db:5432` (PostgreSQL) |
| `forge-privesc` | `forge-privesc:22` (SSH) |

This is the post-foothold perspective — what you can reach after exploiting `forge-web` or `forge-privesc` and pivoting internally.

---

## Quickstart

```bash
make up
make operator-shell
```

Inside the container, run the baseline recon script:

```bash
/scripts/operator-recon.sh
```

This script provides a fast baseline view of the lab. It does not exploit targets — it only runs safe enumeration checks (DNS resolution, HTTP preview, fast port scan, DB connectivity). Use it to build repeatable operator workflows and confirm your internal vantage point before beginning a scenario.

You can also run it non-interactively from the host:

```bash
make operator-recon
```

Inside the container, `netshoot` provides `curl`, `nmap`, `netcat`, `dig`, `psql` client tooling, and more.

---

## Example Commands Inside the Operator Shell

### DNS resolution

```bash
getent hosts forge-web
getent hosts forge-internal
getent hosts forge-db
getent hosts forge-privesc
```

### HTTP reachability

```bash
curl http://forge-web:8080
curl http://forge-web:8080/robots.txt
curl http://forge-web:8080/admin
curl http://forge-internal:9090/health
```

### Port scanning (internal scope only)

```bash
nmap -sV forge-web
nmap -sV forge-internal
nmap -sV forge-db
nmap -p 22 forge-privesc
```

### Database enumeration

```bash
psql -h forge-db -U app -d appdb
# password: SuperSecret1!   (lab credential — see docs/lab-credentials.md)
```

---

## Relationship to Attack Scenarios

The operator container is not required for any existing scenario — it is an auxiliary tool. Its primary use cases are:

1. **Verify your mental model** after completing a scenario: can you reach what you think you should be able to reach?
2. **Practice enumeration commands** without running exploits from the host.
3. **Simulate post-foothold pivot**: after exploiting `forge-web`, you could in a real engagement pivot to reach `forge-internal:9090`. The operator container lets you practice those follow-on commands in isolation.

---

## Speed Drill

Use this drill to build enumeration speed and discipline. Target: identify all reachable services within 2 minutes of entering the container.

1. Run `make reset` to start from a clean state.
2. Run `make operator-shell` to enter the container.
3. Execute `/scripts/operator-recon.sh` and read the output.
4. Identify all targets and their reachable ports before the timer expires.

Repeat until the workflow is automatic. The goal is not to exploit — it is to move through baseline enumeration without hesitation.

---

## Safety Rules

- `forge-operator` has no published ports. Nothing inside it is reachable from the host without `docker exec`.
- It runs without elevated privileges, host mounts, or Docker socket access.
- Scanning inside the operator container is scoped to the lab networks (`10.10.0.0/24` and `10.10.1.0/24`). Do not modify it to scan external addresses.

---

## Operator Mode vs. Proctor Mode

These are two separate tools with different purposes:

| | Operator Mode | Proctor Mode |
|-|--------------|-------------|
| **Purpose** | Internal enumeration from a post-foothold vantage point | Flag submission and score tracking |
| **Access** | `make operator-shell` → exec into container | Browser at `http://127.0.0.1:8090` |
| **Is it a target?** | No | No |
| **Network position** | `public_net` + `internal_net` | `public_net` only (host port only) |

Do not treat `forge-proctor` as an attack target. It is a training utility, not a vulnerable service. See [proctor-mode.md](proctor-mode.md) for usage.

---

## Stopping the Container

```bash
make operator-down
```

This removes the container but leaves all other lab services running.
