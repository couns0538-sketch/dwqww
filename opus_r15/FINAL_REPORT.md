# R15 (Opus) - FINAL REPORT - INTERIM (written 12:33 PC clock; the final version replaces this file)

Everything here is UNPROVEN until the crew gates it. No SPRT games were run, no Elo or speed claims are made.
Lock FD3A5190 = `C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_v23.exe`, sha256
`fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072`, md5 `2b4821e537c7004b8b588ef9e2ca07b1`; pins bench
d11 312866, d13 862329, d16 3024920, d20 12389307, d22 34048354; perft 5 startpos 4865609, kiwipete 193690690.
Branch `opus-r15-20261103` (worktree `D:\o15\wt`); scratch and exes under `D:\o15`. No sub-agents; every review is a
structured self-review, NOT independent.

## Status at 12:33
- Job 0: the four R14-B CR fixes were already pushed 10:05-10:31; re-verified on fresh clones (38 + 20 + 51 + 43 PASS).
- Base: the unpatched lock source through kit v2.3 `-Expose` = FD3A5190 byte for byte (11:38).
- Job 1: C1-C5 complete (kit pc1 = pc2, OFF = pins, ON live, smoke 0 illegal / 0 crashes, CI ASan+UBSan green); C6
  plain-checked, its kit pack running; two zero-build extras queued.
- Job 2: pin_check, cand_pack, gate_summary + 6 more tools with self-tests, 2 skills, the forge-uci MCP server.
- Left: C6 pack, extras, cand_pack -NoPatch self-test, final CI tie (ci_record), 30-minute bug check, final report.

## Candidates so far (D:\o15\cands\INDEX.md has every field)
| line | setoption | exe sha256 | exe md5 | ON bench d11 / d13 / d16 / d20 / d22 |
|---|---|---|---|---|
| C1 PruneLmrHist | PruneLmrHist 1 | fe99a27db187980d1786be7300da17b72cfb323f15a041b9ec215950670cc47e | cd7b651f344032e75b1c5a1c10beb32b | 294465 / 815919 / 2071386 / 14396694 / 33272164 |
| C2 QsMovePrune | QsMovePrune 3 | ff63a706e83e2e750b19f3ba61a1b2175033624696d9982f36611e86d8ffa9a2 | 2b0bdecee31448565a5ead2d93b15247 | 363674 / 815943 / 3220620 / 16380404 / 35367903 |
| C3 TtProbcut | TtProbcut 360 | 4c48a25bdc051659795b653e3b30bf5a6063bf84813c9f0e8ab1bbb733a87723 | 92b69c3f81cb1b9a86e5106527674df8 | 322040 / 845712 / 2757689 / 9154533 / 20921486 |
| C4 IirShallowTt | IirShallowTt 1 | 34055169d6c33e5ba94cfecc6b4699ede5e7dfa8a77c3e093c6343e72f2aea05 | 5ef69ec6f71b8a0bc60f360f65a85943 | 309855 / 724372 / 2173900 / 12053035 / 19939843 |
| C5 ContHistSplit | ContHistSplit 1 | 3b9f56da360852656514e7cd591c04fdb0ee4159e2070f26dd9060b32580f9f7 | 25f4015a2173f2c7b4ded606bea41b2a | 323985 / 753650 / 3128498 / 11261436 / 29194446 |
