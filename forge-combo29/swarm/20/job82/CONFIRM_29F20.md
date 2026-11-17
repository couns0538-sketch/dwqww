# S-C55 — 29-F20's NUMBERS are right, but its second arm was not the configuration it names; and the case it could not test is now measured

Seat 20. Builds: `/agent/repos/build-v3/forge` sha256 `227aae56ef1678479cf08d0fc3e3c73683753e89d61f12b252f0fec9e388471e`
(`-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`), instrumented `48619d74…`; and `/agent/repos/build-pc/forge`
(PC r15, **no** `-DFORGE_NNUE_V3`). PC20 (S14 17 options + 5 extras), Threads 1, Hash 16, `bench 13`.

## What 29-F20 claimed
With **no** net file: `NNUEArch` defaults false, and `v3::active()` is `requested && loaded() != nullptr`, so
"with `NNUEArch true` but no net the v3 path still does NOT activate"; they counted **357,740 calls** to
`Evaluator::evaluate_runtime` during `bench 13` under PC20, and **the same 357,740** with `NNUEArch true` and no net.
They explicitly declined to claim anything about the owner's PC: *"I cannot test that because the net is not shared."*

## Confirmed: the number and the reading
Arm A (`NNUEArch` untouched, built-in net): **357,740 `evaluate_runtime` calls**, `bench 13` = **587,276 nodes**.
Reproduced exactly on my instrumented build — their figure is right, and the hand-written evaluation is on the path
in that configuration. Their caution about the owner's PC was well placed.

## Corrected: arm B was not a distinct configuration, on the build they used
On their build (`-DFORGE_NNUE_V3` **absent**), `NNUEArch` is **not a UCI option at all**:

```
info string unknown option NNUEArch
```

so `setoption name NNUEArch value true` was **silently ignored** and arm B ran the *identical* configuration to arm A.
**That is why the two counts are equal** — 357,740 twice is not evidence that "v3 does not activate without a net";
it is evidence that the option never existed in that binary. Their conclusion happens to be true, but this experiment
did not test it.

On a build where the option **does** exist (`-DFORGE_NNUE_V3=1`), arm B cannot be measured at all: the fail-loud rule
ends the program.

| arm | `NNUEArch` exists? | `bench 13` | `evaluate_runtime` calls |
|---|---|---|---|
| A — built-in net, no v3 | yes / no (same result) | 587,276 | **357,740** |
| B — `NNUEArch true`, no net, **their build** | **NO — "unknown option", ignored** | 587,276 | 357,740 (same run as A) |
| B — `NNUEArch true`, no net, **v3 build** | yes | **none — `ERROR`, exit 2** | n/a |
| C — test net loaded (**new, was untestable**) | yes | 3,652,372 | **0** |

## The case they could not test, now measured (the useful addition)
File 7 supplies a deterministic stand-in for the PC's net, so the arm that was previously unreachable is reachable.
With the v3 net loaded (arm C):

- **`evaluate_runtime` = 0 calls** in 3,652,372 nodes. The hand-written evaluation leaves the path **entirely**.
- `bench 13` = 3,652,372 nodes, matching file 7's published pin exactly.

So on the **source-level** reading and now on measurement: `static_evaluate` returns `static_evaluate_v3(...)` at
`src/search.cpp:1184` before the built-in path is reached, and `evaluate_runtime` is never called. **29-F20's
"the hand-written evaluation is on the path in every configuration reachable in this repository" was true when it was
written; it is no longer true now that a net can be produced from file 7's script.**

## What I am NOT claiming
- Not that 29-F20 was wrong when written. It was correct about every configuration it could build, and it flagged the
  gap honestly. This check closes the gap rather than faulting the seat.
- **29-F21 is untouched**: that the *built-in* net is **residual** (`FORGE_NNUE_RESIDUAL 1`, so `eval` adds hce + nnue)
  is a property of the built-in path and is consistent with all four arms above. File 7's v3 net is **standalone**
  (`eval_scale 400`, and `src/nnue_v3.cpp:395` refuses a residual v3 net), which is a *different* net, not a
  contradiction of 29-F21.
- File 7's own warning stands: this test net is a shape/weight stand-in, so "0 calls" is a statement about the **code
  path**, which is what 29-F20 asked about — not about the owner's actual trained net's behaviour.

## Status
**S-C55 CONFIRMS 29-F20's measurement, CORRECTS its arm structure, and closes its stated gap.** Evidence
`job82/check_29F20.json`, `job82/check_29F20.py`, raw arm output above.
