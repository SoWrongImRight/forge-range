# 06 — Kubernetes Security

**Objective:** Enumerate and exploit misconfigurations in the lab Kubernetes cluster.

## Prerequisites

```bash
make kind-up
kubectl apply -f kind/manifests/web.yaml
make kind-load
```

## Skills practiced

- kubectl enumeration
- ConfigMap credential exposure
- Overly permissive pod security contexts
- Container escape concepts

## Steps

1. Enumerate the cluster:
   ```bash
   kubectl get all -A
   kubectl get configmaps -o yaml
   kubectl get pods -o yaml | grep -i env -A3
   ```

2. Find credentials in ConfigMap:
   ```bash
   kubectl get configmap forge-config -o jsonpath='{.data}'
   ```

3. Exec into a running pod:
   ```bash
   kubectl exec -it deploy/forge-web -- /bin/sh
   # Check for mounted secrets, env vars, service account tokens
   cat /var/run/secrets/kubernetes.io/serviceaccount/token
   env
   ```

4. Note the permissive security context (`allowPrivilegeEscalation: true`).

## Defensive notes

- Never put passwords in ConfigMaps; use Kubernetes Secrets or an external vault
- Set `allowPrivilegeEscalation: false` and `runAsNonRoot: true` in security contexts
- Apply NetworkPolicies to restrict pod-to-pod communication
- Use RBAC to limit what service accounts can do
