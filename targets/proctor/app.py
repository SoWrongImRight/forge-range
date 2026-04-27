"""
ForgeRange Proctor — local-only scoring and progress tracking.
Not a vulnerable service. Do not target it in scenarios.
"""
from contextlib import asynccontextmanager
import hashlib
import os
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

DB_PATH = os.environ.get("PROCTOR_DB_PATH", "/data/proctor.db")
SESSION_SECRET = os.environ.get("PROCTOR_SESSION_SECRET", "forge-range-local-proctor-secret-change-me")

_FLAG_SEEDS = [
    # V1 — Docker Compose scenario (Scenario 01: Full Attack Chain)
    ("FLAG{enum_the_web}", "Enumeration Flag", "forge-web", "Stage 0 / Enumeration", 10),
    ("FLAG{lateral_move_success}", "Internal API Flag", "forge-internal", "Stage 3 / Lateral Movement", 25),
    ("FLAG{db_creds_found}", "Database Flag", "forge-db", "Stage 3 / Lateral Movement", 25),
    ("FLAG{root_privesc_complete}", "Root Privilege Escalation Flag", "forge-privesc", "Stage 4 / Privilege Escalation", 40),
    # V2 — Kubernetes Pivot scenario (Scenario 02; optional — requires make kind-up)
    ("FLAG{k8s_web_foothold}", "Kubernetes Web Foothold", "forge-k8s-web", "V2 / Pod Foothold", 20),
    ("FLAG{k8s_internal_service}", "Kubernetes Internal Service", "forge-k8s-internal", "V2 / Service Discovery", 30),
    ("FLAG{k8s_service_account_discovery}", "Kubernetes Service Account Discovery", "forge-k8s-web", "V2 / Service Account Discovery", 30),
]

_FALSE_FLAG_SEEDS = [
    ("FLAG{admin_panel_owned}", "Admin Panel Decoy", "Decoy admin panel flag", 0),
    ("FLAG{docker_socket_escape}", "Container Escape Decoy", "Decoy container escape flag", 0),
    ("FLAG{ssh_banner_flag}", "SSH Banner Decoy", "Decoy SSH banner flag", 0),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(value: str) -> str:
    return hashlib.sha256(value.strip().encode()).hexdigest()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000).hex()


def _preview(value: str) -> str:
    v = value.strip()
    return (v[:8] + "...") if len(v) > 8 else (v + "...")


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            salt          TEXT    NOT NULL,
            created_at    TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS flags (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            code_hash  TEXT    NOT NULL UNIQUE,
            label      TEXT    NOT NULL,
            target     TEXT    NOT NULL,
            stage      TEXT    NOT NULL,
            points     INTEGER NOT NULL,
            is_active  INTEGER NOT NULL DEFAULT 1,
            created_at TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS false_flags (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            code_hash      TEXT    NOT NULL UNIQUE,
            label          TEXT    NOT NULL,
            reason         TEXT    NOT NULL,
            penalty_points INTEGER NOT NULL DEFAULT 0,
            created_at     TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS submissions (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                INTEGER NOT NULL REFERENCES users(id),
            submitted_value_hash   TEXT    NOT NULL,
            submitted_value_preview TEXT   NOT NULL,
            status                 TEXT    NOT NULL,
            points_awarded         INTEGER NOT NULL DEFAULT 0,
            flag_id                INTEGER REFERENCES flags(id),
            false_flag_id          INTEGER REFERENCES false_flags(id),
            created_at             TEXT    NOT NULL
        );
    """)
    now = datetime.utcnow().isoformat()
    for code, label, target, stage, points in _FLAG_SEEDS:
        conn.execute(
            "INSERT OR IGNORE INTO flags (code_hash,label,target,stage,points,is_active,created_at) VALUES(?,?,?,?,?,1,?)",
            (_hash(code), label, target, stage, points, now),
        )
    for code, label, reason, penalty in _FALSE_FLAG_SEEDS:
        conn.execute(
            "INSERT OR IGNORE INTO false_flags (code_hash,label,reason,penalty_points,created_at) VALUES(?,?,?,?,?)",
            (_hash(code), label, reason, penalty, now),
        )
    conn.commit()
    conn.close()


# ── App setup ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(_app: FastAPI):
    _init_db()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, max_age=86400)

templates = Jinja2Templates(directory="templates")
templates.env.autoescape = True


# ── Session helpers ───────────────────────────────────────────────────────────

def _uid(request: Request):
    return request.session.get("user_id")


def _flash(request: Request, msg: str, cat: str = "info") -> None:
    msgs = request.session.get("_flash", [])
    msgs.append({"msg": msg, "cat": cat})
    request.session["_flash"] = msgs


def _ctx(request: Request, **kw):
    flashes = request.session.pop("_flash", [])
    return {"request": request, "user_id": _uid(request), "flashes": flashes, **kw}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})


@app.get("/")
def index(request: Request):
    if _uid(request):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(request, "index.html", _ctx(request))


@app.get("/register")
def register_get(request: Request):
    if _uid(request):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(request, "register.html", _ctx(request))


@app.post("/register")
def register_post(request: Request, username: str = Form(...), password: str = Form(...)):
    username = username.strip()
    if not username or len(username) > 32:
        _flash(request, "Username must be 1–32 characters.", "error")
        return templates.TemplateResponse(request, "register.html", _ctx(request), status_code=400)
    if not password:
        _flash(request, "Password is required.", "error")
        return templates.TemplateResponse(request, "register.html", _ctx(request), status_code=400)
    salt = secrets.token_hex(16)
    pw_hash = _hash_password(password, salt)
    now = datetime.utcnow().isoformat()
    conn = _get_db()
    try:
        conn.execute(
            "INSERT INTO users (username,password_hash,salt,created_at) VALUES(?,?,?,?)",
            (username, pw_hash, salt, now),
        )
        conn.commit()
        row = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        request.session["user_id"] = row["id"]
        request.session["username"] = username
        return RedirectResponse("/dashboard", status_code=303)
    except sqlite3.IntegrityError:
        _flash(request, "Username already taken.", "error")
        return templates.TemplateResponse(request, "register.html", _ctx(request), status_code=400)
    finally:
        conn.close()


@app.get("/login")
def login_get(request: Request):
    if _uid(request):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(request, "login.html", _ctx(request))


@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    username = username.strip()
    conn = _get_db()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    if not row or _hash_password(password, row["salt"]) != row["password_hash"]:
        _flash(request, "Invalid username or password.", "error")
        return templates.TemplateResponse(request, "login.html", _ctx(request), status_code=401)
    request.session["user_id"] = row["id"]
    request.session["username"] = row["username"]
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/dashboard")
def dashboard(request: Request):
    uid = _uid(request)
    if not uid:
        return RedirectResponse("/login", status_code=302)
    conn = _get_db()
    user = conn.execute("SELECT username FROM users WHERE id=?", (uid,)).fetchone()
    total_score = conn.execute(
        "SELECT COALESCE(SUM(points_awarded),0) AS s FROM submissions WHERE user_id=? AND status='valid'",
        (uid,),
    ).fetchone()["s"]
    max_score = conn.execute(
        "SELECT COALESCE(SUM(points),0) AS s FROM flags WHERE is_active=1"
    ).fetchone()["s"]
    all_flags = conn.execute(
        "SELECT * FROM flags WHERE is_active=1 ORDER BY points"
    ).fetchall()
    solved_ids = {
        r["flag_id"]
        for r in conn.execute(
            "SELECT flag_id FROM submissions WHERE user_id=? AND status='valid'", (uid,)
        ).fetchall()
    }
    recent = conn.execute(
        "SELECT * FROM submissions WHERE user_id=? ORDER BY created_at DESC LIMIT 10",
        (uid,),
    ).fetchall()
    conn.close()
    flags_ctx = [
        {
            "label": f["label"],
            "target": f["target"],
            "stage": f["stage"],
            "points": f["points"],
            "solved": f["id"] in solved_ids,
        }
        for f in all_flags
    ]
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        _ctx(
            request,
            username=user["username"],
            total_score=total_score,
            max_score=max_score,
            flags=flags_ctx,
            recent=list(recent),
        ),
    )


@app.get("/submit")
def submit_get(request: Request):
    if not _uid(request):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request, "submit.html", _ctx(request))


@app.post("/submit")
def submit_post(request: Request, flag_value: str = Form(...)):
    uid = _uid(request)
    if not uid:
        return RedirectResponse("/login", status_code=302)
    normalized = flag_value.strip()
    if not normalized:
        _flash(request, "Flag value cannot be empty.", "error")
        return templates.TemplateResponse(request, "submit.html", _ctx(request), status_code=400)
    value_hash = _hash(normalized)
    preview = _preview(normalized)
    now = datetime.utcnow().isoformat()
    conn = _get_db()
    flag_row = conn.execute(
        "SELECT * FROM flags WHERE code_hash=? AND is_active=1", (value_hash,)
    ).fetchone()
    if flag_row:
        dup = conn.execute(
            "SELECT id FROM submissions WHERE user_id=? AND flag_id=? AND status='valid'",
            (uid, flag_row["id"]),
        ).fetchone()
        if dup:
            status, points, flag_id, ff_id = "duplicate_valid", 0, flag_row["id"], None
            msg, cat = f"Already solved: {flag_row['label']}. No additional points.", "warn"
        else:
            status, points, flag_id, ff_id = "valid", flag_row["points"], flag_row["id"], None
            msg, cat = f"Correct! {flag_row['label']} — {points} points.", "success"
    else:
        ff_row = conn.execute(
            "SELECT * FROM false_flags WHERE code_hash=?", (value_hash,)
        ).fetchone()
        if ff_row:
            status, points, flag_id, ff_id = "false_flag", 0, None, ff_row["id"]
            msg, cat = f"Decoy flag detected ({ff_row['label']}). No points awarded.", "warn"
        else:
            status, points, flag_id, ff_id = "invalid", 0, None, None
            msg, cat = "Invalid flag. Not recognized.", "error"
    conn.execute(
        """INSERT INTO submissions
           (user_id,submitted_value_hash,submitted_value_preview,status,points_awarded,flag_id,false_flag_id,created_at)
           VALUES(?,?,?,?,?,?,?,?)""",
        (uid, value_hash, preview, status, points, flag_id, ff_id, now),
    )
    conn.commit()
    conn.close()
    _flash(request, msg, cat)
    return RedirectResponse("/dashboard", status_code=303)
