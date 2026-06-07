"""Stage 2 — Prospeo: turn company domains into decision-makers with verified emails.

Docs:
  https://prospeo.io/api-docs/search-person  (find people at a company)
  https://prospeo.io/api-docs/enrich-person  (resolve a person to a verified email)
Auth: `X-KEY` header carrying the API key.

(Originally this stage just found people and Eazyreach handled the
LinkedIn -> email lookup. Eazyreach ran out of credits to hand out, so per
their FAQ I switched that lookup over to Prospeo's own enrich endpoint —
saved a whole integration and it works fine.)

Only keeping C-suite / VP / founder folks here — anyone more junior isn't
really worth the email.
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
    """Grab up to `max_contacts` C-suite/VP people at `domain`.

    Returns dicts with name, job_title, linkedin_url, company_domain — that's
    all enrich_email needs to go find an actual address next.
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
    """Turn a LinkedIn URL into a verified email, or None if there isn't one.

    Not passing `only_verified_email` here on purpose — that flag still costs
    a credit even when it comes back empty. Cheaper to just ask for whatever
    they've got and throw it away ourselves if it's not VERIFIED + revealed.
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
    """Look up an email for each contact, drop the ones that come back empty.

    Brevo should only ever see addresses we're fairly sure are real.
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
