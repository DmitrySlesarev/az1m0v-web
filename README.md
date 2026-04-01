# az1m0v-web

Public web front for **https://www.az1m0v.com**: a Flask application in Docker, PostgreSQL for accounts, OpenResty as the reverse proxy for the main site on port 80, and **per-user [code-server](https://github.com/coder/code-server)** (VS Code in the browser) on **dedicated host ports** after registration. Each IDE container clones the EV project from GitHub (HTTPS by default; see below for SSH).

## Architecture

| Traffic | Behaviour |
|--------|------------|
| `http://host/` (port **80**) | OpenResty proxies to Gunicorn/Flask: landing page (crowdfunding-style copy summarising the az1m0v EV platform) and `/register`. |
| After sign-up | Browser **HTTP redirect** to `{VSCODE_PUBLIC_SCHEME}://{VSCODE_PUBLIC_HOST}:{port}/` — the user’s personal code-server on a **published host port** in `[VSCODE_PORT_MIN, VSCODE_PORT_MAX]`. |
| Port **5000** | Direct access to the Flask app (useful for debugging); in `docker-compose.yml` the `web` service publishes `5000:5000`. |

The `web` container mounts **`/var/run/docker.sock`** so it can start sibling `codercom/code-server` containers that publish ports on the **host** (Docker maps `hostPort:8080` inside the IDE container).

Data stored in PostgreSQL: user email, password hash, assigned `vscode_port`, optional `vscode_container_name`.

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
- Flask directly: **http://localhost:5000/**  
- Health check: **http://localhost/health** (JSON `{"status":"ok"}`)

Register at **http://localhost/register**. You are redirected to **http://localhost:9000/** (first free port in range) with a random code-server password set in the container environment (see logs: `docker logs az1m0v-codeserver-<id>`).

### Environment variables

See `.env.example`. Important:

| Variable | Purpose |
|----------|---------|
| `VSCODE_PUBLIC_HOST` | Hostname used in the redirect URL (e.g. `www.az1m0v.com`). |
| `VSCODE_PUBLIC_SCHEME` | `http` or `https` for that redirect. |
| `VSCODE_PORT_MIN` / `VSCODE_PORT_MAX` | Inclusive range of **host** ports for code-server; must be open in the firewall. |
| `EV_REPO_GIT_URL` | Default `https://github.com/DmitrySlesarev/az1m0v.git` (public clone). |
| `ENABLE_VSCODE_SPAWN` | Set `0` to disable Docker API and only assign ports in DB (e.g. tests). |

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
├── app/                 # Flask app (templates, static, routes, models)
├── openresty/nginx.conf # Reverse proxy for port 80 → web:5000
├── docker-compose.yml
├── Dockerfile
├── wsgi.py
├── requirements.txt
└── tests/
```

## Licence

Add your licence file to match the main az1m0v project if desired.
