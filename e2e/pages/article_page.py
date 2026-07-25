"""
One article at /articles/{slug}, and the discussion under it.

This is where a visitor writes to an author: the application has no private
messages, so the comment box is the channel it does offer.
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from .base_page import BasePage


class ArticlePage(BasePage):
    def __init__(self, page: Page, slug: str | None = None) -> None:
        super().__init__(page)
        if slug is not None:
            self.path = f"/articles/{slug}"

    # ------------------------------------------------------------------- article

    @property
    def title(self) -> Locator:
        return self.page.locator(".article-header h1")

    @property
    def author_name(self) -> Locator:
        """Who wrote it, from the byline."""
        return self.page.locator(".byline .author-name")

    # ------------------------------------------------------------------ comments

    @property
    def comments_section(self) -> Locator:
        return self.page.locator("section.comments")

    @property
    def comment_box(self) -> Locator:
        return self.page.get_by_label("Your comment")

    @property
    def post_comment_button(self) -> Locator:
        return self.page.get_by_role("button", name="Post comment")

    @property
    def sign_in_prompt(self) -> Locator:
        """Shown instead of the comment box to a visitor who is not signed in."""
        return self.comments_section.locator(".sign-in-prompt")

    @property
    def comments(self) -> Locator:
        return self.comments_section.locator("li.comment")

    def comment_with_text(self, text: str) -> Locator:
        return self.comments.filter(has_text=text)

    def comment_author_of(self, text: str) -> Locator:
        return self.comment_with_text(text).locator(".comment-author")

    # ------------------------------------------------------------------- actions

    def write_comment(self, text: str) -> None:
        """
        Post a comment and wait until it is in the thread.

        The thread runs oldest first, so a new comment lands on the last page and
        the application navigates there itself; waiting for the text to appear
        covers both the request and that jump.
        """
        self.comment_box.fill(text)
        self.post_comment_button.click()
        self.comment_with_text(text).wait_for()
