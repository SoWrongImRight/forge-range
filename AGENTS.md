# AGENTS.md — ForgeRange

Rules and context for any automated agent (Claude Code, CI scripts, or similar tools) working in this repository.

---

## Absolute Prohibitions

An agent **must never**:

- Add outbound network calls to real external hosts.
- Add active scanning of anything other than `127.0.0.1` or the Docker-internal subnets.
- Embed real credentials, API keys, cloud tokens, or SSH keys.
- Add persistence mechanisms, scheduled tasks that phone home, or stealth behavior.
- Bind any Docker service port to `0.0.0.0` or a non-loopback address.
- Remove or work around intentional vulnerabilities (command injection, SSTI, broken auth) — they exist for training.
- Push to remote repositories without explicit user instruction.

---

## Permitted Actions

An agent may:

- Edit source files in `targets/`, `scenarios/`, `docs/`, `scripts/`, `kind/`.
- Add new Docker Compose services that follow the loopback-only and fake-credential rules.
- Add new scenario files following the existing structure.
- Run `make verify`, `make smoke`, `bash -n`, and `docker compose config` to validate changes.
- Run `make up`, `make down`, `make reset` to manage local lab state.
- Run `make kind-up` and `make kind-down` if kind is installed.

---

## Validation Checklist

Before reporting a task complete, an agent must:

1. Run `bash -n scripts/verify.sh && bash -n scripts/smoke.sh` — no syntax errors.
2. Run `docker compose config` — YAML parses cleanly.
3. Run `make help` — all expected targets appear.
4. If Docker is available: run `make reset && make verify && make smoke` — all checks pass.
5. Confirm no new host port bindings use `0.0.0.0`.
6. Confirm no real secrets were introduced.

---

## Repo Conventions

- Scripts in `scripts/` use `bash -n` compatible syntax.
- All Makefile targets have `## Description` comments for `make help`.
- All new credentials go in `docs/lab-credentials.md`.
- All new exposed ports go in `docs/network-map.md`.
- Scenario READMEs include: objective, scope, hints (before walkthrough), walkthrough in a collapsed `<details>` block, flags, reset steps, and defensive lessons.
