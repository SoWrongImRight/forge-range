# Proctor Mode — Local Scoring and Progress Tracking

`forge-proctor` is a local-only scoring service for the ForgeRange lab. It lets you submit flags, track your score, and monitor progress across scenario runs.

> **Local-only warning:** This service has no internet connectivity, no cloud backend, no email, and no real authentication system. All state is stored in a SQLite database inside the `proctor_data` Docker volume. It is intended for personal training use on your own workstation only.

---

## Purpose

- Award points when valid flags are submitted.
- Record false/decoy flags without awarding points.
- Prevent double-scoring the same flag in the same session.
- Show a dashboard of solved vs. unsolved flags, score, and submission history.
- Provide a repeatable baseline: reset scores between timed runs with `make proctor-reset`.

---

## Starting the Service

Proctor starts automatically with the rest of the lab:

```bash
make up
```

Confirm it is running:

```bash
make ps          # shows forge-proctor in the container list
make proctor-url # prints the URL
```

---

## URL

```
http://127.0.0.1:8090
```

Bound to loopback only. Not reachable from the LAN or internet.

---

## Account Creation

Proctor has no default account. Create one on first use:

1. Open `http://127.0.0.1:8090/register`.
2. Choose a username (max 32 characters) and a password.
3. Your account is created immediately and you are logged in.

Passwords are hashed with `pbkdf2_hmac` (SHA-256, 260,000 iterations, random per-user salt). No plaintext passwords are stored.

---

## Flag Submission Flow

1. Find a flag during a scenario (e.g., `FLAG{enum_the_web}` from `/flag` on the web app).
2. Open `http://127.0.0.1:8090/submit`.
3. Paste the flag value exactly as found. Whitespace is trimmed automatically.
4. Submit. You will be redirected to the dashboard with the result.

**Alternatively**, run the recon script from the operator container or use `make proctor-url` to get the URL, then open it in a browser.

---

## Scoring Table

| Flag | Label | Target | Stage | Points |
|------|-------|--------|-------|--------|
| `FLAG{enum_the_web}` | Enumeration Flag | `forge-web` | Stage 0 / Enumeration | 10 |
| `FLAG{lateral_move_success}` | Internal API Flag | `forge-internal` | Stage 3 / Lateral Movement | 25 |
| `FLAG{db_creds_found}` | Database Flag | `forge-db` | Stage 3 / Lateral Movement | 25 |
| `FLAG{root_privesc_complete}` | Root Privilege Escalation Flag | `forge-privesc` | Stage 4 / Privilege Escalation | 40 |
| **Total** | | | | **100** |

---

## Submission Status Values

| Status | Meaning | Points |
|--------|---------|--------|
| `valid` | Correct flag, first submission | Full flag points |
| `duplicate_valid` | Correct flag, already solved | 0 |
| `false_flag` | Known decoy flag | 0 |
| `invalid` | Not recognized | 0 |

---

## False Flag Behavior

The lab seeds three decoy flags. If you submit one, it is recorded as `false_flag` with zero points. The dashboard shows the decoy label and reason. No penalty is applied.

Seeded decoys (labels only — values are not listed here intentionally):

- Admin Panel Decoy
- Container Escape Decoy
- SSH Banner Decoy

False flags exercise the same discipline as real engagements: not every interesting-looking string is a valid finding.

---

## Dashboard

The dashboard shows:

- Your username and current score vs. maximum (100 points).
- A flag progress table: label, target, stage, points, and solved status. **Flag values are never displayed.**
- Recent submissions: a short preview (first 8 characters + `...`), status, points, and timestamp.

Submitted flag values are hashed (SHA-256) immediately on receipt. Only the 8-character preview is stored for display purposes. The full submitted value is never saved in plaintext.

---

## Reset Behavior

To wipe all scores and accounts and start fresh:

```bash
make proctor-reset
```

This stops the proctor container, removes the `proctor_data` volume (deleting the SQLite database), and restarts the container. All other lab services continue running unaffected.

Use this between timed scenario runs to get a clean scoreboard.

To reset the entire lab including proctor data:

```bash
make reset     # destroys all volumes including proctor_data, rebuilds everything
```

---

## Data Persistence

Scores, accounts, and submission history persist in the named Docker volume `proctor_data` at `/data/proctor.db` inside the container. This volume survives `make down` and `make up` cycles. It is only deleted by `make proctor-reset` or `make reset`.

---

## Privacy Note

- Submitted flag values are hashed immediately and never stored in plaintext.
- Only the first 8 characters of the submitted value are stored as a display preview.
- All data is local. Nothing is sent to any external service.

---

## Limitations

- This is not a production identity system. There is no account recovery, no rate limiting on login, and no CSRF tokens in V1.4. These are acceptable trade-offs for a local single-user training tool.
- The session secret in `docker-compose.yml` is a lab default. It is suitable for local use only. Do not deploy this service to any shared or internet-accessible host.
- There is no admin panel or multi-user leaderboard in V1.4.

---

## Relationship to Operator Mode and Scenario 01

| Tool | Purpose | How to access |
|------|---------|---------------|
| **Operator container** | Internal enumeration from a post-foothold vantage point | `make operator-shell` |
| **Proctor service** | Flag submission and score tracking | `http://127.0.0.1:8090` |

These tools are complementary. Use the operator container to practice enumeration; use Proctor to record your findings and measure progress.

Neither tool is part of Scenario 01's attack path. Do not treat `forge-proctor` as an attack target.

---

## Quick Reference

```bash
make up                # starts proctor with the rest of the lab
make proctor-url       # prints http://127.0.0.1:8090
make proctor-reset     # wipe all proctor data and restart clean
make verify            # includes proctor health check
make smoke             # includes proctor reachability check
```
