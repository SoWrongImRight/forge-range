# ForgeRange — Optional kind Kubernetes Layer

The `kind` layer adds a local Kubernetes cluster so you can practice container and cluster enumeration skills alongside the Docker Compose targets. It is **optional** — the first full attack chain scenario runs entirely on Docker Compose and does not require kind.

---

## Purpose

- Practice `kubectl` enumeration and pod inspection.
- Find credentials intentionally stored in a ConfigMap (real-world anti-pattern).
- Explore a deliberately permissive pod security context.
- Understand how Kubernetes manifests map to the same vulnerable services you exploited in Docker Compose.

OSCP context: OSCP does not currently include Kubernetes targets, but container enumeration skills transfer directly. Understanding how pods expose ports, how secrets land in environment variables, and how security contexts affect privilege is increasingly relevant for post-OSCP and real engagements.

---

## Prerequisites

- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) installed and on `PATH`
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed and on `PATH`
- Docker daemon running
- The Docker Compose lab images already built (`make up` at least once, or `make reset-docker`)

---

## Commands

### Bring up the cluster

```bash
make kind-up
```

This creates a `kind` cluster named `forge-range` with:
- One control-plane node with NodePort `30080` mapped to `127.0.0.1:30080`
- Two worker nodes

### Load lab images into kind

Before deploying the web manifest, load the local Docker image into kind's image store:

```bash
make kind-load
```

### Deploy the vulnerable web manifest

```bash
kubectl apply -f kind/manifests/web.yaml
```

This deploys:
- A `forge-web` Deployment with intentionally permissive security context (`allowPrivilegeEscalation: true`, `runAsNonRoot: false`)
- A NodePort Service exposing port `30080` on `127.0.0.1`
- A ConfigMap (`forge-config`) with credentials stored as plaintext — an intentional anti-pattern for practice

### Verify deployment

```bash
kubectl get pods -A
kubectl get svc
kubectl get configmap forge-config -o yaml
```

The web app will be reachable at `http://127.0.0.1:30080` once the pod is Running.

### Tear down the cluster

```bash
make kind-down
```

This deletes the cluster entirely. Run `make kind-up` again to recreate it from scratch.

---

## Network Topology

| Exposure | Bind | Notes |
|----------|------|-------|
| `127.0.0.1:30080` | NodePort on control-plane | Loopback only; mapped in `kind/cluster.yaml` |
| All other cluster traffic | cluster-internal | Not exposed to host |

---

## Scenario 06 — Kubernetes Enumeration

See [scenarios/06-kubernetes/README.md](../scenarios/06-kubernetes/README.md) for the guided exercise using this cluster.

Skills covered:
- `kubectl get` enumeration (pods, services, configmaps, secrets)
- Finding credentials in ConfigMaps
- Inspecting pod security context for privilege escalation paths
- Comparing cluster-internal vs. host-exposed ports

---

## Cleanup

To reset the kind cluster to a clean state:

```bash
make kind-down
make kind-up
make kind-load
kubectl apply -f kind/manifests/web.yaml
```

To remove kind entirely (does not affect Docker Compose lab):

```bash
make kind-down
```

The Docker Compose lab continues running independently of the kind cluster state.
