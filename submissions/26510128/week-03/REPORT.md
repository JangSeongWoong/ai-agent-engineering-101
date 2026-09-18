# Week 03 — Contract Net with LLM Contractors

## 1. Setup

This experiment reproduces the Contract Net Protocol with one manager and three LLM contractors. The manager sends the same task announcement to all three contractors, each contractor independently decides whether to bid, and the manager awards the task to the valid bidder with the highest confidence.

### Provider and model

- Provider: OpenRouter through the OpenAI-compatible API
- Model: `nvidia/nemotron-3.5-lightning:free`
- Temperature: `0.2`
- Max tokens per contractor bid: `220`
- Human intervention: none
- Task set: `tasks.json`, fixed before the experiment
- Runs: at least 3 per condition

### Contractors and prompts

The same JSON response schema is required in all conditions:

```json
{"bid": true, "confidence": 0, "reason": "one short sentence"}
```

The three contractor names are A, B, and C.

- Baseline:
  - A: numerical calculation and algebra
  - B: writing, editing, and tone
  - C: programming and debugging
- Homogeneous:
  - A, B, and C all use the same general problem-solving skill description
- Overconfident:
  - Same as baseline, except contractor C is additionally instructed to always bid with confidence 95 or higher

The manager does not use an LLM. It awards each task to the valid bidder with the highest confidence. Confidence ties are broken deterministically by contractor name (A before B before C).

### Message accounting

For every task:

- one announcement sent to each contractor = 3 messages,
- each valid bid with `bid=true` = 1 message,
- one award, if any contractor bids = 1 message.

Unparseable model output is treated as no bid and is recorded in the log and the run note.

### How to run

From `submissions/26510128/week-03`:

```powershell
$env:OPENAI_BASE_URL="https://openrouter.ai/api/v1"
$env:OPENAI_API_KEY="<YOUR_OPENROUTER_API_KEY>"
$env:AGENT_MODEL="nvidia/nemotron-3.5-lightning:free"
$env:AGENT_TEMPERATURE="0.2"
$env:AGENT_MAX_TOKENS="220"

python contract_net.py --runs 3
```

The command appends nine rows to `results.csv` and writes one log file per run under `logs/`.

Structural checker, from the repository root:

```powershell
python scripts/check_week03.py submissions/26510128/week-03
```

## 2. Results

This table should match the nine rows in `results.csv` after the experiment is run.

| Run | Condition | Tasks | Correct | Messages | Unassigned | Misawards | Note |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | baseline | — | — | — | — | — | pending run |
| 2 | baseline | — | — | — | — | — | pending run |
| 3 | baseline | — | — | — | — | — | pending run |
| 4 | homogeneous | — | — | — | — | — | pending run |
| 5 | homogeneous | — | — | — | — | — | pending run |
| 6 | homogeneous | — | — | — | — | — | pending run |
| 7 | overconfident | — | — | — | — | — | pending run |
| 8 | overconfident | — | — | — | — | — | pending run |
| 9 | overconfident | — | — | — | — | — | pending run |

## 3. Smith (1980) vs. this reproduction

| Comparison item | Smith (1980) distributed sensing | Week 03 reproduction |
|---|---|---|
| Who the nodes are | Distributed sensing/computing nodes with known capabilities and local information | Three LLM contractors A, B, and C with capabilities described in system prompts |
| How a task is announced | Manager broadcasts a task abstraction, eligibility specification, bid specification, and expiration time | Manager sends the same structured text announcement to A, B, and C |
| How a bid is produced | A node derives a bid from explicit state/capability information and fixed rules | An LLM judges task-skill fit and generates `bid`, `confidence`, and `reason` |
| What guarantees bid honesty | Bid content is grounded in known node properties and programmed rules; deception/overconfidence is not the central assumption | No protocol-level guarantee. Confidence is self-reported by the LLM and can be distorted by prompting |
| How an award is chosen | Manager evaluates bids according to the bid specification and local selection rule | Highest confidence among valid bidders; deterministic contractor-name tie-break |
| What allocation quality means | A useful contractor is selected so the distributed sensing/task-sharing objective can be completed effectively | The awarded contractor matches the predeclared `gold` contractor in `tasks.json` |
| What negotiation costs | Communication and bid-processing overhead across distributed nodes | Counted messages: announcements + positive bids + awards; model calls also add latency/token cost, though tokens are not a required Week 03 metric |
| Failure modes | No eligible bidder, communication/availability issues, poor local selection or decomposition | No bid, malformed JSON, model-call failure, homogeneous ambiguity, confidence miscalibration, overconfident contractor stealing awards |

## 4. Interpretation

Complete this section after the nine runs. The interpretation must connect observed metric changes to the condition that caused them and cite concrete log lines. In particular, compare baseline allocation quality with homogeneous ambiguity and with the overconfident condition. If contractor C wins non-code tasks in the overconfident condition because it reports confidence 95 or higher, treat that as evidence that the Contract Net award rule has no built-in defense against a strategically or incorrectly inflated bid. Also report any malformed JSON replies as a failure mode rather than deleting those runs.
