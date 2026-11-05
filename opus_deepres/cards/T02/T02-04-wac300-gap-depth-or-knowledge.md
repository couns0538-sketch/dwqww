# T02-04: WAC300 gap of the npt nets (263-269 ON vs 271-272 OFF): speed or knowledge - an equal-node run decides
Status: COMPLETE (hypotheses, own measurements and the separating test; the test itself was not run - research only)

## Source
Own records, read-only: QA pack `C:\Users\Administrator\grok-pc\qa_npt_w4s10_20261101\pack\wac_tactics.py` (pinned
md5 E87D2ACE... in `run_w4s10_pc.ps1`; suite `x_wacnew.epd` md5 D258D594...) and its outputs
`D:\forge_coder_checks\npt_w4s10\run_20261101_121847\` (`wac_OFF1.json`, `wac_ON_final_ftp1.json`, `wac_OFF2.json`,
bench `off.txt`, `on_final_ftp1_full.txt`); gates NPTW4S4-07 / NPTW4S4-09L in FORGE_RESULTS.csv (tools/tried_gates.py);
the owner's summary (every w4 net 263-269, net-off 271-272; own re-read of the s10 run: OFF 272 / 273, ON 267).

## Licence
Own records and own tools only; nothing external was read for this card.

## Mechanism
Four hypotheses, each with what it predicts (numbers: w4 s10 final ftp1 net, WAC300 at `go movetime 200`, Threads 1,
Hash 16, fresh hash per position, OFF run twice):
- H1 speed: the K32H3^ L1-1024 eval costs time. Same exe, bench: OFF 2.07-2.16 Mnps vs ON 1.11-1.21 Mnps (corrected by verify: all five bench depths 11-22 in off.txt /
  on_final_ftp1_full.txt give OFF 1.95-2.17 vs ON 1.02-1.21 Mnps, ON/OFF 0.47-0.58 per depth), and ON needs
  more nodes for the same depth (d20: 19.8M vs 12.4M nodes; 16.3 s vs 5.7 s). In WAC at 200 ms: median depth OFF 17,
  ON 15. Predicts: at equal nodes (NPS cost removed) the gap closes or reverses.
- H2 knowledge (data filter): the training rows exclude the positions WAC is made of - the self-play writer drops
  in-check rows, capture / ep / promotion best moves, mate scores and |cp| > 3000 (skill forge-selfplay-datagen:
  17.5 % + 9.3 % + 0.9 % of searches), so a position just before a winning sacrifice is rare in the data, while the
  lock's HCE has explicit threat / hanging-piece / king-safety terms. Predicts: the gap stays at equal nodes and the
  misses cluster where the solution is a capture or check or leaves material down.
- H3 scale vs margins: futility / razoring / null-move / SEE margins were tuned on the lock eval's cp scale; a net with
  another effective scale prunes differently (the ~60 % bigger ON tree per ply fits this). Predicts: the gap stays at
  equal nodes, misses spread over all solution types, ON / OFF ratio of median |score| on quiet positions off by > 20 %.
- H4 noise: for this one net 13 positions are lost (both OFF runs solve, ON fails) and 8 won: a sign test on 21
  discordant positions is far from significant (p ~ 0.38); only the consistency over all w4 nets makes the gap real.

## Forge fit
No engine change. Lock grep: the HCE has threat / hanging-piece / king-safety terms
(`include/forge/eval_params.hpp:39-44` ThreatByMinor ... HangingPiece, `:72` KingSafetyWeights; 36 hits) and the
search has cp margins tuned on the lock eval (`include/forge/search.hpp:205-210` Razor*/Futility*, `:221`
QsFutilityMargin, `:242` CaptureFutilityBase; 44 hits). The net loads through EvalFileHalfKA (empty = lock eval);
the QA tool needs `go nodes N` / `go depth D` modes besides `go movetime T`, node logging (~10 lines), a root-eval dump.

## Expected gain
None directly - a diagnostic. It decides where the npt deficit (-86 to -116 Elo vs AL1 in 248-288-game SPRTs, H0
accepted) lives: if H1, data filters at fixed net size (T02-02, T02-03) cannot close it and speed or a smaller L1 is
the lever (track T05); if H2, keeping some tactical rows becomes a data card. Forge estimate: 0 Elo, **UNPROVEN**.

## Effort
Crew 0.5 h (nodes / depth modes + a 20-line classifier). CPU: 6 WAC runs (OFF and one w4 net at N nodes, depth 15,
depth 17; ~1-3 min each on 1 thread), 2 more for net s17, the 12k quiet FEN set at depth 10 per engine. GPU: none.

## Test plan
1. Equal nodes: `go nodes N`, N from one OFF run at 200 ms with nodes logged (today's json has no node field; bench
   NPS suggests ~400k), OFF vs the w4 s10 net, same exe and suite. ON >= OFF - 1 = H1 confirmed. (Fixed depth alone
   would favour ON: its tree is ~60 % bigger per ply, so equal depth gives it more effort.)
2. Second probe, fixed depth 15 and 17 (knowledge at depth vs tree shape). If ON trails at equal nodes, classify the
   positions OFF solves and ON misses: solution move capture / check / quiet, material after the move, ON minus OFF
   root static eval. Captures / checks dominate = H2; spread + scale ratio off by > 20 % = H3.
3. Repeat step 1 with a second w4 net (s17) to rule out H4. Whichever lever wins goes to its own gate route: UHO SPRT
   [0, 5] at STC, then LTC (a speed change = nps ABBA only).

## OFF-by-default design
Nothing in the engine changes; EvalFileHalfKA stays empty by default, so the lock bench / perft pins are untouched.
The nodes / depth modes are new arguments of the QA tool (default = today's movetime behaviour).
