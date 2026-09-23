# Week 04 — Speech acts in three negotiation formats

## 1. Setup and reproducibility

This experiment uses one buyer LLM and one seller LLM negotiating a single integer price. The buyer opens; the seller has a private integer reserve (lowest acceptable price), while the buyer has a private integer budget (highest acceptable price). Each role receives its own system prompt containing only its own private limit. Neither agent is sent the other agent's limit or the `deal_possible` label. The manager/harness knows the two limits for retrospective evaluation only. The buyer and seller alternate for up to six **messages**, starting with the buyer.

**Fixed settings:** OpenRouter via the OpenAI-compatible API, model `nvidia/nemotron-3-super-120b-a12b:free`; temperature `0.2`, maximum response tokens `350`, turn limit `6`. The same `scenarios.json`, shared role-prompt wording, model, temperature, and turn limit apply to all conditions. `OPENAI_BASE_URL` and `OPENAI_API_KEY` must be supplied in the local terminal; the key is never committed. Every model call also requests `extra_body={"reasoning":{"enabled":False}}`. The runner spaces requests by `AGENT_REQUEST_INTERVAL=4` seconds and retries HTTP 429 up to `AGENT_MAX_RETRIES=3` with increasing waits. Persistent HTTP 429 pauses the experiment without fabricating episode metrics; restarting skips already completed (run, condition, scenario) combinations and leaves failed attempts visible in `results.csv`.

**Shared role prompt:** Each agent is told it is buying/selling the scenario's item, that its own private limit must not be disclosed, to propose/accept only within that limit, and to use only four speech acts: `propose`, `accept-proposal`, `reject-proposal`, `refuse`. It may accept only the other side's outstanding offer. The buyer is required to open.

**The exact three format paragraphs** (the only condition-specific role-prompt text) are in `negotiation.py`, `FORMAT`:

- `free`: “Reply in plain English. Express your chosen action naturally; no tags or JSON. When making an offer state a clear integer price. When accepting, explicitly agree to the last price proposed by the other side.”
- `tagged`: “Start every message with exactly one tag: (propose), (accept-proposal), (reject-proposal), or (refuse). Then write plain English. For (propose) state one integer price. For (accept-proposal), accept ONLY the other side's last proposed price.”
- `structured`: “Reply with exactly one JSON object, with performative one of propose, accept-proposal, reject-proposal, refuse; and content an object. For propose include an integer price: {"performative":"propose","content":{"price":70}}. For other acts use "content":{}. No code fences, commentary, or extra fields.”

**Reader prompt:** “You are a protocol reader, not a negotiating party. Interpret ONE message and return exactly one JSON object with keys performative and price. performative MUST be one of propose, accept-proposal, reject-proposal, refuse. For a price proposal, price MUST be an integer; for all other acts, price MUST be null. If the message is a question without a matching act, use refuse. Do not change the act based on whether an offer is economically attractive. Do not add commentary or markdown.”

In `free`, the LLM reader labels every message's act and price; in `tagged`, a regex reads the act and the LLM reader extracts a price only for proposals; in `structured`, a JSON parser extracts both without a reader model call. A parser failure counts toward `format_errors`, and the agents can continue until the turn cap. An invalid acceptance (no outstanding **other-side** offer) is also a format/protocol error and does not create a deal. An accepted offer ends the episode with its outstanding integer price; `refuse` ends with `no_deal`; reaching the turn limit ends `open`.

**Metrics:** `deal_possible = int(reserve <= budget)`. `correct=1` exactly for a valid deal when a deal is possible or for `no_deal` when none is possible; otherwise 0. `violation=1` if a recorded deal is below reserve, above budget, or lacks a valid price. `turns` counts exchanged buyer/seller messages, `format_errors` counts failed/invalid protocol reads, and `reader_calls` counts LLM calls made **to interpret messages** (not the buyer/seller response-generation calls). Crashed or rate-limited episodes remain in the CSV with blank measurements and the error in `note`. A completed pair is never rerun automatically; incomplete pairs can be retried and their earlier failure row is retained.

**How to run, from the Week 04 submission directory (PowerShell):**

```powershell
$env:OPENAI_BASE_URL="https://openrouter.ai/api/v1"
$env:OPENAI_API_KEY="<YOUR_OPENROUTER_API_KEY>"
$env:AGENT_MODEL="nvidia/nemotron-3-super-120b-a12b:free"
$env:AGENT_TEMPERATURE="0.2"
$env:AGENT_MAX_TOKENS="350"
$env:AGENT_TURN_LIMIT="6"
$env:AGENT_REQUEST_INTERVAL="4"
$env:AGENT_MAX_RETRIES="3"

python negotiation.py --max-episodes 1
```

Re-run the last command as the free-model quota permits: it appends one completed episode then stops, without overwriting previous results. Once sufficient quota is available, `python negotiation.py` resumes all remaining episodes. A clean reproduction should use a separate copy of this directory **without pre-existing `results.csv` and `logs/`**, since outputs append. The four scenarios were committed before any episodes were run.

From the repository root, check structure:

```powershell
python scripts/check_week04.py submissions/26510128/week-04
```

## 2. Results

**Pending actual API episodes. Do not enter fabricated measurements.** After running at least three repeats of all four scenarios in each condition (36 completed episodes in total, excluding any preserved failed attempts), replace this section with a per-condition summary and the full per-episode `results.csv` table.

| Condition | Completed episodes | Correct (count) | Violations (count) | Mean turns | Format errors (total) | Reader calls (total) |
|---|---:|---:|---:|---:|---:|---:|
| free | pending | pending | pending | pending | pending | pending |
| tagged | pending | pending | pending | pending | pending | pending |
| structured | pending | pending | pending | pending | pending | pending |

The per-episode table must reproduce every row of `results.csv`, including any aborted attempts with blank counts and a failure note.

## 3. FIPA-ACL and the three reproduction conditions

| Dimension | FIPA-ACL reference | Free | Tagged | Structured |
|---|---|---|---|---|
| Where illocutionary force lives | Required `performative` field in the ACL message envelope | In natural-language context; inferred by the reader LLM | Parenthesized literal tag at start of text, matched by regex | JSON `performative` field, parsed programmatically |
| Content language | Declared content language and ontology with agreed semantics | Unconstrained plain English | Plain English after the tag | JSON object with an integer `content.price` for proposals |
| Who interprets content | Receivers use specified content-language semantics | LLM reader classifies act and extracts price on every message | Regex reads act; LLM reader extracts proposal price only | JSON parser validates act and proposed integer |
| How conversation ends | Depends on the agreed interaction protocol and its termination rules | Parsed acceptance/refusal or six-message cap | Tagged acceptance/refusal or cap | Parsed JSON acceptance/refusal or cap |
| What guarantees sincerity | Declarative act semantics describe intentions, but explicit act labels alone do not independently enforce truthful private limits | System prompts only; outcome checked after the fact | Same prompts; tag provides no independent budget verification | Same prompts; typed fields provide no independent budget verification |
| What a message costs to read | Parsing/semantic interpretation and message transport depend on infrastructure | One additional LLM reader call per exchanged message | One extra reader call for a tagged proposal; regex alone for other acts | No model reader calls; local JSON parser |
| Failure modes | Mismatched ontology/content language, unsupported act, deceptive or inconsistent agents | Ambiguous English, unsupported questions, reader misclassification, parse/API failures | Missing/invalid tag or failed proposal-price reader | Invalid JSON/schema/price, valid-looking yet insincere offers |

## 4. Interpretation

**Pending actual logged results.** Compare the observed condition-level correctness, violations, mean turns, format errors and reader calls without claiming that small, quota-interrupted samples establish a population effect. Include concrete references to `logs/<run>.txt`: one example of an ambiguous free-form question or reader misclassification (if observed), a tagged proposal and its reader cost, a structured parsed proposal and its zero reader-model cost, and any private-limit violation. If an expected failure does not occur, say so rather than inventing one. Separate model/provider failures from format-specific failures, and retain any rate-limited episodes as incomplete observations.
