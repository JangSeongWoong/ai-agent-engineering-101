# Week 02 A/B Experiment Report

## 1. Variant Definition

This experiment compares two harnesses while keeping the model, task, tools, and input file fixed.

- **Common settings**
  - Task: find the hour (HH:00) with the most `ERROR` lines in `app.log`
  - Expected answer: `14:00`
  - Tools: `read_file(path)` and `count_pattern(path, pattern)`
  - Model/provider: OpenRouter with the same model for both harnesses
  - Input: the provided `app.log`, unchanged

- **ReAct harness**
  - Reconsiders the next action after each observation.
  - Keeps the full interaction history in context.
  - Stops when the model returns a final answer or the iteration cap is reached.
  - Tool errors are returned as observations and the model can adapt on the next step.

- **Plan-then-Execute harness**
  - Creates the full plan first as a JSON list, then executes the plan step by step.
  - Allows at most one replan if an `OFF_PLAN` condition occurs.
  - Uses the same tools and model as ReAct, so the main experimental difference is the harness behavior.

The main harness-axis differences are therefore context/decision timing, termination behavior, and error-recovery flexibility.

## 2. Measurements

Run the experiment with:

```powershell
python run_ab.py --runs 3
```

Then copy the six rows from `results.csv` into the table below.

| Run | Harness | Success | Tokens | Iterations | Interventions | Note |
|---:|---|:---:|---:|---:|---:|---|
| 1 | react |  |  |  |  |  |
| 2 | react |  |  |  |  |  |
| 3 | react |  |  |  |  |  |
| 4 | plan_exec |  |  |  |  |  |
| 5 | plan_exec |  |  |  |  |  |
| 6 | plan_exec |  |  |  |  |  |

## 3. Interpretation

Complete this section after the six runs. Compare success rate, token usage, iteration count, and any replanning or failures shown in the logs. Explain which harness characteristic likely caused each observed difference. For example, if ReAct uses more iterations but succeeds more consistently, connect that to its ability to reconsider after each observation. If Plan-then-Execute uses fewer tokens or iterations but occasionally fails because the initial plan is malformed or too rigid, connect that outcome to its up-front planning and limited replanning policy.

Do not change the success criterion after seeing the results; failed runs remain part of the experiment.
