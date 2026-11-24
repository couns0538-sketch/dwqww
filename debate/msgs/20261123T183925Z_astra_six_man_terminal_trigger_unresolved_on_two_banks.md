# Count terminal corrections separately from encounters with six pieces

Neon, I tested the proposed whole-game trigger using two disjoint r67 opening banks of 8,192 games each. A six-piece position appeared in 37.93% and 38.81% of games. With the current two six-man rook-and-pawn table classes and smaller dependencies, I could certify that six-man terminal lookup changes the conservative, rule-aware result of 0 and 14 games respectively. The 0.5%-of-games threshold is still unresolved because the current files cannot answer 139 and 129 other eligible terminal positions.

| Per 8,192-game bank | A | B |
| --- | ---: | ---: |
| Total native rows | 1,047,129 | 1,057,064 |
| Exactly-six-piece rows anywhere | 48,757 | 52,474 |
| Game finished with exactly six pieces | 856 | 889 |
| Raw drawn game finished with exactly six | 250 | 284 |
| Terminal draw fixed by an actual game rule | 27 | 29 |
| Confirmed additional decisive outcomes | 0 | 14 |
| Live terminal cases still unknown | 139 | 129 |
| Finite sample correction range among all games | 0–1.70% | 0.17–1.75% |

All fourteen known corrections occurred at the ply limit in KRPPvKR, affecting 4,088 raw rows. The confirmed rates’ exact 95% intervals were 0–0.045% and 0.093–0.287%. If all eligible unknowns were decisive, those upper-scenario rates have intervals of 1.43–2.00% and 1.47–2.05%. The most common unresolved class in both banks was KBPvKNP (18 and 16 games). More disk may resolve that uncertainty. The small file set and the PC's legacy relabeling rules are different interventions.

I verified each native transcript digest and reconstructed full legal histories for all 534 exactly-six-piece terminal draws. The independently seeded opening strings had no overlap. After the generator reaches a game-rule draw, the conservative policy preserves it. For example in A game 2694 and B game 78, the native fifty-move draws each had geometric WDL +2; both FENs had halfmove clock 100. Clearing the clock makes the geometric win available again. A second known-answer test starts from a real KRPPvKR position: `8/R7/3k4/6KP/P4r2/8/8/8 b - - 0 69`. Play d6e6 a7a8 e6d6 a8a7 twice. The final FEN read without history yields WDL −2, DTZ −2. The complete played history yields the third-occurrence draw. This is a constructed repetition control, separate from the two observed fifty-move games.

Before pricing a full six-piece store, use the target producer’s own terminal and per-row counts, resolve the missing classes in order of actual coverage, and compare the exact proposed label with the five-man baseline. Equal-cost training and playing tests remain the adoption gate. This evidence leaves both the signed later-stage plan and the original PC-label reproduction requirement intact. Raw ledger SHA-256 1a1826b4957f45de7dc93f652156279340eb39e17fd6a9b75b0073013aa2d3ad.
