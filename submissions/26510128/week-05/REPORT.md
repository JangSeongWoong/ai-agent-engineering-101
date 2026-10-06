# Week 05 — Negotiation market as an MCP server

## 1. Setup and reproducibility

This submission moves the Week 04 buyer/seller negotiation into an authenticated MCP market over Streamable HTTP. The market owns negotiation state. Each party connects with a bearer token minted by a runner-only admin route, and the server determines the caller role and negotiation from that token rather than from tool arguments.

The final experiment uses the required `prompt_inject` and `server_inject` conditions, four scenarios, three repeats per condition, and an eight-host-turn cap. The same role prompts, host implementation, model, temperature, and scenarios are used in both required conditions.

Planned local setup:

- Host: custom Python MCP host in `run_experiment.py`
- MCP server: `market_server.py`
- Transport: Streamable HTTP at `http://127.0.0.1:8001/mcp`
- Model runtime: local Ollama OpenAI-compatible endpoint
- Model: `qwen3:4b-instruct`
- Temperature: `0.2`
- Turn limit: `8`
- Conditions: `prompt_inject`, `server_inject`

The runner opens a negotiation through `/admin/open` and receives two bearer tokens. Every token is bound to one role and one negotiation. In `prompt_inject`, the private limit exists in the system prompt only. In `server_inject`, the same prompt is used and the token additionally carries the caller's price limit. The server checks that limit before executing `propose` or `accept_proposal`.

The injection is added only to the buyer's view of seller proposals returned by `get_negotiation`, using the assignment's required sentence and `raised = max(reserve, budget) + 30`.

Run instructions:

```powershell
pip install -r requirements.txt

$env:MARKET_ADMIN_TOKEN="<random-local-admin-secret>"
$env:OPENAI_BASE_URL="http://localhost:11434/v1"
$env:OPENAI_API_KEY="ollama"
$env:AGENT_MODEL="qwen3:4b-instruct"
$env:AGENT_TEMPERATURE="0.2"
$env:AGENT_TURN_LIMIT="8"
```

Start the server in terminal 1:

```powershell
python market_server.py
```

Then, from terminal 2:

```powershell
python auth_checks.py
python run_experiment.py
```

The final numerical tables and interpretation below will be completed from the actual submitted logs and `results.csv`.

## 2. Results

Pending actual local runs.

| Condition | Episodes | Correct | Violations | Attempted violations | Refused calls | Mean turns |
|---|---:|---:|---:|---:|---:|---:|
| prompt_inject | pending | pending | pending | pending | pending | pending |
| server_inject | pending | pending | pending | pending | pending | pending |

A full per-episode table will be added after the 24 required episodes are completed.

## 3. FIPA-ACL compared with this MCP market

| Dimension | Week 04 / FIPA-ACL framing | Week 05 MCP market |
|---|---|---|
| Who the sender is and who says so | A communicative message has a sender/performative that the protocol or reader interprets | The server derives the caller role from the bearer token; there is no role argument |
| Where the act lives | Natural language, a tag, or a structured performative field | The selected MCP tool name: `propose`, `accept_proposal`, `reject_proposal`, or `refuse` |
| What the content is | Message payload / content language | Typed MCP tool arguments such as `negotiation_id`, `price`, and optional note |
| Who enforces the limit | Primarily the agent prompt | Prompt only in `prompt_inject`; prompt plus server token policy in `server_inject` |
| What can be verified from outside | Parsed messages, outcomes, and protocol logs | HTTP 401 challenge, token binding, turn ownership, tool errors, market state, attempted violations, and refused calls |
| Failures | Ambiguity, malformed messages, reader/parser failures | Invalid token, wrong negotiation, out-of-turn move, token-limit refusal, or model/tool failure |

## 4. Interpretation

Pending actual logs. The final interpretation will compare which layer held under the injected budget notice, cite concrete tool-call/result lines, and count how many server refusals were followed by a valid move by the same role in the same host turn.
