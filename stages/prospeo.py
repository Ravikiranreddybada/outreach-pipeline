"""Stage 2 — Prospeo: turn company domains into decision-makers with verified emails.

Docs:
  https://prospeo.io/api-docs/search-person  (find people at a company)
  https://prospeo.io/api-docs/enrich-person  (resolve a person to a verified email)
Auth: `X-KEY` header carrying the API key.

Vocallabs originally pointed us at Eazyreach for the LinkedIn -> email step,
but their FAQ later said to skip it (credits are limited) and use Prospeo's
own enrichment for both contacts *and* emails — which is what this module
now does end to end. We filter on seniority so we only surface C-suite and
VP-level people, since those are the ones worth mailing.
"""

import os
import time

import requests

SEARCH_PERSON_URL = "https://api.prospeo.io/search-person"
ENRICH_PERSON_URL = "https://api.prospeo.io/enrich-person"

TARGET_SENIORITIES = ["Founder/Owner", "C-Suite", "Vice President"]
MAX_RATE_LIMIT_RETRIES = 5


class ProspeoError(Exception):
    """Raised when Prospeo can't surface decision-makers for a domain."""


def find_decision_makers(domain: str, max_contacts: int = 5) -> list[dict]:
    """Return up to `max_contacts` C-suite/VP people at `domain`.

    Each contact dict has at least `name`, `job_title`, `linkedin_url`, and
    `company_domain` — everything `enrich_email` needs to resolve a verified
    work email next.
    """
    api_key = os.environ.get("PROSPEO_API_KEY")
    if not api_key:
        raise ProspeoError("PROSPEO_API_KEY is not set — check your .env file")

    headers = {"X-KEY": api_key, "Content-Type": "application/json"}
    contacts: list[dict] = []
    page = 1
    rate_limit_retries = 0

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
            if response.headers.get("x-daily-request-left") == "0":
                reset_in = response.headers.get("x-daily-reset-seconds", "some hours")
                raise ProspeoError(
                    f"Prospeo's daily request quota is exhausted (resets in {reset_in}s) — "
                    "this is an account-level limit, not a bug; try again once it resets"
                )
            rate_limit_retries += 1
            if rate_limit_retries > MAX_RATE_LIMIT_RETRIES:
                raise ProspeoError(f"Prospeo kept rate-limiting search for {domain} — giving up")
            time.sleep(2 * rate_limit_retries)
            continue
        rate_limit_retries = 0
        payload = response.json() if response.content else {}
        if payload.get("error_code") == "NO_RESULTS":
            break
        if not response.ok:
            raise ProspeoError(f"Prospeo search failed for {domain} ({response.status_code}): {response.text}")
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


def enrich_email(linkedin_url: str) -> str | None:
    """Resolve a LinkedIn profile URL to a verified work email, or None.

    We deliberately don't pass `only_verified_email`: that flag makes Prospeo
    burn a credit on every miss too. Instead we ask for whatever it has and
    only keep the result if its status comes back VERIFIED.
    """
    api_key = os.environ.get("PROSPEO_API_KEY")
    if not api_key:
        raise ProspeoError("PROSPEO_API_KEY is not set — check your .env file")

    headers = {"X-KEY": api_key, "Content-Type": "application/json"}
    body = {"data": {"linkedin_url": linkedin_url}}

    response = requests.post(ENRICH_PERSON_URL, headers=headers, json=body, timeout=30)

    if response.status_code == 429:
        if response.headers.get("x-daily-request-left") == "0":
            reset_in = response.headers.get("x-daily-reset-seconds", "some hours")
            raise ProspeoError(
                f"Prospeo's daily request quota is exhausted (resets in {reset_in}s) — "
                "this is an account-level limit, not a bug; try again once it resets"
            )
        time.sleep(2)
        response = requests.post(ENRICH_PERSON_URL, headers=headers, json=body, timeout=30)

    payload = response.json() if response.content else {}
    if payload.get("error_code") in ("NO_MATCH", "INSUFFICIENT_CREDITS"):
        return None
    if not response.ok or payload.get("error"):
        raise ProspeoError(f"Prospeo enrichment failed for {linkedin_url} ({response.status_code}): {response.text}")

    email = (payload.get("person") or {}).get("email") or {}
    if email.get("email") and email.get("status") == "VERIFIED" and email.get("revealed"):
        return email["email"]
    return None


def resolve_emails(contacts: list[dict]) -> list[dict]:
    """Attach a verified `email` to each contact dict that has one.

    Contacts whose LinkedIn profile can't be enriched into a verified,
    revealed email are dropped — Brevo only ever sees deliverable addresses.
    """
    resolved = []
    for contact in contacts:
        try:
            email = enrich_email(contact["linkedin_url"])
        except ProspeoError:
            continue
        if email:
            resolved.append({**contact, "email": email})
    return resolved
