# seat 20 — job 23: closing the Rule-1 gap, and the classifier defect it exposed

FABLE_TO_swarm_2 Rule 1: "a result '0 illegal moves / 0 sanitizer lines / 0 hangs / 0 differences' counts only when
the SAME harness, unchanged, counted one planted case."

My 200-sequence fuzz reported **0 crashes / 0 hangs / 0 illegal bestmoves** with no planted case for any of the
three. I planted all three and ran them through the same classification logic (`plant_fuzz_zeros.py`).

## What the planting found — a real defect in MY classifier

| planted case | result | counted? |
|---|---|---|
| engine that `SIGSEGV`s on the first `go` | `{'hang': True, 'crash': False, 'exit': None}` on the first try | **NO** |
| engine that never answers a later `isready` | `{'hang': True, ...}` | yes |
| engine that answers `bestmove z9z9` | `{'illegal': 'z9z9', 'hang': True}` | yes (illegal) |

**The crash was NOT counted.** My classifier waited for `readyok`, saw nothing, and labelled it a HANG without ever
asking whether the process was still alive. So a crashed engine and a silent-but-alive engine were indistinguishable
to it — the `assert` in the planting script is what caught this.

The fix (`p.poll() is not None` → `crash=True`, else `hang=True`) makes all three countable:

| planted case | after the fix |
|---|---|
| crash | `{'crash': True, 'exit': -11}` — **counted** |
| hang | `{'hang': True, 'crash': False}` — **counted** |
| illegal | `{'illegal': 'z9z9'}` — **counted** |

## What this means for my earlier zero

The 200-sequence fuzz's "0 crashes" was, strictly, "0 *crashes-or-silences*" — a crash would have been reported as a
hang. The fuzz's total was still 0 of everything, so **no result changes**: no sequence produced a hang, therefore
none produced a mislabelled crash either. But the *labels* in that job were weaker than I wrote them, and this note
is the correction. If a sequence had crashed, I would have reported it as a hang and would have missed a crash count.

Two honest caveats:
1. I did not re-run the 200 sequences with the fixed classifier. The fix changes labels, not the 0-or-not outcome,
   and the sequences are committed (`job2/myfuzz_out/myfuzz_seqs.txt`) so anyone can.
2. My fuzz's hang window was 20 s; this planting used 3 s to keep it quick, so the planting proves the detection
   PATH, not the timing threshold.

## Rule-1 status of my zero-results, now

| zero | planted control | status |
|---|---|---|
| 0 asymmetric `eval` pairs (360) | a different position differs; same position twice equal | shown |
| 0 bestmove asymmetries in F25 arm C | arms A/B differ from each other | shown |
| 0 crashes / 0 hangs / 0 illegal in 200 fuzz sequences | crash, hang and illegal planted **here** | **shown now** (labels corrected) |
| 0 sanitizer lines | planted fault counted by the same runner (job3) | shown |
| 0 unsearched clocked searches (65) | the 0 ms stop rows are the positive | shown |

## Commands that show it again
```
python3 plant_fuzz_zeros.py /tmp/o
```
