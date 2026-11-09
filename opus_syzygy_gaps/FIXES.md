# FIXES — qa-syzygy-gaps-fixes-20261109

Branch from CR tip `6df0c739`. Pack/tool/doc only. No engine source or search behaviour changed. No long benches re-run. No grok-pc work.

| # | source | item | change | verification |
|---|---|---|---|---|
| 1 | CR SHOULD / QA MED F2 | `logs/root_p6_clock.txt` D_bad 350 vs json 0 | Regenerated the summary header from committed `logs/root_p6_clock.json` (`D_bad:0`); kept the existing detail `B\t…` rows unchanged. Nothing invented. | Parsed compact header as JSON; every field equals `root_p6_clock.json`; detail rows still start with `B\t` (12 lines). |
| 2 | CR SHOULD / QA LOW | `tools/fathom_root.c:87` sentinel before bound | Loop now `i < TB_MAX_MOVES && results[i] != TB_RESULT_FAILED`. | `rg` shows new order; no other edit in the file. |
| 3 | CR SHOULD / QA LOW | `tools/warm_identity.py` docstring still said mask `0x3` | Docstring body now says `0xF000` (CPUs 12–15), matching `MASK = 0xF000`. | `python3 -m py_compile`; no remaining `0x3 (CPUs 0-1` string. |
| 4 | CR SHOULD / QA LOW | `tools/uci_tb.py` / `warm_claims.py` stray engines on error | `Engine.quit()`: UCI quit, then `terminate`/`kill` of **this worker's own child** if still alive. Workers use `try`/`finally: quit()`. Docstring updated. | `python3 -m py_compile` both; AST parse OK. No engines launched on the box (no PC / no tables). |
| 5 | CR SHOULD / QA LOW | `logs/suite_parent.txt` mate Traceback | Replaced the bare `Traceback…` line with an explicit "no result (tool error…)" annotation pointing at BENCH; did not invent mate counts. | Line present; BENCH parent mate cell notes the annotation. |
| 6 | CR NIT / QA LOW | mate read-side 100/1500 honesty | `STATUS.md`, `HANDOFF.md`, `BENCH.md`: pack evidence = first **100 of 1500** mate rows; full `mutants_read_side.sh r1` **stopped unfinished by Couns**. | Grep for "stopped unfinished by Couns" / "100 of 1500" in those three files. |

## Deferred (not changed — would be engine / search, or not a pack fix)

None from the CR SHOULD/NIT list. Engine patch and candidate head `989399b` untouched.

## Manifests

`tools/make_manifests.sh` regenerated `MANIFEST.md5` and `MANIFEST.sha256` over every pack file except the two manifests; both verify clean.
