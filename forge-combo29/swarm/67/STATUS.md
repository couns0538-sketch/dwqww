# swarm-67 — protocol-boundary fuzz (ASan + UBSan)

**Complete.** See `FUZZ.md` for the generated report; every number there is
computed by `report.py` from the two evidence files in this directory.

## Bottom line

| | base `6b98f217` | `integrate/combo29-all` |
|---|---|---|
| cases | 167 | 167 |
| crashes (sanitizer / non-zero exit) | **0** | **0** |
| hangs (protocol liveness) | **0** | **0** |
| sanitizer lines | **0** | **0** |
| unbounded searches (not hangs) | 8 | 8 |
| `bestmove 0000` replies | 11 | 7 |

No crash, no hang, no sanitizer line, in any class, on either build. The engine
answered `readyok` after `stop` in every case and was usable at the end of each
run (`nodes 400` from a fresh `go perft 2`).

**The crash hazard at this boundary is protocol-level, not memory-safety.**

## Read this before trusting any row

`FUZZ.md` opens with a **corrections record**: nine items, enumerated rather
than estimated — five wrong claims about the engine (four from the coordinator,
one from this seat) and four defects in this harness (all this seat).

Two of those are the same error twice: a fingerprint used without first asking
what it would return if the hypothesis were false.

1. **Perft-2 collision.** `e2e4 e7e5` and `e2e4 e7e5 g1f3 b8c6` are both 835, so
   a perft-2 test of truncate-vs-splice cannot separate them. At perft 3 all five
   prefixes are distinct (8902 / 13160 / 24825 / 23193 / 24079) and the answer is
   unambiguous. Index 4 is reported as **ambiguous** rather than counted: there
   is nothing after the bad token for the two hypotheses to disagree about, so
   four of five indices discriminate.
2. **Fingerprint equal by construction.** A lone-king board has 3 legal moves and
   so does the same board after one king move, so `perft 1 = 3` cannot tell
   "moves applied" from "moves dropped". `perft 2` gives 9 vs 15.

Rule carried forward: before a measurement can confirm a hypothesis, state what
it would have returned if the hypothesis were false. If that value is the same,
the measurement is not evidence.

The second of those traps was made by this seat too, in the same turn as
diagnosing it in the coordinator's work — so the record names the inheritance
rather than implying the errors were all someone else's.

## Build

```
cmake -S forge-combo29 -B /tmp/asan -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 cmake --build /tmp/asan -j
```

Clang 18 cannot link sanitized binaries on this VM (`libclang_rt.asan*` and
`-lstdc++` are absent). GCC 13 needs the explicit `LIBRARY_PATH`.

## Method

- `os.read()` on non-blocking fds for stdout and stderr; no `select()`, no
  `readline()`.
- Every wait has a hard deadline; an overrunning case is killed.
- Waits are on `bestmove`, `readyok`, or `nodes N` — never on `info depth`.
- Reply lines are timestamped and attributed to the most recent preceding write,
  so refusal placement is measured, not inferred from text order.
- **A hang is a liveness failure, not a missing `bestmove`.** An unrestricted
  `go` must run until `stop`. The first harness version conflated the two and
  produced 7 false hangs.
- The harness refuses to run if two cases share an id — a duplicate silently
  makes two cases indistinguishable in the artifacts and corrupts every
  cross-run lookup. One was introduced and removed during this work.

## Self-test (proves the harness can fail)

`python3 selftest.py /tmp/brokenb/forge` → `SELFTEST PASS`

- Sanitizer detector: 4/6 over-64-char `position fen` cases flagged against an
  engine with a planted heap overflow; 0 false positives over 12 ordinary cases.
- Hang detector: a wrapper that reads and never answers is flagged
  `unresponsive`; a healthy wrapper is not.
- All FEN fixtures validated legal with python-chess 1.11.2.

## Findings

1. No memory-safety or liveness defect found.
2. `bestmove 0000` covers checkmate, stalemate and an empty `searchmoves`
   restriction; only the last carries an `info string`, so checkmate and
   stalemate are indistinguishable on the wire.
3. An illegal move in the list **truncates**: legal prefix applied, remainder
   dropped, one `info string`, no refusal. Junk *before* `moves` is worse — it is
   skipped and the moves are applied anyway, silently.
4. **Malformed FENs above six fields are refused in silence** — no reply at all.
   Reply-scanning cannot cover this class.
5. A refused `position` searches the previous board.
6. Mid-search `setoption` truncates the search at the `setoption` write.
7. Book moves use a clock-seeded RNG; board identity is fingerprinted with
   `go perft` instead of comparing `bestmove`.

## Correction carried forward

The `info string invalid FEN` diagnostic is emitted **on the `position`
command**, in every harness pattern measured. It never appears in the `go`
output. 49 refusals across both patterns all attribute to `position`.

## Files

- `fuzz.py` — harness
- `cases.py` — 167-case corpus, fixtures verified with python-chess
- `selftest.py` — planted-bad-input controls
- `report.py` — generates `FUZZ.md` from evidence
- `FUZZ.md` — the report
- `evidence-asan-base.json`, `evidence-asan-integrate.json` — run artifacts
