"""
The site header, which is on every page.

It is also the suite's answer to "am I signed in?": the header shows *Sign out*
and the account name to a signed-in visitor and *Sign in* / *Join* to everybody
else, so asking it is asking the application rather than inspecting its storage.
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page


class Header:
    def __init__(self, page: Page) -> None:
        self.page = page
        self._header = page.locator("header.site-header")

    # ------------------------------------------------------------ signed in or not

    @property
    def sign_out_button(self) -> Locator:
        return self._header.get_by_role("button", name="Sign out")

    @property
    def sign_in_link(self) -> Locator:
        return self._header.get_by_role("link", name="Sign in")

    @property
    def account_name(self) -> Locator:
        """The display name next to the avatar."""
        return self._header.locator(".account-name")

    # ------------------------------------------------------------------ navigation

    @property
    def people_link(self) -> Locator:
        return self._header.get_by_role("link", name="People")

    @property
    def account_link(self) -> Locator:
        """The avatar and name, which lead to the account settings."""
        return self._header.locator("a.account")

    def go_to_people(self) -> None:
        self.people_link.click()

    def go_to_settings(self) -> None:
        self.account_link.click()

    def sign_out(self) -> None:
        self.sign_out_button.click()
