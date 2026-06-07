# Automated Outreach Pipeline — Vocallabs SDE Intern Assignment

## Project Goal
Build a fully automated cold-outreach CLI pipeline. One input (company domain), four stages fire automatically, zero human steps in between.

## Pipeline Flow
```
company.domain → Ocean.io → Prospeo → Brevo
```
> Update (per Vocallabs FAQ on the submission form, received after the brief):
> their shared Eazyreach credit pool ran out for new applicants, so they told
> everyone to skip Eazyreach and use Prospeo's own enrichment for the
> LinkedIn → email step too. Prospeo now covers stage 2 *and* stage 3.

1. **Ocean.io** — seed domain → list of lookalike company domains
2. **Prospeo** — domains → C-suite/VP contacts + LinkedIn URLs → verified work emails
3. **Brevo** — emails → personalized outreach sent

## Usage (when done)
```bash
python pipeline.py stripe.com
```

## API Keys
All stored in `.env` file:
- `OCEAN_API_KEY` — Ocean.io
- `PROSPEO_API_KEY` — Prospeo (covers contacts + email enrichment)
- `BREVO_API_KEY` — Brevo

## Project Structure
```
outreach-pipeline/
├── CLAUDE.md           ← you are here
├── .env                ← API keys (never commit this)
├── pipeline.py         ← main entrypoint
├── stages/
│   ├── __init__.py
│   ├── ocean.py        ← stage 1: find lookalike companies
│   ├── prospeo.py      ← stage 2: find decision makers + resolve verified emails
│   └── brevo.py        ← stage 3: send outreach
├── requirements.txt
└── .gitignore
```

## What's Done
- [x] Domain bought: ravikiranreddy.online
- [x] Private email: ravikiran@ravikiranreddy.online (DNS propagating)
- [x] Ocean.io account (logged in with college email)
- [x] Prospeo account + API key
- [x] Brevo account + API key
- [x] .env file with the 3 API keys this build now needs

## What's Left
- [x] Read Ocean.io, Prospeo, Brevo API docs
- [x] Build stages/ocean.py
- [x] Build stages/prospeo.py (contacts + email enrichment)
- [x] Build stages/brevo.py
- [x] Build pipeline.py (main entrypoint with safety checkpoint)
- [x] Test end to end against live APIs (Ocean.io, Prospeo, Brevo all
      verified live; Brevo IP allowlisted at
      app.brevo.com/security/authorised_ips)
- [ ] Record demo video (explaino.app)
- [ ] Submit on jobapply.site

## Deadline
June 8, 2026 EOD

## Submission Requirements
1. Demo video via explaino.app
2. GitHub repo link
3. Submit on: jobapply.site/d09ca246-605e-47ca-a59c-f802dfc6f5cd

## Key Notes
- Must have a safety checkpoint before emails fire (show summary, ask y/N)
- Clean modular code — one stage = one file
- Handle rate limits, missing contacts, partial failures gracefully
