# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""
AgentRT Airymax: Market Client

Python client for communicating with the market_d daemon via JSON-RPC 2.0
over Unix domain socket (default) or TCP.

Endpoints mirror market_d RPC methods:
  - register_agent   → register an agent
  - search_agents    → search agents
  - install_agent    → install an agent
  - uninstall_agent  → uninstall an agent
  - register_skill   → register a skill
  - search_skills    → search skills
  - uninstall_skill  → uninstall a skill
  - check_update     → check for a newer version
  - sync_registry    → sync with the remote registry
  - health_check     → daemon health probe

Protocol: JSON-RPC 2.0 over Unix socket or TCP.
See market_service.h and market_d/src/main.c for the C-side definitions.
"""

from __future__ import annotations

import json
import logging
import os
import socket
import struct
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from .errors import (
    MarketConnectionError,
    MarketError,
    MarketNotFoundError,
    market_error_from_code,
)
from .models import (
    AgentInfo,
    InstallRequest,
    InstallResult,
    SearchParams,
    SkillInfo,
)

# Default socket path matching market_d DEFAULT_SOCKET_PATH_UNIX
_DEFAULT_SOCKET_PATH = "/var/run/agentrt/market.sock"


def _resolve_default_socket_path() -> str:
    """优先从 $AIRY_RUNTIME_DIR / $AIRY_HOME 推导 socket 路径，回退硬编码的默认值。

    与 agentrt-env.sh 的路径铁律一致：AIRY_RUNTIME_DIR 默认 $AIRY_HOME/run。
    """
    runtime = os.environ.get("AIRY_RUNTIME_DIR")
    if runtime:
        return str(Path(runtime) / "market.sock")
    airy_home = os.environ.get("AIRY_HOME")
    if airy_home:
        return str(Path(airy_home) / "run" / "market.sock")
    return _DEFAULT_SOCKET_PATH

_DEFAULT_TCP_HOST = "127.0.0.1"
_DEFAULT_TCP_PORT = 2034  # AIRY_PORT_MARKET_D（SSoT airy_defaults.h）
_DEFAULT_TIMEOUT = 10.0
_MAX_BUFFER = 65536


class MarketClient:
    """JSON-RPC 2.0 client for market_d daemon.

    Communicates with market_d via Unix domain socket (default) or TCP.
    All public methods are synchronous and thread-safe (each call opens
    a new connection).

    Usage:
        client = MarketClient()
        agents = client.search_agents(SearchParams(query="code-review"))
        result = client.install_agent(InstallRequest(id="architect-agent"))
    """

    def __init__(
        self,
        socket_path: Optional[str] = None,
        use_tcp: bool = False,
        tcp_host: str = _DEFAULT_TCP_HOST,
        tcp_port: int = _DEFAULT_TCP_PORT,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        """Initialize market client.

        Args:
            socket_path: Path to Unix domain socket. Defaults to
                         $AIRY_RUNTIME_DIR/market.sock (fallback /var/run/agentrt/market.sock).
            use_tcp: If True, connect via TCP instead of Unix socket.
            tcp_host: TCP host address (only used if use_tcp=True).
            tcp_port: TCP port (only used if use_tcp=True).
            timeout: Connection and read timeout in seconds.
        """
        self._socket_path = socket_path or _resolve_default_socket_path()
        self._use_tcp = use_tcp
        self._tcp_host = tcp_host
        self._tcp_port = tcp_port
        self._timeout = timeout
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _create_connection(self) -> socket.socket:
        """Create a new connection to market_d."""
        try:
            if self._use_tcp:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self._timeout)
                sock.connect((self._tcp_host, self._tcp_port))
            else:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(self._timeout)
                sock.connect(self._socket_path)
            return sock
        except FileNotFoundError:
            raise MarketConnectionError(
                f"market_d socket not found at {self._socket_path}. "
                "Is market_d daemon running?"
            )
        except ConnectionRefusedError:
            raise MarketConnectionError(
                f"market_d refused connection. Is market_d daemon running?"
            )
        except OSError as e:
            raise MarketConnectionError(
                f"Failed to connect to market_d: {e}"
            )

    def _call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a JSON-RPC call to market_d.

        Args:
            method: RPC method name (e.g., "register_agent").
            params: Method parameters as a dict.

        Returns:
            The 'result' field from the JSON-RPC response.

        Raises:
            MarketConnectionError: On connection failure.
            MarketError: On RPC-level or daemon-level errors.
        """
        request_id = self._next_id()
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": request_id,
        }
        request_bytes = json.dumps(request).encode("utf-8")

        sock = None
        try:
            sock = self._create_connection()
            sock.sendall(request_bytes)

            # Read response with framing (market_d sends raw JSON, no header)
            chunks: List[bytes] = []
            while True:
                try:
                    chunk = sock.recv(_MAX_BUFFER)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    # Try to parse JSON to detect completeness
                    try:
                        json.loads(b"".join(chunks).decode("utf-8"))
                        break
                    except json.JSONDecodeError:
                        # Incomplete JSON, continue reading
                        continue
                except socket.timeout:
                    break

            if not chunks:
                raise MarketConnectionError(
                    f"No response from market_d for method '{method}'"
                )

            response_data = json.loads(b"".join(chunks).decode("utf-8"))

            # Check for JSON-RPC error
            if "error" in response_data:
                error = response_data["error"]
                error_code = error.get("code", -1)
                error_message = error.get("message", "Unknown error")
                raise market_error_from_code(
                    code=error_code,
                    message=f"{method}: {error_message}",
                    details=json.dumps(error) if error else "",
                )

            # Check for successful result
            if "result" in response_data:
                return response_data["result"]

            raise MarketError(
                f"Unexpected response format from market_d for '{method}'",
                details=json.dumps(response_data) if response_data else "",
            )

        except (MarketError, MarketConnectionError):
            raise
        except Exception as e:
            raise MarketConnectionError(
                f"Communication error with market_d ({method}): {e}"
            )
        finally:
            if sock:
                try:
                    sock.close()
                except OSError:
                    logger.debug("Failed to close market_d socket", exc_info=True)

    # ── Agent Operations ──

    def register_agent(self, agent: AgentInfo) -> bool:
        """Register a new agent in the market.

        Corresponds to market_service_register_agent() in market_service.h
        and handle_register_agent() in main.c.

        Args:
            agent: AgentInfo with registration details.

        Returns:
            True if registration succeeded.

        Raises:
            MarketValidationError: Missing required fields.
            MarketAlreadyExistsError: Agent with same ID already registered.
            MarketConnectionError: Daemon not accessible.
        """
        if not agent.agent_id:
            raise market_error_from_code(
                -32602,
                message="agent_id is required for registration",
            )

        params = {"agent": agent.to_json()}
        result = self._call("register_agent", params)

        if isinstance(result, dict) and result.get("status") == "registered":
            return True
        return False

    def search_agents(self, params: Optional[SearchParams] = None) -> List[AgentInfo]:
        """Search for agents matching the given criteria.

        Corresponds to market_service_search_agents() in market_service.h
        and handle_search_agents() in main.c.

        Args:
            params: Search criteria (keyword, limit, offset, etc.).

        Returns:
            List of matching AgentInfo objects.

        Raises:
            MarketConnectionError: Daemon not accessible.
        """
        search_params = params or SearchParams()
        result = self._call("search_agents", search_params.to_json())

        if isinstance(result, list):
            return [AgentInfo.from_json(item) for item in result]
        return []

    def install_agent(self, request: InstallRequest) -> InstallResult:
        """Install an agent from the market.

        Corresponds to market_service_install_agent() in market_service.h
        and handle_install_agent() in main.c.

        Args:
            request: InstallRequest with agent_id and optional version.

        Returns:
            InstallResult with installation details.

        Raises:
            MarketValidationError: Invalid agent_id.
            MarketNotFoundError: Agent not found in registry.
            MarketInstallError: Installation failed.
            MarketConnectionError: Daemon not accessible.
        """
        if not request.id:
            raise market_error_from_code(
                -32602,
                message="agent_id is required for installation",
            )

        result = self._call("install_agent", request.to_json())

        if isinstance(result, dict):
            return InstallResult(
                success=result.get("status") == "installed",
                message=result.get("message", ""),
                installed_version=result.get("installed_version", ""),
                install_path=result.get("install_path", ""),
                error_code=result.get("error_code", 0),
            )
        return InstallResult(success=False, message="Unexpected response format")

    def uninstall_agent(self, agent_id: str) -> bool:
        """Uninstall an agent from the market.

        Corresponds to market_service_uninstall_agent() in market_service.h
        and handle_uninstall_agent() in market_rpc.c.

        Args:
            agent_id: ID of the agent to uninstall.

        Returns:
            True if the agent was uninstalled.

        Raises:
            MarketValidationError: Missing agent_id.
            MarketNotFoundError: Agent not registered/installed.
            MarketConnectionError: Daemon not accessible.
        """
        if not agent_id:
            raise market_error_from_code(
                -32602,
                message="agent_id is required for uninstallation",
            )

        result = self._call("uninstall_agent", {"agent_id": agent_id})
        return isinstance(result, dict) and result.get("status") == "uninstalled"

    # ── Skill Operations ──

    def register_skill(self, skill: SkillInfo) -> bool:
        """Register a new skill in the market.

        Corresponds to market_service_register_skill() in market_service.h
        and handle_register_skill() in main.c.

        Args:
            skill: SkillInfo with registration details.

        Returns:
            True if registration succeeded.
        """
        if not skill.skill_id:
            raise market_error_from_code(
                -32602,
                message="skill_id is required for registration",
            )

        params = {"skill": skill.to_json()}
        result = self._call("register_skill", params)

        if isinstance(result, dict) and result.get("status") == "registered":
            return True
        return False

    def search_skills(self, params: Optional[SearchParams] = None) -> List[SkillInfo]:
        """Search for skills matching the given criteria.

        Corresponds to market_service_search_skills() in market_service.h
        and handle_search_skills() in main.c.

        Args:
            params: Search criteria.

        Returns:
            List of matching SkillInfo objects.
        """
        search_params = params or SearchParams()
        result = self._call("search_skills", search_params.to_json())

        if isinstance(result, list):
            return [SkillInfo.from_json(item) for item in result]
        return []

    def uninstall_skill(self, skill_id: str) -> bool:
        """Uninstall a skill from the market.

        Corresponds to market_service_uninstall_skill() in market_service.h
        and handle_uninstall_skill() in market_rpc.c.

        Args:
            skill_id: ID of the skill to uninstall.

        Returns:
            True if the skill was uninstalled.

        Raises:
            MarketValidationError: Missing skill_id.
            MarketNotFoundError: Skill not registered.
            MarketConnectionError: Daemon not accessible.
        """
        if not skill_id:
            raise market_error_from_code(
                -32602,
                message="skill_id is required for uninstallation",
            )

        result = self._call("uninstall_skill", {"skill_id": skill_id})
        return isinstance(result, dict) and result.get("status") == "uninstalled"

    # ── Update & Sync ──

    def check_update(self, resource_id: str) -> Dict[str, Any]:
        """Check whether a newer version of an agent or skill is available.

        Corresponds to market_service_check_update() in market_service.h
        and handle_check_update() in market_rpc.c.

        Args:
            resource_id: Agent or skill ID to check.

        Returns:
            Dict with ``id``, ``has_update`` and optional ``latest_version``.

        Raises:
            MarketValidationError: Missing resource_id.
            MarketNotFoundError: ID not found in the registry.
            MarketConnectionError: Daemon not accessible.
        """
        if not resource_id:
            raise market_error_from_code(
                -32602,
                message="id is required for update check",
            )

        result = self._call("check_update", {"id": resource_id})
        return result if isinstance(result, dict) else {"has_update": False}

    def sync_registry(self) -> bool:
        """Synchronize the local index with the remote registry.

        Corresponds to market_service_sync_registry() in market_service.h
        and handle_sync_registry() in market_rpc.c.

        Returns:
            True if the sync completed.

        Raises:
            MarketConnectionError: Daemon not accessible.
        """
        result = self._call("sync_registry", {})
        return isinstance(result, dict) and result.get("status") == "synced"

    # ── Health Check ──

    def health_check(self) -> Dict[str, Any]:
        """Check market_d daemon health.

        Corresponds to handle_health_check() in main.c.

        Returns:
            Dict with service name, healthy status, and timestamp.

        Raises:
            MarketConnectionError: Daemon not accessible.
        """
        result = self._call("health_check", {})
        return result if isinstance(result, dict) else {"healthy": False}

    def ping(self) -> bool:
        """Quick check if market_d is reachable.

        Returns:
            True if daemon is healthy and reachable.
        """
        try:
            health = self.health_check()
            return health.get("healthy", False)
        except MarketError:
            return False