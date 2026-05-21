# Workflow Details

## SATK Loading Pattern

Use this MATLAB setup before `load_system(model)`:

```matlab
rootDir = pwd;
restoredefaultpath;
rehash toolboxcache;
addpath(fullfile(rootDir, 'ITKCToolsV015', 'ModelingTools', '01_Csc'));
addpath(fullfile(rootDir, 'ITKCToolsV015', 'GenLib'));
addpath(rootDir);
run('init_Global.m');
load('<model>.mat');
load_system('ITKLib.slx');
load_system('<model>.slx');
```

If the original config references missing RTE/BSW custom code headers, attach a simulation-only config instead of changing the model file:

```matlab
if any(strcmp(getConfigSets(modelName), 'CodexSimOnlyCfg'))
    detachConfigSet(modelName, 'CodexSimOnlyCfg');
end
cs = Simulink.ConfigSet;
set_param(cs, 'Name', 'CodexSimOnlyCfg');
attachConfigSet(modelName, cs, true);
setActiveConfigSet(modelName, 'CodexSimOnlyCfg');
```

## Model Reading

Collect:

- Root input names and port order.
- Root output names and port order.
- Data types from `CornexCsc.Signal.DataType` where available.
- Subsystem hierarchy.
- Parameters from block masks, descriptions, `CornexCsc.Parameter.Value`, lookup tables, constants, and data dictionaries.
- Decision-producing blocks and their required outcomes: Switch true/false, RelationalOperator true/false, each `MinMax` winning input, each `MultiPortSwitch` selector/default, each Saturate low/pass/high region.

Do not assume `.mat` variables are valid until `CornexCsc.Signal` and `CornexCsc.Parameter` resolve to classes.

### Static SLX Inspection

Use SATK/MATLAB as the authority, but static `.slx` XML inspection is a useful preflight when you need exact block parameters or connectivity quickly:

```bash
unzip -p <model>.slx simulink/systems/system_*.xml | rg "MultiPortSwitch|MinMax|Saturate|<Line|PwrLim"
```

This is especially useful for:

- finding `DataPortOrder`, `Inputs`, `UpperLimit`, `LowerLimit`, constants, and calibration names before designing stimuli;
- mapping SIDs from coverage reports/screenshots to block names and line sources/destinations;
- checking whether a selector is filter-derived, lookup-derived, or a direct root input.

Do not use XML alone for final values. Run simulation after drafting the stimuli.

## Coverage Heuristics

For each major subsystem, create one or more Test rows that cover:

- Nominal enabled path.
- Each Boolean/condition input flipped one at a time.
- Threshold low/equal/high values.
- Lookup table representative regions and edge breakpoints.
- Saturation and Min/Max limits.
- For `MinMax` blocks, every input port must win at least once unless it is unreachable; equality/tie cases do not count as a reliable win.
- For `MultiPortSwitch` blocks, cover every valid selector value and any default/otherwise branch. Derive selector legality per block, not from a similarly named enum elsewhere in the model.
- For `Saturate` blocks, cover input below lower limit, inside limits, and above upper limit.
- Safe divide denominator zero and nonzero cases.
- Delay, latch, stopwatch, and edge-detect transitions.
- Gradient limiter/ramp behavior with enough time steps.
- Mode switches with only model-valid selector values.

Prefer fewer meaningful tests over many random tests. Coverage is the first priority, but invalid selector values that make the model stop are not useful unit-test cases unless the test explicitly targets diagnostic behavior.

## Coverage Feedback Loop

When a coverage report or screenshot shows uncovered decisions:

1. Map each uncovered outcome back to the block and port/selector/region.
2. Add a supplemental TCSD Test or action step whose only purpose is to make that outcome happen.
3. Use initialization or a long enough hold when LowPass, Delay, GradientLimiter, or lookup selector logic sits upstream of the decision.
4. Re-run simulation/backfill and, when possible, coverage. Keep iterating until the target is met or the remaining outcome has a concrete unreachable/invalid reason.

### Regeneration Pattern

When repairing coverage after a reviewed workbook already exists:

- create a new versioned workbook, for example `Model_Test0002_tcsd.xlsx`;
- create matching versioned JSON/results files so the old simulation evidence remains available;
- reuse model-specific simulation scripts if they encode working setup fixes, but parameterize workbook/spec/result paths where possible;
- keep added Tests narrow and name the uncovered block/outcome in `Test Case Description`.

## Simulation Backfill

Use simulation to compute expected values for top-level outputs only. If internal signals are useful for reasoning, keep them in notes, not as TCSD expectations.

`expValue(var1,duration,offset)` uses time-window controls: `duration` is the check duration and `offset` is the offset from the current interval. These are not numeric tolerance arguments.

For ramped outputs, do not write a single hold-style expectation. TCSD keeps or window-checks the sampled expected value over time, so a sampled ramp value becomes a wrong constant expectation. Prefer omitting that output from the Test, or generate a separate dense 10 ms staircase only when the user explicitly wants ramp-shape checking.

Do not let expected-output stability rules reduce stimulus coverage. It is acceptable for a Test to exist mainly to cover a decision outcome and contain few or no `expValue(...)` lines for dynamic outputs.

For larger modules such as HvGrid, many root outputs may be vectors or unsupported by the target TCSD import. Build a root-output allowlist from model metadata and backfill scalar top-level outputs first. Validate vector outputs are absent unless the vector macro syntax and element mapping are confirmed.

### Parameter Overrides for Coverage

Scalar calibration overrides are useful when model dynamics hide a decision outcome during short unit-test-style steps:

- shorten filter time constants for voltage/speed selector coverage;
- disable ramp/gradient limiter enable switches when the goal is final Min/Max candidate coverage rather than ramp-shape verification;
- keep the override visible in `Initialization` with `p Param = value;` and describe why in the Test description/action comment.

Avoid table/array overrides unless the parser and target unit-test toolchain support them.
