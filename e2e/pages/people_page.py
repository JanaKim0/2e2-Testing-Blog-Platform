"""The people directory at /people, and its search."""

from __future__ import annotations

from playwright.sync_api import Locator

from .base_page import BasePage


class PeoplePage(BasePage):
    path = "/people"

    @property
    def search_field(self) -> Locator:
        return self.page.get_by_label("Search people")

    @property
    def search_button(self) -> Locator:
        return self.page.get_by_role("button", name="Search")

    @property
    def results(self) -> Locator:
        """Every person card currently on the page."""
        return self.page.locator("a.user-card")

    @property
    def empty_message(self) -> Locator:
        return self.page.locator("p.empty")

    def card_for(self, username: str) -> Locator:
        """
        The card belonging to one person.

        Matched on the `@username` line rather than the display name, because a
        username is unique and a display name is not.
        """
        return self.results.filter(has_text=f"@{username}")

    # ------------------------------------------------------------------- actions

    def search_for(self, text: str) -> None:
        self.search_field.fill(text)
        self.search_button.click()
        # The page keeps its query in the URL - deliberately, so a search can be
        # shared - which makes the address the signal that it was taken on board.
        self.page.wait_for_url(lambda url: f"query={text}" in url)

    def open_profile_of(self, username: str) -> None:
        self.card_for(username).click()
        self.page.wait_for_url(f"**/authors/{username}")
