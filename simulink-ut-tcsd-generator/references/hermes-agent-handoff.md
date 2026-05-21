# Hermes Agent Handoff

Read this reference when another agent must generate Simulink unit-test TCSD cases without access to the original development conversation. It captures the reusable lessons from the ACCtl sample, PwrLimEng generation/repair, and HvGrid generation work.

## Mission

Given a module-level Simulink model `<model>.slx` and its matching `<model>.mat`, generate a unit-test TCSD Excel workbook in the same style as the ACCtl/PwrLimEng examples. The first priority is model coverage, especially decision coverage. Expected outputs are secondary and must be derived from simulation only where stable and only for top-level Outports.

## Default Task Contract

If a user tells Hermes or another agent to use `simulink-ut-tcsd-generator` for a model, all standard requirements in this handoff are implicit. Do not ask the user to repeat them.

A minimal prompt is sufficient:

```text
使用 simulink-ut-tcsd-generator，为 <workdir>/<model>.slx 和 <workdir>/<model>.mat 生成单元测试 TCSD 用例。
```

The agent must automatically:

- copy `assets/support-package` into the workdir;
- use Simulink Agentic Toolkit / SATK to read the model;
- generate coverage-first unit-test TCSD cases, prioritizing decision coverage;
- write expected values only for top-level Outports;
- simulate when possible and backfill stable top-level outputs from simulation;
- omit hold-style expectations for ramping or continuously changing outputs;
- build the workbook from the bundled canonical template `assets/templates/tcsd_template.xlsx`;
- save `outputs/<model>_Test0001_tcsd.xlsx`, or the next versioned filename if it exists;
- keep the JSON case spec, simulation-result JSON, and a short validation report with the workbook.

Only ask for clarification when the `.slx`, matching `.mat`, MATLAB/SATK runtime, or a required dependency is actually missing.

## Assumptions and Required Runtime

- The agent runs on the same machine/user account that can read this skill directory.
- MATLAB, Simulink, Simulink Agentic Toolkit, and the local SATK bridge are available.
- The supplied `.mat` is the model-specific authority for signal objects, calibration objects, lookup tables, and parameter values.
- The user normally provides only `<model>.slx` and `<model>.mat`; reusable Cornex/ITK dependencies must come from this skill.

If any of those assumptions are false, stop and report the missing runtime or file dependency before inventing cases.

## Support Package

The reusable dependency package is bundled at:

```text
assets/support-package/
```

It contains:

- `Cornex_Config.sldd`
- `CornexMdlCfg.mat`
- `ITKLib.slx`
- `init_Global.m`
- `ITKCToolsV015/ModelingTools/01_Csc` including `+CornexCsc`
- `ITKCToolsV015/GenLib`

For a fresh work folder, copy it before loading the model:

```bash
cp -R <skill_dir>/assets/support-package/. <model_workdir>/
```

`<skill_dir>` is the folder containing this `SKILL.md`. Do not rely on the old conversation’s workspace having those files already.

## Known Dependency Lessons

- If `CornexCsc.Signal` or `CornexCsc.Parameter` is missing, MATLAB may load MAT variables as raw numeric arrays such as `uint32 [6x1]`. Fix the path, clear the workspace, and reload the MAT.
- Add `ITKCToolsV015/ModelingTools/01_Csc`, `ITKCToolsV015/GenLib`, the model workdir, and the skill `scripts/` folder to the MATLAB path before loading/simulating.
- If the model’s original config references missing generated-code headers such as `rte_bsw_analog.h`, attach an in-memory `CodexSimOnlyCfg` and simulate with that. Do not edit the source `.slx`.
- Load `ITKLib.slx` before the model if present.
- Kill stale `matlab-mcp-core-server` processes after SATK calls if they remain running and block later calls.

## Preferred End-to-End Workflow

1. Create or select a clean model workdir.
2. Copy `assets/support-package/.` into the workdir.
3. Place the user’s `<model>.slx` and `<model>.mat` in the same workdir.
4. Load support paths, run `init_Global.m`, load the MAT, load `ITKLib.slx`, then load the model.
5. Derive root Inports and Outports from the model, including port order, data type, and dimensions. Do not guess.
6. Inspect hierarchy and decision-producing blocks: Switch, RelationalOperator, MinMax, MultiPortSwitch, Saturate, Lookup, Safe_Divide, Delay, Latch, StopWatch, LowPass, GradientLimiter.
7. Build a coverage-obligation checklist before writing TCSD rows.
8. Create a JSON spec or workbook draft, then build the final workbook from `assets/templates/tcsd_template.xlsx`.
9. Extract TCSD actions to simulation JSON.
10. Run simulation and export results.
11. Backfill only stable top-level output expectations.
12. Validate workbook shape, `expValue` left-hand names, vector-output omissions, and Excel zip integrity.
13. If coverage feedback exists, add versioned supplemental Tests and repeat.

## TCSD Style Learned From ACCtl/PwrLimEng

- The bundled `assets/templates/tcsd_template.xlsx` is the canonical Excel input form for the downstream automatic test software. Do not create a blank workbook from scratch.
- One `TCSD` sheet.
- Row 2 is `TestGroup`.
- Test rows use `Type = Test` and `Work Status = reviewed`.
- Preserve the template's columns, freeze pane, cell styles, comments/status options, and workbook structure.
- `Test Case Description` should include a method, such as requirement analysis, boundary value, equivalence class, or coverage feedback.
- `Initialization` assigns all root inputs required for deterministic startup, plus explicit parameter overrides as `p ParamName = value;`.
- `Action` uses relative time markers like `[+100ms]` or `[+0.2s]`.
- Executable lines end with English semicolons.
- Comments use `//`.
- Keep comments practical: name the branch/selector/condition change being targeted.

## Expected Output Rules

The biggest correctness issue in the thread was expected-output semantics:

- Only top-level Outports may be used as `expValue(...)` left-hand sides. Do not put internal/local signals or `out_mil_ec` names into TCSD expected outputs.
- `expValue(var1,duration,offset)` means:
  - `var1`: expected value or input-signal name string;
  - `duration`: check duration;
  - `offset`: offset from the current interval.
- The second and third arguments are not numeric tolerance. Do not use them to express tolerance.
- For simulation-sampled expected values, write `expValue(value)` by default.
- If an output ramps or changes during the following hold interval, omit that output from the Test. Do not write one sampled value and then let the unit-test/MQT checker compare it as a held constant.
- Stimulus coverage and expected-output coverage are separate. Keep a Test/action if it improves model coverage even when few outputs are stable enough to backfill.

## Coverage Design Rules

Treat every decision outcome as an obligation:

- `MinMax`: every input port should win at least once. Avoid equal/tie values because coverage attribution can be ambiguous.
- `MultiPortSwitch`: cover every valid selector value and default/otherwise only if the model safely accepts that selector.
- `Saturate`: cover below-low, pass-through, and above-high regions by proving the pre-saturation input crosses the limits. If calibration/lookup values can never exceed a limit, record the remaining region as unreachable rather than unsafe table manipulation.
- `RelationalOperator`/`Switch`: cover both true and false by driving the actual trigger signal across the block criterion. For sign criteria such as `< 0`, `<= 0`, `~= 0`, or `u2 ~= 0`, include negative, zero, and positive/equality-side values as applicable.
- `Safe_Divide`: denominator zero/protected path and normal nonzero path.
- `Lookup_n-D`: use low/mid/high and edge breakpoints that influence downstream decisions.
- `LowPass`/filter/GradientLimiter upstream of a selector: use Initialization, longer hold time, or explicit scalar parameter override so the intended selector/result actually settles.
- Delay/latch/StopWatch: use multi-step action sequences for initial, set, hold, reset, and timeout states.
- Coverage closure requires evidence. Do not mark a feedback item fixed only because a Test comment says it targets that outcome; confirm with a coverage rerun or a focused probe of the relevant internal block inputs/selectors.

## Static SLX Inspection

SATK/MCP/MATLAB is the authority. Static `.slx` XML inspection is only a supplement after SATK/MCP/MATLAB model reading has been attempted or used, and only for exact SIDs, block parameters, and line connectivity:

```bash
SKILL_DIR=/path/to/simulink-ut-tcsd-generator
MODEL_SLX=MODEL.slx
python3 "$SKILL_DIR/scripts/inspect_slx_xml.py" "$MODEL_SLX" --pattern "MultiPortSwitch|MinMax|Saturate|<Line|<Branch"
```

Do not pipe `.slx`/zip/XML output directly into interpreters such as `python3 -c`, `perl`, `ruby`, or `node -e`. That pattern can trigger security approval and encourages bypassing SATK/MCP model reading.

Use static inspection to find SIDs, constants, block parameters, `DataPortOrder`, `Inputs`, `UpperLimit`, `LowerLimit`, and line connectivity. Always run simulation after designing stimuli.

## Simulation and Script Lessons

- Use the skill scripts rather than rewriting large boilerplate:
  - `scripts/build_tcsd_from_json.py`
  - `scripts/extract_tcsd_cases.py`
  - `scripts/simulate_tcsd_cases.m`
  - `scripts/backfill_expected_outputs.py`
  - `scripts/setup_ut_support.m`
  - `scripts/satk_eval.py`
- The generic extractor supports scalar numeric values and bracketed numeric vectors such as `[5000 5000 5000 5000]`.
- The generic simulation script handles vector root inputs/outputs; backfill should still usually allow only scalar top-level outputs unless vector TCSD macro mapping is confirmed.
- `openpyxl` is required for the Python workbook scripts. If system Python lacks it, use the runtime Python available in the agent environment or install/use an environment with `openpyxl`.
- Write model-specific helper scripts only when the generic scripts cannot reasonably support a model-specific constraint. If such a script encodes a working MATLAB setup, parameterize paths instead of hardcoding one workbook forever.

## PwrLimEng Lessons

Relevant root outputs for expected values:

- `PwrLimEng_tqEngMax`
- `PwrLimEng_tqISGMax`
- `PwrLimEng_tqISGMin`
- `PwrLimEng_pwrMaxISGMecChrg`
- `PwrLimEng_pwrMaxISGMecDchrg`
- `PwrLimEng_effISGDchrg`

Important misses and fixes:

- The first draft covered execution well but decision coverage was low. The feedback screenshot showed condition coverage around 90.9%, decision coverage around 69.3%, and execution 100%.
- A later `PwrLimEng_Test0002` repair improved coverage but still missed outcomes because several Tests described the desired branch without making the internal decision input actually reach it. For future repair passes, create `PwrLimEng_Test0003_tcsd.xlsx` or another versioned workbook and verify each feedback item with coverage/probes.
- A `Max` in `A02_ISGMaxMinTq/B01_PredSpd` had only input 1 winning. Add a speed-decrease case so derivative/filter output is negative and the zero/other input wins, then a speed-increase step to cover the other side.
- `Abs` blocks need source-sign coverage, not just magnitude coverage. In `A01_EngMaxTq`, a normal negative `icisg_tqISGMin` covers only the negative-source side; add a positive-source case if the coverage report flags the other side. In `B01_PredSpd`/efficiency paths, use negative speed or a strong transition before the `Abs` when the source sign is what matters.
- `B02_ISGPwrEff` `MultiPortSwitch` covered selector `0/1/2` but missed `3` and `4`. Use 380V/400V in Initialization or shorten `PwrLimEng_tiISGVoltFilt_C`; a short 0.2s step with the original LowPass may not settle enough.
- For `B02_ISGPwrEff`, setting `icisg_uAct` to 400 or 450 is not sufficient evidence that selector `*,4` was reached. Probe the selector after LowPass/lookup, or force a settled high-voltage selector with Initialization/parameter override.
- `B02_ISGPwrEff` `Saturation1` must cover below-low, pass-through, and above-high pre-saturation values. Before generating cases, inspect or probe the signal entering `Saturation1`; extreme `icisg_uAct`, speed, or torque values are not evidence by themselves. If the MAT lookup/calibration tables keep values within `[0.1, 1]`, document low/high saturation branches as unreachable rather than using unsafe table edits.
- AWD and non-AWD efficiency paths can have separate MultiPortSwitch/Saturate blocks; cover high-voltage selector regions in both when present.
- In `B04_ISGPwrEffAWD`, the final Switch true branch requires `icisg_tqAct < 0`. AWD mode, high voltage, or `icisg_tqAct > 0` only exercises the false branch; include a negative `icisg_tqAct` step and confirm the logical trigger is true.
- `B03_ISGLimTq` final output Min/Max blocks need tests where each candidate wins: input torque limit, power-derived limit, zero override/protection, startup/temperature limit.
- For `B03_ISGLimTq`, final candidate coverage must be checked by probing the candidate inputs of the final Max/Min blocks. Reducing charge/discharge power or disabling ramping can still leave a different candidate winning.
- For final Min/Max candidate coverage, use explicit `p ...RampEna_C = 0` when ramp limiters otherwise prevent the intended candidate from becoming selected within the test interval. Keep separate tests for GradientLimiter behavior.
- Do not backfill hold-window expected values for ramped torque outputs. The instant value can be right while the later hold check fails.
- When regenerating after coverage feedback, write a versioned workbook such as `PwrLimEng_Test0002_tcsd.xlsx` and preserve the previous workbook.

## HvGrid Lessons

HvGrid is a larger integration-style model. The main lesson is to build a strong nominal baseline before targeting branches:

- Many unrelated gate signals can make a desired branch unreachable if they are left at zero.
- Cover feature clusters as separate Tests:
  - high-voltage ready normal drive path;
  - zero-voltage Safe_Divide protection;
  - battery charge/discharge limits;
  - V2L/V2In/DC-charge modes;
  - ECC priority, SOC hysteresis, and low-temperature logic;
  - APU charging and engine-start request;
  - energy/odometer reset edges;
  - front/rear motor bypass and stall heating;
  - relay open/close and heating delay paths.
- HvGrid has vector root inputs such as `EMTqFil_dtqIncGrdt` and `EMTqFil_dtqDecGrdt`; express them as bracketed numeric vectors in TCSD initialization/action when needed.
- HvGrid has vector root outputs such as `HvGrid_pwrAvl`. Do not auto-backfill vector outputs unless the target TCSD/MQT macro syntax and element mapping are known. Build and pass a scalar-output allowlist to the backfill script.
- For latch/hysteresis/delay, use multi-step sequences that cross low/high thresholds and then return. Static one-shot initialization is rarely enough.

## Validation Checklist Before Delivery

- Workbook path is under `outputs/`.
- Source `.slx` and `.mat` are unchanged.
- `unzip -t <workbook>.xlsx` succeeds.
- Sheet name is `TCSD`.
- Test rows have `Type = Test` and `Work Status = reviewed`.
- All root inputs needed for startup are initialized.
- Every `expValue(...)` left-hand side is a top-level Outport.
- No internal/local/MIL signal names appear as expected outputs.
- No three-argument `expValue` is present unless it is intentionally checking a stable window.
- Vector outputs are omitted unless explicitly supported.
- Selector values do not make simulation stop.
- Coverage feedback, if available, has been translated into supplemental Tests or justified as unreachable/invalid.

## Readiness for Hermes

This skill is suitable for a Hermes-style agent if it can:

- read the skill directory and its `assets/`, `references/`, and `scripts/`;
- copy `assets/support-package/.` into the model workdir;
- run Python with `openpyxl`;
- run SATK/MATLAB to load and simulate the model;
- create small model-specific JSON/spec helper scripts when model structure requires judgment.

It is not a fully push-button generator. The intended agent still must inspect the model and design coverage-oriented stimuli. The bundled scripts make Excel creation, action extraction, simulation, and expected-output backfill repeatable.
