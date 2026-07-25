"""The sign-in form at /login."""

from __future__ import annotations

from playwright.sync_api import Locator

from .base_page import BasePage
from .header import Header


class LoginPage(BasePage):
    path = "/login"

    @property
    def login_field(self) -> Locator:
        """
        The one field that takes either a username or an email address.

        Worth naming precisely: the application does not have a separate email
        box on this form, and a test about "leaving the email empty" is really a
        test about leaving this field empty.
        """
        return self.page.get_by_label("Username or email")

    @property
    def password(self) -> Locator:
        return self.page.get_by_label("Password", exact=True)

    @property
    def submit_button(self) -> Locator:
        return self.page.get_by_role("button", name="Sign in")

    @property
    def heading(self) -> Locator:
        return self.page.get_by_role("heading", name="Welcome back")

    # ------------------------------------------------------------------- actions

    def submit(self) -> None:
        self.submit_button.click()

    def sign_in(self, login: str, password: str) -> None:
        """Sign in and wait until the header agrees that it worked."""
        self.login_field.fill(login)
        self.password.fill(password)
        self.submit()
        Header(self.page).sign_out_button.wait_for()
