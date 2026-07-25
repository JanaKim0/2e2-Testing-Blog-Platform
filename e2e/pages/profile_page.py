"""An author's public profile at /authors/{username}."""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from .base_page import BasePage


class ProfilePage(BasePage):
    def __init__(self, page: Page, username: str) -> None:
        super().__init__(page)
        # An instance attribute rather than a class one: which profile this is
        # only becomes known when the object is built.
        self.path = f"/authors/{username}"
        self.username_opened = username

    # -------------------------------------------------------------------- header

    @property
    def display_name(self) -> Locator:
        return self.page.locator(".profile-head h1")

    @property
    def handle(self) -> Locator:
        """The `@username` under the display name."""
        return self.page.locator(".profile-head .username")

    @property
    def follow_button(self) -> Locator:
        """Reads *Follow*, or *Following* once you do."""
        return self.page.locator(".profile-actions button")

    @property
    def article_count(self) -> Locator:
        return self.page.locator(".counts .count").first

    # ------------------------------------------------------------------ articles

    @property
    def articles(self) -> Locator:
        return self.page.locator("article.article-card")

    def article_link(self, title: str) -> Locator:
        return self.articles.get_by_role("link", name=title)

    def open_article(self, title: str) -> None:
        self.article_link(title).click()
        self.page.wait_for_url("**/articles/**")
