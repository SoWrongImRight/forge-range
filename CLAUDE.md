# CLAUDE.md — ForgeRange

ForgeRange is a deliberately vulnerable, local-only training lab. This file tells Claude Code how to work in this repository safely and correctly.

---

## Safety Boundary — Non-Negotiable

- **Never add internet-targeting behavior.** No outbound connections to real hosts, no active scanning of anything beyond 127.0.0.1, no real credential use.
- **Never add persistence or stealth mechanisms.** No malware-like behavior, no detection evasion, no rootkits.
- **Keep all published ports bound to 127.0.0.1.** Not 0.0.0.0, not a LAN IP.
- **Use only fake lab credentials** from docs/lab-credentials.md. Never embed real passwords, tokens, or API keys.
- The intentional vulnerabilities exist for authorized local self-study. Do not harden them away accidentally — the lab needs to remain broken in the documented ways.

---

## Repo Structure

```
targets/web/        Flask app — intentionally vulnerable (command injection, SSTI, exposed endpoints)
targets/internal/   Flask API — intentionally broken auth (hard-coded bypass)
targets/db/         PostgreSQL init — plaintext passwords, seeded users
targets/privesc/    Ubuntu container — sudo misconfig, SUID, writable cron
scenarios/          Attack scenario walkthroughs (hints + full walkthrough)
scripts/            verify.sh (comprehensive) and smoke.sh (quick)
docs/               Network map, credentials, reset guide, study plan
kind/               Optional Kubernetes cluster config and manifests
```

---

## Working in This Repo

### Adding a new target

1. Create `targets/<name>/Dockerfile` and `targets/<name>/app.py` (or equivalent).
2. Add the service to `docker-compose.yml` on the correct network (`public_net`, `internal_net`, or both).
3. Bind any exposed host port to `127.0.0.1`.
4. Document all credentials in `docs/lab-credentials.md`.
5. Update `docs/network-map.md`.
6. Add a container check to `scripts/verify.sh`.

### Adding a new scenario

1. Create `scenarios/NN-name/README.md` following the structure in `scenarios/01-full-attack-chain/README.md`.
2. Include: objective, scope, prerequisites, hints, walkthrough (in a collapsed section), flags, reset steps, defensive lessons.
3. Ensure the scenario is testable with `make reset && make verify`.

### Modifying intentional vulnerabilities

- Do not accidentally fix a vulnerability. The `/ping` command injection, `/greet` SSTI, `/admin` missing auth, and `/backup` credential leak are all intentional.
- If you add a new vulnerability, document it in the relevant scenario and in `docs/lab-credentials.md` if it exposes credentials.

### Modifying the Makefile

- All new targets must have a `## Comment` for `make help` to pick them up.
- Do not remove `verify`, `smoke`, `reset`, `up`, `down`, `kind-up`, `kind-down`, `logs`, `ps`.

---

## Validation After Changes

Always run after any edit:

```bash
bash -n scripts/verify.sh    # syntax check
bash -n scripts/smoke.sh     # syntax check
docker compose config        # YAML validation
make help                    # confirm all targets visible
```

If Docker is running, also run:

```bash
make reset
make verify
make smoke
```

---

## Out of Scope for v1

Do not add these until specifically requested:

- Active Directory / Windows targets
- Public cloud resources
- Service mesh or SIEM stack
- C2 frameworks
- Persistence or evasion modules
