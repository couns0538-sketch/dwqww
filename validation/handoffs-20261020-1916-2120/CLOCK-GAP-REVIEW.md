# Targeted clock-gap handoff review

**The three reported historical intervals and original source/binary identities check out. The original time-forfeit cause remains unresolved.** This adds diagnostic evidence; it does not repair, retry or rehabilitate the invalid TT match, and supplies no new candidate17 launch clearance or blocker beyond the already retained operational anomaly.

Only this report was written. No engine, match, build, attached analysis script, full 11,229-search analysis, Git operation, production/config/skill edit or new experiment was run. GrokChess was outside scope. Root separately verified all 28 uploaded payloads and ZIP SHA256 `bc811cf04f70cfb39b28e53e1cc696bbfb4b185428f4ac71d5dc1411dddf7ea6` in `clock-gap-replay/ROOT-VERIFY.json`.

## Independently verified

Compared handoff files under `clock-gap-replay/extracted/files/` against the previously restored original CI files in `/workspace/.cloud-setup/tt-strength-final-39403471059/verified/files/`, whose restoration is recorded by `validation/tt-strength-20261020/final-audit/RESTORE-VERIFIED.json`. All checked bytes match: baseline/candidate/Fastchess ELF executables; both original source tarballs; SPRT communication log, PGN, manifest, state, command and study summary. Original CI build provenance binds the engine files to baseline `c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e` and candidate `8865666cc0ab4961cd507bae40ff6ce44e9319df`.

| Original artifact | SHA256 |
|---|---|
| Baseline ELF | `039a26d266bc33f26c5fcd23dcf7d140adbc5768ccf14e8403eb8204a8718dd7` |
| Candidate ELF | `f172de75f4a7ac3f5520d696ac11e8273444826c5b3434b1aa55052d3cb3f09e` |
| Fastchess ELF | `e50a2688b24e2efc051092a0b69a9517402805382ee56ce05b13f1ca0b942706` |
| Baseline source tar | `ed3f394724f75d4695f12e576d99be27855d374619427aa7fbceac605a45aa77` |
| Candidate source tar | `132cf06bc1175d3309dcd1ea9953307144efda6c792ccec4aa3e991c25d99451` |
| Original Fastchess log | `5be5004c9e6efd383ba42d5181d231fa2f89fbd74aa9a691478b6707f1a9c1d3` |

Independently parsed only the targeted original exchange and subtracted timestamps using integer microseconds:

| Original log record | Time |
|---|---|
| line276633, Baseline `go wtime 423 btime 63 winc 20 binc 20` | 09:59:55.091251 |
| line276643, depth10 info, `time 24` | 09:59:55.199898 |
| line276644, `bestmove e6e1` | 09:59:55.199947 |
| line276647, baseline loses on time by45ms | 09:59:55.200065 |

Therefore `bestmove − go = 108.696ms`; `(last info − go) − 24ms = 84.647ms`; and `bestmove − last info = 0.049ms`. These agree with the handoff and our existing `final-audit/forfeit-exchange.json`. The discrepancy is already present at the last **logger observation** of depth info; it was not introduced solely by a long logger-observed gap after that record.

Inspected both frozen source tarballs as data. Both `src/uci.cpp:157,321` capture `command_start` immediately after `getline` and assign it to `limits.request_start`. Both `include/forge/search.hpp:35` define that field. Baseline `Searcher::search:1411–1414` and `Worker::search:1151–1152` preserve it; candidate equivalents are at1458–1461 and1198–1199. Thus an explanation based solely on these exact binaries omitting pre-worker admission time is unsupported. This agrees with our existing clock-contract lineage; it is not a reason to add another origin patch.

The baseline info emitter samples elapsed wall time **before** acquiring the output mutex, computing printed hash occupancy, formatting the remainder and flushing (`src/search.cpp:1215–1224`). Its sampled `time 24` is not an engine write timestamp. The go logger timestamp also precedes the engine's actual `getline`/origin capture. The observed84.647ms difference can therefore span several unobserved boundaries; it does not distinguish delayed command receipt, scheduling, output-side work/wait or transport/logger handling.

As a bounded secondary check, independently recomputed all40 local replay wall/lag values from the two supplied timestamped JSONL journals without executing their replay script. Every value matches its result JSON. The reported baseline20-search median/max are28.124/32.016ms, candidate27.645/31.744ms; maximum last-info discrepancies are1.083/1.294ms. Both journals end with a sent `quit`, and their result records report exit0. These establish internally consistent negative-reproduction records on the handoff host; they do not reproduce original scheduler/TT/history conditions.

## Limits and effect on current work

The handoff's full-log totals, quantiles and “only one >=20ms baseline discrepancy” are preserved claims from its whole-trace analysis, **not independently recomputed in this targeted review**. Its two unit-test passes were read as retained evidence, not rerun. The supplied replay script leaves stderr unread and does not join/assert reader completion or embed before/after binary hashes in its result; those records cannot independently establish a complete clean stderr/lifecycle audit. The supplied ELF identities do match the original CI artifacts, but that match alone cannot retroactively strengthen execution provenance.

Our separate `validation/time-forfeit-causal-20261020/REPORT.md` already retains a single telemetry cold→warm negative reproduction, original31ms hard budget and unresolved historical delay. The handoff's repeated unchanged-binary fixture is additional negative-reproduction evidence, not independent strength games or a substitute for that experiment's provenance. Its recommendation to start a latest-integration stress project is not adopted by this review.

The remaining question is **which interval between Fastchess's logged send, the engine's command receipt/time sample, and Fastchess's output observation contained the exceptional delay**. Neither these original logger records nor later successful local replays answer it. There is no new demonstrated clock-code defect, speed gain, Elo gain, general reliability proof or Stockfish3200 result. Preserve this handoff and proceed under candidate17's separately frozen proof/readiness gates without importing these40 searches as match evidence or changing its protocol.
