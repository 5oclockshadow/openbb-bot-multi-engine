from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class MCPServerConfig:
    """Represents a single MCP child server in the JSON config."""

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.module = config.get("module")  # e.g., "app.mcp_children.openbb_server"
        self.class_name = config.get("class")  # e.g., "OpenBBServer"
        self.enabled = config.get("enabled", True)
        self.port = config.get("port", 5000)
        self.tools = config.get("tools", [])
        self.init_params = config.get("init_params", {})
        self.timeout = config.get("timeout", 30)

    def is_valid(self) -> tuple[bool, str]:
        """Validate the config. Returns (is_valid, error_message)."""
        if not self.module:
            return False, f"Server '{self.name}' missing 'module'"
        if not self.class_name:
            return False, f"Server '{self.name}' missing 'class'"
        if self.port < 1024 or self.port > 65535:
            return False, f"Server '{self.name}' port {self.port} out of range"
        return True, ""

    def __repr__(self) -> str:
        return f"MCPServerConfig(name={self.name}, enabled={self.enabled}, port={self.port})"


class MCPConfigLoader:
    """Loads and watches MCP server configs from a JSON file."""

    def __init__(self, config_path: str | None = None) -> None:
        self.config_path = Path(config_path or settings.MCP_CONFIG_PATH)
        self.servers: dict[str, MCPServerConfig] = {}
        self.last_mtime = 0.0

    def load(self) -> dict[str, MCPServerConfig]:
        """Load servers from JSON. Returns dict of MCPServerConfig by name."""
        if not self.config_path.exists():
            logger.warning(f"Config file {self.config_path} not found. Starting with empty servers.")
            return {}

        try:
            with open(self.config_path) as f:
                data = json.load(f)
            self.servers = {}
            for name, config in data.get("servers", {}).items():
                server_cfg = MCPServerConfig(name, config)
                is_valid, error_msg = server_cfg.is_valid()
                if not is_valid:
                    logger.error(f"Validation failed: {error_msg}")
                    continue
                self.servers[name] = server_cfg
            logger.info(f"Loaded {len(self.servers)} MCP servers from config.")
            return self.servers
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MCP config: {e}")
            return {}

    def has_changed(self) -> bool:
        """Check if the config file has been modified."""
        if not self.config_path.exists():
            return False
        mtime = self.config_path.stat().st_mtime
        if mtime != self.last_mtime:
            self.last_mtime = mtime
            return True
        return False

    def reload(self) -> dict[str, MCPServerConfig]:
        """Reload the config if changed."""
        if self.has_changed():
            logger.info("Config change detected. Reloading...")
            return self.load()
        return self.servers
