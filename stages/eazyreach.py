"""Stage 3 — Eazyreach: turn LinkedIn profile URLs into verified work emails.

Eazyreach is OAuth-style: you trade a client id + secret for a short-lived
bearer token, then call the resolver with that token. Their reference docs
live behind login at https://docs.eazyreach.app (account required, see
.env.example for the credentials this client expects). These two constants
are the only things that should need updating once you're looking at the
real spec from your dashboard — the surrounding flow (cache the token, retry
once on 401, back off on 429) is written to be endpoint-agnostic.
"""

import os
import time

import requests

TOKEN_URL = "https://api.eazyreach.app/oauth/token"
RESOLVE_URL = "https://api.eazyreach.app/v1/resolve-email"


class EazyreachError(Exception):
    """Raised when Eazyreach can't resolve a LinkedIn profile to an email."""


class EazyreachClient:
    """Thin OAuth2 client-credentials wrapper around the Eazyreach API.

    Caches the bearer token for its lifetime so we don't re-authenticate on
    every single contact in the run.
    """

    def __init__(self):
        self.client_id = os.environ.get("EAZYREACH_CLIENT_ID")
        self.client_secret = os.environ.get("EAZYREACH_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise EazyreachError("EAZYREACH_CLIENT_ID/SECRET are not set — check your .env file")
        self._token = None
        self._token_expires_at = 0.0

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at:
            return self._token

        try:
            response = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            raise EazyreachError(f"Couldn't reach Eazyreach's auth endpoint ({TOKEN_URL}): {exc}") from exc

        if not response.ok:
            raise EazyreachError(f"Eazyreach auth failed ({response.status_code}): {response.text}")

        payload = response.json()
        self._token = payload["access_token"]
        # Refresh a little early so we never call out with a stale token.
        self._token_expires_at = time.time() + payload.get("expires_in", 3600) - 60
        return self._token

    def resolve_email(self, linkedin_url: str) -> str | None:
        """Return a verified work email for `linkedin_url`, or None if not found."""
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = requests.get(
                RESOLVE_URL,
                headers=headers,
                params={"linkedin_url": linkedin_url},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise EazyreachError(f"Couldn't reach Eazyreach's resolve endpoint ({RESOLVE_URL}): {exc}") from exc

        if response.status_code == 401:
            # Token may have just expired — refresh once and retry.
            self._token = None
            headers["Authorization"] = f"Bearer {self._get_token()}"
            response = requests.get(RESOLVE_URL, headers=headers, params={"linkedin_url": linkedin_url}, timeout=30)

        if response.status_code == 404:
            return None
        if response.status_code == 429:
            time.sleep(2)
            return self.resolve_email(linkedin_url)
        if not response.ok:
            raise EazyreachError(f"Eazyreach resolve failed for {linkedin_url} ({response.status_code}): {response.text}")

        payload = response.json()
        email = payload.get("email")
        if email and payload.get("verified", True):
            return email
        return None


def resolve_emails(contacts: list[dict]) -> list[dict]:
    """Attach a verified `email` to each contact dict that has one.

    Contacts whose LinkedIn profile can't be resolved to a verified email are
    dropped — Brevo only ever sees deliverable addresses.
    """
    client = EazyreachClient()
    resolved = []
    for contact in contacts:
        try:
            email = client.resolve_email(contact["linkedin_url"])
        except EazyreachError:
            continue
        if email:
            resolved.append({**contact, "email": email})
    return resolved
