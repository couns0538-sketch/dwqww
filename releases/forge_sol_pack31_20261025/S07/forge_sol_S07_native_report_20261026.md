# S07 native screen closure — 2026-10-26

The root-authorized native sweep and the single WAC300 screen both closed with actual outer command return code 0. The immutable tool SHA256 remains `7262dcf8259781396849c217e8713868d8f37736e63ec6015ff99c845b57baf7`; the canonical executable remains `e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b`. No compiler, replacement executable, engine/tool source edit, native repeat, publication or engine acceptance occurred.

The protocol is `forge_sol_S07_native_protocol_20261026.json`. The root confirmed S33/S48 Monte Carlo workers and raw audit had closed before launch. Both modes used primary Python with the existing chess dependency, CPU 4, nice 19, Threads=1, Hash=16, OwnBook=false. Each mode's first native process received exactly bare `bench 11` then `quit`; both printed 308972 before any UCI configuration. Later processes explicitly disabled OwnBook.

| Native control | Result |
|---|---|
| OFF d11/d13/d16/d20/d22, empty option object | 308972 / 745494 / 2460422 / 11901452 / 31111774 |
| ON d11/d13/d16/d20/d22, same empty option object | 308972 / 745494 / 2460422 / 11901452 / 31111774 |
| Current absolute deep-node guard for this control | PASS; zero node differences |
| PC precheck for this control | null; option_live_required=false |
| Sweep outer command | return code 0; 289.0936 s |
| WAC300, go movetime 1000, empty option object | **271 / 300** |
| WAC native illegal moves / exceptions | 0 / 0 |
| WAC independently recalculated scoring disagreements | 0 |
| WAC outer command | return code 0; 276.73 s |

WAC elapsed time can be below 300 seconds because a search may finish before its movetime budget. Raw stdin contains exactly 300 `go movetime 1000`, 300 `ucinewgame`, 300 Clear Hash operations and original EPD-derived positions. Raw stdout contains exactly 300 corresponding bestmoves. Every raw bestmove was independently checked for legality and membership in the unordered bm/am sets using the original frozen EPD. No move/result was reconstructed. The actual suite SHA256 is `9bfb7b42cf5bbc7f3d60ff767ca3be460e0ae4d9110ef9a71ddf0bd7071d4d46`.

The WAC result is one box screen, not an Elo estimate or a Zen5 performance claim. The same-empty-options sweep validates the frozen reference and tool path. Altered candidate options, distinct candidate ON WAC scores, and candidate acceptance remain UNVERIFIED. Historical 283-point screen figures were not substituted for this observed 271-point result. No run was repeated to change the score.

Evidence:

- `forge_sol_S07_native_sweep_20261026/`: all 11 native process transcripts, raw streams, actual return codes, hashes and complete tool result.
- `forge_sol_S07_native_wac300_20261026/`: first bare bench plus the single 300-position UCI process, raw streams, all 300 result records and actual process return codes.
- `forge_sol_S07_native_outer_capture_20261026/`: outside-tool command argv, declared cwd/environment, raw stdout/stderr, actual return codes, source/binary/tool/suite/protocol hashes, launch and cleanup receipts.
- `native_final_readonly_audit.json`: all 43 native output manifest entries and raw stream sizes/hashes verified; all 230 original source/book files across L75/L′77/B78 rehashed unchanged; 15 owned native/tool PIDs absent after close; observer closed.
- `native_engine_affinity_observations.jsonl`: 25 observation rows, 38 engine thread samples, all CPU 4 and nice 19; observer on CPU 0.

OS reads of native child `/proc/PID/cwd` and `/proc/PID/environ` returned PermissionError. Those errors are preserved in `native_engine_environment_observations.jsonl`. Exact cwd/environment launch arguments are captured from the owning Python launch calls; they are not described as independent OS observations.

Native result SHA256:

- Sweep: `b9a160bc1c43c7db9b2cddd30494552b518378120564fd037dfde7ffceaddae8`.
- WAC: `9c03f5ad65dbb9e33972e27acfd92f8a22dad689ee9cda2bd0da0630a0b7d8b4`.

Unsolved but legal WAC positions (29): WAC.002, WAC.021, WAC.033, WAC.049, WAC.055, WAC.101, WAC.131, WAC.132, WAC.141, WAC.145, WAC.163, WAC.165, WAC.176, WAC.190, WAC.196, WAC.204, WAC.205, WAC.222, WAC.226, WAC.230, WAC.241, WAC.245, WAC.247, WAC.256, WAC.258, WAC.265, WAC.291, WAC.293, WAC.296.

The earlier preparation README/report retain their original pre-native UNVERIFIED statements as a historical preparation record. This closure report supplies the later native control and single-score evidence. Root owns integration/publication and all engine acceptance decisions.
