-- Lab database seed — intentionally misconfigured for practice
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,   -- stored in plaintext for lab realism
    role TEXT DEFAULT 'user'
);

INSERT INTO users (username, password, role) VALUES
    ('admin',  'admin123',      'admin'),
    ('alice',  'password1',     'user'),
    ('bob',    'letmein',       'user'),
    ('svc_acct','Serv1ce!Pass', 'service');

CREATE TABLE IF NOT EXISTS flags (
    id SERIAL PRIMARY KEY,
    name TEXT,
    value TEXT
);

INSERT INTO flags (name, value) VALUES
    ('db_flag', 'FLAG{db_creds_found}');
