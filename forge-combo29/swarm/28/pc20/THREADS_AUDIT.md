# Threads audit (swarm rule: any score reported must be Threads 1)

Rule from seat 04: at Threads 4 the PC build gives four different scores on one position (+2576, mate 13,
mate 18, mate 16) while Threads 1 gives +2207 four times with identical nodes. A non-reproducible score
changes the tree, which changes the time — so it matters doubly in the clock area.

## The question asked: were my 08-F11 tail numbers measured at the default thread count?
Seat 08 measured 08-F11, not me, so the relevant check is their harness. Their `job5/raw/.meta` records:

```
options sent: S14 + Threads 1 + Hash 16 + OwnBook false + ucinewgame per search; Move Overhead default 10
```

So **08-F11's base numbers were taken at Threads 1 explicitly**, not at a default that might have been >1.
The engine's own default is 1 (`option name Threads type spin default 1 min 1 max 256` on both builds), so
even a no-setoption run is Threads 1.

## My own harnesses
Every script of mine that sends a search command was audited. Eleven send a `go`, and **ten send `Threads 1`
explicitly**. The one exception is deliberate:

| script | sends Threads 1? | why |
|---|---|---|
| `job1/timing.py`, `job2/lowtime.py`, `job3/movestogo.py`, `job4/hardlimit.py` | yes | every clock measurement |
| `correction/movetime_sweep.py`, `correction/sf6_recheck.py` | yes | correction round |
| `checks/check_s01f5.py`, `check_27f2.py`, `check_21f2.py`, `repetition_root.py` | yes | other seats' checks |
| `job5/verify_patch.py`, `counter_reset_case.py`, `patch_clock.py` | yes | patch verification |
| `job5/asan_patch.py` | yes | sanitizer runs |
| `pc20/tail_pc20.py`, `score_rep.py` | yes | this re-run |
| **`pcbuild/pins.py`** | **no, on purpose** | the four honesty pins are DEFAULT-option numbers (FABLE_TO_swarm_4); the engine default is Threads 1 |

## The measurement that settles it (`score_rep_out.txt`)
Same position, PC r15, PC20, `go depth 12`, five fresh processes per thread count:

| threads | distinct scores | distinct moves | distinct node counts |
|---|---|---|---|
| 1 | 1 (`cp 54` five times) | 1 (`e1g1`) | 1 (27,066 every time) |
| 4 | 5 (`cp 61/63/67/74/75`) | 2 (`c1e3`, `e1g1`) | 5 (45,399 - 102,116) |

Threads 1 is exactly reproducible; Threads 4 is not, and on this position the **move** varies too, which is
beyond what seat 04 reported (they saw the move stay fixed). So the rule is well founded and my numbers sit
on the right side of it.
