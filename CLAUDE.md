# Automated Outreach Pipeline — Vocallabs SDE Intern Assignment

## Project Goal
Build a fully automated cold-outreach CLI pipeline. One input (company domain), four stages fire automatically, zero human steps in between.

## Pipeline Flow
```
company.domain → Ocean.io → Prospeo → Eazyreach → Brevo
```

1. **Ocean.io** — seed domain → list of lookalike company domains
2. **Prospeo** — domains → C-suite/VP contacts + LinkedIn URLs
3. **Eazyreach** — LinkedIn URLs → verified work emails
4. **Brevo** — emails → personalized outreach sent

## Usage (when done)
```bash
python pipeline.py stripe.com
```

## API Keys
All stored in `.env` file:
- `OCEAN_API_KEY` — Ocean.io
- `PROSPEO_API_KEY` — Prospeo
- `EAZYREACH_CLIENT_ID` + `EAZYREACH_CLIENT_SECRET` — Eazyreach
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
│   ├── prospeo.py      ← stage 2: find decision makers
│   ├── eazyreach.py    ← stage 3: resolve emails
│   └── brevo.py        ← stage 4: send outreach
├── requirements.txt
└── .gitignore
```

## What's Done
- [x] Domain bought: ravikiranreddy.online
- [x] Private email: ravikiran@ravikiranreddy.online (DNS propagating)
- [x] Ocean.io account (logged in with college email)
- [x] Prospeo account + API key
- [x] Eazyreach account (phone: +919676312146) + Client ID + Secret
- [x] Brevo account + API key
- [x] .env file with all 4 API keys

## What's Left
- [ ] Read Ocean.io, Prospeo, Eazyreach, Brevo API docs
- [ ] Build stages/ocean.py
- [ ] Build stages/prospeo.py
- [ ] Build stages/eazyreach.py
- [ ] Build stages/brevo.py
- [ ] Build pipeline.py (main entrypoint with safety checkpoint)
- [ ] Test end to end
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
- Eazyreach needs Client ID + Client Secret (OAuth style, not a simple API key)
