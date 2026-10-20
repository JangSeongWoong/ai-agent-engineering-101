# Week 07 — Agent Market: Reputation and Verification

Student ID: **26510128**  
Harness: custom OpenAI-compatible Python decision loop, local Ollama `qwen3:4b-instruct`.

## Scope and current status
This submission extends the successful Week 06 A2A buyer/seller agents.
**The student's local market test printed `25/25 passed -> PASS` on 2026-10-20.**
This is a LOCAL test result, not proof of joining the live market.
The genuine join log and live Round 2 deal are still required.

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

## 3. Rounds 0, 1 and 2 — LIVE DATA REQUIRED
The lecture defines R0 (random shop, no reviews), R1 (review/memory-based shop
selection), R2 (shop and buyer signed receipts tied to a genuine market order).
**Do not fill in trade counts, market shares or round comparisons until they
are visible in the actual dashboard and/or `logs/market-kit.log`.**
- Round 0 — actual shop, price, result: **pending evidence**
- Round 1 — actual reviews, selection and result: **pending evidence**
- Round 2 — `verified True` receipt with `review accepted`: **pending evidence**

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
`pricing_policy.py` stores **observed** signed seller deals to
`.market/seller-sales.jsonl`. Market reviews may be imported from a real
dashboard to `.market/seller-reviews.json`, shaped as
`{"shop":"JangSeongWoong","reviews":[{"stars":4,"review":"...", "round":2}]}`.
Only after >=2 real reviews and >=2 observed deals does it adjust opening
asks (+3 for high trust, -5 for low trust or overcharging complaints).
The invariant `ask >= reserve` remains code-enforced.
**Before/after market share and average price are pending live dashboard
data; do not report a price adjustment as demonstrated before actual use.**

### Challenge 2 — avoid dishonest participants
The buyer scores low-star comments, suspicious receipt warnings and prior
receipt mismatches; the official **synthetic** review test demonstrates
it chose the good-review shop 3/3 times, avoiding the bad-review shop.
This is not yet evidence of encountering a live dishonest participant.
A real suspicious shop and avoidance trace from the market must be
recorded in `logs/challenge-2/`.

## 6. Deployment — PENDING
A live deployment requires GitHub claim code from the market join page,
a publicly reachable seller (tunnel or hosted URL), and a running buyer kit.
Use the same local `shop_key.pem` to sign if deploying the seller separately.
Never commit `*.pem`, a claim code, API secrets or tokens.
Record the actual host, market nickname, registration and live verified
ledger line here once the deployment is running.

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
