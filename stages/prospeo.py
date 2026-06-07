"""Stage 2 — Prospeo: turn company domains into decision-maker contacts.

Docs: https://prospeo.io/api-docs/search-person
Auth: `X-KEY` header carrying the API key.

We filter on seniority so we only surface C-suite and VP-level people, since
those are the ones worth mailing.
"""

import os
import time

import requests

SEARCH_PERSON_URL = "https://api.prospeo.io/search-person"

TARGET_SENIORITIES = ["Founder/Owner", "C-Suite", "Vice President"]


class ProspeoError(Exception):
    """Raised when Prospeo can't surface decision-makers for a domain."""


def find_decision_makers(domain: str, max_contacts: int = 5) -> list[dict]:
    """Return up to `max_contacts` C-suite/VP people at `domain`.

    Each contact dict has at least `name`, `job_title`, `linkedin_url`, and
    `company_domain` — everything the next stage (Eazyreach) needs to resolve
    a verified work email.
    """
    api_key = os.environ.get("PROSPEO_API_KEY")
    if not api_key:
        raise ProspeoError("PROSPEO_API_KEY is not set — check your .env file")

    headers = {"X-KEY": api_key, "Content-Type": "application/json"}
    contacts: list[dict] = []
    page = 1

    while len(contacts) < max_contacts:
        body = {
            "page": page,
            "filters": {
                "company": {"websites": {"include": [domain]}},
                "person_seniority": {"include": TARGET_SENIORITIES},
            },
        }

        response = requests.post(SEARCH_PERSON_URL, headers=headers, json=body, timeout=30)

        if response.status_code == 429:
            time.sleep(2)
            continue
        if not response.ok:
            raise ProspeoError(f"Prospeo search failed for {domain} ({response.status_code}): {response.text}")

        payload = response.json()
        if payload.get("error"):
            raise ProspeoError(f"Prospeo returned an error for {domain}: {payload}")

        results = payload.get("results") or []
        if not results:
            break

        for entry in results:
            person = entry.get("person") or entry
            linkedin_url = person.get("linkedin_url")
            if not linkedin_url:
                continue
            contacts.append(
                {
                    "name": person.get("full_name"),
                    "job_title": person.get("current_job_title"),
                    "linkedin_url": linkedin_url,
                    "company_domain": domain,
                }
            )
            if len(contacts) >= max_contacts:
                break

        pagination = payload.get("pagination") or {}
        if pagination.get("current_page", page) >= pagination.get("total_page", page):
            break
        page += 1

    return contacts
