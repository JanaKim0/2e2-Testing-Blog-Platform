"""
Every setting the test run depends on, in one place.

The values are read from the environment so the suite can be pointed at an
already-running instance (or at a different checkout) without editing code, but
every one of them has a default that works on a plain developer machine.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# The test project and the application under test sit side by side, so the
# application can be found relative to this file instead of being configured.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_APP_ROOT = PROJECT_ROOT.parent / "Blog Platform"


def _env(name: str, fallback: str) -> str:
    """An environment variable, treating an empty value as absent."""
    value = os.environ.get(name, "").strip()
    return value or fallback


def _flag(name: str, fallback: bool) -> bool:
    return _env(name, "true" if fallback else "false").lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # ---- Where the application under test lives ----
    app_root: Path = field(default_factory=lambda: Path(_env("E2E_APP_ROOT", str(DEFAULT_APP_ROOT))))

    # ---- Ports ----
    # Deliberately far from 8080/4200 and their immediate neighbours: those are
    # the ports a developer uses by hand, and a test run must never collide with
    # a session that is already open - or, worse, quietly drive somebody else's
    # build against somebody else's database.
    backend_port: int = field(default_factory=lambda: int(_env("E2E_BACKEND_PORT", "18081")))
    frontend_port: int = field(default_factory=lambda: int(_env("E2E_FRONTEND_PORT", "14300")))

    # ---- Lifecycle ----
    # With this off the harness assumes both servers are already running and
    # only waits for them, which makes a debugging loop much faster.
    start_servers: bool = field(default_factory=lambda: _flag("E2E_START_SERVERS", True))
    # The backend needs to compile before it answers; the Angular dev server
    # needs to build the whole app. Both are slow on a cold start.
    backend_startup_timeout: int = field(default_factory=lambda: int(_env("E2E_BACKEND_TIMEOUT", "240")))
    frontend_startup_timeout: int = field(default_factory=lambda: int(_env("E2E_FRONTEND_TIMEOUT", "300")))

    # ---- Test accounts ----
    # The subject of the suite: registered by the first scenario, reused by the
    # rest of them.
    new_username: str = field(default_factory=lambda: _env("E2E_NEW_USERNAME", "testiranje"))
    new_email: str = field(default_factory=lambda: _env("E2E_NEW_EMAIL", "testiranje@example.com"))
    new_password: str = field(default_factory=lambda: _env("E2E_NEW_PASSWORD", "Testiranje-2024"))
    new_display_name: str = field(default_factory=lambda: _env("E2E_NEW_DISPLAY_NAME", "Testiranje"))
    # What the last scenario changes the password to.
    changed_password: str = field(default_factory=lambda: _env("E2E_CHANGED_PASSWORD", "Testiranje-2025-new"))

    # The counterpart the second scenario writes to. Seeded through the API,
    # because the application ships no administrator account of its own.
    admin_username: str = "admin"
    admin_email: str = "admin@example.com"
    admin_password: str = "Admin-password-2024"
    admin_display_name: str = "Admin"
    admin_article_title: str = "House rules for this blog"

    # ---- Isolation ----
    # A throwaway H2 database and uploads folder, wiped before every run, so the
    # suite starts from a known state and never touches the real PostgreSQL
    # database a developer has been working in.
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / ".appdata")
    log_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "logs")
    reset_database: bool = field(default_factory=lambda: _flag("E2E_RESET_DATABASE", True))

    @property
    def backend_url(self) -> str:
        return f"http://localhost:{self.backend_port}"

    @property
    def frontend_url(self) -> str:
        return f"http://localhost:{self.frontend_port}"

    @property
    def api_url(self) -> str:
        return f"{self.backend_url}/api"

    @property
    def backend_dir(self) -> Path:
        return self.app_root / "backend"

    @property
    def frontend_dir(self) -> Path:
        return self.app_root / "frontend"

    @property
    def h2_dir(self) -> Path:
        """Where the throwaway H2 database files are kept."""
        return self.data_dir / "h2"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"


settings = Settings()
