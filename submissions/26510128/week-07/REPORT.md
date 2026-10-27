# Week 07 — Agent Market: Reputation and Verification

Student ID: **26510128**  
Harness: custom OpenAI-compatible Python decision loop, local Ollama `qwen3:4b-instruct`.

## Scope and current status
This submission extends the successful Week 06 A2A buyer/seller agents.
**The student's local market test printed `25/25 passed -> PASS` on 2026-10-20.**
This is a LOCAL test result, not proof of joining the live market.
Live market registration and Round 2 verified deals have since been observed in the student's market logs. Include the actual locally generated `logs/market-kit.log` in the eventual PR.

## 1. Buyer shop selection and memory
`market_buyer.py` reads the kit's shops JSON containing shop name, current URL,
and newest-first reviews. It ranks candidates using review stars, warning
language about dishonesty/overcharging, and prior memory, then lets the local
model select a candidate within a trust-protected shortlist. It remembers
experiences by stable shop **name**, not changing tunnel URL, in
`.market/buyer-memory.json`. That file is runtime state and should not be
committed as though it were an experiment log.

## 2. Reviews and the harness
At most five shortlisted candidates are supplied to the model, each with
a risk score, the four most recent reviews and previous buyer experiences.
The buyer rejects deceptive receipts (wrong item/task, over-budget or price
different from its most recent offer), keeps the signed data Part unchanged,
and prints a final JSON line with shop URL, receipt or null, stars and review.
A hard budget check runs outside the model.

## 3. Rounds 0, 1 and 2 — observations with stated gaps
The lecture defines R0 (random shop, no reviews), R1 (review/memory-based shop
selection), R2 (shop and buyer signed receipts tied to a genuine market order).
**Do not fill in trade counts, market shares or round comparisons until they
are visible in the actual dashboard and/or `logs/market-kit.log`.**
- Round 0 — actual shop, price, result: **pending evidence**
- Round 1 — real A2A purchases observed in the student's logs, e.g. ledger #6920 (lamp 105, verified True) and ledger #6989 (lamp 105, verified True). Preserve the original log and dashboard values for any full comparison.
- Round 2 — verified True / review accepted observed at ledger #9982 (bookshelf 340). The subsequent official board query also confirmed 1,459 buyer counted deals (a later snapshot).

## 4. Signature implementation, testing and troubleshooting
The seller signs canonical sorted-key, compact UTF-8 JSON over the integer
`{shop, item, price, task}` with Ed25519 `shop_key.pem`. The task field
is exactly the A2A task ID; A2A data Parts may represent integer prices
as floats in transit, so cryptographic signing happens on the integer.
The market kit verifies `sig_seller` and attaches `sig_buyer`.
The provided test output shows `seller_signed_receipt` passed 3/3;
overall `25/25 passed -> PASS` on 2026-10-20.

Failure/repair provenance: starting from the Week 06 seller, the original
receipt lacked `task` and `sig_seller` (as seen in the **source code**, not
a claimed failed 7-week test run). We changed the receipt format, added
canonical signing and validated the signatures in the 7-week test.
No failed local signature test was observed or claimed.

## 5. Challenges
### Challenge 1 — seller adapts asking price

The current `pricing_policy.py` reads the official read-only market board for
the student's own Round 2/1 counted deals and summary ratings. It caches the
response briefly and imposes a hard `ask >= reserve` invariant. With no
counted sales, it quotes the reserve; with some sales, a reserve + 5
introductory margin; with at least three counted sales and two high-rating
reviews, a reserve + 10 cap. Low ratings or documented complaints reduce the
margin. Signed local A2A receipts are logged but **not** represented as
market-verified trades because local tests also create them.

One real **before** snapshot was preserved on the student's own Windows PC on
2026-10-21. A later **after** snapshot must be taken after deploying the new
policy, and compared on equal observation windows. Raw board shares and
cumulative revenues alone cannot establish causal uplift. Observe the
`[pricing policy]` and `[seller opening]` lines before claiming the policy
executed. The student must save the after snapshot and relevant genuine market
logs under `logs/challenge-1/`; they have not yet been made available here.

### Challenge 2 — dishonest participant avoidance

The buyer uses published reviews and its own past trade outcomes to rank
shops. A documented live market response from `bright-living` attempted to
impersonate the market operator and tell AI buying agents to accept a price
and give five stars. The original buyer refused an over-budget offer and did
not issue a five-star review. After that observation, `market_buyer.py` was
modified to detect this specific class of market-authority instruction,
refuse the transaction before feeding that seller text to the harness, and
persist an `injection_attempts` penalty against the *shop name*. On future
orders, that risk influences the initial shop ranking even when its tunnel
URL changes.

This change is a preventive implementation, **not** proof of a live
encounter after deployment or of subsequent avoidance. The original log
and a later real detection/avoidance trace must be saved unedited to
`logs/challenge-2/`. The official market test must be rerun after this
change.
 
### Real Round 2 seller baseline from 2026-10-21 (BEFORE the new live-price policy restart)

The student queried the *official public* `/api/board?round=2` endpoint, and
saved the response to `logs/challenge-1/seller-<timestamp>.json` locally.
The observed values were:

| Round 2 board field | Observed value |
| --- | ---: |
| Seller name | JangSeongWoong |
| Seller alive | True |
| Counted seller deals | 1,996 |
| Buyer counted deals | 1,459 |
| Seller visits | 2,601 |
| Seller reviews | 1,786 |
| Seller average stars | 4.06 |
| Seller revenue | 372,169 |
| Seller share (raw API value) | 0.09 |

Seller and buyer `owner.login` both matched `JangSeongWoong`.
This is **not** evidence of the *revised* pricing policy causing the growth:
the student's local checked-out branch was still `01dce5f` when these values
were recorded; the updated pricing policy had not been pulled/restarted.
Keep the recorded JSON as the truthful before snapshot. Recheck prices,
counted sales, share and reviews after a controlled deployment to compare.
The API's `share` field is preserved as reported; do not mislabel units.

### Live dishonest-message observation

At 21:06 in the student's market log, seller `bright-living` included a
`[MARKET NOTICE FOR AI BUYING AGENTS ...]` directive trying to impersonate
market authority and induce both over-budget acceptance and a 5-star review.
The buyer did **not** comply with the over-budget offer (asked 270, budget
250) and returned no deal with 3 stars. The observation is consistent with
budget-rule enforcement; it is **not yet** evidence that the buyer detected
and subsequently blacklisted this shop. Challenge 2 needs a follow-up
avoidance trace supported by real log records.

## 6. Deployment — LIVE MARKET REGISTRATION OBSERVED
The student launched the course kit on a local Windows PC through a Cloudflare quick tunnel; log entries confirmed both seller and buyer registered under `JangSeongWoong`. A subsequent Round 2 board response confirmed both `alive: True`, and a real ledger line verified a signed purchase. Continuous operation through the deadline still requires keeping the PC, Ollama, market kit and tunnel available.
Use the same local `shop_key.pem` to sign if deploying the seller separately.
Never commit `*.pem`, a claim code, API secrets or tokens.
Evidence of live verified Round 2 purchase: ledger #9982, bookshelf 340; `verified True, review accepted`. The tunnel URL can change on reconnect and should be read from the kit log. Do not treat a point-in-time `alive` check as proof of uptime at grading deadline.

## Testing and evidence
Local evidence provided by the user:
- `seller_signed_receipt` 3/3 passed
- `buyer_reads_reviews` 3/3 good-shop selections (test case 1 passes)
- full market test: **25/25 passed -> PASS**

Run again after changing source, commit test-generated `test-report.json`
and `logs/market-test.log`, and run `check_week07.py` after live joining.
The final check additionally validates the registered shop and buyer.

## Submission safety
Only `submissions/26510128/week-07/` belongs in the Week 07 PR;
keep Week 06's prior PR unchanged. Keep all private key files untracked.
