# S07 portable depth sweep and WAC300 screen

The native reference sweep passed all five fixed node counts in both control series. One WAC300 run at 1000 ms scored **271/300**, with **zero illegal moves or exceptions**. Frozen inputs stayed unchanged and all owned processes closed. These are box-screen observations, with no Elo or Zen5 speed claim. Full native details are in `forge_sol_S07_native_report_20261026.md`.

The original tool is unchanged, SHA256 `7262dcf8259781396849c217e8713868d8f37736e63ec6015ff99c845b57baf7`. The test module adds only two fixture locators; all 24 tests and every test function/class AST match the previous version. Original preparation files remain preserved outside this delivery as dated history.

Requirements: Python 3 and python-chess (`import chess`; verification used chess 1.11.2). No original workspace or native engine is needed for the tests. The packet includes the exact two P23b import inputs under `provided/` and the original 22,862-byte WAC corpus, SHA256 `9bfb7b42cf5bbc7f3d60ff767ca3be460e0ae4d9110ef9a71ddf0bd7071d4d46`.

From this directory, with chess installed in the selected interpreter:

```bash
python3 -B -m unittest discover -s . -p 'test_forge_sol_S07_screen_sweep_20261026.py' -v
```

If using a separate existing chess package, set `PYTHONPATH` only to its site-packages directory. Test fixture defaults are adjacent to the test module:

- `FORGE_S07_FILES_ROOT` overrides `HERE / 'provided'`.
- `FORGE_S07_WAC_SUITE` overrides `HERE / 'forge_sol_S07_wac300_20261026.epd'`.

`forge_sol_S07_locator_contract_proof_20261026.json` records the genuine old-module RED/new-module GREEN configuration check. The relocated packet verification receipt records a fresh run of all 24 tests using its copied fixtures and only the existing chess dependency on PYTHONPATH. Test subprocesses are clearly synthetic Python doubles; they make no native engine claims.

CLI examples use new output directories:

```text
python3 -B forge_sol_S07_screen_sweep_20261026.py p23b-import --source-root provided --out NEW_DIRECTORY
python3 -B forge_sol_S07_screen_sweep_20261026.py wac-validate --suite forge_sol_S07_wac300_20261026.epd --out NEW_DIRECTORY
python3 -B forge_sol_S07_screen_sweep_20261026.py sweep --engine-argv-json '["/absolute/frozen/forge"]' --reference lock --off-options-json '{}' --on-options-json '{}' --out NEW_DIRECTORY
python3 -B forge_sol_S07_screen_sweep_20261026.py wac300 --engine-argv-json '["/absolute/frozen/forge"]' --reference lock --suite forge_sol_S07_wac300_20261026.epd --movetime-ms 1000 --options-json '{}' --out NEW_DIRECTORY
```

Each native mode first sends bare `bench 11` in a fresh process before UCI configuration. Later processes use Threads=1, Hash=16, OwnBook=false. Expected lock nodes at depths 11/13/16/20/22 are 308972/745494/2460422/11901452/31111774. The guard fails when `abs(ON/OFF - 1) > 0.20` at d20 or d22; the PC precheck is the first changed depth. Different option sets must change a node count to pass the live check. Unadvertised release tunables require an explicit `--allow-unadvertised-options-json` declaration. `--expected-engine-sha256` pins argv[0]. These controls do not establish playing strength.

WAC scoring uses the final legal bestmove in the unordered bm set and outside am. Earlier PV moves do not score a position. Invalid input, illegal moves, timeouts, unknown options, nonzero exits and incomplete/truncated captures fail. An otherwise complete WAC runtime PASS reports the observed score without imposing a minimum score.

`forge_sol_S07_native_evidence_20261026.tar.gz` contains the original native raw streams and receipts; `forge_sol_S07_native_evidence_index_20261026.json` lists every member's byte count and SHA256. No executable binary or source tree is included. The fixture index and delivery manifest cover the small inputs and packet files.

The comparability audit preserves fresh 271. Historical CR 286/287 identify different-net candidates; their historical lock controls were 283/284. Available harnesses use final bestmoves, and a saved historical lock result independently rescores 283. Exact independent CR harness/raw runs are missing, so the gap's cause remains **UNVERIFIED**. No native run was repeated. A later reference mismatch must remain recorded while other authorized checks continue.
