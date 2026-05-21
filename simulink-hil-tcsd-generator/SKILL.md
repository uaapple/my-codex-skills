---
name: simulink-hil-tcsd-generator
description: Generate coverage-oriented HIL TCSD Excel test cases from Simulink models. Use when the user provides a specific `.slx` model and matching `.mat` data file and asks Codex to create, repair, or backfill HIL test cases in the same TCSD style as the ACCtl/PwrLimEng examples, especially when Simulink Agentic Toolkit, Cornex/ITK dependencies, `.sldd` data dictionaries, or simulation-derived expected outputs are involved.
---

# Simulink HIL TCSD Generator

Use this skill to turn one Simulink module model plus its MAT data file into a TCSD Excel workbook whose tests prioritize model coverage.

## Core Rules

- Use Simulink Agentic Toolkit first for model understanding: `model_overview`, `model_read`, `model_query_params`, `model_resolve_params`, and `evaluate_matlab_code`.
- If direct MATLAB MCP tools are unavailable, run `scripts/satk_eval.py` with a MATLAB code file.
- Copy `assets/support-package` into the working folder before loading the model unless the project already has equivalent Cornex/ITK dependencies.
- Use `assets/templates/tcsd_template.xlsx` as the TCSD style template.
- Fill expected outputs only for top-level Outport signals. Never put model-internal/local signals in `Action` as `expValue(...)`.
- TCSD expectation syntax is `outSignal = expValue(var1, duration, offset);`. `var1` is a numeric expected value or an input-signal name string, `duration` is the expected-value check duration, and `offset` is the offset relative to the current time interval. Extra arguments are time-window controls, not numeric tolerance.
- For simulation-sampled values, write `expValue(value)` by default. Use `expValue(value,duration,offset)` only when deliberately checking a stable value over that time window.
- Do not write hold-style expectations for outputs that keep changing before the next action step. Backfill only outputs that are stable across the following hold interval; omit ramping outputs from that Test unless deliberately generating dense per-sample staircase expectations.
- Generate tests for coverage first: enable/disable branches, threshold sides, limiters, lookup-table regions, delay/latch behavior, divide-by-zero protection, and mode switches.
- Treat decision outcomes as explicit coverage obligations. For `MinMax`, make each input become the selected output at least once. For `MultiPortSwitch`, cover every valid selector value and the default/otherwise branch when present. For `Saturate`, cover below-low, pass-through, and above-high regions.
- For filtered selector or gradient-limited logic, use Initialization, long enough hold time, or documented scalar parameter overrides to make the intended outcome actually settle before expecting coverage.
- Do not stop after one static draft when coverage evidence is available. Use coverage reports, screenshots, or simulation probes to add supplemental tests for uncovered decision outcomes, then rebuild/backfill the workbook.
- When regenerating after coverage feedback, create a versioned workbook/output JSON rather than overwriting the last reviewed workbook unless the user explicitly asks for overwrite.
- Preserve user files. Do not overwrite the source `.slx` or `.mat`; write outputs under `outputs/`.

## Workflow

1. **Prepare workspace**
   - Confirm the user-provided `.slx` and matching `.mat` are in the working folder.
   - Copy the support package:
     ```bash
     cp -R /path/to/skill/assets/support-package/. .
     ```
   - Keep the model-specific `.slx` and `.mat` supplied by the user as the authority.

2. **Load and inspect the model**
   - Use SATK to load support paths, run `init_Global.m`, load the `.mat`, load `ITKLib.slx`, then load the model.
   - Derive root Inport and Outport order from the model, not from guesses.
   - Read the subsystem hierarchy and the blocks around Switch, Multiport Switch, Lookup Table, Delay, Latch, GradientLimiter, Safe_Divide, Min/Max, and logical operators.
   - Use static `.slx` XML inspection as a cheap supplement when block paths, SIDs, constants, or line connectivity are needed before a full MATLAB probe.
   - Build a block-level coverage-obligation checklist before writing tests. See `references/coverage-closure.md`.

3. **Design TCSD cases**
   - Create one TestGroup and multiple Test rows.
   - Each Test should describe one functional coverage target.
   - In `Test Case Description`, state the test method such as boundary value, equivalence class, requirement analysis, or coverage feedback.
   - In `Initialization`, assign all root inputs and any needed parameter overrides (`p Param = value;`).
   - In `Action`, step inputs over time with `[+100ms]`, `[+0.2s]`, etc.
   - Use explicit time units (`s`, `ms`, etc.), terminate executable statements with English semicolons, and write comments with `//`.
   - Describe input/output meanings or condition changes in `Action` comments when they clarify the coverage target.
   - Add targeted supplemental Tests for uncovered `MinMax`, `MultiPortSwitch`, `Saturate`, relational, and selector outcomes before optimizing for compactness.
   - Keep coverage-only stimuli even when their outputs are dynamic and therefore have few expected-output lines.
   - Add only top-level output expectations.

4. **Build the Excel**
   - Either edit the template directly or create a JSON spec and run `scripts/build_tcsd_from_json.py`.
   - Keep sheet name `TCSD`, columns, freeze pane, and reviewed status consistent with the template.

5. **Backfill expected outputs from simulation**
   - Extract actions with `scripts/extract_tcsd_cases.py`.
   - Run `scripts/simulate_tcsd_cases.m` through `scripts/satk_eval.py`.
   - Apply results with `scripts/backfill_expected_outputs.py`.
   - Validate that every `expValue(...)` left side is a root Outport.

6. **Verify**
   - Run `unzip -t` on the output workbook.
   - Inspect the TCSD sheet with a spreadsheet library or artifact-tool.
   - Check there are no internal-signal expectations and no unsupported input values exposed by simulation.
   - If model coverage evidence is available, verify decision coverage first. Add tests or record an explicit unreachable/invalid-selector reason for any remaining uncovered outcome.

## References

- Read `references/hermes-agent-handoff.md` when handing this workflow to another agent, when the agent lacks the original conversation context, or when assessing whether the skill is ready for Hermes-style execution.
- Read `references/workflow-details.md` when starting a new model.
- Read `references/coverage-closure.md` when designing or repairing cases for coverage.
- Read `references/tcsd-rules.md` before editing or validating the workbook.
- Read `references/support-package.md` when dependency loading fails.
