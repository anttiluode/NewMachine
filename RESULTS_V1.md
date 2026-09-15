# NewMachine v1 Results — Oracle Context Specialists

v0 showed that state-side and threshold-side control are output-equivalent in a memoryless unit but diverge once hidden state persists.

v1 then asks a narrower calibration question: **given an oracle context label, does the appropriate intervention site behave as v0 predicts?**

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

| metric | basket only | chandelier only | oracle hybrid |
| --- | ---: | ---: | ---: |
| overall event fraction | 0.38708 | 0.47857 | 0.42637 |
| HIDE event fraction | 0.05532 | 0.05195 | 0.05195 |
| RESET event fraction | 0.15725 | 0.07849 | 0.15725 |
| state RMSE vs clean reference | 0.09446 | 0.10206 | **0.04914** |
| HIDE recovery error | 0.15603 | **0.0000016** | **0.0000008** |
| RESET recovery error | **0.10148** | 0.21077 | **0.10148** |
| mean of HIDE/RESET recovery columns | 0.12875 | 0.10538 | **0.05074** |

The frozen pre-registered inequality for that last arithmetic summary passed. But it should not be read as an independent performance discovery.

The oracle hybrid simply takes the specialist operation in each context. Its RESET cell is basket-like and its HIDE cell is chandelier-like. The `0.05074` summary is just the mean of those two selected cells. Likewise the previously quoted `60.6%` and `51.9%` reductions are algebraic restatements of the same four context cells, not additional measured evidence.

## What v1 actually earns

The policies cross by context exactly as v0 predicts.

In HIDE, there is nothing wrong with resident state. Basket-like control changes it anyway, creating a recovery scar. Chandelier-like control changes only publication, so the hidden trajectory remains essentially identical to the clean reference.

In RESET, resident state is driven by known contamination. Chandelier-like control can hide the output but cannot prevent contamination from entering persistent state. Basket-like state control can counteract that contamination.

So the earned statement is:

> **Once the gated variable has memory, intervention site changes future computation. Given an oracle context label, the appropriate specialist is context-dependent.**

That is narrower than claiming the architecture is already useful. The context label is supplied by the experiment, and the contexts themselves are defined so that one intervention is appropriate.

## Remaining controls

Two objections are therefore carried into v2 rather than argued away:

1. one signed scalar command may reproduce the oracle hybrid exactly, which would show that two independent controller output channels are unnecessary;
2. simultaneous state repair + publication hold may or may not add anything beyond a communication/fidelity tradeoff.

The held-out RESET event fractions are also only approximately matched (`0.0785` to `0.1573`), so the state-RMSE row should not be used as a budget-fair performance headline.

No claim is made that cortical basket and chandelier cells implement these exact synthetic operations.
