"""
A thin REST client, used for seeding only.

The scenarios themselves go through the browser - that is the point of the
suite - but the *preconditions* do not have to. Creating the counterpart account
the second scenario writes to, and giving it something to comment on, is setup:
driving it through the UI would double the runtime and, worse, would mean a
broken registration page failed three tests instead of one.

So: everything under test happens in the browser, everything merely required
happens here.
"""

from __future__ import annotations

from typing import Any

import requests

from .config import Settings


class ApiClient:
    def __init__(self, settings: Settings) -> None:
        self._api = settings.api_url
        self._token: str | None = None

    # ------------------------------------------------------------------ session

    def register(self, username: str, email: str, password: str, display_name: str) -> dict[str, Any]:
        """Create an account and keep its token for the calls that follow."""
        payload = self._post(
            "/auth/register",
            {
                "username": username,
                "email": email,
                "password": password,
                "displayName": display_name,
            },
        )
        self._token = payload["token"]
        return payload

    def login(self, login: str, password: str) -> dict[str, Any]:
        payload = self._post("/auth/login", {"login": login, "password": password})
        self._token = payload["token"]
        return payload

    def try_login(self, login: str, password: str) -> bool:
        """
        Whether these credentials are accepted.

        Used to prove a password change from the outside: the old one must stop
        working and the new one must start.
        """
        response = requests.post(
            f"{self._api}/auth/login",
            json={"login": login, "password": password},
            timeout=15,
        )
        if response.status_code == 200:
            return True
        if response.status_code in (400, 401, 403):
            return False
        response.raise_for_status()
        return False

    def sign_out(self) -> None:
        self._token = None

    # -------------------------------------------------------------------- users

    def user_exists(self, username: str) -> bool:
        response = requests.get(f"{self._api}/users/{username}", timeout=15)
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    # ----------------------------------------------------------------- content

    def publish_article(self, title: str, summary: str, content: str) -> dict[str, Any]:
        """Publish an article as whoever is currently signed in."""
        return self._post(
            "/articles",
            {
                "title": title,
                "summary": summary,
                "content": content,
                "categorySlug": None,
                "tags": [],
                "status": "PUBLISHED",
            },
        )

    def own_articles(self) -> list[dict[str, Any]]:
        """The signed-in account's own articles, drafts included."""
        response = requests.get(
            f"{self._api}/me/articles",
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["content"]

    def comments_on(self, slug: str) -> list[dict[str, Any]]:
        response = requests.get(f"{self._api}/articles/{slug}/comments", timeout=15)
        response.raise_for_status()
        return response.json()["content"]

    # ----------------------------------------------------------------- plumbing

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self._api}{path}",
            json=body,
            headers=self._headers(),
            timeout=30,
        )
        if not response.ok:
            raise AssertionError(
                f"Seeding failed: POST {path} answered {response.status_code} - {response.text}"
            )
        return response.json()

    def _headers(self) -> dict[str, str]:
        # The API is stateless: the token travels with every request or not at all.
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}
