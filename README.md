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

> Heads up — the brief originally had Eazyreach doing the LinkedIn → email
> step. They ran out of credits to hand around though, so the FAQ said to
> just use Prospeo for that too. Saved an integration, works fine.

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

## A few things worth knowing

- Rate limits (429s) get a short backoff and a retry instead of blowing up
  the run. Hit Prospeo's *daily* quota a few times while testing this — that
  one fails fast with a clear message instead of spinning forever.
- A company with no contacts, or someone whose email doesn't check out, just
  gets skipped. No reason to let one bad apple stop the whole run.
- Skipped Prospeo's `only_verified_email` flag on purpose — it still eats a
  credit even on a miss. Cheaper to grab whatever it returns and check the
  status ourselves, only keeping stuff marked `VERIFIED` + `revealed`.
