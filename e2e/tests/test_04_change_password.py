"""
Scenario 4 - signed in as `testiranje`, change your own password.

A form that says "your password has been changed" has proved nothing on its own,
so the confirmation message is only the first assertion here. What settles it is
that the old password stops being accepted and the new one starts - checked
against the API, and then again through the sign-in form, because that is where
it matters to a person.

This scenario runs last on purpose: it is the one that changes the credentials
the rest of the suite signs in with.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from e2e.api_client import ApiClient
from e2e.config import Settings
from e2e.pages import Header, LoginPage, SettingsPage


@pytest.mark.e2e
def test_changing_your_own_password(
    login_page: LoginPage,
    settings_page: SettingsPage,
    header: Header,
    api: ApiClient,
    settings: Settings,
    test_account: dict[str, str],
) -> None:
    old_password = test_account["password"]
    new_password = settings.changed_password

    # ---- signed in as testiranje ----
    login_page.open()
    login_page.sign_in(test_account["username"], old_password)

    # ---- on the account page, and it is the right account ----
    header.go_to_settings()
    expect(login_page.page).to_have_url(f"{settings.frontend_url}/settings")
    expect(settings_page.username).to_have_value(settings.new_username)

    # ---- change the password ----
    settings_page.change_password(current=old_password, new=new_password)

    expect(settings_page.password_success).to_be_visible()
    expect(settings_page.password_success).to_contain_text("Your password has been changed")
    expect(settings_page.password_error).to_have_count(0)

    # ---- the change is real, not just a message ----
    assert not api.try_login(settings.new_username, old_password), (
        "the old password is still accepted, so the change did not take effect"
    )
    assert api.try_login(settings.new_username, new_password), (
        "the new password is not accepted, so the account has been locked out "
        "rather than updated"
    )

    # ---- and a person can actually use it ----
    # Signing out and back in through the form is the whole point of the feature;
    # the two checks above only prove the API agrees.
    header.sign_out()
    expect(header.sign_in_link).to_be_visible()

    login_page.open()
    login_page.sign_in(settings.new_username, new_password)
    expect(header.account_name).to_have_text(settings.new_display_name)
