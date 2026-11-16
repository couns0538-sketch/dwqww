## 2026-11-16T21:53:41Z (from `date -u`)
seat 21, area 1 (FEN INPUT under ASan + UBSan), branch for-fable-and-opus/swarm-21

# FINAL STATE

**Two things asked for in this last window, both done**

1. **Third independent verification of seat 12's `two_doors_mate.patch.txt`** →
   **21-C6 CONFIRMS, FIX VERIFIED.** Applied to a scratch copy, built ASan+UBSan (35
   `__asan_` symbols), then A/B against the unpatched ASan build with the same harness:
   - unpatched: all FOUR door cases miss a mate in 1 (fifty-move ×2 colours, threefold
     repetition ×2 colours) — `0` nodes, `cp 0`;
   - patched: all four find it — `mate 1`, 105 nodes;
   - controls (counter 99; two occurrences) identical on both builds;
   - a quiet drawn root is STILL adjudicated at `0` nodes, so root adjudication is not
     deleted (the failure mode 30-F8 warned about does not occur here);
   - pins 312866 / 862329 / 3024920 / 4865609 unchanged;
   - sanitizer runner saw nothing in any of the 20 case outputs (caveat in the report: the
     planted-fault proof was against this build configuration, not this exact binary).
   `REPORT_job16.md`, `job16/verify_fix.py`, `job16/fixout/` (patched), `job16/fixout_base/`.

2. **One-page apply sheet for the fullmove-0 patch** → `APPLY_fullmove0.patch.md`:
   the fault, the two-line change, the apply command with dry run, the four pins before and
   after, the fault before and after, the six negative controls with their refusal lines, the
   6,073-position regression, the 200-position perft-2 check, and the caveats. No report
   reading required.

**New finding from the fix work**: 21-F11 — a checkmated root is scored `score mate 0`
(`4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60` → `mate 0`, `bestmove 0000`). `0000` is right;
`mate 0` is not. Present on both base and patched builds, so it is a fourth door.

**Totals**: findings 21-F1..F11 (11), checks 21-C1..C6 (30-F6, 30-F7, 08-F5, 24-F1 and seat
12's two-door fix all independently confirmed; C2 confirms the brief's prefix rule), and
21-P1, the verified fullmove-0 patch with its apply sheet.

**Integrity**: every search since the 19-F12 notice goes through `job6/safe_engine.py`; every
check asserts the line it parses was found and carries a plant that must fail; every case
asserts FEN acceptance so a stale board cannot produce a result. Cold baselines are fresh
processes only — no `Clear Hash`, no cross-search node comparisons (seat 10's rule). My wrong
turns in this job are recorded in `REPORT_job16.md`: a piped-`quit` first version that read as
all-MISSED, and a mis-read repetition table that I re-ran with proper controls before claiming.

**Next command if continued**: `cd forge-combo29/swarm/21 && python3 job16/fenmoves.py ~/b/asan/forge job16/out_fenmoves` (extends 21-F11 across stalemate and insufficient material).
