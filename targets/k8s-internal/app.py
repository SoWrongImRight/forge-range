"""
ForgeRange V2 — Kubernetes internal API target.
Returns the internal service flag. No authentication — intentional for lab.
"""
import os

from flask import Flask, jsonify

app = Flask(__name__)

FLAG = os.environ.get("FLAG_K8S_02", "FLAG{k8s_internal_service}")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/secret")
def secret():
    # INTENTIONAL: unauthenticated endpoint returns a flag — missing access control
    return jsonify({"flag": FLAG, "service": "forge-k8s-internal"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
