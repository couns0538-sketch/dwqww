# fable_movegen_proof: do the job-2 speed candidates behave exactly like the lock?

Job "Fable 5.2, job 3", 2026-11-10, branch `fable52-movegen-proof-20261110` (started from the job-2 tip `08897a88`). Times are Europe/Vienna.

**Read first:** `PROOF.md` (conclusions, verdict per candidate, limits), then `STATUS.md` (state, rulings, resume commands), `REVIEW_LOG.md` (what the reviews found and what was done about it), `evidence/TABLES.md` (every number, generated from the receipts).

## What this pack is

A test harness and its evidence. It compares six candidates with the lock `combo29` for correctness only: the same legal moves in the same generation order, the same checkers bitboard, the same static evaluation with the net on and off. It tests neither speed nor playing strength, and it changes no engine source, no lock and no file of another job.

Terms used here:

- **Lock**: the engine build everything is compared with, `combo29`, exe MD5 `c0051c99695f48bf93272d96fe7548c3`.
- **Candidate**: one of EVL (EVADE_LEGAL), PCM (PAWN_CAPMASK v2), CKL (CHECKERS_KL v3, mode 1), WNP (WITNESS_NOPIN), KPC (KING_PAWN_CACHE v2), BUN (BUNDLE3 = EVL + PCM + CKL). QA's folder `build_v3\BUN` is a different build (the five-flag bundle) and is not tested here.
- **Release executable**: the PGO/LTO build that would be used in play. It speaks UCI only.
- **Auxiliary probe**: `mgprobe.exe`, new test code compiled together with the six unmodified engine source files of one tree. It is a separate artifact: same source, other code generation (no LTO, no PGO). It exists because the release executables print the legal moves (`go perft`) but neither the checkers bitboard nor the static eval.
- **Tier R** and **tier A**: checks on the release executables and on the auxiliary probes.
- **Pin**: a number the lock is known to produce (bench node counts, perft totals).
- **Perft divide**: the number of positions below each legal move of a position, to a fixed depth.
- **Chunk**: 100,000 positions of the fuzz corpus, defined by a seeds file, a master seed and a chunk number.

## Folder map

| Path | Content |
|---|---|
| `PROOF.md`, `STATUS.md`, `README.md`, `REVIEW_LOG.md` | reports |
| `MANIFEST.tsv`, `DONE.md` | MD5 and SHA256 of every file of the pack, inventory of what stays on the PC |
| `harness/mgprobe.cpp` | the auxiliary probe (subcommands `id`, `gen`, `run`, `uciscript`, `keys`) |
| `harness/mg_format.py`, `mg_compare.py` | transcript codec and comparator |
| `harness/uci_session.py`, `pinguard3.py` | pinned UCI driver, batch runner, perft-output comparator, tie check; affinity and priority guard |
| `harness/selftest.py`, `stub_engine.py` | positive and negative controls of the harness |
| `harness/checks_release.py` | pins, perft divide, warm transcript, Threads soak |
| `harness/chess_oracle.py`, `edge_bases.py`, `edge.py` | independent rules oracle, hand-made edge positions, edge-suite builder and runner |
| `harness/fuzz.py` | corpus, both fuzz tiers, ledgers, cache-state variants, search signatures, counts |
| `harness/replay.py` | runs a counted ledger row again and compares every hash with the row |
| `harness/coverage.py` | which lines of each patch the test inputs execute |
| `harness/wnp_targets.py` | constructed positions that are decisive for WITNESS_NOPIN |
| `harness/report.py` | copies the compact evidence into `evidence/` and derives the tables and verdicts |
| `scripts/` | `job3_env.ps1`, `pin_run.ps1` (pinned launcher with disk guard), `freeze_inputs.ps1`, `build_aux.ps1`, `make_manifest.ps1` |
| `suite/edge_suite.tsv`, `edge_expected.tsv`, `wnp_targets.tsv` | the edge suite with class, category, predicate and provenance per entry; the oracle's expectations; the WITNESS_NOPIN targets |
| `evidence/` | receipts, ledgers, logs and generated tables copied from the job folder |

On the PC only (they contain engine binaries, engine source copies and a FEN dataset): `D:\forge_jobs_20261109\fable2\out\job3\` with `bin` (verified copies of the executables), `src` (verified copies of the source trees), `aux2` (probes of harness 2 with receipts), `aux` (probes of harness 1), `runs` (all receipts and ledgers; `runs\h1` is the earlier run with harness 1), `logs`, `corpus` (seed files), `fail` (failure evidence; empty if nothing ever differed). `MANIFEST.tsv` lists these files with their hashes.

## What was compared, and where

| Field | Release executable (tier R) | Auxiliary probe (tier A) |
|---|---|---|
| Legal moves, membership and order | yes: `go perft 1`, and `go perft 2` adds the number of replies per move | yes: `legal_moves()`, the three generated lists (All, Captures, Quiets), `legal_moves(true)` |
| `is_legal`, `gives_check` per generated move | no | yes, in three king-line states (first query, after other queries, after make and unmake) |
| Checkers bitboard | **not observable** | yes: after `set_fen`, after `make_move` with and without king lines, after every legal move, at the null-move child |
| `has_legal_move` | not observable (runs only inside search) | yes, before and after king lines exist |
| Static eval, net on and off | **not observable** | yes: net off, net on by refresh and incrementally, raw net term, uncached hand-crafted eval, re-evaluation of earlier positions with a warm cache |
| Search output | yes: pins, warm transcript, search signatures (supplementary) | no |

A lock-exe perft block must equal the lock probe's legal list at every fuzz position (the "tie"), which shows that each position was really reached by the executable and that probe and executable list the same moves in the same order.

## Status words

- `EQUAL` / `MATCH` / `OK`: compared and identical.
- `MISMATCH` / `DIFFERENCE`: a well-formed candidate output differs. Only a reproduced and isolated difference on a legal position is a FAIL.
- `MALFORMED`, `HARNESS_ERROR`, `TIMEOUT`: the run cannot be judged (missing or damaged output, unusable reference, wrong inputs, time limit). Never a candidate verdict; such a chunk is not counted.
- `CRASH`: a candidate process ended with an error code; treated as a difference to confirm.

## How to re-run

Start from a shell that is itself pinned to cores 3-6 at Idle priority (the launcher pins itself as its first act and its children inherit that; a launcher started from an unpinned shell runs its first milliseconds on the caller's cores).

```powershell
. D:\forge_jobs_20261109\fable2\repo\fable_movegen_proof\scripts\job3_env.ps1
[void](J3-Pin 0x78)
$H = "$J3_PACK\harness"; $L = "$J3_PACK\scripts\pin_run.ps1"
function Py($a) { powershell.exe -NoProfile -ExecutionPolicy Bypass -File $L -Exe $J3_PY -ArgLine "-I -B $a" }

powershell.exe -NoProfile -ExecutionPolicy Bypass -File $J3_PACK\scripts\freeze_inputs.ps1    # verify every input by hash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $J3_PACK\scripts\build_aux.ps1 -Tag EVL   # refuses an existing folder
Py "$H\selftest.py"                                   # harness controls, about one minute ("selftest.py ledger": the report controls alone)
Py "$H\checks_release.py pins EVL --redo"             # 13 pins of one executable (also: divide, warm, soak; then: summary)
Py "$H\chess_oracle.py"                               # the oracle against published perft counts
Py "$H\edge.py build"                                 # rebuild and re-validate the edge suite
Py "$H\edge.py run EVL"                               # the suite, one tag against the lock, both tiers
Py "$H\fuzz.py aux v1 0-0 --cands EVL"                # one chunk of the auxiliary tier for one candidate
Py "$H\fuzz.py uci v1 0-0 --cands EVL"                # the same chunk on the release executables
Py "$H\fuzz.py count"                                 # totals from the ledgers
Py "$H\coverage.py EVL"                               # which changed lines the inputs execute (needs build_aux.ps1 -Tag EVL -Coverage)
Py "$H\wnp_targets.py run WNP"                        # the constructed WITNESS_NOPIN targets
Py "$H\report.py"                                     # evidence folder, tables, verdicts
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $J3_PACK\scripts\make_manifest.ps1 -Verify
```

A chunk that already has an `OK` row for a candidate is skipped, so a fuzz command can be repeated or continued without counting anything twice.

To replay a counted ledger row and compare every hash of the new run with the row (the ledgers are not changed; a receipt goes to `out\job3\runs\replay`):

```powershell
Py "$H\replay.py aux v1 7 EVL"            # tier A, chunk 7 (chunks 0-99 use seeds v1, 100-199 use v2), candidate EVL
Py "$H\replay.py uci v2 150 EVL,BUN"      # tier R, chunk 150, two candidates
```

The same by hand, step by step (redirections go through `cmd`, because PowerShell 5.1 would re-encode the files):

```powershell
$P = "$J3_OUT\aux2"; $T = "$J3_OUT\tmp"
cmd /c "$P\LOCK\mgprobe.exe gen --seeds $J3_OUT\corpus\seeds_v1.txt --master 4D47465A20261110 --chunk 7 --positions 100000 > $T\path.txt"
cmd /c "$P\LOCK\mgprobe.exe run < $T\path.txt > $T\lock.bin"
cmd /c "$P\EVL\mgprobe.exe run < $T\path.txt > $T\evl.bin"
Py "$H\mg_compare.py $T\lock.bin $T\evl.bin --path $T\path.txt --tag EVL"      # exit 0 = EQUAL
Py "$H\mg_format.py $T\lock.bin 1 3"                                           # readable dump of three records
```

A cache-state variant (ledger `fuzz_warm`) is the same chunk with its cache-clear marks changed, so it is reproduced by running the whole chunk in order: `Py "$H\fuzz.py warmseq v1 0-0 --cands KPC"` appends new rows for chunk 0 in both variants. The state depends on the sequence of positions, not on one FEN.

## Rules this pack keeps

Every process runs on cores 3-6 (mask `0x78`) at Idle priority and is read back before it gets work; at most three engines at once; nothing starts when D: has less than 30.3 GiB free; all output goes under `out\job3`; git runs only in the repo with `GIT_NO_LAZY_FETCH=1`; hashes come from `System.Security.Cryptography` or `hashlib`; no GPL code, table or constant is used (the random generator is SplitMix64 and xoshiro256**, written from their public-domain descriptions; the rules oracle is own code).

## What this job did not do

No engine source, lock, gate, queue, net or dataset was touched. No game, match, SPRT or tuning run was started. No process of another job was stopped. CHECKERS_KL was tested at mode 1 only. A PASS in `PROOF.md` does not authorise a lock change.
