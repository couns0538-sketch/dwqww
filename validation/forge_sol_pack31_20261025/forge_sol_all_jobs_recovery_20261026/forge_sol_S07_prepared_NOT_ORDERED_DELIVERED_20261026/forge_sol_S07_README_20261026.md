# S07 depth sweep and WAC300 tool — 2026-10-26

This is the original S07 Python tool, its synthetic subprocess tests, supplied-artifact import, and actual corpus parser proof. Native engine screens remain **UNVERIFIED** until the root runner performs them after the S33/S48 work and closes the cache leases. No engine source is modified. No Elo claim is made.

Files:

- `forge_sol_S07_screen_sweep_20261026.py`: standalone standard-library CLI; WAC modes additionally require python-chess.
- `test_forge_sol_S07_screen_sweep_20261026.py`: subprocess tests using a deliberately synthetic UCI process; it is not a chess engine.
- `forge_sol_S07_report_20261026.md`: evidence and unverified native fields.
- `forge_sol_S07_supplied_p23b_final_20261026/result.json`: offline supplied raw bench/table import.
- `forge_sol_S07_actual_wac_final_20261026/result.json`: parser-only proof for the actual original WAC corpus.

The shipped test defaults reference this workspace's supplied source and WAC files; they are external read-only dependencies, not regenerated fixtures. The actual suite is `/workspace/forge-sol-next-20261024/int16-review/wac300.epd`, 22,862 bytes, SHA256 `9bfb7b42cf5bbc7f3d60ff767ca3be460e0ae4d9110ef9a71ddf0bd7071d4d46`. This equals the P23b supplied `x_wacnew.epd` hash. System python3 lacks chess; an existing package is available at `/workspace/.cloud-setup/venv/lib/python3.12/site-packages` (chess 1.11.2). No installation is needed in this workspace.

```bash
PYTHONPATH=/workspace/.cloud-setup/venv/lib/python3.12/site-packages python3 -B -m unittest discover -s /workspace/forge-pack24-20261026/S07 -p 'test_*.py' -v
```

CLI modes:

```text
p23b-import --source-root FILES --out NEW_DIRECTORY
wac-validate --suite ORIGINAL_WAC_EPD --out NEW_DIRECTORY
sweep --engine-argv-json '["/absolute/frozen/forge"]' --off-options-json '{}' --on-options-json '{}' --out NEW_DIRECTORY
wac300 --engine-argv-json '["/absolute/frozen/forge"]' --suite ORIGINAL_WAC_EPD --movetime-ms 1000 --options-json '{}' --out NEW_DIRECTORY
```

`--out` must not exist and must have an existing nonsymlink parent. Each runtime invocation starts with a fresh process receiving only `bench 11` and `quit`; it must exit normally and match 308972 when `--reference lock` (the default). Only then can a UCI process start. All five depths (11/13/16/20/22) run separately for OFF and ON with Threads=1, Hash=16, OwnBook=false. Core overrides and command injection are rejected. `--expected-engine-sha256 FULL_SHA256` pins argv[0]; all existing file arguments are also hashed before/after. File arguments should be absolute because subprocesses run inside the new output directory. `--reference none` is an explicit non-lock comparison and makes no lock identity claim.

The current guard is exactly `abs(ON/OFF - 1) > 0.20` at d20 or d22. Equality at 20% passes that guard. The PC precheck is the earliest changed depth among all five; no changed depth fails the option-live check when the supplied OFF/ON option objects differ. These screens do not establish that every code path or option interaction has been exercised.

UCI names are checked against the handshake. Historical release Forge accepts source tunables while omitting them from the handshake. An explicit caller declaration permits those names:

```text
--off-options-json '{"RefutLmr":0,"RefutLmrMinR":6,"RefutLmrPlies":1}'
--on-options-json '{"RefutLmr":4,"RefutLmrMinR":6,"RefutLmrPlies":1}'
--allow-unadvertised-options-json '["RefutLmr","RefutLmrMinR","RefutLmrPlies"]'
```

The allowlist is recorded as a caller declaration. It is not an engine-advertised validation claim. Its source is supplied P23b README/search tunables. Unknown-option and invalid-value diagnostics still fail the run.

WAC modes parse the original EPD once with `chess.Board.from_epd`, require its exact frozen hash and 300 unique IDs, and validate every board and bm/am move. Runtime uses fresh ucinewgame and Clear Hash for each position and `go movetime T`. A result passes the position when the returned move is legal, belongs to the bm set, and is outside the am set. Multiple accepted moves are unordered; WAC.274 accepts g6b6 or g6g5 and excludes g6d6. Invalid/illegal bestmoves remain recorded with exceptions and fail the run. Unsolved but legal positions reduce the score without becoming protocol failures. No result is reconstructed from historical chunks. A WAC runtime PASS means all 300 records completed without process, parsing, identity or legality failures; it is not a minimum-score or strength pass.

`result.json` and `processes.json` retain argv, return code, timeout and cleanup state, input hashes, and raw stdin/stdout/stderr file hashes. Bench summaries are parsed again from complete captured stdout after process exit. Capture is bounded at 4 MiB per output stream; truncation fails. Children receive quit, then termination/kill on timeout, and are waited. On POSIX, lingering members of the newly created child process group are killed after its leader exits. A timeout, nonzero exit, stderr, incomplete capture, changed input, duplicate summary or unknown-option diagnostic cannot become PASS. The default timeout is 120 seconds per awaited reply; choose it explicitly for slower hardware. Runtime WAC allows movetime plus this reply margin.

The tool does not compile, copy source trees, acquire host resource leases, choose CPU affinity, change host limits, or publish. The root caller owns those steps and must keep native runs out of the S33/S48/cache-lease window.

Current controls supplied by the parent:

- L: `FILES/01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src`.
- L′: `FILES/01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src`.
- B: `FILES/01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src`.
- `FILES` is `/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files`.
- Canonical frozen native ELF identified by the parent: `/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/_verify/build_Lp/forge`, expected SHA256 `e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b`.
- Parent's current merged-tests SHA256: `55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c`.

Those native identities are handoff inputs. This S07 preparation has not executed that ELF or independently requalified the three source controls. Native sweep and native WAC score fields remain UNVERIFIED.
