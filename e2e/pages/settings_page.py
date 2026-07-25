"""
The account page at /settings.

Three separate forms live here - picture, profile and password - and two of them
contain a field labelled something-password. Every locator is therefore scoped to
its own panel, so "the new password field" cannot accidentally resolve to
whatever else the page happens to hold.
"""

from __future__ import annotations

from playwright.sync_api import Locator

from .base_page import BasePage


class SettingsPage(BasePage):
    path = "/settings"

    # ------------------------------------------------------------------- panels

    def _panel(self, heading: str) -> Locator:
        return self.page.locator("section.panel").filter(
            has=self.page.get_by_role("heading", name=heading, exact=True)
        )

    @property
    def password_panel(self) -> Locator:
        return self._panel("Password")

    @property
    def profile_panel(self) -> Locator:
        return self._panel("Profile")

    # ---------------------------------------------------------------- password

    @property
    def current_password(self) -> Locator:
        return self.password_panel.get_by_label("Current password")

    @property
    def new_password(self) -> Locator:
        return self.password_panel.get_by_label("New password")

    @property
    def change_password_button(self) -> Locator:
        return self.password_panel.get_by_role("button", name="Change password")

    @property
    def password_success(self) -> Locator:
        return self.password_panel.get_by_role("status")

    @property
    def password_error(self) -> Locator:
        return self.password_panel.get_by_role("alert")

    @property
    def new_password_error(self) -> Locator:
        return self.field_error_under(self.new_password)

    # ----------------------------------------------------------------- profile

    @property
    def display_name(self) -> Locator:
        return self.profile_panel.get_by_label("Display name")

    @property
    def email(self) -> Locator:
        return self.profile_panel.get_by_label("Email")

    @property
    def username(self) -> Locator:
        """
        Shown but disabled: a username is part of every link to the person.

        Located through its wrapper rather than its label, because this one
        `<label>` carries no `for` attribute and does not wrap its input, so it
        is not actually tied to the field. Worth knowing: a screen reader has the
        same problem, which makes it a small accessibility gap in the
        application rather than an awkwardness in the test.
        """
        return self.profile_panel.locator(
            "div.field", has=self.page.get_by_text("Username", exact=True)
        ).locator("input")

    # ------------------------------------------------------------------ actions

    def change_password(self, current: str, new: str) -> None:
        self.current_password.fill(current)
        self.new_password.fill(new)
        self.change_password_button.click()
