# R15 TOOLS - what each tool, skill and server is for and how to verify it

Branch `opus-r15-20261103`, folder `opus_r15/`. Usage details and pitfalls: `opus_r15/tools/README.md`. Every tool is
re-runnable, refuses to overwrite its outputs, and has a self-test with planted failures (results in
`opus_r15/tools/test_logs/`). Own work runs on CPUs 0-1 at Idle; scratch under `D:\o15`.

## Scripts (opus_r15/tools)
| tool | for | verify (self-test, last result) |
|---|---|---|
| pin_check.ps1 | any exe vs the lock pins (bench d11/13/16 [+20/22], perft 5 x2); ON lines must be advertised, in range, accepted, live | `bash test_pin_check.sh D:\o15\logs\<new>` -> 12 / 12 |
| cand_pack.ps1 | patch -> gate-ready exe + RESULT.json + INDEX row (kit pc1 = pc2, pins, smoke, lint) | `bash test_cand_pack.sh <new>` -> 9 / 9; C1-C5 full runs PASS |
| kit_build_r15.sh | QA kit v2.3 `-Expose` wrapper for D:\o15 (fixed pc_gate, disk floors) | unpatched lock -> sha256 fd3a5190... (opus_r15/base/) |
| smoke2m.py | 2-minute timed ON self-play, legality by the engine's own perft 1, crash / hang / time loss | `bash test_smoke2m.sh <new>` -> 11 / 11 + 5 |
| cleanroom_lint.py | patches and commit messages: no names / licence headers / protected files | `python -I -B test_cleanroom_lint.py <new>` -> 15 / 15 |
| make_index.py | INDEX.md from the RESULT.json + ci.json records | run by cand_pack; output `D:\o15\cands\INDEX.md` |
| index_check.py | before queueing: hashes, record checks, CI, advertised option + range | `python -I -B test_index_check.py <new>` -> 8 / 8 |
| gate_summary.py | gate W/D/L, Ptnml, Elo, nElo, exact LLR, problem games, games/h; `--watch` gate speed; `--html` one sortable page of all gates (the "app": D:\o15\reports\gates_20261103.html, 63 gates) | `bash test_gate_summary.sh <new>` -> 8 / 8 + 2; all 62 F: gates with a PGN reproduce exactly |
| extra_check.py | an existing exe whose option was never gated alone: copy, pin_check OFF / ON, smoke, "extra" record | runs x1 / x2 (INDEX "existing exes" section) |
| ci_record.py | ties a green sanitizer CI run to the exact built patches, writes ci.json + evidence | `python -I -B test_ci_record.py <new>` -> 4 / 4 |
| mate_reprobe.py | re-probes every flip of R13's mate probe (3M nodes) at 30M nodes, OFF and ON, and names REAL losses | its run on C1-C6 (cands/*/mate_reprobe.json); a lost mate ON misses at 30M while OFF finds it = exit 1 |
| report_rows.py | the FINAL_REPORT tables straight from the records (no hand-copied hashes) | used for FINAL_REPORT.md |
| final_checks_r15.sh | end-of-round checks: patches on fresh lock copies with exact ON nodes, index_check, all self-tests, lint, sync | its result line in FINAL_REPORT.md |
| plain_build_r15.sh, fresh_lock.sh, export_src.sh | quick plain builds, fresh lock copies, clean exports | used for every candidate |
| lowrun.ps1, pc_gate.ps1, cpu_users.ps1, doc_lint.py, hash_sweep.py, commit_span.py (R14-B); selfplay_smoke.py, run_pinned.py (R13) | copied unchanged | their own R14-B / R13 tests; pc_gate CR fix 3 re-verified in Job 0 |

## Skills (live in C:\Users\Administrator\.claude\skills, copies in opus_r15/skills)
| skill | for | verify |
|---|---|---|
| forge-r15-candidates | idea -> patch -> plain check -> cand_pack -> CI row -> index_check; facts, pitfalls | listed by the harness as an available skill (2026-11-03 12:16); its commands are the ones run for C1-C5 |
| forge-gate-summary | gate summaries, the fastchess printing / LLR facts, normal gate speed | listed by the harness; its numbers come from test_logs/gate_summary_all_F.txt |

## MCP server
| server | for | verify |
|---|---|---|
| forge-uci (`opus_r15/mcp/forge_uci_mcp.py`, standard-library Python, stdio JSON-RPC) | tools pin_check, uci_options, bench, perft, gate_summary, index_check, pc_status for any Claude Code session; engines at Idle on CPUs 0-1 | `python -I -B opus_r15/mcp/test_forge_uci_mcp.py` -> 18 / 18 over the real stdio transport; registered at user scope with `bash opus_r15/mcp/setup_forge_mcp.sh` (2026-11-03 12:18, `claude mcp get forge-uci`: Connected) |

Existing servers considered (web search 2026-11-03): AnglerfishChess/chess-uci-mcp (MIT, Python >= 3.12 + uv) and
a Go MCP server for one well-known engine (MIT) bridge a UCI engine for position analysis (best move, eval, options); none checks
bench / perft pins, option lines or gate results, and both need an install (uv / Go) that this PC does not have.
chess-uci-mcp is the licence-clean choice if position analysis is ever wanted; nothing was installed in R15. Plugins:
none made - the two skills plus the server cover the R15 workflows without a plugin wrapper.
