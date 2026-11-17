# REPORT_check_11F8 — independent check of seat 11's S-F8 and seat 02's partial refutation

**What this is:** seat 11's S-F8 claimed `setoption` with the value word omitted is "accepted SILENTLY and changes
nothing". Seat 02's S-C2 partly refuted it: the mechanism is right, but it is not silent. Seat 11 then revised it
itself as S-F22. **I checked it independently on both builds because a two-seat disagreement is worth a third
measurement even after one side concedes** — a concession can be right for the wrong reason.

**The answer: seat 02 is right on both builds, and seat 11's mechanism is right.** Four combinations, two builds,
identical outcomes.

```
                                    base 6b98f217                      PC r15
no value word    unknown-option line  info string unknown option UseNNUE false  (same)
                 eval                 hce 18 nnue 20 total 38  = DEFAULT       (same)
with value word  unknown-option line  none                                      (same)
                 eval                 hce 18 nnue 0 total 18   = APPLIED       (same)
```

So:
- **NOT silent** — the no-value form prints `info string unknown option UseNNUE false`. Seat 11's headline was wrong
  and seat 02's correction holds.
- **NOT applied** — `nnue` stays at the default 20, so the option did not take effect. Seat 11's mechanism is right:
  the token loop at `src/uci.cpp:265` swallows `false` into the option NAME, that name is unknown, and the
  unknown-name path reports it.
- **With the value word it works** — `nnue 0`, no unknown-option line.

**What my check adds beyond the two seats.** Seat 02 stated the behaviour held on "both builds"; I ran both and that
is true. Seat 11's S-F22 said the same. So this is a **confirmation of the settled state**, not a new dispute — and it
is worth having because the claim is now measured on two builds by three independent harnesses.

**How sure:** high. The check asserts each expectation and exits non-zero on a missing line or an unexpected value, so
a silent skip cannot pass. Both runs exited 0.

## Honesty numbers

```
base     /home/ubuntu/builds/bld-release/forge  (6b98f217)   bench 11 312866 / bench 13 862329
PC r15   /home/ubuntu/builds/bld-pc/forge                   none 312866 / S14 242796 / PC20 278024
harness  check_11F8/check_setoption.py  — raises on a missing eval line, exits 1 on any wrong value
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| no-value form on the base build | done | `check_11F8/base.txt` | unknown-option line printed, nnue stays 20 |
| no-value form on the PC build | done | `check_11F8/pc.txt` | identical |
| with-value form on both | done | same | nnue 0, no unknown line |
| harness fails loudly on a missing line | done by construction | `check_setoption.py` | raises `Missing`, exits 1 |

## Findings

`S-C8 | CONFIRMS seat 02's S-C2 (the partial refutation of seat 11's S-F8) on both builds | check_11F8/base.txt check_11F8/pc.txt (again: `python3 check_11F8/check_setoption.py ~/builds/bld-release/forge /tmp/o.txt`) | `setoption name UseNNUE false` without the value word is NOT silent — both builds print `info string unknown option UseNNUE false` — and NOT applied, since eval still reads nnue 20 (the default); with `value false` it applies (nnue 0) and prints nothing. So seat 11's mechanism (the token loop swallowing the value into the option name) is right and its "silently" headline is wrong, exactly as seat 02 found, now measured independently on both builds |`

## Suspicions, not proven

- None. The four combinations cover the claim.

## What I did NOT do

- Did not test other options with omitted values, so I cannot say whether any option's unknown-name path differs.
- Did not read `src/uci.cpp:265`/`:476` myself to confirm seat 11's and seat 02's line numbers; the behaviour is
  established, the citations are theirs.

## Times

`check_11F8/` run at 04:47Z; see the file mtimes and the STATUS block.
