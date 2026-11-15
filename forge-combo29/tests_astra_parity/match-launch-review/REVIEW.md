# Independent Job B launch review

Reviewed 2026-11-15T01:35:52Z. No engine, match, Git mutation or root-state write was performed. This is source review, not executed match coverage. The reviewed launcher is retained in `protocol-reviewed.mjs.txt`; numbered official-runner excerpts, full-file hashes and command output are adjacent.

No blocking launch issue found in the requested scope.

| Requirement | Source evidence and conclusion |
|---|---|
| 100 games, 50 openings, two colors | The plan explicitly sets `-rounds 50 -games 2`. `roundrobin/scheduler.hpp:19–22` computes one pairing × 50 rounds × two games for two players. `schedule/base_scheduler.hpp:43–59` fetches an opening only at the first game of a pair and retains its ID for both. `roundrobin.cpp:79–91` swaps the colors on the even game; the default `noswap` and `reverse` values are false in `types/tournament.hpp:69–70`. |
| Omitted `-repeat` | `cli.cpp:654–660` implements bare `-repeat` by setting `games=2`. The explicit `-games 2` already supplies the same value; there is no separate repeat flag to enable. |
| Same binary, only HindsightDepth differs | The plan uses `d.binary` for both engines. Their common explicit options are Threads=1, Hash=16, OwnBook=false, MateAlphaGuard=false; HindsightDepth is true versus false. Source/binary identity must still pass the existing declaration and runtime audits. |
| Exactly node-limited commands | `-each nodes=50000` applies to both engine configurations (`cli.cpp:239–244`); `parseEngineKeyValues` assigns the node limit (`cli.cpp:202–203`). Time, increment, fixed time and move limits default to zero (`timecontrol.hpp:17–27`); depth defaults to zero (`engine_config.hpp:20–21`). `uci_engine.cpp:122–165` therefore emits `go nodes 50000` without a clock/depth argument. |
| UCI protocol without `proto=uci` | The runner uses UciEngine. The optional `proto` parser accepts only `uci` and assigns no configuration field (`cli.cpp:220–224`), so omission does not select another protocol. |
| No adjudication or SPRT | Draw, resign, maximum-move, tablebase and SPRT structs all default `enabled=false`. No corresponding enabling option occurs in the plan. Normal chess terminal rules remain applicable. |
| Deterministic book slice | The plan sets the fixed seed and successive opening starts. `tournament_manager.cpp:44` seeds before tournament construction. `opening_book.cpp:23,40–50` shuffles, rotates by start minus one, then truncates to the requested rounds. Each pair uses the same selected opening. |
| Saved config does not load old settings | The plan supplies only `-config outname=...`. `cli.cpp:539–543` loads a file only for the separate `file` key; `outname` sets the output path. |

The official-runner binary SHA256 was read as `f8f1706b6b4906d524dd0ac0547deb9ec2b6b10b4e32d7bde66914ddee0ebd4f`, matching the prepared protocol. Actual first-batch option traces, PGN pair assignments, node commands, full saved config, and process outcomes remain required runtime evidence. This review does not replace those checks.

Two exploratory searches included nonexistent guessed source subdirectories and returned exit 2; the subsequent reads used the actual paths above. They did not run or modify any executable, source or experiment.
