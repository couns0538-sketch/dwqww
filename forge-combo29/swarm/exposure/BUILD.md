# BUILD and rerun

Everything in `FINDINGS.md` is reproducible from this directory. Two build facts dominate:
the compiler trap, and the fact that the audit needs **three** builds, not two.

## Compiler trap

`/usr/bin/c++` on the audit machine is clang 18 with a broken header path. Always:

```bash
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 \
  cmake <src> -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 make -j"$(nproc)"
```

## The three arms, and why the third one exists

| arm | what it is | why |
|---|---|---|
| `base` | commit `6b98f217`, unmodified | the build under audit |
| `patched` | base + seat 12 + seat 27 | the repair the owner is asked to ship |
| `nobail` | `patched` with the guard compiled out | **instrument only** |

The third arm is not optional. On a drawn root the base searches **nothing**, so the question
"would the search have played a different move" has no answer from the base build. The `nobail`
arm searches the same position and is the only available reference. It is explicitly **not** a
shipping candidate.

```bash
bash build_all.sh            # builds all three under /tmp/forge-exposure/build
```

`build_all.sh` also asserts the composed repair's sha256:
`24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`.

## Path containment (all scripts)

Every script reads and writes paths that come from the command line, so all of them go through
`scripts/paths.py`, which confines those paths to the evidence root (the directory above
`scripts/`, or `FORGE_EXPOSURE_ROOT`). Two consequences:

- **Relative `--out` values are relative to the evidence root**, not the shell's cwd. `--out
  oracle.json` writes `<root>/oracle.json`.
- **A path that escapes the root is refused**, not silently clipped: `--out /tmp/x.json` raises
  `path escapes the evidence root`. Put outputs under the root instead.

This exists because SonarCloud flags CLI-supplied paths as path traversal, and the finding is
correct as a data-flow statement even for local analysis scripts. The fix is containment rather
than suppression, and it is tested: `under_root('../../etc/passwd')` and
`glob_under_root('../../*')` both raise, while normal relative paths resolve. Re-running
`final_numbers.py` after this change reproduced every figure byte-identically — the refactor
changed no number.

## Order of operations

Each step writes JSON that the next consumes. `FORGE_EXPOSURE_ROOT` points the scripts at the
directory holding `build-*/` and the JSON; it defaults to the parent of `scripts/`.

```bash
export FORGE_EXPOSURE_ROOT=/tmp/forge-exposure
ln -sfn /tmp/forge-exposure/build $FORGE_EXPOSURE_ROOT 2>/dev/null || true
# scripts expect build-base/, build-patched/, build-nobail/
cd $FORGE_EXPOSURE_ROOT && for a in base patched nobail; do ln -sfn /tmp/forge-exposure/build/$a build-$a; done
```

| step | command | output | what it proves |
|---|---|---|---|
| 1 | `python3 scripts/pins.py` | stdout | the four honesty pins on both builds |
| 2 | `python3 scripts/oracle.py` | `oracle.json` | the predicate reimplementation matches the binary, 10/10 |
| 3 | `python3 scripts/random_null.py --games 4600 --max-plies 200 --out random_null.json` | `random_null.json` | the original null's corpus never reaches the guard |
| 4 | `python3 scripts/play_all.py --depth 10 --games 250 --seed 101 --out prod/d10_s101.json` (repeat seeds 101–106) | `prod/*.json` | the firing rate |
| 5 | `python3 scripts/cost.py --runs 'prod/d10_s*.json' --depth 10 --out cost_prod.json` | `cost_prod.json` | move change and cost per root |
| 6 | `python3 scripts/mechanism.py --cost cost_prod.json --out mech_prod.json` | `mech_prod.json` | the bail plays the generated head |
| 7 | `python3 scripts/pairs.py --depth 10 --games 250 --seed 101 --out pairs_s101.json` | `pairs_s101.json` | games whose result changes |
| 8 | `python3 scripts/final_numbers.py` | `final_numbers.json` | every figure quoted in FINDINGS.md |

Steps 4 and 5 are the expensive ones: about 8 minutes for the six-seed corpus and 4 minutes for
the adjudication on this machine.

## Step 2 is the one that must be able to fail

`oracle.py` validates the module the entire audit rests on. Confirm it is not vacuous by
planting a fault:

```bash
cd scripts && cp predicates.py /tmp/pred.bak
sed -i 's/halfmove_clock >= 100/halfmove_clock >= 99/' predicates.py
python3 oracle.py     # must print a FAIL on halfmove_99 and ORACLE FAIL
cp /tmp/pred.bak predicates.py
python3 oracle.py     # back to ORACLE PASS
```

A checker is tested by giving it a case whose answer is already known — never by reading it.

## Fixed depth, not a clock

Games are played at `go depth N` because the engine is deterministic at a fixed depth: the same
seed reproduces the same game move-for-move, which is what makes every number here auditable.
Clock play is not reproducible and cannot support a paired comparison. Depth 10 was chosen after
timing (~0.009 s per position), deep enough for coherent play and cheap enough to sample 1,500
games; depth 6 is run as an independence check, and agrees.

## Two traps in the engine's protocol, both of which fabricate results

- **`go perft` ends with a bare `nodes N` line and no `bestmove`.** Reading it like a search
  hangs or mis-parses.
- **Sending `quit` (or closing stdin) before `bestmove` has been read makes the engine abort and
  print a fabricated `bestmove a2a3` with zero info lines.** `scripts/uci.py` exists to read every
  search through to `bestmove` before writing the next command.
