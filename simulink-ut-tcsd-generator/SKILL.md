---
name: simulink-ut-tcsd-generator
description: Generate coverage-oriented Simulink unit-test TCSD Excel cases from models. Use when the user provides a specific `.slx` model and matching `.mat` data file and asks Codex to create, repair, or backfill unit-test cases in the same TCSD style as the ACCtl/PwrLimEng examples, especially when Simulink Agentic Toolkit, Cornex/ITK dependencies, `.sldd` data dictionaries, or simulation-derived expected outputs are involved. When this skill is named for a model, treat the full coverage-first UT TCSD workflow as the default task contract without requiring the user to repeat it.
---

# Simulink Unit-Test TCSD Generator

Use this skill to turn one Simulink module model plus its MAT data file into a TCSD Excel unit-test workbook whose tests prioritize model coverage.

## Default Invocation Contract

When the user invokes or names `simulink-ut-tcsd-generator` and provides a model work folder, `.slx`, or `.mat`, assume the complete workflow below by default. The user should not need to restate the standard requirements every time.

Minimal user prompt is enough:

```text
使用 simulink-ut-tcsd-generator，为 <workdir>/<model>.slx 和 <workdir>/<model>.mat 生成单元测试 TCSD 用例。
```

By default, you must:

- Copy `assets/support-package` into the model workdir before loading the model unless equivalent dependencies already exist there.
- Use Simulink Agentic Toolkit / SATK for model reading and MATLAB evaluation.
- Generate coverage-first unit-test cases, with decision coverage as the first optimization target.
- Fill `expValue(...)` only for top-level Outports, never for internal/local/MIL signals.
- Simulate successfully when possible, then backfill only stable top-level output expectations from simulation results.
- Avoid hold-style expected values for dynamic, ramping, or continuously changing outputs.
- Build the Excel workbook from `assets/templates/tcsd_template.xlsx`; this bundled template is the canonical TCSD input format expected by the downstream automatic test software.
- Write the templated workbook to `outputs/<model>_Test0001_tcsd.xlsx`, or the next versioned filename if that output already exists.
- Preserve a generation JSON spec, simulation-result JSON, and a short validation report alongside the workbook.

Ask the user only when required input files or runtime dependencies are missing, or when the model cannot be loaded after applying the bundled support package.

## Core Rules

- Use Simulink Agentic Toolkit / MCP first for model understanding: `model_overview`, `model_read`, `model_query_params`, `model_resolve_params`, and `evaluate_matlab_code`.
- If direct MATLAB MCP tools are unavailable, run `scripts/satk_eval.py` with a MATLAB code file.
- Do not replace SATK/MCP/MATLAB model reading with static `.slx` XML parsing. Static XML is only a supplement after SATK/MCP/MATLAB has been attempted or used, and only for exact SIDs, block parameters, or connectivity.
- Do not pipe `.slx`/zip/XML output directly into interpreters such as `python3 -c`, `perl`, `ruby`, or `node -e`. If static XML inspection is needed, use `scripts/inspect_slx_xml.py MODEL.slx --pattern REGEX` or a checked-in file-reading script.
- Copy `assets/support-package` into the working folder before loading the model unless the project already has equivalent Cornex/ITK dependencies.
- Use `assets/templates/tcsd_template.xlsx` as the required TCSD workbook template. Preserve its `TCSD` sheet, columns, row conventions, freeze pane, styles, comments/status options, and workbook structure so the downstream automatic test software can import it.
- Write vector root-input assignments element by element in TCSD, for example `Sig 1=5000;`, `Sig 2=5000;`. Do not write whole-vector input assignments like `Sig = [5000 5000];` unless the target importer has been explicitly confirmed to support them.
- End every Test `Action` with a final relative delay marker such as `[+0.1s]` so the target has a run/sampling interval after the last assignment or expectation. Do not let a Test end on an input assignment or `expValue(...)` line.
- Fill expected outputs only for top-level Outport signals. Never put model-internal/local signals in `Action` as `expValue(...)`.
- TCSD expectation syntax is `outSignal = expValue(var1, duration, offset);`. `var1` is a numeric expected value or an input-signal name string, `duration` is the expected-value check duration, and `offset` is the offset relative to the current time interval. Extra arguments are time-window controls, not numeric tolerance.
- For simulation-sampled values, write `expValue(value)` by default. Use `expValue(value,duration,offset)` only when deliberately checking a stable value over that time window.
- Do not write hold-style expectations for outputs that keep changing before the next action step. Backfill only outputs that are stable across the following hold interval; omit ramping outputs from that Test unless deliberately generating dense per-sample staircase expectations.
- Generate tests for coverage first: enable/disable branches, threshold sides, limiters, lookup-table regions, delay/latch behavior, divide-by-zero protection, and mode switches.
- Treat decision outcomes as explicit coverage obligations. For `MinMax`, make each input become the selected output at least once. For `MultiPortSwitch`, cover every valid selector value and the default/otherwise branch when present. For `Saturate`, cover below-low, pass-through, and above-high regions.
- Treat every `Logical Operator` block as an MC/DC obligation. For N-input OR, include an all-false case plus one case per input where only that input is true. For N-input AND, include an all-true case plus one case per input where only that input is false. Account for NOT/inverted upstream signals by targeting the truth value at the operator input, not just the raw root signal value.
- For every `Saturate` block, identify the pre-saturation input signal and prove it is below the lower limit, inside range, and above the upper limit. Do not infer saturation coverage only from extreme root inputs or from the saturated output value. If the upstream lookup/calibration range cannot cross a limit with valid inputs, mark that outcome unreachable rather than forcing unsafe table edits.
- For every `Abs` block, design coverage on the pre-Abs source signal: negative, zero, and positive values. Do not treat a positive `Abs` output as covering a positive source input.
- For every `Switch` or `RelationalOperator`, inspect the actual trigger/criterion and drive the trigger signal to both sides of the condition. For sign-based criteria such as `< 0`, `<= 0`, `~= 0`, or `u2 ~= 0`, include explicit negative, zero, and positive/equality-side values as applicable; do not assume toggling an adjacent mode or selector covers the true branch.
- For filtered selector or gradient-limited logic, use Initialization, long enough hold time, or documented scalar parameter overrides to make the intended outcome actually settle before expecting coverage.
- A TCSD comment or Test description is not coverage evidence. After coverage feedback names a missing outcome, treat it as unresolved until a rerun coverage report or a targeted simulation probe shows the intended block input, selector, or branch actually occurred.
- When repairing misses, probe intermediate decision inputs if needed for stimulus design, but never write those internal signals as TCSD `expValue(...)` expectations.
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
   - Use static `.slx` XML inspection only as a supplement after SATK/MCP/MATLAB model reading, when block paths, SIDs, constants, or line connectivity are needed. Prefer `scripts/inspect_slx_xml.py`; do not use shell pipelines that feed zip/XML output into inline interpreter commands.
   - Build a block-level coverage-obligation checklist before writing tests. See `references/coverage-closure.md`.

3. **Design TCSD cases**
   - Create one TestGroup and multiple Test rows.
   - Each Test should describe one functional coverage target.
   - In `Test Case Description`, state the test method such as boundary value, equivalence class, requirement analysis, or coverage feedback.
   - In `Initialization`, assign all root inputs and any needed parameter overrides (`p Param = value;`).
   - In `Action`, step inputs over time with `[+100ms]`, `[+0.2s]`, etc.
   - Expand vector root inputs into element assignments, for example `EMTqFil_dtqIncGrdt 1=5000;` through `EMTqFil_dtqIncGrdt 4=5000;`.
   - Add a final `[+0.1s]` or equivalent final delay at the end of every Test `Action`.
   - Use explicit time units (`s`, `ms`, etc.), terminate executable statements with English semicolons, and write comments with `//`.
   - Describe input/output meanings or condition changes in `Action` comments when they clarify the coverage target.
   - Add targeted supplemental Tests for uncovered `MinMax`, `MultiPortSwitch`, `Saturate`, `Logical Operator`, relational, and selector outcomes before optimizing for compactness.
   - For each supplemental Test, record the exact missing decision outcome it targets. Do not count it as closed merely because the stimulus appears plausible.
   - Keep coverage-only stimuli even when their outputs are dynamic and therefore have few expected-output lines.
   - Add only top-level output expectations.

4. **Build the Excel**
   - Start from `assets/templates/tcsd_template.xlsx`; do not create a fresh workbook from scratch.
   - Either edit a copy of the template directly or create a JSON spec and run `scripts/build_tcsd_from_json.py --template <skill_dir>/assets/templates/tcsd_template.xlsx`.
   - Keep sheet name `TCSD`, columns, row 2 `TestGroup`, freeze pane, comments/status options, cell styles, and reviewed status consistent with the template.

5. **Backfill expected outputs from simulation**
   - Extract actions with `scripts/extract_tcsd_cases.py`.
   - Run `scripts/simulate_tcsd_cases.m` through `scripts/satk_eval.py`.
   - Apply results with `scripts/backfill_expected_outputs.py`.
   - Validate that every `expValue(...)` left side is a root Outport.

6. **Verify**
   - Run `unzip -t` on the output workbook.
   - Inspect the TCSD sheet with a spreadsheet library or artifact-tool.
   - Check there are no internal-signal expectations and no unsupported input values exposed by simulation.
   - If model coverage evidence is available, verify decision coverage first. For each feedback item, confirm the outcome with a coverage rerun or a targeted probe of the decision block inputs/selectors. Add tests or record an explicit unreachable/invalid-selector reason for any remaining uncovered outcome.

## References

- Read `references/hermes-agent-handoff.md` when handing this workflow to another agent, when the agent lacks the original conversation context, or when assessing whether the skill is ready for Hermes-style execution.
- Read `references/workflow-details.md` when starting a new model.
- Read `references/coverage-closure.md` when designing or repairing cases for coverage.
- Read `references/tcsd-rules.md` before editing or validating the workbook.
- Read `references/support-package.md` when dependency loading fails.
