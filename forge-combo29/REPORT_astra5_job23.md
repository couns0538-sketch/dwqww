# Astra5 Job 23 — does Forge search the same way from a FEN?

## 1. Step 0 passed on both builds

The r15d and kF executables reproduced their Job 16 and Job 22 SHA-256 hashes. This Intel host reported `nproc 5`. GCC 14.2 with `-march=znver4` reproduced the executables originally built with `-march=native` on AMD. The two 29-file source manifests and the synthetic net768 checksum also matched. [Build identities](astra5/job23/build.txt) · [Build instructions and checksums](astra5/job23/provenance/job23-build-provenance.txt)

Each build passed five checks in five fresh processes. With default settings, benches 11 and 13 returned 312,866 and 862,329 nodes and perft 5 returned 4,865,609. With PC20, net768, Threads 1 and Hash 16, the benches returned 882,074 and 4,275,906. Every net-enabled run logged the load checksum `30ab43b4ba5db5f3` and `NNUE v3 active`. [r15d transcripts](astra5/job23/step0/r15d) · [kF transcripts](astra5/job23/step0/kF) · [Job 22 readback](astra5/job23/step0/job22-comparison.txt)

## 2. K23 and C23 passed

Two separate r15d processes used the start-FEN driver to replay games 700001–700010. Each produced 1,183 records, zero NA fields and 4,863,663 summed nodes. Both files had SHA-256 `b85eb5f01afbbb12771b1a8cf5c579f3c6db3873fa0779f9fce94ca0c5b25a76` and `cmp` exited 0. [Repeated runs](astra5/job23/K23-cmp.txt)

Changing only `LmrQuietBase` from 93 to 60 gave 1,193 records, zero NA fields and 5,100,705 summed nodes. All ten games had at least one different record. The first discrepancy came at the first searched ply, where both runs chose the same move. [C23 byte comparison](astra5/job23/C23-cmp.txt) · [Per-game control audit](astra5/job23/audit/C23-change.txt)

```text
K23  700001 8 g4f5 3823
C23  700001 8 g4f5 2293
```

## 3. Prediction graded

The three categorical forecasts all held. S1 was IDENTICAL, S1 MATCHES R and B1 was IDENTICAL. The forecast put the B1 versus R difference in 0–50 of the 2,000 games. One game differed, inside the range. The prediction was committed alone and pushed before the first measured search. [Frozen prediction](https://github.com/couns0538-sketch/dwqww/commit/bea49f8316aea089b0bb91bbc051d76f539bd0f6) · [Run chronology](astra5/job23/audit/start.txt)

## 4. Whole-game record streams

All four measured runs completed games 700001–702000 before the cutoff. The checksum covers each complete move-and-node record file, including its final newline. The reading in each measured row compares the two builds running the same driver. [Comparison and game counts](astra5/job23/audit/results.txt) · [S1 completion](astra5/job23/audit/S1-boundary.txt) · [B1 completion](astra5/job23/audit/B1-boundary.txt)

| Run | Build | Driver | Games | Records | NA | Node sum | SHA-256 | Reading |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| [K23-1](astra5/job23/K23-1/records-manifest.tsv) | r15d | S | 10 | 1,183 | 0 | 4,863,663 | `b85eb5f01afbbb12771b1a8cf5c579f3c6db3873fa0779f9fce94ca0c5b25a76` | cmp 0, repeat |
| [K23-2](astra5/job23/K23-2/records-manifest.tsv) | r15d | S | 10 | 1,183 | 0 | 4,863,663 | `b85eb5f01afbbb12771b1a8cf5c579f3c6db3873fa0779f9fce94ca0c5b25a76` | cmp 0, repeat |
| [C23](astra5/job23/C23/records-manifest.tsv) | r15d | S | 10 | 1,193 | 0 | 5,100,705 | `a5b3745a1a0f1e5c7e65754b17777f34c6ec2d4f02aa2d4969c85489f56280dc` | cmp 1, changed |
| [S1-r15d](astra5/job23/S1-r15d/records-manifest.tsv) | r15d | S | 2,000 | 232,013 | 0 | 960,586,052 | `846c0fbcf195f4e609cf62ea1493f524e2ff67d62cfcd9c156cd389b91a93f75` | IDENTICAL |
| [S1-kF](astra5/job23/S1-kF/records-manifest.tsv) | kF | S | 2,000 | 232,013 | 0 | 960,586,052 | `846c0fbcf195f4e609cf62ea1493f524e2ff67d62cfcd9c156cd389b91a93f75` | IDENTICAL |
| [B1-r15d](astra5/job23/B1-r15d/records-manifest.tsv) | r15d | B | 2,000 | 232,013 | 0 | 960,586,083 | `6f13e8f98e9ffc87c0e116a321abe6077571ac7a23a5a8b3cce5592dceb6cad2` | IDENTICAL |
| [B1-kF](astra5/job23/B1-kF/records-manifest.tsv) | kF | B | 2,000 | 232,013 | 0 | 960,586,083 | `6f13e8f98e9ffc87c0e116a321abe6077571ac7a23a5a8b3cce5592dceb6cad2` | IDENTICAL |

## 5. Against Job 22 driver R

**S1 MATCHES R.** The r15d start-FEN file matched the exact prefix of the Job 22 r15d startpos file across all 2,000 games and 232,013 search records. Sending the literal starting FEN and the full move history reproduced the earlier result. [Reference prefix and full-stream hashes](astra5/job23/provenance/verified-reference.txt) · [Byte comparisons](astra5/job23/audit/results.txt)

**B1 versus R differed in 1 of 2,000 games.** Every recorded best move agreed. Only two node fields changed, both in game 701704, for a total increase of 31 nodes. The first differing record was at absolute ply 9. [Game-level readback and legal repetition example](astra5/job23/audit/701704-audit.txt)

```text
R   701704 9 g8f6 4661
B1  701704 9 g8f6 4677

R   701704 10 e3e5 7899
B1  701704 10 e3e5 7914
```

## 6. Declared readings

**S1 IDENTICAL · S1 MATCHES R · B1 IDENTICAL · KEEPS**

B1 versus R is descriptive under the declared rule. [S1 direct comparison](astra5/job23/audit/S1-byte-comparison.txt) · [B1 direct comparison](astra5/job23/audit/B1-byte-comparison.txt)

## Facts

Every search used PC20 + synthetic net768, Threads 1, Hash 16 and `go softnodes 2000`. Each arm kept one engine process for both colors from its first game through its last. The driver sent `ucinewgame` and waited for `readyok` before every game. Game IDs seeded python-chess's random opening moves. The two already-terminal openings, 700591 and 701791, counted as games and contributed zero search records. Counts come from game-completion receipts. [Driver](astra5/job23/driver/selfplay.py) · [Terminal-opening fixtures](astra5/job23/driver/fixture-check.txt) · [Process and protocol audit](astra5/job23/audit/recipe-audit.txt)

A record holds the game ID, zero-based absolute ply, best move and node count from the last UCI info line before `bestmove`. Driver S sent the standard starting FEN and every move. Driver B sent python-chess's FEN after the random opening and only the moves played since that FEN. Both drivers adjudicated from the original board with its full game history. [Search and FEN command construction](astra5/job23/driver/selfplay.py) · [Job 22 reference verification](astra5/job23/provenance/verified-reference.txt)

## Suspicions

The omitted repetition history is a plausible explanation for the two changed node counts. Forge reads the halfmove clock from the book FEN and starts its list of position keys with a single entry. An offline replay of the Job 22 games found 1,849 search roots whose reversible history reached before the book FEN. At just two roots, both in game 701704, clipping that history removed one of two matching positions from before the current search root. The full history contained the same position at plies 4 and 8. The book history retained only ply 8. Both eligible roots coincided with the measured node differences. After the played moves `d2e3 g8f6`, the legal continuation `e3d2 f6g8` would produce a third occurrence with full history and a second with book-FEN history. [Screen method and source lines](astra5/job23/audit/repetition-screen-method.txt) · [Counts and matching positions](astra5/job23/audit/repetition-screen-result.txt) · [Game 701704 records](astra5/job23/audit/701704-audit.txt)

## What I did not do

WHAT THIS CANNOT SEE: the PC's own build (clang 23 for Windows, its profile), its trained net, its book FENs (yours come from 8 random plies), 16 processes at once, a whole round (about 7,800 games a worker), the random plies the PC's self-play also plays inside a game, other node limits.

## What I am not sure about

The UCI records show where the reported node counts diverged. Confirming the internal cause would require the unplayed search continuations and their repetition or cutoff decisions. Search-tree identity inside matching rows and playing strength remain unmeasured. [Raw search output](astra5/job23/B1-r15d/raw-last-manifest.tsv)

## Pre-commit working tree and evidence files

```text
$ git status --short && ls -R forge-combo29/astra5/job23
 A forge-combo29/REPORT_astra5_job23.md
M  forge-combo29/astra5/job23/stamps.txt
forge-combo29/astra5/job23:
B1-kF
B1-r15d
C23
C23-cmp.txt
C23-controller.txt
K23-1
K23-1-controller.txt
K23-2
K23-2-controller.txt
K23-cmp.txt
S1-kF
S1-r15d
audit
build.txt
driver
prediction.txt
provenance
stamps.txt
step0

forge-combo29/astra5/job23/B1-kF:
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job23/B1-r15d:
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job23/C23:
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job23/K23-1:
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job23/K23-2:
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job23/S1-kF:
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job23/S1-r15d:
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job23/audit:
701704-audit.txt
B1-barriers.tsv
B1-boundary.txt
B1-byte-comparison.txt
B1-controller.txt
B1-final.txt
C23-change.txt
K23-repeat.txt
S1-barriers.tsv
S1-boundary.txt
S1-byte-comparison.txt
S1-controller.txt
S1-final.txt
audit_game_records.py
compare23.py
control-raw-verification.tsv
final-readback.txt
measured-raw-verification.tsv
recipe-audit.txt
repetition-screen-method.txt
repetition-screen-result.txt
repetition_screen.py
results.txt
start.txt
verify_raw23.py

forge-combo29/astra5/job23/driver:
archive23.py
derivation.txt
fixture-check.txt
fixtures.py
selfplay.py
stage.py

forge-combo29/astra5/job23/provenance:
job23-build-provenance.txt
kF-input.sha256.txt
kF-znver4-log.txt
net-generation.txt
r15d-input.sha256.txt
r15d-znver4-log.txt
source-build.txt
verified-reference.txt

forge-combo29/astra5/job23/step0:
build.txt
compare_pins.py
controls.py
job22-comparison.txt
kF
net-generation.txt
pc20.txt
r15d

forge-combo29/astra5/job23/step0/kF:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt

forge-combo29/astra5/job23/step0/r15d:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
```
