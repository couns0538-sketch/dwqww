# T1 book resolution: PC-specific ideas for the crew (not tried in this job)

1. **Confirm the ratio for small changes.** T1 measures at 2:1 node odds (nElo near 300). Gates decide changes of
   0-10 nElo, so the ratio still has to be measured near zero.
   - Cheapest way on this PC: the same script on CPUs 2-3 with `nodes=20000` vs `nodes=16000`, 3000 pairs per book.
     Fixed nodes make the result independent of the crew load; ~1.2 h per book at the ~85 games/min seen here.
   - The fastchess "nElo" of each book then gives the small-change ratio with an SE of 4.5 nElo per book.
2. **At gate time control.** The gates play 10+0.1, Threads 2, Hash 16, conc 4 on CPUs 4-15. One way to settle it:
   play the next near-zero candidate twice, once per book (same exe pair, same TC), in a gate gap, and compare the
   pentanomial variance and nElo. That costs real gate hours, so it is for the owner to plan.
3. **SPRT bounds after a book switch.** The gates use `-sprt elo0=0 elo1=10 model=normalized`, so the bounds are in
   nElo, and nElo depends on the book.
   - Keep [0, 10] on UHO: the gates get faster when UHO raises nElo per change, but "+10 nElo" then stands for a
     smaller logistic-Elo change than on 8moves.
   - To keep the old meaning, scale the bounds by the measured ratio r: [0, 10 r] on UHO.
   - Either is valid; it is a policy choice. Write it into the gate runner's RUN_INFO so later readers know.
4. **Opening offsets.** UHO_Lichess_4852_v1 has 2,632,036 positions: 1,457,270 white to move, 1,174,766 black to move,
   2-16 plies (books README). The gates' `order=random start=<N>` scheme gives no reuse for thousands of gates. With
   `-repeat`, each opening is played with both colours.
5. **OwnBook.** The lock defaults to `OwnBook=true`. Every UHO run must pass `option.OwnBook=false`, as the gates already
   do; T1 did the same.
6. **Games per hour.** Mean game length per book is in RESULT.md (plies). A book with shorter games also gives more
   games per hour at the same TC; count that together with the nElo ratio.
7. **Other suites in the same CC0 repo** to try if UHO_Lichess_4852_v1 does not suit Forge: `UHO_4060_v4.epd` (241,670),
   `UHO_XXL_2022_+110_+139.pgn` (253,847), `noob_3moves.epd` (150,932) for a balanced control.
