"""Stage 3 — Brevo: send each resolved contact a personalized outreach email.

Docs: https://developers.brevo.com/docs/send-a-transactional-email
Auth: `api-key` header carrying the API key.
"""

import os
import time

import requests

SEND_URL = "https://api.brevo.com/v3/smtp/email"

SUBJECT_TEMPLATE = "Quick question for {first_name} at {company_domain}"

BODY_TEMPLATE = """\
Hi {first_name},

I came across {company_domain} and noticed you're {job_title} there — that's exactly \
the kind of role we build for at Vocallabs.

We help teams like yours turn cold outbound into warm conversations by automating the \
sourcing-to-send pipeline end to end, so reps spend their time talking to people who are \
actually a fit instead of building lists.

Worth a quick chat this week to see if it's useful for {company_domain}?

Best,
{sender_name}
"""


class BrevoError(Exception):
    """Raised when Brevo can't send an outreach email."""


def _first_name(full_name: str | None) -> str:
    if not full_name:
        return "there"
    return full_name.strip().split()[0]


def _build_email(contact: dict, sender_name: str) -> dict:
    first_name = _first_name(contact.get("name"))
    context = {
        "first_name": first_name,
        "company_domain": contact["company_domain"],
        "job_title": contact.get("job_title") or "a leader",
        "sender_name": sender_name,
    }
    return {
        "subject": SUBJECT_TEMPLATE.format(**context),
        "text": BODY_TEMPLATE.format(**context),
    }


def send_outreach(contacts: list[dict]) -> list[dict]:
    """Send a personalized email to every contact and report what happened.

    Returns a list of `{contact, status, detail}` so the caller can show the
    user a clear summary of sends, skips, and failures — partial failures here
    must never crash the run.
    """
    api_key = os.environ.get("BREVO_API_KEY")
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_name = os.environ.get("SENDER_NAME", "The Outreach Team")
    if not api_key or not sender_email:
        raise BrevoError("BREVO_API_KEY / SENDER_EMAIL are not set — check your .env file")

    headers = {"api-key": api_key, "Content-Type": "application/json"}
    results = []

    for contact in contacts:
        email = _build_email(contact, sender_name)
        body = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": contact["email"], "name": contact.get("name") or contact["email"]}],
            "subject": email["subject"],
            "textContent": email["text"],
        }

        response = requests.post(SEND_URL, headers=headers, json=body, timeout=30)

        if response.status_code == 429:
            time.sleep(2)
            response = requests.post(SEND_URL, headers=headers, json=body, timeout=30)

        if response.ok:
            results.append({"contact": contact, "status": "sent", "detail": response.json().get("messageId")})
        else:
            results.append({"contact": contact, "status": "failed", "detail": f"{response.status_code}: {response.text}"})

    return results
