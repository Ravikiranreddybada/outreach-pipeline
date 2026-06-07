"""Stage 1 — Ocean.io: turn a seed company domain into a list of lookalike companies.

Docs: https://app.ocean.io/docs/searchCompaniesV3
Auth: `x-api-token` header carrying the API token.
"""

import os

import requests

SEARCH_URL = "https://api.ocean.io/v3/search/companies"


class OceanError(Exception):
    """Raised when Ocean.io can't give us lookalikes for the seed domain."""


def find_lookalike_companies(seed_domain: str, limit: int = 20) -> list[str]:
    """Return up to `limit` company domains that look like `seed_domain`.

    Ocean.io's lookalike search takes a seed domain and returns companies with
    similar firmographics (size, industry, market). We page through results
    with `searchAfter` until we hit the limit or run out of matches.
    """
    api_token = os.environ.get("OCEAN_API_KEY")
    if not api_token:
        raise OceanError("OCEAN_API_KEY is not set — check your .env file")

    headers = {"x-api-token": api_token, "Content-Type": "application/json"}
    domains: list[str] = []
    search_after = None
    page_size = min(limit, 25)

    while len(domains) < limit:
        body = {
            "size": page_size,
            "companiesFilters": {"lookalikeDomains": [seed_domain]},
        }
        if search_after:
            body["searchAfter"] = search_after

        response = requests.post(SEARCH_URL, headers=headers, json=body, timeout=30)

        if response.status_code == 429:
            raise OceanError("Ocean.io rate limit hit — slow down and retry shortly")
        if not response.ok:
            raise OceanError(f"Ocean.io search failed ({response.status_code}): {response.text}")

        payload = response.json()
        results = payload.get("companies") or payload.get("results") or []
        if not results:
            break

        for company in results:
            domain = company.get("domain") or company.get("domainName")
            if domain and domain.lower() != seed_domain.lower():
                domains.append(domain)

        search_after = payload.get("searchAfter")
        if not search_after:
            break

    return domains[:limit]
