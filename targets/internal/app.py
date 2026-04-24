"""
Internal service — reachable only after lateral movement.
Lab use only.
"""

import os
from flask import Flask, request, jsonify

app = Flask(__name__)

SECRET = os.environ.get("SECRET_KEY", "changeme")
FLAG = os.environ.get("FLAG_02", "flag not set")


@app.route("/")
def index():
    return jsonify({"service": "forge-range internal", "hint": "try /health and /secret"})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# Intentional broken auth — trivial bypass for lab practice
@app.route("/secret")
def secret():
    token = request.headers.get("X-Internal-Token", "")
    if token == SECRET or token == "lab-bypass":   # INTENTIONAL VULN
        return jsonify({"flag": FLAG, "secret_key": SECRET})
    return jsonify({"error": "forbidden"}), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090, debug=False)
