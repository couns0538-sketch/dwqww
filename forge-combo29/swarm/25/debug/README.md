# EXPERIMENT: clock-99 mechanism (seat 25)

STATUS: EXPERIMENT ONLY. This folder holds instrumentation and its output. It contains NO change to the
repository's engine source: the instrumentation exists only as a text patch here plus a scratch tree
(/agent/repos/dbg) built with -DFORGE_CLOCK99_DEBUG=1. Nothing here may be committed as source, and the patch
must not be applied to the repository tree.

## Files
| file | what it is |
|---|---|
| `instrument.py` | builds the instrumented scratch copy by exact string replacement, then emits a real `diff -u` |
| `FORGE_EXPERIMENT_clock99_debug.patch.txt` | the resulting patch (stderr-only prints, all behind FORGE_CLOCK99_DEBUG) |
| `run_experiment.py` | the three-case experiment (breaking@99, non-breaking@99, control@98) capturing stdout and stderr separately |
| `experiment_1.txt` | the output: which root path fires, and the per-depth root score/PV length |
| `experiment_2.py` / `experiment_2.txt` | the 9 reset moves, each played and searched with the clock zeroed |
| `experiment_3.py` / `experiment_3.txt` | `searchmoves` on individual reset moves |
| `experiment_4.py` / `experiment_4.txt` | every root move searched alone, compared with the unrestricted root score |
| `verify_mechanism.py` / `verify_mechanism.txt` | the mechanism restated as three PASS/FAIL assertions |
| `MECHANISM.md` | the conclusion, in full |

## Where the instrumented build lives
/agent/repos/dbg (scratch copy) -> /home/ubuntu/build/dbg/forge, built Release with
`-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_CLOCK99_DEBUG=1`. Not in the repository.

## Reproduce
```bash
python3 forge-combo29/swarm/25/debug/instrument.py      # writes the patch
# apply the patch to a scratch copy, build with -DFORGE_CLOCK99_DEBUG=1, then:
python3 forge-combo29/swarm/25/debug/run_experiment.py /path/to/dbg/forge
python3 forge-combo29/swarm/25/debug/verify_mechanism.py /path/to/pc/forge   # needs no instrumentation
```
`verify_mechanism.py` runs against the NORMAL PC build: the mechanism is visible from `searchmoves` alone.
