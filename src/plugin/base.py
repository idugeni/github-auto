"""Plugin system for extensible architecture."""

from __future__ import annotations

import importlib
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


class Plugin(ABC):
    """Base class for all plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""

    @property
    def description(self) -> str:
        """Plugin description."""
        return ""

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize plugin with configuration."""

    def cleanup(self) -> None:
        """Cleanup plugin resources."""


class EmailProviderPlugin(Plugin):
    """Plugin for email providers."""

    @abstractmethod
    def create_provider(self, config: dict[str, Any]) -> Any:
        """Create email provider instance."""


class CaptchaSolverPlugin(Plugin):
    """Plugin for CAPTCHA solvers."""

    @abstractmethod
    def create_solver(self, config: dict[str, Any]) -> Any:
        """Create CAPTCHA solver instance."""


class PluginManager:
    """Manage plugins."""

    def __init__(self, plugin_dir: str = "plugins"):
        self._plugin_dir = Path(plugin_dir)
        self._plugins: dict[str, Plugin] = {}

    def discover(self) -> list[str]:
        """Discover available plugins."""
        discovered = []

        if not self._plugin_dir.exists():
            return discovered

        for path in self._plugin_dir.iterdir():
            if path.is_dir() and (path / "__init__.py").exists():
                discovered.append(path.name)
            elif path.suffix == ".py" and path.stem != "__init__":
                discovered.append(path.stem)

        log.info("Discovered %d plugins: %s", len(discovered), discovered)
        return discovered

    def load(self, plugin_name: str) -> Optional[Plugin]:
        """Load a plugin by name."""
        if plugin_name in self._plugins:
            return self._plugins[plugin_name]

        try:
            # Try to import from plugin directory
            if self._plugin_dir.exists():
                module_path = self._plugin_dir / plugin_name
                if module_path.is_dir():
                    module = importlib.import_module(f"plugins.{plugin_name}")
                else:
                    module = importlib.import_module(f"plugins.{plugin_name}")
            else:
                module = importlib.import_module(f"plugins.{plugin_name}")

            # Find plugin class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr is not Plugin:
                    plugin = attr()
                    self._plugins[plugin_name] = plugin
                    log.info("Loaded plugin: %s v%s", plugin.name, plugin.version)
                    return plugin

        except Exception as exc:
            log.error("Failed to load plugin %s: %s", plugin_name, exc)

        return None

    def load_all(self) -> dict[str, Plugin]:
        """Load all discovered plugins."""
        for name in self.discover():
            self.load(name)
        return self._plugins

    def get(self, name: str) -> Optional[Plugin]:
        """Get loaded plugin by name."""
        return self._plugins.get(name)

    def initialize_all(self, config: dict[str, Any]) -> None:
        """Initialize all loaded plugins."""
        for name, plugin in self._plugins.items():
            try:
                plugin.initialize(config.get(name, {}))
                log.info("Initialized plugin: %s", name)
            except Exception as exc:
                log.error("Failed to initialize plugin %s: %s", name, exc)

    def cleanup_all(self) -> None:
        """Cleanup all plugins."""
        for name, plugin in self._plugins.items():
            try:
                plugin.cleanup()
            except Exception as exc:
                log.error("Failed to cleanup plugin %s: %s", name, exc)

    @property
    def list(self) -> list[str]:
        """List loaded plugin names."""
        return list(self._plugins.keys())
