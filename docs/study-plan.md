# Study Plan

A practical progression for using ForgeRange as an OSCP preparation lab. Each phase builds on the previous one. Complete each phase multiple times until the techniques feel automatic — repetition matters more than speed.

---

## Phase 1 — Docker Lab Fundamentals

**Goal:** Get comfortable with the lab environment before focusing on attack techniques.

**Tasks:**

- Run `make up` and `make verify` successfully.
- Read [docs/network-map.md](network-map.md) and draw the topology from memory.
- Read [docs/lab-credentials.md](lab-credentials.md) — understand where each credential lives and why.
- Browse all four target services manually using `curl` or a browser.
- Understand what each `make` target does without looking at the Makefile.

**OSCP skills:** Lab setup, tool verification, reading documentation before touching targets.

- Open `http://127.0.0.1:8090`, create a local Proctor account, and familiarize yourself with the scoring interface.

**Done when:** `make verify` passes clean and you can explain the network topology without notes.

---

## Phase 2 — First Full Attack Chain

**Goal:** Complete [scenarios/01-full-attack-chain/README.md](../scenarios/01-full-attack-chain/README.md) end-to-end using only the hints section (no walkthrough).

**Tasks:**

- Run through phases 1–7 of the scenario using only the hints.
- Capture all four flags.
- Document your findings in a plain text file as you go (practice report writing).
- Submit each flag to Proctor (`http://127.0.0.1:8090/submit`) as you discover it. Compare your score per run to track improvement.
- Reset the lab and repeat the chain from scratch without notes.
- On the second run, time yourself. Use `make proctor-reset` between timed runs to start with a fresh scoreboard.

**OSCP skills:**
- HTTP enumeration (robots.txt, hidden endpoints)
- OS command injection
- Server-side template injection
- Credential discovery from application responses
- Container-to-container lateral movement
- SSH access from discovered credentials
- Linux privilege escalation (sudo, SUID, cron)

**Done when:** You can complete the full chain in under 45 minutes with no references.

---

## Phase 3 — Linux Privilege Escalation Repetition

**Goal:** Master all three privesc paths on `forge-privesc` until they are automatic.

**Tasks:**

- SSH to `127.0.0.1:2222` as `labuser`.
- Escalate via each method independently:
  1. `sudo python3` — understand why this is dangerous (GTFOBins: `python`)
  2. SUID `find_lab` binary — understand SUID execution and `find -exec`
  3. World-writable cron job — understand the timing, write a payload, wait and verify
- For each method: explain aloud what the misconfiguration is and how you would fix it.
- Practice the enumeration steps: `sudo -l`, `find / -perm -4000`, `ls -la /etc/cron.d/`.

**OSCP skills:**
- Linux local enumeration
- Sudo misconfiguration exploitation
- SUID binary identification and abuse
- Cron job hijacking
- Post-exploitation: reading root files, understanding file permissions

**Done when:** You can identify all three vectors in under 5 minutes and escalate via any of them confidently.

---

## Phase 4 — Kubernetes Terrain Layer

**Goal:** Add Kubernetes enumeration to your toolkit using the optional kind cluster.

**Prerequisites:** Complete Phases 1–3. Install `kind` and `kubectl`.

**Tasks:**

- Run `make kind-up && make kind-load && kubectl apply -f kind/manifests/web.yaml`.
- Enumerate the cluster: pods, services, configmaps.
- Find the credentials stored in `forge-config` ConfigMap.
- Identify the permissive security context in the web pod.
- Access the web app at `http://127.0.0.1:30080` and repeat the web exploitation steps.
- Read [kind/README.md](../kind/README.md) and [scenarios/06-kubernetes/README.md](../scenarios/06-kubernetes/README.md).

**OSCP skills:**
- `kubectl` enumeration workflow
- Understanding how pod security contexts affect privilege
- Identifying credentials in cluster resources (ConfigMaps vs. Secrets)
- Comparing container behavior across Docker and Kubernetes

**Done when:** You can enumerate a kind cluster, identify misconfigurations, and explain what a ConfigMap is vs. a Secret.

---

## Phase 5 — Optional Hybrid VM Layer (future)

**Goal:** Add a traditional VM target to practice against a full OS rather than a container.

This phase is not yet implemented in ForgeRange v1. It is the natural next step after the container-only work:

- Import a VulnHub/OSCP-style VM into VirtualBox or UTM.
- Repeat the same enumeration and exploitation workflow against a full OS.
- Practice pivoting from the Docker lab to a VM on the same host-only network.

**OSCP skills:** Everything above, plus full-OS post-exploitation, shell stabilization, and multi-host pivoting.

---

## General Study Notes

- **Reset before every run.** `make reset && make verify` ensures a clean state and trains the habit.
- **Write notes as you go.** OSCP is an exam with a written report. Practice capturing findings, commands, and output at every step.
- **Explain techniques aloud.** If you cannot explain why a technique works, you do not yet understand it well enough to adapt it under pressure.
- **Repeat, not just progress.** Each phase should be repeated until automatic. Spending an extra day on Phase 2 is more valuable than rushing to Phase 4.
- **Use GTFOBins and PayloadsAllTheThings** for reference — but try from memory first.
