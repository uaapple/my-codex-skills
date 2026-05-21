# Coverage Closure

Use this reference when designing or repairing TCSD cases for model coverage. Coverage is the first priority; expected outputs are added afterward only where top-level outputs are stable.

## Build Coverage Obligations

Create a short checklist before writing the workbook:

- `Switch` / relational logic: true and false outcomes.
- `MinMax`: each input port is the selected maximum/minimum at least once.
- `MultiPortSwitch`: every valid selector value, plus default/otherwise branch when the block has one.
- `Saturate`: below lower limit, pass-through region, above upper limit.
- `Lookup_n-D`: representative low/mid/high breakpoints and edge values that drive downstream selectors.
- `Safe_Divide`: denominator zero/protected path and normal nonzero path.
- `Abs` / sign-sensitive logic: negative, zero, and positive inputs.
- Delay/latch/edge/stopwatch: initial state, set edge, reset edge, hold/timeout path.
- Gradient limiter / LowPass: increase, decrease, disabled/bypass, and enough hold time for downstream decisions to change.

For every item, write one of: `covered by TC_xxx`, `needs supplemental test`, or `unreachable because ...`.

## Generate Targeted Stimuli

- Make one condition dominate at a time. For `MinMax`, set a clear margin so the intended port wins; avoid equal values because coverage tools may attribute ties unexpectedly.
- For `MultiPortSwitch`, derive selector values from the actual block and upstream logic. Do not assume a model-wide enum is valid for every switch.
- When a selector is produced by voltage/current/speed filtering or lookup logic, hold the source input long enough for the selector to settle, or put the desired source value in Initialization.
- For Saturate, use values comfortably outside limits, not just exact boundaries.
- If a value causes simulation to stop because the selector is invalid, do not keep it as a normal unit-test case. Cover the default branch only when the block and model allow that selector safely.
- Use scalar parameter overrides to accelerate filters or bypass ramping only when needed for coverage. Keep them explicit in `Initialization` and avoid hiding model behavior without explanation.

## Use Coverage Feedback

When a coverage report shows uncovered outcomes:

1. Locate the exact block path and missing outcome, such as `input 2 is the maximum` or `selector = 3`.
2. Identify the root inputs or calibration parameters that control the block input/selector.
3. Add a supplemental Test with a narrow description naming the block/outcome.
4. Run simulation to ensure the model accepts the stimulus.
5. Backfill only stable top-level outputs. Do not add internal expected signals to prove the outcome.
6. Re-run coverage if possible; repeat until the target is met or remaining outcomes are justified.

Do not mark a missing outcome as closed only because the Test name, comments, or input values appear to target it. A supplemental Test is successful only when coverage feedback changes, or when a focused simulation probe confirms the relevant internal block input/selector actually crossed the intended side.

Useful probes for closure, while still keeping TCSD expectations top-level only:

- `Abs`: log or infer the source signal sign; cover negative, zero, and positive source values before the `Abs`, not just positive magnitudes after it.
- `MinMax`: log every candidate input during the step and confirm the intended candidate is strictly greater/less than the others. Avoid ties and near-ties.
- `MultiPortSwitch`: log the integer selector at the block input. High source values such as voltage or mode commands do not prove the selector reached the intended port when a filter, lookup, or quantizer is upstream.
- `Saturate`: log the pre-saturation value and confirm it is below low, inside range, and above high. Exact boundary values normally do not cover both sides.
- `Switch` / relational logic: log the logical trigger value; for sign-based switches, deliberately cover both positive and negative root inputs.
- Filtered or ramp-limited paths: use longer hold time, Initialization, or explicit parameter overrides, then confirm the downstream decision saw the settled value.

## PwrLimEng Feedback Pattern

The PwrLimEng feedback exposed common misses:

- A `Max` block in `A02_ISGMaxMinTq/B01_PredSpd` had only input 1 winning. Add a speed-decrease case so the derivative/filtered acceleration path goes negative and the zero input wins; then add a speed-increase step so the other port wins.
- A `MultiPortSwitch` in `B02_ISGPwrEff` covered selectors `0/1/2` but not `3` and `4`. Put 380V/400V values in Initialization or shorten `PwrLimEng_tiISGVoltFilt_C` so the selector settles. A short step with a slow LowPass may not move the selector far enough.
- For AWD/non-AWD efficiency selection, toggle the root mode signal and cover the same high-voltage selector regions in both paths when separate MultiPortSwitch blocks exist.
- Saturation in efficiency paths needs explicit below-low, normal, and above-high cases. If the real lookup tables never exceed the saturation limits, record the high/low saturation outcome as unreachable from normal calibration rather than inventing unsafe table overrides.
- `B03_ISGLimTq` output Min/Max blocks need cases where each candidate limit wins, including torque command, electrical power limit, zero override, and startup/temperature limit branches.
- For final Min/Max candidate coverage, disable ramp limiters with explicit `p ...RampEna_C = 0` when the ramp output prevents a stable candidate from becoming the selected value within the test interval. Keep separate ramp tests for GradientLimiter behavior.

The later PwrLimEng_Test0002 feedback added a stronger lesson: coverage intent was present in several Test descriptions, but the actual coverage report still showed holes. When fixing similar models:

- In `A01_EngMaxTq`, `Abs` before the engine torque comparison needs both signs of `icisg_tqISGMin`; a normal negative torque limit only covers the negative-source side.
- In `B01_PredSpd`, cover negative `icisg_nAct` or a sufficiently strong decreasing speed transition before the `Abs`, and separately confirm the `Max` constant-zero input wins. A mild speed decrease may still leave the filtered acceleration path above zero.
- In `B02_ISGPwrEff`, selector `*,4` for the `MultiPortSwitch` is not guaranteed by setting `icisg_uAct` to 400/450. Probe the selector after the voltage LowPass/lookup path, or initialize/override the filter so the selector actually becomes port 4.
- In `B02_ISGPwrEff`, `Saturation1` needs explicit pre-saturation values below 0.1 and above 1.0. If normal lookup/calibration data keeps both inputs inside `[0.1, 1]`, document those branches as unreachable rather than claiming them covered.
- In `B04_ISGPwrEffAWD`, the final Switch true branch requires `icisg_tqAct < 0`; AWD mode alone usually covers only the false branch.
- In `B03_ISGLimTq`, final `PwrLimEng_tqISGMin` Max and `PwrLimEng_tqISGMax` Min candidate coverage must be verified by probing candidate inputs. Cases that reduce charge/discharge power or disable ramping may still leave the wrong candidate selected.
- For a PwrLimEng coverage-repair pass, prefer producing a new version such as `PwrLimEng_Test0003_tcsd.xlsx`, with a short report mapping each Word/coverage feedback item to `confirmed covered`, `still uncovered`, or `unreachable`.

## HvGrid Pattern

The HvGrid run exposed issues common to larger integration-style modules:

- Start from a complete nominal input baseline. Large modules have many unrelated gates; missing one can prevent the target branch from becoming reachable.
- Use model metadata to split scalar and vector root outputs. Backfill scalar top-level outputs first and omit vector outputs unless the TCSD macro/index mapping is known.
- Cover feature clusters as separate Tests: high-voltage ready path, zero-voltage Safe_Divide, battery charge/discharge limits, V2L/V2In/DC-charge modes, ECC priority/SOC hysteresis, startup/relay delay, energy reset edges, and motor bypass/stall heating.
- For latch, hysteresis, and delay logic, use multi-step actions that cross low/high thresholds and then return, rather than only one static initialization.
- For large modules, use JSON specs plus generated Excel instead of hand-editing. Keep a scalar-output allowlist and a validation script that rejects internal, local, and vector expectations.
