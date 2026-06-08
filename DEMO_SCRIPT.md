# Demo recording notes (explaino.app)

Aiming for ~4-6 min. Terminal with a big font, editor open in another tab
for the code walk. Don't read this word for word on camera — just use it to
remember what to hit.

---

## 1. Open (15-20s)

Something like:

> "This is a cold-outreach pipeline — give it one company domain and it runs
> three stages back to back with no manual steps in the middle: finds
> lookalike companies, finds their decision-makers with verified emails, and
> sends each of them a personalized note. Only thing it stops for is a
> safety check right before it actually sends anything."

---

## 2. Run it (10s)

Show the command before hitting enter:

```bash
python pipeline.py razorpay.com
```

> "One domain in. Everything else from here is automatic."

---

## 3. Let it run, narrate as it goes (90-120s)

Don't talk over the API calls — just call out what's happening as each block
prints:

- **`[1/3] Ocean.io`** — finds companies that look like the seed one, similar
  size/industry/market, hands back a list of domains
- **`[2/3] Prospeo`** — for each of those, finds C-suite/VP people and pulls
  a verified email for each — not guesses, actual verified addresses
- **`[3/3] Brevo`** — gets to the send step... and stops

---

## 4. The checkpoint — this is the bit they actually care about (45-60s)

When `READY TO SEND — N email(s)...` shows up:

> "Before it fires anything it shows me exactly who's about to get an email —
> name, title, company, address — and asks me to confirm."

Type **`N`**, let it bail cleanly:

> "Say no, nothing goes out. No half-sent batches."

If you want to also show a real send going through — run it again on a
narrower domain, type `y`, show it land in your inbox. Up to you whether
that's worth doing on camera.

---

## 5. Quick look at the code (90-120s)

Keep this short — structure over line-by-line.

1. **`pipeline.py`** — "entrypoint, ~100 lines. Calls each stage, passes the
   output to the next, owns the confirm step. Stages don't know about each
   other at all."
2. **`stages/`** — one file per stage (`ocean.py`, `prospeo.py`, `brevo.py`),
   each one doing exactly one job.
3. Pop open `prospeo.py` and point at one or two of:
   - the `X-KEY` header
   - the pagination loop (`current_page`/`total_page`)
   - `enrich_email` — mention you skip the `only_verified_email` flag because
     it costs a credit even on a miss, so you check the status yourself
4. Show a resilience bit — the `try/except requests.RequestException`, or
   the rate-limit retry cap. Good line for this:

   > "Actually ran into Prospeo's daily request cap a few times while
   > building this — so now it checks for that specific header and fails
   > with a clear message instead of just retrying forever and going nowhere."

   That's a real thing that happened, not a hypothetical — use it.

---

## 6. The Eazyreach swap — good "honesty" moment (30-45s)

> "Original brief had a fourth stage — Eazyreach — turning LinkedIn profiles
> into emails. I'd actually built and tested that integration live when
> Vocallabs put out an FAQ saying their Eazyreach credits had run dry and to
> just use Prospeo for that step instead. So I pulled Eazyreach out and
> pointed that job at Prospeo's enrich endpoint — same pipeline, one fewer
> moving part, same result."

Can pull up `git log --oneline` here if you want to back it up — shows it
was a real incremental build and not a last-minute rewrite.

---

## 7. Close (15s)

> "That's the whole thing — one domain in, personalized outreach out, with a
> human checking before anything sends. Repo's linked in the submission."

---

## Before you hit record

- [ ] Fresh Prospeo key in `.env` (the old one ate its daily quota during testing)
- [ ] Brevo IP allowlisted — done already
- [ ] Bump the terminal font up
- [ ] Run it once through quietly first so you know the timing/pacing
- [ ] Decide ahead of time: abort with `N` only, or also show a real send with `y`
- [ ] Keep `git log --oneline` handy in case you want to show the build history




Test Run Steps
Step 1: Open Terminal in the project folder
Test Run Steps
Step 1: Open Terminal in the project folder
cd /Users/ravikiranreddybada/Documents/outreach-pipeline
Step 2: Activate the virtual environment
source .venv/bin/activate
(You'll see (.venv) appear at the start of your terminal line)

Step 3: Run the pipeline with a test domain
python pipeline.py razorpay.com
You can use any company domain — razorpay.com, stripe.com, zomato.com, etc.e
Step 2: Activate the virtual environment
source .venv/bin/activate
(You'll see (.venv) appear at the start of your terminal line)

Step 3: Run the pipeline with a test domain
python pipeline.py razorpay.com
You can use any company domain — razorpay.com, stripe.com, zomato.com, etc.