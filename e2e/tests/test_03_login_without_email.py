"""
Scenario 3 - signing in fails when the login field is left empty.

A note on the wording of the requirement. It asks for a login attempt with the
*email* field not filled in, and the sign-in form does not have one: it has a
single box that accepts either a username or an email address. So "the email was
not filled in" is, on this form, exactly "that box was left empty", and that is
what is tested.

What makes it a real test rather than a screenshot of a red message is the last
assertion: no request is sent at all. The form is expected to catch this itself,
not to find out from the server.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from e2e.config import Settings
from e2e.pages import Header, LoginPage


@pytest.mark.e2e
def test_signing_in_without_a_login_fails(
    login_page: LoginPage,
    header: Header,
    settings: Settings,
    test_account: dict[str, str],  # the control step at the end signs in for real
) -> None:
    login_page.open()
    expect(login_page.heading).to_be_visible()

    # Every request the page makes from here on, so the assertion below can show
    # that none of them was a sign-in attempt.
    requests: list[str] = []
    login_page.page.on(
        "request",
        lambda request: requests.append(f"{request.method} {request.url}"),
    )

    # The password is filled in and the login is not: the attempt has to fail on
    # the missing field, not on being empty all over.
    login_page.password.fill(settings.new_password)
    login_page.login_field.fill("")
    login_page.submit()

    # The form says which field it is unhappy about, next to that field.
    field_error = login_page.field_error_under(login_page.login_field)
    expect(field_error).to_be_visible()
    expect(field_error).to_have_text("Enter your username or email")

    # Nobody was signed in: still on the form, still a guest.
    expect(login_page.page).to_have_url(f"{settings.frontend_url}/login")
    expect(header.sign_in_link).to_be_visible()
    expect(header.sign_out_button).to_have_count(0)

    # And the server was never asked. A form that let this through and relied on
    # a 400 coming back would pass every assertion above and still be wrong.
    assert not _login_attempts(requests), (
        "the form sent the incomplete credentials to the server instead of "
        f"rejecting them itself: {_login_attempts(requests)}"
    )

    # A control for the assertion above. "No request was sent" is only worth
    # anything if a request *would* have been seen, so the field is filled in and
    # the same form submitted again - this time it must reach the server.
    login_page.login_field.fill(settings.new_username)
    login_page.submit()
    expect(header.sign_out_button).to_be_visible()

    assert _login_attempts(requests), (
        "the completed form did not reach the server either, so the assertion "
        "above proved nothing about the empty one"
    )


def _login_attempts(requests: list[str]) -> list[str]:
    return [entry for entry in requests if entry.endswith("/api/auth/login")]
