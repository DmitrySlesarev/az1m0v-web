"""Start per-user code-server containers on the Docker host (requires socket mount)."""

from __future__ import annotations

import logging
import os
import secrets
import string
from typing import TYPE_CHECKING

from app.extensions import db
from app.models import User

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)


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


def ensure_vscode_for_user(user: User, app_config: dict) -> tuple[int, str | None]:
    """
    Returns (host_port, error_message).
    When ENABLE_VSCODE_SPAWN is false, only assigns port without starting Docker.
    """
    port = next_free_port(app_config)
    git_url = app_config["EV_REPO_GIT_URL"]

    if not app_config.get("ENABLE_VSCODE_SPAWN", True):
        user.vscode_port = port
        user.vscode_container_name = None
        return port, None

    name = _container_name(user.id)
    password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))

    try:
        client = _client()
    except Exception as e:  # pragma: no cover - environment specific
        log.exception("Docker client failed")
        return port, f"Docker unavailable: {e}"

    try:
        old = client.containers.get(name)
        old.stop(timeout=5)
        old.remove()
    except Exception:
        pass

    shell_cmd = (
        f"rm -rf /tmp/az1m0v && git clone --depth 1 {git_url!s} /tmp/az1m0v "
        "&& exec code-server --bind-addr 0.0.0.0:8080 --auth password /tmp/az1m0v"
    )
    try:
        client.containers.run(
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
        return port, str(e)

    user.vscode_port = port
    user.vscode_container_name = name
    return port, None
