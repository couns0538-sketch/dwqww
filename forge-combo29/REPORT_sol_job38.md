# Sol — Job 38 fastchess fixed-node identity

## Step 0. Unchanged build and fastchess pins

The unchanged GCC 14.2.0 Job 34 binaries both passed all five fresh-process pins. The defaults gave 312866 for `bench 11`, 862329 for `bench 13` and 4865609 for `go perft 5`. PC20 with synthetic net768 gave 882074 and 4275906 for the two benches and reported `NNUE v3 active` with checksum `30ab43b4ba5db5f3`. [r15d raw pins](sol/job38/pin-evidence/r15d.raw.txt) · [kF raw pins](sol/job38/pin-evidence/kF.raw.txt) · [Job 34 build evidence](sol/job34/build-evidence/build-all.txt)

The version line was `fastchess alpha 1.8.3 20261107-d7b47e8`. `nproc` returned 5. I ran 4 games at once with one thread per engine. [Version](sol/job38/pin-evidence/fastchess-version.txt) · [nproc](sol/job38/pin-evidence/nproc.txt)

## K38 and C38. Known answer and sensitivity

**K38 PASS.** The two r15d runs at 20,000 hard nodes per move matched every move and PGN node field in all 10 games on UHO lines 4001–4010. Each recorded 1,130 plies at PC20, active net768, Threads 1 and Hash 16. [K38 readback](sol/job38/K38.stats.json) · [Raw PGNs](sol/job38/raw)

**C38 PASS.** With r15d and `LmrQuietBase=60` on both sides, the same ten roots and 20,000 hard nodes per move produced 1,416 plies and 10 differing games against K38a’s PC20 `LmrQuietBase=93`. [C38 readback](sol/job38/C38.stats.json) · [Raw PGN](sol/job38/raw/C38.pgn)

The first difference was in the PGN node field. UHO line 4001, game 1, ply 1 from the opening. FEN `rn2kb1r/ppq1pppp/2pp1n2/7b/2BPP1P1/2N2N1P/PPP2P2/R1BQK2R b KQkq - 0 7`. K38a move `b8d7` and node field `16847`. C38 move `b8d7` and node field `8983`.

The first move difference followed. UHO line 4001, game 1, ply 3 from the opening. FEN `rn2kb1r/ppq1pppp/2pp1n2/7b/2BPP1P1/2N2N1P/PPP2P2/R1BQK2R b KQkq - 0 7`. K38a move `d7e5` and node field `17983`. C38 move `h8g8` and node field `7637`.

## Prediction and grade

I froze `90835c2` after C38 and before G20. The prior equal fixed-node traces led me to predict zero differing games at each of the three limits. [Frozen prediction](sol/job38/prediction.json) · [UTC stamps](sol/job38/stamps.txt)

| Match | Forecast differing games | Observed | Grade |
| --- | ---: | ---: | --- |
| G20 | 0–0 | 0 | met |
| G50 | 0–0 | 0 | met |
| G250 | 0–0 | 0 | met |

## G20, G50 and G250. Move lists and PGN node fields

Every measured game had two engines of the same build with PC20, active synthetic net768, Threads 1, Hash 16 and OwnBook false. Both used the stated hard node limit per search and fresh processes for each game. The reading compares the two builds using the same opening FEN.

| Match | Hard nodes / move | UHO lines | r15d games / plies | r15d move SHA-256 | kF games / plies | kF move SHA-256 | Games differing / compared | Reading |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| G20 | 20,000 | 4011–4310 | 300 / 32,814 | `92ed005ce3ecaa8d75f7ed345ccbe540f32228b4192773f42ed27c41210dda5a` | 300 / 32,814 | `92ed005ce3ecaa8d75f7ed345ccbe540f32228b4192773f42ed27c41210dda5a` | 0 / 300 | **IDENTICAL** |
| G50 | 50,000 | 4311–4460 | 150 / 14,034 | `649e80b97a328fc39096d0a3ec129ec4cc8a5ddc20c0aca28c09295ba8bc0bc9` | 150 / 14,034 | `649e80b97a328fc39096d0a3ec129ec4cc8a5ddc20c0aca28c09295ba8bc0bc9` | 0 / 150 | **IDENTICAL** |
| G250 | 250,000 | 4461–4484 | 24 / 2,173 | `ec91ab55c5730dc11e9315a0bae456f64978aea86b2d8ff9cad2429dc60c7cb3` | 24 / 2,173 | `ec91ab55c5730dc11e9315a0bae456f64978aea86b2d8ff9cad2429dc60c7cb3` | 0 / 24 | **IDENTICAL** |

[FEN-sorted move lists](sol/job38/move-lists) · [Per-game comparisons](sol/job38/analysis.json) · [Independent readback](sol/job38/independent.json)

## Facts

The pinned UHO book had the requested ranges. I used `restart=on` and `nodes=true`, which this fastchess version accepts. `-noswap` kept X1 White because fastchess otherwise swaps even game IDs. X2 was Black even at roots where Black was to move. Each raw log contains both NNUE preflights. [Raw argv, PGNs and net receipts](sol/job38/raw) · [Fastchess color logic](https://github.com/Disservin/fastchess/blob/d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75/app/src/matchmaking/tournament/roundrobin/roundrobin.cpp#L79-L91)

The archived PGNs emitted a node field on 101,718 of 101,718 recorded plies across controls and measured runs. 0 emitted fields were zero. The comparison uses the recorded field at each ply. [Node-field and move tally](sol/job38/analysis.json)

## Suspicions

The default zero field can arise when no eligible search info is available. It gives no whole-search count. [Fastchess move-data assignment](https://github.com/Disservin/fastchess/blob/d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75/app/src/matchmaking/match/match.cpp#L275-L310)

## What this check cannot see

The PC's engine build (clang 23 for Windows, its profile), its trained nets (net768 is made up), its UHO book in
random order with the second game of each opening (colours reversed), engines kept across games as the PC's gate
keeps them (your job 35 covered one process playing many games), more than one thread.

## What I did not do

I reused the pinned binaries and synthetic net on the cloud. I made no engine source changes and ran no experiments on the owner’s PC.

## What I am not sure about

The paired evidence covers the selected roots and recorded PGN fields. Search output that fastchess chose not to serialize is outside that comparison.

## Reproduction

The scripts use python-chess 1.11.2. The primary parser associates each game with its sequential opening and compares UCI moves and the PGN node fields by FEN. An independent parser checks the archived bytes, rounds, move lists and node fields. [Runner](sol/job38/run_match38.py) · [Primary parser](sol/job38/analyze38.py) · [Independent parser](sol/job38/independent38.py) · [UTC stamps](sol/job38/stamps.txt) · [Precommit tree](sol/job38/precommit-readback.txt)
