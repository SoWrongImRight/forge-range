## ForgeRange

ForgeRange is developed and maintained by Carroll Groomes Holding (CGH) and FoundryOps.

This lab is part of the ForgeRange training system, focused on building operator-level capability in modern infrastructure environments.

ForgeRange is a deliberately vulnerable, local-only practice lab for container, web, credential, lateral movement, privilege escalation, and optional `kind` exercises. It is intended for authorized self-study on a single workstation.

### Lab Safety Boundary

- Run ForgeRange only on a workstation you control for isolated lab work.
- Keep all published Docker and `kind` ports bound to `127.0.0.1` unless a scenario explicitly documents a different requirement.
- Do not expose this lab to a LAN, VPN, cloud host, port forward, reverse proxy, or public internet.
- Use only the fake credentials documented in [docs/lab-credentials.md](docs/lab-credentials.md).
- Do not add malware, persistence, stealth, unsolicited scanning, or internet-targeting behavior to this repository.
- Reset lab state after exercises with the commands in [docs/reset-guide.md](docs/reset-guide.md).

### Quick Start

```bash
make up
make verify
```

## V2 Kubernetes Scenario

Scenario 02 adds an optional Kubernetes layer using `kind`:

- **Optional** — Docker Scenario 01 continues to work unchanged.
- **Started with** `make kind-up` — creates the cluster, builds images, deploys the scenario.
- **Web entry point:** `http://127.0.0.1:18080` (loopback only; NodePort on kind cluster)
- **Scored in Proctor Mode** — submit V2 flags at `http://127.0.0.1:8090` (80 additional points)
- **Requires** `kind` and `kubectl` on your `PATH`

```bash
make kind-up       # create cluster, build and load images, deploy scenario
make kind-verify   # confirm namespace, pods, services, and web health
```

See [scenarios/02-kubernetes-pivot/README.md](scenarios/02-kubernetes-pivot/README.md) and [kind/README.md](kind/README.md) for details.

### Proctor Mode

ForgeRange includes a local scoring UI at `http://127.0.0.1:8090`:

- Create a local account (no email, no cloud, no internet dependency).
- Submit flags as you discover them during scenarios.
- Earn points for valid flags; false flags are recorded as decoys with no points.
- Track your progress and score across multiple runs.
- Reset scores independently with `make proctor-reset` without disturbing lab targets.

Proctor is a training utility. It is not part of the attack path and is not intentionally vulnerable. See [docs/proctor-mode.md](docs/proctor-mode.md) for full details.

### Verification

`make verify` checks:

- required local tools
- Docker daemon and Compose configuration
- expected running containers
- localhost-only exposure for the public web service
- service reachability for the web app, internal API, and database
- optional `kind` and `kubectl` status when those tools are installed

### Reset

- `make reset-docker` rebuilds the Docker Compose lab from scratch.
- `make reset-kind` deletes the optional `kind` cluster if it exists.
- `make reset-all` resets both Docker Compose and `kind`.

See [docs/network-map.md](docs/network-map.md) for the current network layout.

## ⚠️ Legal & Usage Disclaimer

This repository is a controlled cybersecurity training environment designed for **authorized, local use only**.

All techniques demonstrated are intended solely for educational purposes within systems you own or have explicit permission to test.

**Do not use this lab or its contents to:**
- scan or attack systems without authorization
- target public infrastructure or third-party services
- perform illegal or unethical activities

The authors assume **no liability** for misuse.

By using this repository, you agree to use it responsibly and within the bounds of applicable law.

---

© 2026 Carroll Groomes Holding, LLC. All rights reserved.
