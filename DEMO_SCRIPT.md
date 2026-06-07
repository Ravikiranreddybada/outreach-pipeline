# Demo Recording Script (explaino.app)

Target length: ~4-6 minutes. Record in a terminal with a clean, large font.
Have the project open in your editor in a second window/tab for the code walk.

---

## 1. Cold open (15-20s)

Say, on camera or in voiceover:

> "This is an automated cold-outreach pipeline. You give it one company
> domain, and it runs three stages end to end with zero manual steps in
> between — finding lookalike companies, surfacing their decision-makers
> with verified emails, and sending each of them a personalized outreach
> note. The only manual step is a safety checkpoint before anything actually
> sends."

---

## 2. Show the one-line command (10s)

Open a terminal in the project folder and show the command before running it:

```bash
python pipeline.py razorpay.com
```

> "One input — a seed domain. Everything after this is automatic."

Press enter.

---

## 3. Narrate each stage as it streams (90-120s)

Let the output scroll — don't talk over the API calls, just point at what's
happening as each block appears:

- **`[1/3] Ocean.io`** — "It expands the seed domain into companies that look
  like it — similar size, industry, market. Output: a clean list of domains."
- **`[2/3] Prospeo`** — "For each of those companies, it finds C-suite and
  VP-level decision-makers, then resolves each one to a verified work email —
  no guessing, no catch-all addresses."
- **`[3/3] Brevo`** — "And finally it's ready to send — but it stops here
  first."

---

## 4. The safety checkpoint — your "good judgment" moment (45-60s)

This is the most important beat in the whole demo. When the
`READY TO SEND — N email(s)...` summary appears:

> "Before anything actually fires, it shows me exactly who it's about to
> email — name, title, company, address — and asks for confirmation."

Type **`N`** and let it abort cleanly:

> "If I say no, nothing goes out. No partial sends, no surprises."

*(Optional, if you want to show a real send: run it again on a different/
narrower domain, type `y`, and show the email landing in your inbox via
Brevo. Only do this if you're comfortable sending a real — if test —
outreach email.)*

---

## 5. Quick code walk (90-120s)

Switch to your editor. Keep this tight — show structure, not every line.

1. **`pipeline.py`** — "This is the entrypoint. It's maybe 100 lines: call
   stage one, feed its output to stage two, feed that to stage three, and
   own the safety checkpoint. No stage knows about the others."
2. **`stages/` folder** — "One file per stage — `ocean.py`, `prospeo.py`,
   `brevo.py`. Each is independently readable and testable."
3. **Pick ONE integration detail to show off** — e.g. open `prospeo.py` and
   point at:
   - the `X-KEY` auth header
   - the pagination loop (`current_page` / `total_page`)
   - the `enrich_email` function — explain you deliberately *don't* pass
     `only_verified_email=True` because that flag burns a credit on every
     miss; instead you check the returned status yourself and only keep
     emails marked `VERIFIED` and `revealed`.
4. **Show one resilience detail** — e.g. the `try/except requests.RequestException`
   wrapping, or the rate-limit retry cap with the daily-quota header check.
   Say something like:

   > "While building this I actually hit Prospeo's daily request quota during
   > testing — so I added a check for their `x-daily-request-left` header
   > that fails fast with a clear message instead of retrying forever."

   This is a *true story* — use it. It's exactly the kind of "handles rate
   limits gracefully" detail they say they're grading on.

---

## 6. The pivot story — "be honest" (30-45s)

The brief originally routed LinkedIn → email through Eazyreach. Tell this
story plainly — it shows you read instructions carefully AND adapt when
they change:

> "The original brief had a fourth stage — Eazyreach — resolving LinkedIn
> profiles to emails. After I'd built it and tested the integration live,
> Vocallabs' own FAQ said their shared Eazyreach credit pool had run out and
> to use Prospeo's own enrichment for that step instead. So I removed
> Eazyreach and pointed that responsibility at Prospeo's `enrich-person`
> endpoint — same pipeline, one less hop, same end result."

(You can show the git history briefly here — `git log --oneline` — to prove
this was a real, incremental build, not a last-minute scramble.)

---

## 7. Wrap (15s)

> "That's the full pipeline — one domain in, personalized outreach out,
> with a human checkpoint before anything sends. Code's on GitHub, link's
> in the submission."

---

## Recording checklist

- [ ] New Prospeo API key in `.env` (old one hit its daily quota during testing)
- [ ] Brevo IP allowlisted at app.brevo.com/security/authorised_ips
- [ ] Terminal font size bumped up so it's readable on screen
- [ ] Do a silent dry run first so you know roughly how long each stage takes
- [ ] Decide in advance: are you doing a real send (`y`) or just the abort (`N`)?
- [ ] Have `git log --oneline` ready to show if you want to back up the pivot story
