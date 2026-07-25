"""What every page object shares."""

from __future__ import annotations

from playwright.sync_api import Locator, Page


class BasePage:
    #: Where `open()` goes. Overridden by pages that have a fixed address.
    path = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self) -> None:
        # The base URL comes from the browser context, so the path is all that
        # is written here and the port stays in one place - the settings.
        self.page.goto(self.path)

    # ---------------------------------------------------------------- messages

    @property
    def form_error(self) -> Locator:
        """
        The message a form shows when the whole submission failed.

        The application marks these with `role="alert"`, so they are addressed
        the way a screen reader would find them rather than by class name.
        """
        return self.page.get_by_role("alert")

    @property
    def form_success(self) -> Locator:
        """The confirmation a form shows when it worked - `role="status"`."""
        return self.page.get_by_role("status")

    def field_error_under(self, field: Locator) -> Locator:
        """
        The validation message belonging to one field.

        Each field lives in its own `.field` wrapper together with its message,
        so the wrapper is what ties the two together.
        """
        return field.locator("xpath=ancestor::div[contains(@class,'field')][1]").locator(
            ".field-error"
        )
