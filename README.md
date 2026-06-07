# Automated Outreach Pipeline

Give it one company domain. It finds lookalike companies, surfaces their
decision-makers with verified work emails, and sends each of them a
personalized outreach note — fully automated, with one safety checkpoint
before anything actually goes out.

```
company.domain → Ocean.io → Prospeo → Brevo
                 lookalikes  contacts   send
                            + emails
```

## How it works

1. **Ocean.io** expands the seed domain into a list of lookalike companies
   (similar size, industry, and market).
2. **Prospeo** looks up C-suite and VP-level decision-makers at each company,
   then enriches each one to a verified work email.
3. **Brevo** sends each contact a short, personalized outreach email.

Every stage's output feeds the next one automatically — the only manual step
is confirming the send at the safety checkpoint.

> The original brief routed the LinkedIn → email step through Eazyreach.
> Vocallabs' own FAQ later said to skip it (their shared credit pool ran
> out) and use Prospeo's enrichment for that step too — so Prospeo now
> covers contact discovery *and* email resolution.

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
pipeline.py         entrypoint — wires the stages together, owns the checkpoint
stages/
  ocean.py          seed domain -> lookalike company domains
  prospeo.py        company domain -> C-suite/VP contacts -> verified work emails
  brevo.py          contact -> personalized outreach email, sent via Brevo
```

## Notes on resilience

- Rate limits (HTTP 429) are retried with a short backoff instead of crashing
  the run.
- A company with no contacts, or a contact whose email can't be verified,
  is simply skipped — partial data never stops the pipeline.
- Email enrichment skips the `only_verified_email` filter (which would burn a
  credit on every miss) and instead checks the returned status itself, only
  keeping addresses Prospeo marks `VERIFIED` and `revealed`.
