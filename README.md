# az1m0v-web

Public web front for **https://www.az1m0v.com**: a Flask application in Docker, PostgreSQL for accounts, OpenResty as the reverse proxy for the main site on port 80, and **per-user [code-server](https://github.com/coder/code-server)** (VS Code in the browser) on **dedicated host ports** after registration. Each IDE container clones the EV project from GitHub (HTTPS by default; see below for SSH).

## Architecture

| Traffic | Behaviour |
|--------|------------|
| `http://host/` (port **80**) | OpenResty proxies to Gunicorn/Flask: landing page, **`/login`**, **`/register`**, **`/workspace`** (session required). |
| After sign-up | A **confirmation page** on this site shows the IDE URL, the **one-time code-server password**, and a button to open VS Code in the browser. The server waits until the new container answers on the host port (via `host.docker.internal` from the `web` container) so you are not sent to a dead page while `git clone` runs. |
| Host port **`WEB_HOST_PORT`** (default **5001**) | Direct access to the Flask app for debugging; maps to container port 5000. Default is not 5000 so it does not collide with other stacks (e.g. az1m0v dashboard) using 5000. Set `WEB_HOST_PORT=5000` in `.env` if that port is free. |

The `web` container mounts **`/var/run/docker.sock`** so it can start sibling `codercom/code-server` containers that publish ports on the **host** (Docker maps `hostPort:8080` inside the IDE container). **Port selection** merges PostgreSQL with **live Docker bindings** in your configured range, and retries if the daemon reports “port is already allocated”, so a leftover IDE container does not steal the same numeric port from the next signup.

Data stored in PostgreSQL: user email, password hash, assigned `vscode_port`, optional `vscode_container_name`.

### Accounts (login)

- **Register** (`/register`) creates the user and opens a **signed cookie session** (`user_id`), same as after a normal login.
- **Log in** (`/login`) uses email + password (hashed with Werkzeug). After success you are sent to **`/workspace`** (or a safe relative `?next=` path only — open redirects are blocked).
- **Workspace** (`/workspace`) shows your browser IDE URL for your assigned host port. The **code-server password** is only shown once on the post-registration page; we do not store it in the database.
- **Log out** — `POST /logout` (header button). Session lifetime defaults to **14 days** for “remember me” style persistence (`session.permanent`).

For HTTPS deployments, set **`SESSION_COOKIE_SECURE=1`** in the environment so browsers only send the session cookie over TLS.

## Prerequisites

- Docker and Docker Compose v2
- For local IDE spawn: the host must allow the `web` service to talk to the Docker API (socket mount is already in Compose)

## Quick start (Docker Compose)

```bash
cd az1m0v-web
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, SECRET_KEY, and optionally VSCODE_PUBLIC_HOST

docker compose up --build -d
```

- Main site (via OpenResty): **http://localhost/**  
- Flask directly: **http://localhost:5001/** (or `${WEB_HOST_PORT}` if you set it)  
- Health check: **http://localhost/health** (JSON `{"status":"ok"}`)

Register at **http://localhost/register**. You get a page with **Open VS Code in the browser** (first free port in range, often **9000**) and the **login password** for code-server. If anything fails, check `docker logs az1m0v-codeserver-<user_id>`.

### Environment variables

See `.env.example`. Important:

| Variable | Purpose |
|----------|---------|
| `VSCODE_PUBLIC_HOST` | Optional. If unset, the IDE link uses the same **Host** / `X-Forwarded-Host` as the browser (recommended behind OpenResty). Set for fixed production URLs (e.g. `www.az1m0v.com`). |
| `VSCODE_PUBLIC_SCHEME` | Optional. If unset, uses `X-Forwarded-Proto` or the request scheme. |
| `HOST_GATEWAY` | Hostname the `web` container uses to reach **host-published** IDE ports (default `host.docker.internal`, wired in Compose via `extra_hosts`). |
| `VSCODE_PORT_MIN` / `VSCODE_PORT_MAX` | Inclusive range of **host** ports for code-server; must be open in the firewall. |
| `EV_REPO_GIT_URL` | Default `https://github.com/DmitrySlesarev/az1m0v.git` (public clone). |
| `ENABLE_VSCODE_SPAWN` | Set `0` to disable Docker API and only assign ports in DB (e.g. tests). |
| `SESSION_COOKIE_SECURE` | Set to `1` when the site is HTTPS-only so the session cookie is not sent over plain HTTP. |

**SSH URL (`git@github.com:...`)**: the stock image clones over HTTPS. To use SSH, provide a custom image or extend `codercom/code-server` with a deploy key and change the clone command in `app/vscode_manager.py`, or mount `~/.ssh` (not recommended for production without hardening).

## Local development (without full stack)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

export DATABASE_URL=postgresql://az1m0v:az1m0v@localhost:5432/az1m0v_web
export ENABLE_VSCODE_SPAWN=0
# Start PostgreSQL locally or: docker run -d --name pg -p 5432:5432 -e POSTGRES_PASSWORD=az1m0v -e POSTGRES_USER=az1m0v -e POSTGRES_DB=az1m0v_web postgres:16-alpine

python -c "from app import create_app; create_app().app_context().push()"  # optional: use flask shell to init
# Or run:
gunicorn --bind 127.0.0.1:5000 wsgi:application
```

For a quick DB-free smoke test you can point `SQLALCHEMY_DATABASE_URI` to `sqlite:////tmp/az1m0v.db` by patching `create_app` locally; production is intended for PostgreSQL only.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests use SQLite in-memory, `ENABLE_VSCODE_SPAWN=0`, and do not require Docker.

## Production / remote hosting

1. **Server**: Linux VM or bare metal with Docker, ports **80** (and **443** if you terminate TLS) open; open the **VS Code port range** (e.g. 9000–9100) in the firewall and security groups.
2. **Secrets**: set strong `POSTGRES_PASSWORD` and `SECRET_KEY` in `.env` or your orchestrator’s secret store.
3. **DNS**: point `www.az1m0v.com` (and apex if needed) to the server IP.
4. **TLS**: Option A — terminate HTTPS on a host reverse proxy (e.g. Caddy or another nginx) in front of OpenResty on 80. Option B — extend the OpenResty config with `listen 443 ssl` and certificates (Let’s Encrypt). Set `VSCODE_PUBLIC_SCHEME=https` and `VSCODE_PUBLIC_HOST=www.az1m0v.com`.
5. **HTTPS on high ports**: browsers will warn on `https://host:9000` unless you serve TLS on those ports or use a path-based proxy; the common pattern here is **HTTP** on dedicated IDE ports behind a VPN or **TLS with a wildcard cert** on the same host. Document your network policy accordingly.
6. **Docker socket**: granting the `web` container access to the socket is powerful — restrict host access, keep images updated, and consider a dedicated VM per environment.

## Repository layout

```
az1m0v-web/
├── app/                 # Flask app (routes, models, auth helpers, templates, static)
├── openresty/nginx.conf # Reverse proxy for port 80 → web:5000
├── docker-compose.yml
├── Dockerfile
├── wsgi.py
├── requirements.txt
└── tests/
```

## Licence

Add your licence file to match the main az1m0v project if desired.
