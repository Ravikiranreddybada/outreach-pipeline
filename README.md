# Automated Outreach Pipeline

Hand it one company domain and it does the rest: finds companies that look
like it, surfaces decision-makers there with verified work emails, and sends
each of them a short personalized note — fully automated, with one safety
checkpoint before anything actually goes out.

```
company.domain → Ocean.io → Prospeo → Brevo
                 lookalikes  contacts   send
                            + emails
```

## How it works

1. **Ocean.io** takes the seed domain and returns a batch of lookalike
   companies — similar size, industry, market.
2. **Prospeo** finds C-suite/VP/founder-level people at each of those
   companies, then resolves each one to a verified work email.
3. **Brevo** sends every resolved contact a personalized outreach email.

Each stage just feeds the next — the only thing you do by hand is approve the
send when the checkpoint shows up.

> One thing worth flagging: the brief originally had Eazyreach handling the
> LinkedIn → email step as its own stage. They ran out of credits to give out
> mid-way through though, and the FAQ said to just let Prospeo cover that too.
> So that's what this does now — one less integration to maintain, and Prospeo
> already had the data to do it.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then drop in your own API keys
```

> **Brevo IP allowlist:** Brevo will reject sends from an IP it doesn't
> recognize (you'll see a 401 `unrecognised IP address`). Before your first
> real run, add the machine you're sending from at
> https://app.brevo.com/security/authorised_ips — easy to miss and a confusing
> error if you don't know to look for it.

## Usage

```bash
python pipeline.py stripe.com
```

You'll see progress for each stage as it runs, and right before anything goes
out, a checkpoint shows exactly who's about to get an email:

```
============================================================
READY TO SEND — summary for seed domain 'stripe.com'
------------------------------------------------------------
  • 6 personalized email(s) across 4 company(ies)
  • sourced from 10 lookalike company(ies) Ocean.io returned
  • companies: brex.com, plaid.com, ramp.com, square.com
------------------------------------------------------------
  - Jane Doe · VP of Sales · ramp.com · jane@ramp.com
  - ...
============================================================
Send now?  [y] real recipients   [test] my inbox only   [N] cancel:
```

Three ways to answer that prompt:

- `y` — send to the real contacts
- `test` — redirect every email to `TEST_RECIPIENT` from your `.env` instead,
  so you can see a real send land without actually mailing strangers (each
  subject gets a `[TEST → original@address]` prefix so you can still tell who
  it would've gone to)
- anything else (or just hit Enter) — bail out, nothing gets sent

## Project layout

```
pipeline.py         entrypoint — wires the stages together, owns the checkpoint
stages/
  ocean.py          seed domain -> lookalike company domains
  prospeo.py        company domain -> decision-makers -> verified work emails
  brevo.py          contact -> personalized email, sent via Brevo
```

## A few things worth knowing

- 429s get a short backoff and a retry rather than crashing the run. Prospeo
  also enforces a *daily* quota on top of that — hit it a couple times while
  building this, so now it's detected up front and fails with a clear message
  instead of looping forever.
- If a company has no decision-makers, or someone's email doesn't come back
  verified, that contact (or company) just gets skipped and the run keeps
  going. No reason for one bad lookup to take down the whole batch.
- Deliberately not passing Prospeo's `only_verified_email` flag — it still
  burns a credit even when the answer is empty. Cheaper to take whatever comes
  back and check `status == VERIFIED` and `revealed == True` ourselves before
  trusting it.
