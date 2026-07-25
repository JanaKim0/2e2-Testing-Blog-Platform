"""
Starts and stops the application under test.

An end-to-end suite is only honest if it drives the real thing, so the harness
launches the actual Spring Boot API and the actual Angular dev server and waits
until both answer. Two decisions are worth stating:

*Different ports.* The servers come up on 8081 and 4300 rather than the 8080 and
4200 a developer uses by hand, so a test run cannot collide with a session that
is already open - and cannot silently test somebody else's build.

*A throwaway database.* The backend is started on its embedded H2 profile,
pointed at a database directory inside this project that is deleted before every
run. The suite therefore starts from an empty blog every time, which is what
makes "register the user `testiranje`" repeatable, and the developer's real
PostgreSQL data is never touched.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import IO

import requests

from .config import Settings


class ServerStartupError(RuntimeError):
    """Raised when a server did not become reachable in time."""


class AppRunner:
    """Owns the two server processes for the lifetime of the test session."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._processes: list[tuple[str, subprocess.Popen[bytes]]] = []
        self._log_files: list[IO[bytes]] = []

    # ------------------------------------------------------------------ setup

    def start(self) -> None:
        """Bring the whole application up, or verify that it is already up."""
        self._check_layout()

        if not self._settings.start_servers:
            # Explicitly asked to attach to servers somebody else started.
            self._wait_for_backend()
            self._wait_for_frontend()
            return

        self._prepare_directories()
        self._start_backend()
        self._wait_for_backend()
        self._start_frontend()
        self._wait_for_frontend()

    def _check_layout(self) -> None:
        """Fail with a useful message rather than a confusing one later on."""
        missing = [
            path
            for path in (self._settings.backend_dir, self._settings.frontend_dir)
            if not path.is_dir()
        ]
        if missing:
            raise ServerStartupError(
                "The application under test was not found at "
                f"{self._settings.app_root}. Missing: "
                + ", ".join(str(path) for path in missing)
                + ". Point E2E_APP_ROOT at the Blog Platform checkout."
            )

        if self._settings.start_servers and not (
            self._settings.frontend_dir / "node_modules"
        ).is_dir():
            raise ServerStartupError(
                f"The frontend dependencies are not installed. Run 'npm install' in "
                f"{self._settings.frontend_dir} first."
            )

    def _prepare_directories(self) -> None:
        """Wipe the previous run's data, so every run starts from an empty blog."""
        if self._settings.reset_database and self._settings.data_dir.exists():
            shutil.rmtree(self._settings.data_dir, ignore_errors=True)

        self._settings.h2_dir.mkdir(parents=True, exist_ok=True)
        self._settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        self._settings.log_dir.mkdir(parents=True, exist_ok=True)

        for port, name in (
            (self._settings.backend_port, "backend"),
            (self._settings.frontend_port, "frontend"),
        ):
            if _port_in_use(port):
                raise ServerStartupError(
                    f"Port {port} is already in use, so the {name} cannot start there. "
                    f"Stop whatever is listening, or set "
                    f"E2E_{name.upper()}_PORT to a free port."
                )

    # ----------------------------------------------------------------- backend

    def _start_backend(self) -> None:
        environment = os.environ.copy()
        environment.update(
            {
                # An OS environment variable outranks every properties file, so
                # these win over both application.properties and the h2 profile.
                "SERVER_PORT": str(self._settings.backend_port),
                "SPRING_PROFILES_ACTIVE": "h2",
                "SPRING_DATASOURCE_URL": (
                    f"jdbc:h2:file:{_as_h2_path(self._settings.h2_dir / 'blogplatform')}"
                    ";DB_CLOSE_ON_EXIT=FALSE"
                ),
                "APP_STORAGE_LOCATION": str(self._settings.uploads_dir),
                # The dev server the browser talks to lives on a test port, so
                # it has to be an allowed origin.
                "APP_CORS_ALLOWED_ORIGINS": self._settings.frontend_url,
                # The suite seeds exactly the accounts it needs; demo content
                # would only add noise the assertions have to tolerate.
                "APP_DEMO_DATA": "false",
            }
        )

        self._spawn(
            name="backend",
            command=[str(self._maven_wrapper()), "spring-boot:run"],
            cwd=self._settings.backend_dir,
            environment=environment,
        )

    def _maven_wrapper(self) -> Path:
        wrapper = "mvnw.cmd" if sys.platform == "win32" else "mvnw"
        return self._settings.backend_dir / wrapper

    def _wait_for_backend(self) -> None:
        # A public endpoint: reachable means "up", with no account needed.
        self._wait_for_http(
            name="backend",
            url=f"{self._settings.api_url}/categories",
            timeout=self._settings.backend_startup_timeout,
        )

    # ---------------------------------------------------------------- frontend

    def _start_frontend(self) -> None:
        proxy_config = self._write_proxy_config()

        # `npm start` would serve on the developer's port with the developer's
        # proxy, so the dev server is invoked directly with the test settings.
        executable = "npx.cmd" if sys.platform == "win32" else "npx"
        self._spawn(
            name="frontend",
            command=[
                executable,
                "ng",
                "serve",
                "--port",
                str(self._settings.frontend_port),
                "--proxy-config",
                str(proxy_config),
            ],
            cwd=self._settings.frontend_dir,
            environment=os.environ.copy(),
        )

    def _write_proxy_config(self) -> Path:
        """
        The dev server's proxy, generated rather than committed.

        The application's own proxy.conf.json points at port 8080; this one has
        to follow whatever port the backend was actually given, so it is written
        at run time from that single source of truth.
        """
        target = self._settings.backend_url
        content = (
            "{\n"
            f'  "/api": {{ "target": "{target}", "secure": false }},\n'
            f'  "/uploads": {{ "target": "{target}", "secure": false }}\n'
            "}\n"
        )
        path = self._settings.data_dir / "proxy.e2e.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def _wait_for_frontend(self) -> None:
        self._wait_for_http(
            name="frontend",
            url=f"{self._settings.frontend_url}/",
            timeout=self._settings.frontend_startup_timeout,
        )

    # ------------------------------------------------------------------ shared

    def _spawn(
        self,
        name: str,
        command: list[str],
        cwd: Path,
        environment: dict[str, str],
    ) -> None:
        log_path = self._settings.log_dir / f"{name}.log"
        log_file = log_path.open("wb")
        self._log_files.append(log_file)

        print(f"\n[harness] starting the {name}: {' '.join(command)}")
        print(f"[harness] its output goes to {log_path}")

        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            env=environment,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
        )
        self._processes.append((name, process))

    def _wait_for_http(self, name: str, url: str, timeout: int) -> None:
        deadline = time.monotonic() + timeout
        last_error = "no attempt was made"

        while time.monotonic() < deadline:
            crash = self._crashed_process()
            if crash is not None:
                raise ServerStartupError(
                    f"The {crash} exited before the {name} became reachable. "
                    f"See {self._settings.log_dir / (crash + '.log')}."
                )

            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 500:
                    waited = int(timeout - (deadline - time.monotonic()))
                    print(f"[harness] the {name} answered on {url} after {waited}s")
                    return
                last_error = f"HTTP {response.status_code}"
            except requests.RequestException as failure:
                last_error = type(failure).__name__

            time.sleep(2)

        raise ServerStartupError(
            f"The {name} was not reachable on {url} within {timeout}s "
            f"(last attempt: {last_error}). See {self._settings.log_dir / (name + '.log')}."
        )

    def _crashed_process(self) -> str | None:
        for name, process in self._processes:
            if process.poll() is not None:
                return name
        return None

    # --------------------------------------------------------------- teardown

    def stop(self) -> None:
        """Kill both servers, children included."""
        for name, process in reversed(self._processes):
            if process.poll() is not None:
                continue
            print(f"[harness] stopping the {name}")
            _kill_tree(process)

        self._processes.clear()

        for log_file in self._log_files:
            log_file.close()
        self._log_files.clear()


# --------------------------------------------------------------------- helpers


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(1)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def _as_h2_path(path: Path) -> str:
    """H2 wants forward slashes even on Windows."""
    return str(path).replace("\\", "/")


def _kill_tree(process: subprocess.Popen[bytes]) -> None:
    """
    End a server and everything it started.

    Both servers are launched through a wrapper - the Maven wrapper forks a JVM,
    npx forks the Angular CLI - so killing only the process we hold on to would
    leave the actual server listening and the next run would fail on a busy port.
    """
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        process.terminate()

    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()
