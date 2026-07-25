"""
Scenario 1 - a new visitor creates an account.

The account this makes, `testiranje`, is the one the rest of the suite signs in
as, which is why it is created here through the form rather than seeded: the
registration page is the first thing worth proving works.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from e2e.api_client import ApiClient
from e2e.config import Settings
from e2e.pages import Header, RegisterPage


@pytest.mark.e2e
def test_a_new_visitor_can_register(
    register_page: RegisterPage,
    header: Header,
    api: ApiClient,
    settings: Settings,
) -> None:
    register_page.open()
    expect(register_page.heading).to_be_visible()

    register_page.register(
        username=settings.new_username,
        email=settings.new_email,
        password=settings.new_password,
        display_name=settings.new_display_name,
    )

    # Registering signs you straight in and drops you on the latest articles.
    register_page.page.wait_for_url(f"{settings.frontend_url}/")

    # The header is the application's own answer to "who am I?", so it is asked
    # rather than the browser's storage inspected.
    expect(header.sign_out_button).to_be_visible()
    expect(header.account_name).to_have_text(settings.new_display_name)
    expect(header.sign_in_link).to_have_count(0)

    # And the account outlived the page: it is on the server, not just in a
    # signal somewhere in the browser.
    assert api.user_exists(settings.new_username), (
        f"the browser reported a successful registration, but the API does not "
        f"know a user called {settings.new_username}"
    )

    # That the chosen password is usable is not asserted here: the next scenario
    # signs in with it, so a registration that stored an unusable password would
    # fail there rather than pass unnoticed.
