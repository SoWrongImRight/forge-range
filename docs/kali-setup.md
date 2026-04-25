# Kali VM Setup — Blast-Radius-Limited External Perspective

A Kali Linux VM gives you a realistic external attacker perspective: you scan the lab from a separate OS with a full offensive toolset, but without risking your main machine state or your LAN.

---

## Why Host-Only Networking

The critical setting is **host-only** (not bridged, not NAT-with-port-forwarding).

| Mode | Kali reaches lab host | Kali reaches your LAN | Use |
|------|-----------------------|----------------------|-----|
| Bridged | Yes | **Yes** — Kali gets a real LAN IP | **Do not use** |
| NAT | Via port-forwarding only | No | Functional but limited |
| Host-only | Yes | **No** — isolated to hypervisor subnet | Recommended |

Host-only keeps Kali confined: it can reach `127.0.0.1` on the host (where the lab ports are) but cannot initiate connections to your router, other machines, or the internet. This is the correct blast-radius posture for lab work.

---

## Hypervisor Setup

### VMware Fusion (macOS)

1. Create or import a Kali VM.
2. In VM Settings → Network Adapter, select **Host-only**.
3. VMware creates a private subnet (commonly `192.168.X.0/24`) shared between the host and the VM.
4. Note the host's IP on that interface: `ifconfig vmnet1` (or similar) on macOS.

### UTM (macOS, free)

1. Create or import a Kali VM.
2. In VM Settings → Network, set Interface to **Bridged (Host Only)**.
3. UTM assigns an address from its internal subnet (`192.168.64.0/24` by default).
4. The host is reachable at `192.168.64.1` from inside the VM.

---

## Finding the Lab From Kali

The lab ports are bound to `127.0.0.1` on the host. From a host-only VM you reach the host via its host-only IP, not `127.0.0.1`. Two options:

**Option A — use the host's host-only IP directly**

```bash
# From inside Kali, find the host address:
ip route show default
# Default gateway is typically the host's host-only IP.

# Then:
nmap -sV -p 8080,2222 <HOST_ONLY_IP>
curl http://<HOST_ONLY_IP>:8080
ssh labuser@<HOST_ONLY_IP> -p 2222
```

**Option B — add a host-side port forwarder**

On the lab host, run a lightweight forwarder so the lab's `127.0.0.1` ports are also reachable on the host-only interface:

```bash
# Example using socat (install if needed: brew install socat)
socat TCP-LISTEN:8080,bind=<HOST_ONLY_IP>,fork TCP:127.0.0.1:8080 &
socat TCP-LISTEN:2222,bind=<HOST_ONLY_IP>,fork TCP:127.0.0.1:2222 &
```

This is temporary and stops when you kill the processes. No persistent config needed.

---

## Example Workflow From Kali

```bash
export LAB=<HOST_ONLY_IP>

# Port scan the lab surface
nmap -sV -p- $LAB

# Web target
curl http://$LAB:8080
curl http://$LAB:8080/robots.txt
curl http://$LAB:8080/admin

# SSH (privesc target)
ssh labuser@$LAB -p 2222
# password: labpassword   (lab credential — see docs/lab-credentials.md)
```

---

## Hard Rules

These rules keep the VM safe and prevent unintended exposure:

| Rule | Why |
|------|-----|
| Use **host-only** network mode, not bridged | Bridged gives Kali a real LAN IP and allows LAN scanning |
| Do **not** scan anything outside `<HOST_ONLY_IP>` | Anything else is your LAN or the internet |
| Do **not** add VPN profiles to the VM | A VPN would route traffic off the host-only subnet |
| Do **not** configure shared folders | Reduces attack surface if the VM is ever compromised |
| **Snapshot before use** | Lets you roll back to a clean state after each lab session |

---

## Snapshot Workflow

```text
Create snapshot → "Clean Lab Start"
    │
    ├── Run lab session
    │
    └── Revert to snapshot when done (or before next session)
```

Most hypervisors support this as a single click. Treat every lab session as disposable.

---

## What Kali Can and Cannot Reach

| Target | Reachable from Kali (host-only) |
|--------|--------------------------------|
| `forge-web:8080` | Yes — via host-only IP + socat or direct |
| `forge-privesc:2222` | Yes — via host-only IP + socat or direct |
| `forge-internal:9090` | **No** — not published to host |
| `forge-db:5432` | **No** — not published to host |
| Your LAN | **No** — host-only network is isolated |

For internal access (what Kali could reach after pivoting), use `make operator-shell`. See [operator-mode.md](operator-mode.md).
