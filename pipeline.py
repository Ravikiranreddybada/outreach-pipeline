#!/usr/bin/env python3
"""Automated cold-outreach pipeline.

Usage:
    python pipeline.py <company.domain>

One seed domain goes in. Ocean.io expands it into lookalikes, Prospeo finds
decision-makers at each one and resolves their verified work emails, and
Brevo sends each of them a personalized note — with one safety checkpoint
before anything actually goes out.

(Used to be a 4-stage thing with Eazyreach doing the LinkedIn -> email part,
but they ran out of credits to give out and told everyone in the FAQ to just
use Prospeo for that too. One less API to juggle, no real downside.)
"""

import os
import sys

from dotenv import load_dotenv

from stages import brevo, ocean, prospeo

LOOKALIKE_LIMIT = 10
CONTACTS_PER_COMPANY = 3


def run(seed_domain: str) -> None:
    print(f"\n[1/3] Ocean.io — finding companies that look like {seed_domain}...")
    lookalikes = ocean.find_lookalike_companies(seed_domain, limit=LOOKALIKE_LIMIT)
    if not lookalikes:
        print("No lookalike companies came back — nothing to do.")
        return
    print(f"  found {len(lookalikes)} lookalike companies: {', '.join(lookalikes)}")

    print(f"\n[2/3] Prospeo — finding decision-makers and resolving verified emails...")
    contacts: list[dict] = []
    for domain in lookalikes:
        try:
            found = prospeo.find_decision_makers(domain, max_contacts=CONTACTS_PER_COMPANY)
        except prospeo.ProspeoError as exc:
            print(f"  ! skipping {domain}: {exc}")
            continue
        print(f"  {domain}: {len(found)} contact(s)")
        contacts.extend(found)

    if not contacts:
        print("No decision-makers surfaced — nothing to do.")
        return

    resolved = prospeo.resolve_emails(contacts)
    print(f"  resolved {len(resolved)}/{len(contacts)} contacts to a verified email")

    if not resolved:
        print("No verified emails came back — nothing to send.")
        return

    choice = _confirm_send(seed_domain, resolved, sourced_count=len(lookalikes))
    if choice == "abort":
        print("\nAborted before sending — no emails went out.")
        return

    if choice == "test":
        test_recipient = os.environ.get("TEST_RECIPIENT")
        if not test_recipient:
            print("\nTEST_RECIPIENT is not set in .env — can't do a test send.")
            return
        print(f"\n[3/3] Brevo — sending personalized outreach (TEST mode → {test_recipient})...")
        results = brevo.send_outreach(resolved, test_recipient=test_recipient)
    else:
        print(f"\n[3/3] Brevo — sending personalized outreach...")
        results = brevo.send_outreach(resolved)

    _print_send_summary(results)


def _confirm_send(seed_domain: str, contacts: list[dict], sourced_count: int = 0) -> str:
    """The safety checkpoint — show a summary of exactly who's about to get
    mailed and ask before anything fires.

    Returns one of:
      "real"  — send to the actual contacts (typed 'y')
      "test"  — send everything to TEST_RECIPIENT instead (typed 'test')
      "abort" — don't send anything (anything else, incl. just Enter)
    """
    companies = sorted({c["company_domain"] for c in contacts})

    print(f"\n{'=' * 60}")
    print(f"READY TO SEND — summary for seed domain '{seed_domain}'")
    print(f"{'-' * 60}")
    print(f"  • {len(contacts)} personalized email(s) across {len(companies)} company(ies)")
    if sourced_count:
        print(f"  • sourced from {sourced_count} lookalike company(ies) Ocean.io returned")
    print(f"  • companies: {', '.join(companies)}")
    print(f"{'-' * 60}")
    for contact in contacts:
        name = contact.get("name") or "(unknown name)"
        title = contact.get("job_title") or "(unknown title)"
        print(f"  - {name} · {title} · {contact['company_domain']} · {contact['email']}")
    print(f"{'=' * 60}")

    answer = input("Send now?  [y] real recipients   [test] my inbox only   [N] cancel: ").strip().lower()
    if answer == "y":
        return "real"
    if answer == "test":
        return "test"
    return "abort"


def _print_send_summary(results: list[dict]) -> None:
    sent = [r for r in results if r["status"] == "sent"]
    failed = [r for r in results if r["status"] == "failed"]

    print(f"\nDone — {len(sent)} sent, {len(failed)} failed.")
    for result in failed:
        contact = result["contact"]
        print(f"  ! failed to send to {contact['email']} ({contact['company_domain']}): {result['detail']}")


def main() -> None:
    load_dotenv()

    if len(sys.argv) != 2:
        print("Usage: python pipeline.py <company.domain>")
        sys.exit(1)

    seed_domain = sys.argv[1].strip().lower()
    run(seed_domain)


if __name__ == "__main__":
    main()
