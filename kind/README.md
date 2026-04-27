# ForgeRange — Optional kind Kubernetes Layer (V2)

The `kind` layer adds a local Kubernetes cluster for **Scenario 02: Kubernetes Pivot**. It teaches OSCP-adjacent skills inside Kubernetes terrain: pod foothold, cluster-internal service discovery, and service account enumeration. It is **optional** — Scenario 01 runs entirely on Docker Compose and does not require kind.

---

## Architecture

```
[Attacker host / laptop]
      │
      ├─ HTTP:18080 ──────────► forge-k8s-web pod       (namespace: forge-k8s)
      │   command injection          │  FLAG{k8s_web_foothold}
      │                              │
      │                              ├─ HTTP:5000 (cluster DNS)
      │                              │   forge-k8s-internal.forge-k8s.svc.cluster.local
      │                              │   → FLAG{k8s_internal_service}
      │                              │
      │                              └─ HTTPS:443 (Kubernetes API)
      │                                  kubernetes.default.svc
      │                                  GET /api/v1/namespaces/forge-k8s/configmaps/forge-k8s-config
      │                                  → FLAG{k8s_service_account_discovery}
      │
      └─ (no direct route) ──── forge-k8s-internal (ClusterIP — host cannot reach directly)
```

| Component | Type | Exposure |
|-----------|------|----------|
| `forge-k8s-web` | NodePort 30180 → host:18080 | `127.0.0.1:18080` — loopback only |
| `forge-k8s-internal` | ClusterIP | Cluster-internal only — not reachable from host |
| `forge-k8s-config` ConfigMap | Cluster resource | Readable via mounted service account token |
| `forge-k8s-web-sa` ServiceAccount | Cluster resource | Mounted into web pod; limited RBAC (pods + configmaps in `forge-k8s`) |

---

## Prerequisites

- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) installed and on `PATH`
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed and on `PATH`
- Docker daemon running
- The Docker Compose lab does not need to be running — kind is independent

---

## Commands

### Bring up the V2 scenario

```bash
make kind-up
```

This single command:
1. Creates the `forge-range` kind cluster (if not already running) using `kind/cluster.yaml`
2. Builds the `forge-k8s-web` and `forge-k8s-internal` images from `targets/k8s-web/` and `targets/k8s-internal/`
3. Loads both images into the kind cluster's image store
4. Applies all manifests in order: namespace → rbac → configmap → web → internal-api
5. Waits for both deployments to become Ready
6. Prints the URL: `http://127.0.0.1:18080`

### Verify deployment

```bash
make kind-verify
```

Checks namespace, pods, services, and web health endpoint. Also useful after a restart to confirm the scenario is still running.

### Quick manual checks

```bash
kubectl get pods -n forge-k8s
kubectl get svc -n forge-k8s
kubectl get configmap forge-k8s-config -n forge-k8s -o yaml
curl -fsS http://127.0.0.1:18080/health
```

### Tear down the cluster

```bash
make kind-down
```

Deletes the cluster entirely. Run `make kind-up` to recreate from scratch.

### Full reset

```bash
make reset-kind    # destroy kind cluster
make kind-up       # recreate from scratch
```

---

## Manifests

| File | Contents |
|------|----------|
| `kind/manifests/namespace.yaml` | `forge-k8s` namespace |
| `kind/manifests/rbac.yaml` | ServiceAccount, Role (limited), RoleBinding |
| `kind/manifests/configmap.yaml` | `forge-k8s-config` — internal service URL + discovery flag |
| `kind/manifests/web.yaml` | `forge-k8s-web` Deployment + NodePort Service |
| `kind/manifests/internal-api.yaml` | `forge-k8s-internal` Deployment + ClusterIP Service |

---

## Safety Constraints

| Constraint | Implementation |
|------------|---------------|
| No privileged pods | `securityContext.privileged: false` on all containers |
| No hostNetwork | No `hostNetwork: true` in any pod spec |
| No Docker socket | No `/var/run/docker.sock` mounts |
| No hostPath mounts | No `hostPath` volumes in any manifest |
| No cluster-admin RBAC | `forge-k8s-reader` Role limited to `pods` + `configmaps` in `forge-k8s` namespace only |
| Loopback-only NodePort | `listenAddress: "127.0.0.1"` in `kind/cluster.yaml` extraPortMappings |
| Internal service not exposed to host | `forge-k8s-internal` uses `ClusterIP` type |
| Proctor not in attack path | Proctor runs in Docker Compose, separate from the kind cluster |

---

## Operator Pod — Internal Cluster Enumeration

To practice enumeration from inside the cluster (post-foothold simulation), launch an ephemeral netshoot pod:

```bash
kubectl run forge-operator \
  --image=nicolaka/netshoot \
  --restart=Never \
  -it --rm \
  -n forge-k8s \
  -- bash
```

The `--rm` flag deletes the pod on exit. There is no persistent pod left behind.

### Inside the operator pod

```bash
# DNS — verify cluster DNS for both services
nslookup forge-k8s-web.forge-k8s.svc.cluster.local
nslookup forge-k8s-internal.forge-k8s.svc.cluster.local

# HTTP — reach internal service (not reachable from host)
curl http://forge-k8s-internal.forge-k8s.svc.cluster.local:5000/health
curl http://forge-k8s-internal.forge-k8s.svc.cluster.local:5000/secret
```

The operator pod uses the default service account (no special RBAC). It does not have the same API access as the web pod's `forge-k8s-web-sa`. Use it for network enumeration, not API queries.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `make kind-up` fails at cluster creation | kind not installed or Docker not running | Install kind; run `docker info` to check daemon |
| `http://127.0.0.1:18080` unreachable | Pod not yet Ready, or cluster creation failed | Wait 30s and retry; check `kubectl get pods -n forge-k8s` |
| Image pull fails in pod | Image not loaded into kind | Re-run `make kind-up` — it rebuilds and reloads images |
| `kubectl: command not found` | kubectl not installed | Install kubectl |
| Port 18080 already in use | Another process using the port | `lsof -i :18080` to identify; kill or stop it |
| `kind cluster forge-range already exists` | Previous cluster still running | `make kind-down` first, or let kind-up skip creation |

---

## Reset Process

Clean reset for a fresh scenario run:

```bash
make reset-kind    # deletes the cluster and all state
make kind-up       # recreates cluster, builds images, deploys scenario
make kind-verify   # confirm clean state
```

The Docker Compose lab continues running independently. Resetting kind does not affect `forge-web`, `forge-internal`, `forge-db`, `forge-privesc`, `forge-proctor`, or `forge-operator`.

---

## Scenario

See [scenarios/02-kubernetes-pivot/README.md](../scenarios/02-kubernetes-pivot/README.md) for the full guided exercise.

Skills covered:
- Pod-level OS command injection
- `kubectl` enumeration: pods, services, configmaps, RBAC
- Cluster-internal DNS resolution
- Internal service discovery from a pod RCE foothold
- Locating the mounted service account token
- Kubernetes API queries using a bearer token and the pod's CA certificate
- Understanding ConfigMap vs. Secret security boundaries
