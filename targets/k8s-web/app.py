"""
ForgeRange V2 — Kubernetes Web target.
Intentionally vulnerable to OS command injection — authorized self-study only.
"""
import os
import subprocess

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

FLAG = os.environ.get("FLAG_K8S_01", "FLAG{k8s_web_foothold}")

_HOME = """<!doctype html>
<html>
<head><title>ForgeRange — Kubernetes Lab</title></head>
<body>
  <h1>ForgeRange Kubernetes Lab</h1>
  <p>Network diagnostic tool. Enter a hostname or IP to ping.</p>
  <form method="POST" action="/ping">
    <label>Host: <input name="host" type="text" value="127.0.0.1" size="40"></label>
    <button type="submit">Ping</button>
  </form>
  {% if output %}<pre>{{ output }}</pre>{% endif %}
  <hr>
  <small>Pod: {{ pod_name }} | Namespace: {{ namespace }}</small>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(
        _HOME,
        output=None,
        pod_name=os.environ.get("HOSTNAME", "unknown"),
        namespace=open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()
        if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
        else "unknown",
    )


@app.route("/ping", methods=["POST"])
def ping():
    host = request.form.get("host", "127.0.0.1")
    # INTENTIONAL VULN: shell=True with unsanitized user input — command injection
    result = subprocess.run(
        f"ping -c 2 {host}",
        shell=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    output = result.stdout + result.stderr
    return render_template_string(
        _HOME,
        output=output,
        pod_name=os.environ.get("HOSTNAME", "unknown"),
        namespace=open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()
        if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
        else "unknown",
    )


@app.route("/flag")
def flag():
    return jsonify({"flag": FLAG})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
