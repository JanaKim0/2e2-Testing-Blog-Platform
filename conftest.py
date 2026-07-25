"""
Fixtures shared by every scenario.

The session-scoped fixtures do the expensive, once-per-run work: bringing the
application up and seeding the accounts the scenarios need to find. The
function-scoped ones give each test a clean browser and, on failure, a
screenshot of the page as it looked when the assertion broke.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

from playwright.sync_api import Page

from e2e.api_client import ApiClient
from e2e.app_runner import AppRunner
from e2e.config import PROJECT_ROOT, Settings, settings as default_settings
from e2e.pages import (
    ArticlePage,
    Header,
    LoginPage,
    PeoplePage,
    ProfilePage,
    RegisterPage,
    SettingsPage,
)

SCREENSHOT_DIR = PROJECT_ROOT / "reports" / "screenshots"


# --------------------------------------------------------------- the application


@pytest.fixture(scope="session")
def settings() -> Settings:
    return default_settings


@pytest.fixture(scope="session")
def application(settings: Settings) -> Iterator[AppRunner]:
    """The Blog Platform, running for the length of the session."""
    runner = AppRunner(settings)
    runner.start()
    try:
        yield runner
    finally:
        runner.stop()


@pytest.fixture(scope="session")
def api(application: AppRunner, settings: Settings) -> ApiClient:
    """A REST client against the running instance, for setup and verification."""
    return ApiClient(settings)


@pytest.fixture(scope="session")
def admin_account(api: ApiClient, settings: Settings) -> dict[str, Any]:
    """
    The counterpart the second scenario writes to.

    The application ships no administrator account and no demo data is loaded,
    so `admin` is created here - together with one published article, because a
    profile with nothing on it gives a visitor nothing to write on.
    """
    if not api.user_exists(settings.admin_username):
        api.register(
            username=settings.admin_username,
            email=settings.admin_email,
            password=settings.admin_password,
            display_name=settings.admin_display_name,
        )
        article = api.publish_article(
            title=settings.admin_article_title,
            summary="What is welcome here and what is not.",
            content=(
                "Be kind, stay on topic and do not post other people's work as "
                "your own. Questions about anything on this blog are welcome - "
                "leave them in the comments and I will answer."
            ),
        )
        api.sign_out()
    else:
        # Left over from an earlier run against a database that was kept: sign
        # in and pick the article up again rather than publish a second one.
        api.login(settings.admin_username, settings.admin_password)
        article = next(
            item
            for item in api.own_articles()
            if item["title"] == settings.admin_article_title
        )
        api.sign_out()

    return {"username": settings.admin_username, "article": article}


@pytest.fixture
def test_account(api: ApiClient, settings: Settings) -> dict[str, str]:
    """
    Guarantees the `testiranje` account exists before a scenario needs it.

    The first scenario creates it through the registration form, which is the
    honest way round. The later scenarios only *depend* on it existing, so if
    one of them is run on its own the account is seeded through the API instead
    of quietly failing. In a full run this fixture finds the account already
    there and does nothing.
    """
    if not api.user_exists(settings.new_username):
        api.register(
            username=settings.new_username,
            email=settings.new_email,
            password=settings.new_password,
            display_name=settings.new_display_name,
        )
        api.sign_out()

    return {
        "username": settings.new_username,
        "email": settings.new_email,
        "password": settings.new_password,
    }


# -------------------------------------------------------------------- the browser


@pytest.fixture(scope="session")
def base_url(application: AppRunner, settings: Settings) -> str:
    """
    Where the tests point their browser.

    Depending on `application` is what makes every page fixture wait for the
    servers to be up: a test cannot navigate before this is resolved.
    """
    return settings.frontend_url


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any], base_url: str) -> dict[str, Any]:
    return {
        **browser_context_args,
        "base_url": base_url,
        "viewport": {"width": 1440, "height": 900},
        # The API's clock and the assertions' clock should agree.
        "locale": "en-GB",
        "timezone_id": "Europe/Tallinn",
    }


# ---------------------------------------------------------------- the page objects


@pytest.fixture
def header(page: Page) -> Header:
    return Header(page)


@pytest.fixture
def register_page(page: Page) -> RegisterPage:
    return RegisterPage(page)


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    return LoginPage(page)


@pytest.fixture
def people_page(page: Page) -> PeoplePage:
    return PeoplePage(page)


@pytest.fixture
def settings_page(page: Page) -> SettingsPage:
    return SettingsPage(page)


@pytest.fixture
def profile_page(page: Page):
    """A factory, since which profile is wanted depends on the test."""
    return lambda username: ProfilePage(page, username)


@pytest.fixture
def article_page(page: Page):
    """A factory: with a slug to open one directly, without one to read the page
    the browser is already on."""
    return lambda slug=None: ArticlePage(page, slug)


# -------------------------------------------------- a screenshot when a test fails


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    """Records each phase's outcome on the item, for the fixture below to read."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"report_{report.when}", report)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request: pytest.FixtureRequest, page: Page) -> Iterator[None]:
    """
    A picture of the page at the moment a test failed.

    A failed end-to-end assertion says what was expected, but almost never why
    the application disagreed. The screenshot usually does.

    It takes `page` as an argument rather than looking it up, so that pytest
    tears this fixture down *before* the browser: asked for afterwards, the
    screenshot would only ever be of a closed page.
    """
    yield

    report = getattr(request.node, "report_call", None)
    if report is None or not report.failed:
        return

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    target = SCREENSHOT_DIR / f"{request.node.name}.png"
    try:
        page.screenshot(path=str(target), full_page=True)
        print(f"\n[harness] the page at the point of failure: {target}")
    except Exception as failure:  # pragma: no cover - never mask the real failure
        print(f"\n[harness] could not take a screenshot: {failure}")


def pytest_report_header(config: pytest.Config) -> list[str]:
    return [
        f"application under test: {default_settings.app_root}",
        f"frontend: {default_settings.frontend_url}   backend: {default_settings.backend_url}",
        f"servers started by the harness: {default_settings.start_servers}",
    ]
