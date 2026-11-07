# TtReplaceCache - STATUS

**Last update:** 2026-11-06 ~17:08 PC clock. Pack ready for Code Review. No SPRT and no ABBA were run or queued.

## Done
- **Source change.** `tools/apply_trc.py` (anchored, fail closed) applied to a trial_w6 copy.
  - Patch: `tt_replace_cache_after_w6.patch`, md5 aba037b2. It touches include/forge/search.hpp, src/search.cpp and
    src/uci.cpp.
  - Every new line is inside `#if FORGE_SPD_TT_REPLACE_CACHE`.
  - Apply-proof on a fresh trial_w6 copy: identical tree.
- **Identity:** pp_identity at macro 0 is IDENTICAL in all 8 units. The LTO+PGO identity `trc_id` gives pc1 = pc2 =
  4181a589 = trial_w6, byte for byte.
- **Gate:** `trc_gate` gives pc1 = pc2 = ec1cb55e.
  - OFF = all pins, net on and net off, and both perfts.
  - **ON = all pins as well, node-identical** (BENCH.md).
- **Selection order, as stated:**
  - slots 0..3 in order;
  - the first empty slot returns at once;
  - the strictly smallest `depth - 4 * relative_age` wins, and a tie keeps the earlier slot.
  - The ON loop keeps the current pick's metric in `replace_value`. It is computed once before the loop and updated only
    when a slot wins.

## In progress
None.

## Exact next step
1. Code Review of the patch md5 aba037b2.
2. QA owns any quiet ABBA timing of `TtReplaceCache=1` (or of the gate exe vs trial_w6). Node identity means it needs no
   SPRT unless QA wants one.

## Resume commands
```
cd /f/ospd/wt && git checkout opus-tt-replace-cache-20261106
# trees: D:\opus_5h\tt_replace_cache\src\{w6 (parent copy), trc (macro source default 0), trc_id, trc_gate}
bash opus_tt_replace_cache/tools/pp_identity.sh /f/ospd/src/trial_w6 /d/opus_5h/tt_replace_cache/src/trc
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'F:\ospd\wt\opus_speed\tools\build_variants.ps1' \
  -SrcDir 'D:\opus_5h\tt_replace_cache\src\trc_gate' -Tag trc_gate -Variant lp_v1 -Twice -Work 'D:\opus_5h\tt_replace_cache\builds'
```

## Unproven / not claimed
- **Speed:** no claim. There was no timing at all; QA owns the ABBA.
- **ON branch execution:** not shown by a counter build. Nodes are identical by design.
- **Threads > 1:** not tested. The change is inside the TT probe under the same stripe lock (or the lease); the
  selection is the same function of the same slot data.
