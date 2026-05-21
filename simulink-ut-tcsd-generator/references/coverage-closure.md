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

## PwrLimEng Feedback Pattern

The PwrLimEng feedback exposed common misses:

- A `Max` block in `A02_ISGMaxMinTq/B01_PredSpd` had only input 1 winning. Add a speed-decrease case so the derivative/filtered acceleration path goes negative and the zero input wins; then add a speed-increase step so the other port wins.
- A `MultiPortSwitch` in `B02_ISGPwrEff` covered selectors `0/1/2` but not `3` and `4`. Put 380V/400V values in Initialization or shorten `PwrLimEng_tiISGVoltFilt_C` so the selector settles. A short step with a slow LowPass may not move the selector far enough.
- For AWD/non-AWD efficiency selection, toggle the root mode signal and cover the same high-voltage selector regions in both paths when separate MultiPortSwitch blocks exist.
- Saturation in efficiency paths needs explicit below-low, normal, and above-high cases. If the real lookup tables never exceed the saturation limits, record the high/low saturation outcome as unreachable from normal calibration rather than inventing unsafe table overrides.
- `B03_ISGLimTq` output Min/Max blocks need cases where each candidate limit wins, including torque command, electrical power limit, zero override, and startup/temperature limit branches.
- For final Min/Max candidate coverage, disable ramp limiters with explicit `p ...RampEna_C = 0` when the ramp output prevents a stable candidate from becoming the selected value within the test interval. Keep separate ramp tests for GradientLimiter behavior.

## HvGrid Pattern

The HvGrid run exposed issues common to larger integration-style modules:

- Start from a complete nominal input baseline. Large modules have many unrelated gates; missing one can prevent the target branch from becoming reachable.
- Use model metadata to split scalar and vector root outputs. Backfill scalar top-level outputs first and omit vector outputs unless the TCSD macro/index mapping is known.
- Cover feature clusters as separate Tests: high-voltage ready path, zero-voltage Safe_Divide, battery charge/discharge limits, V2L/V2In/DC-charge modes, ECC priority/SOC hysteresis, startup/relay delay, energy reset edges, and motor bypass/stall heating.
- For latch, hysteresis, and delay logic, use multi-step actions that cross low/high thresholds and then return, rather than only one static initialization.
- For large modules, use JSON specs plus generated Excel instead of hand-editing. Keep a scalar-output allowlist and a validation script that rejects internal, local, and vector expectations.
