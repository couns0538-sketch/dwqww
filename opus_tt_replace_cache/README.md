# TtReplaceCache pack (TT replace-metric cache) - default OFF, expected node-identical

- **Branch:** `opus-tt-replace-cache-20261106`. It is cut from the same opus-speed tip as the int8 pack (e5412ac5), so it
  is isolated: it does not stack on the int8 pack.
- **Engine parent:** trial_w6, `F:\ospd\src\trial_w6`.
- **Builds and outputs:** `D:\opus_5h\tt_replace_cache\`.
- **Macro:** `FORGE_SPD_TT_REPLACE_CACHE` (default 0, in include/forge/search.hpp).
- **Gate build only:** UCI `option name TtReplaceCache type spin default 0 min 0 max 1`. ON = `setoption name
  TtReplaceCache value 1`.
- **The change.** Both TT probe paths change: `probe_body` (FORGE_SPD_TT_NOTLS = 1, the lock) and `probe`
  (TT_NOTLS = 0). Each keeps the replace metric `depth - 4 * relative_age` of the current pick in a local.
- **Selection order** is the same as the lock's:
  - slots 0..3 in order;
  - the first empty slot is returned at once;
  - among occupied slots, the strictly smallest metric wins, and a tie keeps the earlier slot.
- **Expected result:** ON is node-identical to the lock. QA owns any later quiet ABBA timing; this pack makes no speed
  claim. If ON nodes ever drift, it is a search change and needs an SPRT.

| file | content |
|---|---|
| tt_replace_cache_after_w6.patch | the source change vs trial_w6 (switches at their source default 0) |
| tools/apply_trc.py | makes the change on a trial_w6 copy (anchored, fail closed) |
| BENCH.md | identity / gate pins, ON nodes |
| STATUS.md | done / in progress / next step / resume commands / unproven claims |
