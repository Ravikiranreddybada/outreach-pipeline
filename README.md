# Automated Outreach Pipeline

Give it one company domain. It finds lookalike companies, surfaces their
decision-makers, resolves verified work emails, and sends each of them a
personalized outreach note — fully automated, with one safety checkpoint
before anything actually goes out.

```
company.domain → Ocean.io → Prospeo → Eazyreach → Brevo
                 lookalikes   contacts   emails     send
```

## How it works

1. **Ocean.io** expands the seed domain into a list of lookalike companies
   (similar size, industry, and market).
2. **Prospeo** looks up C-suite and VP-level decision-makers at each company
   and returns their LinkedIn profile URLs.
3. **Eazyreach** resolves each LinkedIn profile into a verified work email.
4. **Brevo** sends each contact a short, personalized outreach email.

Every stage's output feeds the next one automatically — the only manual step
is confirming the send at the safety checkpoint.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your API keys
```

> **Brevo IP allowlist:** Brevo blocks transactional sends from IPs it
> hasn't seen before (you'll get a 401 `unrecognised IP address`). Before
> your first run, authorize the machine you're running from at
> https://app.brevo.com/security/authorised_ips.

## Usage

```bash
python pipeline.py stripe.com
```

The pipeline will print progress for each stage, then show you exactly who
it's about to email before sending anything:

```
READY TO SEND — 6 email(s) for seed domain 'stripe.com'
  - Jane Doe · VP of Sales · ramp.com · jane@ramp.com
  - ...
Send these emails now? [y/N]
```

Type `y` to fire the emails, anything else to abort with nothing sent.

## Project layout

```
pipeline.py         entrypoint — wires the four stages together, owns the checkpoint
stages/
  ocean.py          seed domain -> lookalike company domains
  prospeo.py        company domain -> C-suite/VP contacts + LinkedIn URLs
  eazyreach.py      LinkedIn URL -> verified work email (OAuth client-credentials)
  brevo.py          contact -> personalized outreach email, sent via Brevo
```

## Notes on resilience

- Rate limits (HTTP 429) are retried with a short backoff instead of crashing
  the run.
- A company with no contacts, or a contact whose email can't be verified,
  is simply skipped — partial data never stops the pipeline.
- Eazyreach doesn't publish a public API reference; `stages/eazyreach.py`
  follows the standard OAuth2 client-credentials shape from their dashboard.
  If your account's exact endpoint paths differ, they're isolated to two
  constants (`TOKEN_URL`, `RESOLVE_URL`) at the top of that file.
