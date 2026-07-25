"""The registration form at /register."""

from __future__ import annotations

from playwright.sync_api import Locator

from .base_page import BasePage


class RegisterPage(BasePage):
    path = "/register"

    # The fields are addressed through their labels, which is how a person finds
    # them - and it means a renamed CSS class does not break the suite while a
    # renamed label, which users would notice, does.
    @property
    def username(self) -> Locator:
        return self.page.get_by_label("Username", exact=True)

    @property
    def email(self) -> Locator:
        return self.page.get_by_label("Email", exact=True)

    @property
    def password(self) -> Locator:
        return self.page.get_by_label("Password", exact=True)

    @property
    def display_name(self) -> Locator:
        # The label reads "Display name (optional)", so this cannot be exact.
        return self.page.get_by_label("Display name")

    @property
    def submit_button(self) -> Locator:
        return self.page.get_by_role("button", name="Create account")

    @property
    def heading(self) -> Locator:
        return self.page.get_by_role("heading", name="Create an account")

    # ------------------------------------------------------------------- actions

    def fill_in(
        self,
        username: str,
        email: str,
        password: str,
        display_name: str | None = None,
    ) -> None:
        self.username.fill(username)
        self.email.fill(email)
        self.password.fill(password)
        if display_name is not None:
            self.display_name.fill(display_name)

    def submit(self) -> None:
        self.submit_button.click()

    def register(
        self,
        username: str,
        email: str,
        password: str,
        display_name: str | None = None,
    ) -> None:
        self.fill_in(username, email, password, display_name)
        self.submit()
