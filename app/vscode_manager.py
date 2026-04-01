"""Start per-user code-server containers on the Docker host (requires socket mount)."""

from __future__ import annotations

import logging
import os
import secrets
import string
import time
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from app.extensions import db
from app.models import User

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)

# Host that resolves to the Docker host from inside another container (see docker-compose extra_hosts).
_HOST_GATEWAY = os.environ.get("HOST_GATEWAY", "host.docker.internal")


def _client():
    import docker

    return docker.from_env()


def _container_name(user_id: int) -> str:
    return f"az1m0v-codeserver-{user_id}"


def next_free_port(app_config: dict) -> int:
    """Return the first unused host port in [VSCODE_PORT_MIN, VSCODE_PORT_MAX]."""
    port_min = app_config["VSCODE_PORT_MIN"]
    port_max = app_config["VSCODE_PORT_MAX"]
    used_rows = db.session.query(User.vscode_port).filter(User.vscode_port.isnot(None)).all()
    used = {r[0] for r in used_rows}
    for p in range(port_min, port_max + 1):
        if p not in used:
            return p
    raise RuntimeError("No free VS Code ports in configured range")


def _host_reachable_http(url: str, timeout: float = 3.0) -> bool:
    """True if something responds on the URL (IDE up or redirect to login)."""
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except urllib.error.HTTPError as e:
        return e.code in (200, 301, 302, 303, 307, 308, 401, 403)
    except (urllib.error.URLError, TimeoutError, OSError):
        return False
    except Exception:  # pragma: no cover - urllib edge cases
        log.debug("ide probe failed for %s", url, exc_info=True)
        return False


def wait_for_ide_on_host(port: int, timeout_sec: float = 60.0) -> bool:
    """
    Poll the published host port via HOST_GATEWAY (from inside the web container).
    Required because the browser is redirected before git clone + code-server finish.
    """
    url = f"http://{_HOST_GATEWAY}:{port}/"
    try:
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            if _host_reachable_http(url, timeout=2.0):
                return True
            time.sleep(0.75)
        return False
    except Exception:
        log.exception("wait_for_ide_on_host failed for %s", url)
        return False


def ensure_vscode_for_user(user: User, app_config: dict) -> tuple[int, str | None, str | None]:
    """
    Returns (host_port, error_message, ide_password).
    ide_password is the code-server login password when spawn succeeds (otherwise None).
    When ENABLE_VSCODE_SPAWN is false, only assigns port without starting Docker.
    """
    port = next_free_port(app_config)
    git_url = app_config["EV_REPO_GIT_URL"]

    if not app_config.get("ENABLE_VSCODE_SPAWN", True):
        user.vscode_port = port
        user.vscode_container_name = None
        return port, None, None

    name = _container_name(user.id)
    password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))

    try:
        client = _client()
    except Exception as e:  # pragma: no cover - environment specific
        log.exception("Docker client failed")
        return port, f"Docker unavailable: {e}", None

    try:
        old = client.containers.get(name)
        old.stop(timeout=5)
        old.remove()
    except Exception:
        pass

    shell_cmd = (
        f"rm -rf /tmp/az1m0v && git clone --depth 1 {git_url!s} /tmp/az1m0v "
        "&& exec /usr/bin/code-server --bind-addr 0.0.0.0:8080 --auth password /tmp/az1m0v"
    )
    try:
        container = client.containers.run(
            os.environ.get("CODE_SERVER_IMAGE", "codercom/code-server:latest"),
            name=name,
            detach=True,
            remove=False,
            ports={"8080/tcp": port},
            environment={"PASSWORD": password},
            entrypoint=["/bin/bash", "-lc"],
            command=[shell_cmd],
        )
    except Exception as e:
        log.exception("code-server start failed")
        return port, str(e), None

    try:
        container.reload()
    except Exception as e:
        log.exception("code-server reload failed")
        return port, f"Docker API error after start: {e}", None

    if container.status != "running":
        try:
            logs = container.logs(tail=80).decode("utf-8", errors="replace")
        except Exception as e:
            logs = f"(could not read logs: {e})"
        log.error("code-server container not running: %s", logs)
        return port, f"Container exited: {logs[-2000:]}", None

    user.vscode_port = port
    user.vscode_container_name = name

    if not wait_for_ide_on_host(port):
        try:
            logs = container.logs(tail=80).decode("utf-8", errors="replace")
        except Exception as e:
            logs = str(e)
        log.warning("code-server slow on port %s: %s", port, logs[-500:])
        return (
            port,
            "The IDE is still starting; wait a few seconds and open the link below (or refresh).",
            password,
        )

    return port, None, password
