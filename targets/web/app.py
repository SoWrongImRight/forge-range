"""
Intentionally vulnerable web application for lab use only.
Do NOT deploy to any public or production environment.
"""

import os
import subprocess
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- Intentional misconfigurations for lab practice ---

INDEX = """
<!doctype html>
<title>forge-range :: web target</title>
<h1>Welcome to the forge-range web target</h1>
<p>This app is intentionally vulnerable. Use it only in the lab.</p>
<hr>
<h2>Ping utility</h2>
<form method="POST" action="/ping">
  <input name="host" placeholder="hostname or IP" size="30">
  <button type="submit">Ping</button>
</form>
<hr>
<h2>Greet</h2>
<form method="GET" action="/greet">
  <input name="name" placeholder="your name" size="30">
  <button type="submit">Greet</button>
</form>
"""


@app.route("/")
def index():
    return render_template_string(INDEX)


# Intentional command injection vector (lab only)
@app.route("/ping", methods=["POST"])
def ping():
    host = request.form.get("host", "")
    # INTENTIONAL VULN: unsanitised shell=True for lab OS command injection practice
    try:
        out = subprocess.check_output(
            f"ping -c 2 {host}", shell=True, stderr=subprocess.STDOUT, timeout=5
        )
        result = out.decode(errors="replace")
    except subprocess.CalledProcessError as e:
        result = e.output.decode(errors="replace")
    except Exception as e:
        result = str(e)
    return f"<pre>{result}</pre><a href='/'>back</a>"


# Intentional SSTI vector (lab only)
@app.route("/greet")
def greet():
    name = request.args.get("name", "stranger")
    # INTENTIONAL VULN: user input passed directly to render_template_string
    return render_template_string(f"<h1>Hello, {name}!</h1><a href='/'>back</a>")


@app.route("/robots.txt")
def robots():
    # Common enumeration finding
    return "User-agent: *\nDisallow: /admin\nDisallow: /backup\n", 200, {"Content-Type": "text/plain"}


@app.route("/backup")
def backup():
    # Exposed credential for lab discovery
    db_url = (
        f"postgres://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}"
        f"@{os.environ.get('DB_HOST')}/appdb"
    )
    return f"<pre># backup config\nDB_URL={db_url}\n</pre>"


@app.route("/admin")
def admin():
    # INTENTIONAL VULN: no authentication — simulates forgotten internal admin panel
    return """<!doctype html>
<title>forge-range :: admin</title>
<h1>Internal Service Registry</h1>
<p><em>This page is for internal use only. Authentication removed during migration — TODO: re-add auth</em></p>
<hr>
<h2>Services</h2>
<pre>
# Internal services — do not share
[web]
  host: forge-web
  port: 8080

[internal-api]
  host: forge-internal
  port: 9090
  token: internal_lab_secret_do_not_reuse

[database]
  host: forge-db
  port: 5432
  user: app
  pass: SuperSecret1!

[privesc-host]
  host: forge-privesc
  port: 22
  user: labuser
  pass: labpassword
  note: SSH backup access — credentials reused from svc_acct rotation
</pre>
"""


@app.route("/flag")
def flag():
    return os.environ.get("FLAG_01", "flag not set")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
