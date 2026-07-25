"""
Scenario 2 - signed in, find the user `admin` and write "hello" to them.

A note on the wording of the requirement, because this is the one place the
suite could not follow it literally. It asks for a chat: the Blog Platform has
none. There is no message entity, no conversation endpoint and no chat page - the
ways it lets one person write to another are comments and nothing else. So the
scenario keeps the part that exists and is worth testing (sign in, search for
`admin`, open their profile, write "hello" where they will read it) and uses the
channel the application actually has.

`admin` is not an account the application ships either, so the harness creates
it, with one published article to write under.
"""

from __future__ import annotations

from typing import Any

import pytest
from playwright.sync_api import expect

from e2e.api_client import ApiClient
from e2e.config import Settings
from e2e.pages import Header, LoginPage, PeoplePage

MESSAGE = "hello"


@pytest.mark.e2e
def test_finding_admin_and_writing_to_them(
    login_page: LoginPage,
    people_page: PeoplePage,
    profile_page,
    article_page,
    header: Header,
    api: ApiClient,
    settings: Settings,
    test_account: dict[str, str],
    admin_account: dict[str, Any],
) -> None:
    # ---- signed in as the account the first scenario created ----
    login_page.open()
    login_page.sign_in(test_account["username"], test_account["password"])
    expect(header.account_name).to_have_text(settings.new_display_name)

    # ---- find admin ----
    header.go_to_people()
    people_page.search_for(settings.admin_username)

    admin_card = people_page.card_for(settings.admin_username)
    expect(admin_card).to_be_visible()
    # One result, and it is the right person: a search that returned everybody
    # would also contain admin.
    expect(people_page.results).to_have_count(1)

    people_page.open_profile_of(settings.admin_username)

    profile = profile_page(settings.admin_username)
    expect(profile.handle).to_have_text(f"@{settings.admin_username}")
    expect(profile.display_name).to_have_text(settings.admin_display_name)

    # ---- write to them ----
    profile.open_article(settings.admin_article_title)

    article = article_page()
    expect(article.title).to_have_text(settings.admin_article_title)
    expect(article.author_name).to_have_text(settings.admin_display_name)

    article.write_comment(MESSAGE)

    # It is in the thread, under this account's name and not somebody else's.
    posted = article.comment_with_text(MESSAGE)
    expect(posted).to_be_visible()
    expect(article.comment_author_of(MESSAGE)).to_have_text(settings.new_display_name)
    # The box is emptied afterwards, so a second message does not start half-written.
    expect(article.comment_box).to_have_value("")

    # ---- and admin will still find it tomorrow ----
    slug = admin_account["article"]["slug"]
    stored = api.comments_on(slug)
    assert [
        comment
        for comment in stored
        if comment["content"] == MESSAGE
        and comment["author"]["username"] == settings.new_username
    ], (
        f"the comment is on the page but the API returns no {MESSAGE!r} from "
        f"{settings.new_username} on {slug}: {stored}"
    )
