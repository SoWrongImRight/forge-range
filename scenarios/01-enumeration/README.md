# 01 — Enumeration

**Objective:** Discover all running services and gather information before attempting exploitation.

## Skills practiced

- Port scanning with nmap
- HTTP header and banner grabbing
- robots.txt and directory enumeration
- Docker network enumeration

## Lab targets

| Target | Address | Notes |
|--------|---------|-------|
| Web app | `http://127.0.0.1:8080` | public-facing, multiple endpoints |
| Internal service | `10.10.1.x:9090` | not directly reachable from attacker |

## Steps

1. Run a port scan against `127.0.0.1`:
   ```bash
   nmap -sV -p- 127.0.0.1
   ```

2. Enumerate the web app:
   ```bash
   curl -s http://127.0.0.1:8080/robots.txt
   gobuster dir -u http://127.0.0.1:8080 -w /usr/share/wordlists/dirb/common.txt
   ```

3. Inspect response headers for version disclosure.

4. Note any credentials or flags discovered.

## Flags

- `FLAG{enum_the_web}` — found in `/flag` on the web target

## Defensive notes

- Disable directory listing
- Remove `/robots.txt` hints in production
- Suppress server version headers (`Server:`, `X-Powered-By:`)
