from __future__ import annotations

import asyncio
import importlib
import logging
from typing import Any

from app.mcp.config import MCPConfigLoader, MCPServerConfig

logger = logging.getLogger(__name__)


class MCPChildProcess:
    """Wraps a running MCP child server process."""

    def __init__(self, name: str, cfg: MCPServerConfig) -> None:
        self.name = name
        self.cfg = cfg
        self.process = None
        self.port = cfg.port
        self.status = "stopped"
        self.tools_list: list[str] = []

    async def start(self) -> None:
        """Start the child server as a subprocess."""
        if not self.cfg.enabled:
            self.status = "disabled"
            return

        try:
            module = importlib.import_module(self.cfg.module)
            server_class = getattr(module, self.cfg.class_name)
            self.process = server_class(**self.cfg.init_params)

            if hasattr(self.process, "start"):
                await self.process.start(port=self.cfg.port)
            self.status = "running"
            self.tools_list = self.cfg.tools
            logger.info(f"Started MCP server '{self.name}' on port {self.cfg.port}")
        except Exception as e:
            self.status = "failed"
            logger.error(f"Failed to start MCP server '{self.name}': {e}")

    async def stop(self) -> None:
        """Stop the child server gracefully."""
        if self.process and hasattr(self.process, "stop"):
            try:
                await self.process.stop()
                self.status = "stopped"
                logger.info(f"Stopped MCP server '{self.name}'")
            except Exception as e:
                logger.error(f"Error stopping MCP server '{self.name}': {e}")
                self.status = "error"

    def get_status(self) -> dict[str, Any]:
        """Return current status of this child server."""
        return {
            "name": self.name,
            "status": self.status,
            "port": self.port,
            "tools": self.tools_list,
        }


class MCPParentServer:
    """Parent MCP server: manages child servers, hot-reload, validation, and tool flattening."""

    def __init__(self, config_path: str | None = None) -> None:
        self.loader = MCPConfigLoader(config_path)
        self.children: dict[str, MCPChildProcess] = {}
        self.watch_interval = 2.0
        self.watch_task = None

    async def initialize(self) -> None:
        """Load initial config and start all enabled servers."""
        self.loader.load()
        for name, cfg in self.loader.servers.items():
            await self._start_child(name, cfg)

    async def _start_child(self, name: str, cfg: MCPServerConfig) -> None:
        if name in self.children:
            logger.warning(f"Child server '{name}' already exists. Skipping.")
            return
        child = MCPChildProcess(name, cfg)
        self.children[name] = child
        await child.start()

    async def _stop_child(self, name: str) -> None:
        if name not in self.children:
            return
        child = self.children[name]
        await child.stop()
        del self.children[name]

    async def hot_reload(self) -> None:
        """Watch for config changes and reload child servers."""
        while True:
            try:
                await asyncio.sleep(self.watch_interval)
                if not self.loader.has_changed():
                    continue

                new_config = self.loader.reload()
                logger.info("Hot-reload triggered. Reconciling child servers...")

                current_names = set(self.children.keys())
                desired_names = set(new_config.keys())
                to_remove = current_names - desired_names
                to_add = desired_names - current_names
                to_update = current_names & desired_names

                for name in to_remove:
                    logger.info(f"Removing child server '{name}'")
                    await self._stop_child(name)

                for name in to_add:
                    logger.info(f"Adding child server '{name}'")
                    await self._start_child(name, new_config[name])

                for name in to_update:
                    old_cfg = self.children[name].cfg
                    new_cfg = new_config[name]
                    if old_cfg.enabled != new_cfg.enabled or old_cfg.port != new_cfg.port:
                        logger.info(f"Restarting child server '{name}'")
                        await self._stop_child(name)
                        await self._start_child(name, new_cfg)

            except Exception as e:
                logger.error(f"Error in hot_reload: {e}")

    async def start(self) -> None:
        """Start the parent server and the hot-reload watcher."""
        await self.initialize()
        self.watch_task = asyncio.create_task(self.hot_reload())
        logger.info("MCP parent server started.")

    async def stop(self) -> None:
        """Stop all child servers and the watcher."""
        if self.watch_task:
            self.watch_task.cancel()
        for name in list(self.children.keys()):
            await self._stop_child(name)
        logger.info("MCP parent server stopped.")

    def get_all_tools(self) -> list[str]:
        """Return a flat list of all tools from all running children. Agent sees this as one list."""
        tools = []
        for child in self.children.values():
            if child.status == "running":
                tools.extend(child.tools_list)
        return tools

    def get_all_prompts(self) -> dict[str, str]:
        """Return aggregated prompts from all children."""
        prompts = {}
        for child in self.children.values():
            if child.status == "running" and hasattr(child.process, "get_prompts"):
                child_prompts = child.process.get_prompts()
                prompts.update(child_prompts)
        return prompts

    def get_status(self) -> dict[str, Any]:
        """Return overall status and all child statuses."""
        return {
            "parent_status": "running",
            "children": {name: child.get_status() for name, child in self.children.items()},
            "total_tools": len(self.get_all_tools()),
            "tools": self.get_all_tools(),
        }
