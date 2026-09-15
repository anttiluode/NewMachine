# NewMachine v1 Results — Complementary Gates

v0 showed that state-side and threshold-side control are output-equivalent in a memoryless unit but diverge once hidden state persists.

v1 asks the more useful question: **are the two control locations complementary?**

The answer in this frozen toy is yes.

## Task

The machine receives two explicit context types.

### HIDE

The observed input is clean. Output should be suppressed temporarily, but the hidden state should remain intact.

### RESET

The observed input contains a fixed positive contamination during the control window. The clean reference does not. Output should be suppressed and the contamination should be prevented from persisting in hidden state.

Three policies are compared:

- `basket_only`: state-side gate in both contexts;
- `chandelier_only`: threshold-side gate in both contexts;
- `hybrid`: threshold-side in HIDE, state-side in RESET.

HIDE and RESET strengths are jointly selected on training seeds only to approach a context event fraction of `0.10`. Metrics below use held-out seeds 200–211.

## Held-out result

| metric | basket only | chandelier only | hybrid |
| --- | ---: | ---: | ---: |
| overall event fraction | 0.38708 | 0.47857 | 0.42637 |
| HIDE event fraction | 0.05532 | 0.05195 | 0.05195 |
| RESET event fraction | 0.15725 | 0.07849 | 0.15725 |
| state RMSE vs clean reference | 0.09446 | 0.10206 | **0.04914** |
| HIDE recovery error | 0.15603 | **0.0000016** | **0.0000008** |
| RESET recovery error | **0.10148** | 0.21077 | **0.10148** |
| combined recovery error | 0.12875 | 0.10538 | **0.05074** |

The pre-registered primary hypothesis was:

```text
hybrid combined recovery error < min(single-gate policies)
```

Result: **passed**.

The hybrid cuts combined recovery error by about 60.6% versus basket-only and 51.9% versus chandelier-only.

## Why the policies cross

In HIDE, there is nothing wrong with the resident state. Basket-like control changes it anyway, creating a recovery scar. Chandelier-like control changes only publication, so the hidden trajectory remains essentially identical to the clean reference.

In RESET, the hidden state is being driven by a known contamination. Chandelier-like control can hide the resulting output but cannot prevent the contamination from being stored. Basket-like state control can counteract the contamination before it becomes persistent state.

So the two operations are not just stronger and weaker versions of one gate:

```text
HIDE  -> keep state, gate publication
RESET -> alter state, gate computation itself
```

## Important limitation

The context label is given directly. The controller does not learn or infer whether the current situation is HIDE or RESET. v1 therefore demonstrates the value of **having two intervention sites**, not an intelligent gating policy.

The held-out RESET event fractions are only approximately matched (`0.0785` to `0.1573`), within the frozen tolerance but not identical. The recovery effect is large and mechanistically expected, but future task-facing work should tighten budget matching.

No claim is made that cortical basket and chandelier cells implement these exact synthetic operations.