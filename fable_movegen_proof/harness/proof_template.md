# PROOF: do the job-2 candidates behave exactly like the lock combo29?

Job "Fable 5.2, job 3", correctness only. Generated {{WRITTEN}} by `harness/report.py` from this template and from the receipts and ledgers of the runs; no number in this file was typed by hand. Times are Europe/Vienna. Terms are defined in `README.md`.

## Recap

**Finding.** {{FINDING_SENTENCE}}

**Verdicts.** {{VERDICT_SENTENCE}}

{{VERDICT_TABLE}}

**What a PASS means here.** A PASS rests on two kinds of evidence, as Couns decided before the work started (decision D1). On the exact release executables, every check their UCI interface allows was completed without a difference: the 13 pins, the perft divide, the legal moves and their order on the edge suite and on the fuzz corpus, the warm-state transcript and the Threads soak. On auxiliary probes, which are new test code compiled with each candidate's unmodified source, at least 20,000,000 positions per candidate were compared in every field, including the two fields the release executables do not print: the checkers bitboard and the static eval. **Checkers and static eval were therefore not observed on the release executables themselves.** The count of 20,000,000 is the auxiliary one (decision D2); the release-executable count is given beside it.

**Completed work.**

{{COMPLETED_LIST}}

**What remains, and what this does not show.**

{{REMAINS_LIST}}

Testing success does not authorise a lock change. Finite testing shows equivalence on the positions tested; it is not a proof for every position.

## 1. Identity of what was tested

Every executable was hashed before it was run, and the six MD5s supplied with the job all matched. Each source tree was compared file by file with the manifest of its build. BUN is BUNDLE3 from job 2's build `bn3_on` (source: the combo29 snapshot plus `BUNDLE3_after_combo29.patch`, md5 `ba2fcf2e78a0e2c85964a1e6e258d150`; built with job 2's lock recipe `tools\spd_build.ps1` and the three switches as `-D`; not rebuilt in this job). No commit holds the combo29 source and the lock executable cannot be rebuilt byte for byte, so BUN and the control LOCKEQ are **pin-equivalent, not byte-identical**: LOCKEQ is the same tree with the switches at 0 and differs from the lock executable in 89 bytes of its debug record only (job 2, `out\job3_prep\PIN_EQUIVALENCE.md`). QA's `build_v3\BUN` is another build (the five-flag bundle) and was not tested.

"ON" means: in the five QA builds the switch's default was changed from 0 to 1 in the source tree (`#define FORGE_SPD_... 1`); in BUN the three switches are passed as `-D...=1` to a tree whose defaults are 0. CHECKERS_KL is at mode 1 everywhere; mode 2 was never built or run. For each auxiliary probe the preprocessor was asked for the effective value of every candidate switch, and the table shows the answer. The net is the one compiled into every tree (`src/nnue_weights.inc`, sha256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`, 256 hidden units, a residual net that is added to the hand-crafted eval).

{{IDENTITY_TABLE}}

{{BINDING_SENTENCE}}

## 2. What the release executables expose

The lock's `uci.cpp` accepts `uci`, `isready`, `ucinewgame`, `setoption`, `position`, `go` (with `go perft N`), `bench`, `ponderhit`, `stop` and `quit`. The commands `d`, `eval`, `checkers`, `moves`, `legalmoves` and `help` were sent to the lock executable and produced no output (`evidence/observe/`). `go perft N` walks `board.legal_moves()` and prints one line per move, so it shows the legal moves in generation order. Nothing prints the checkers bitboard or the static eval, and `has_legal_move` (the function WITNESS_NOPIN changes) and the pawn-cache eval (KING_PAWN_CACHE) run only inside search.

The auxiliary probe reads those fields through the engine's public interface and its existing test hook (`friend struct SearcherTestProbe`). A probe is tied to its release executable in two ways: for the lock, every `go perft` block of the release executable had to equal the probe's legal list at every position of the release-executable fuzz (column "tied" in section 7); and for every tag the same was checked on 2,000 positions (section 8).

## 3. Harness self-test

{{SELFTEST_LINE}}

The self-test never touches an engine binary or engine source. Its positive controls run the lock against a verified byte-for-byte copy of itself, and the lock probe against the lock-equivalent probe (another binary that must behave the same). Its negative controls take a real output of the lock and change one thing in memory: a legal move removed, a move added, two moves swapped, a checkers bit, the eval with the net on, the eval with the net off, `has_legal_move`, each of the 37 fields of a record in turn, a wrong position, two different inputs, a missing record, a cut transcript, garbage, a transcript from the wrong probe, a probe from another harness source, and for the release executables a removed move line, swapped lines, a changed count, a missing block, a malformed line, a refused FEN, a cut output, an engine that never answers. Each must be refused with the field named. Five more controls (L1 to L5) test the report generator and the replay tool: a chunk that was run twice counts once, a row that names other binaries than the frozen ones counts nothing, there is no PASS below 20,000,000 or with an open gate or a difference, only a line `SELFTEST PASS n/n` is a passed self-test, and a replay reproduces a ledger row only if every hash is the row's. The controls were watched failing first, against comparators that always answer "equal" (red runs 1 and 2), against the code before the review fixes (red run 3), and against a counter that counts every row and a verdict that ignores the gates (red run 4).

The full runs and the red runs of the self-test are kept as logs, including the runs made while the harness was being written. The name of a log says what the run was meant to show, not how it ended:

{{SELFTEST_RUNS}}

`GREEN1` was the first run against the real comparators of harness 1. It failed in two release-executable controls because their fixtures were wrong: the changed block's counts no longer added up, so it was refused as malformed before the intended difference was looked at. The fixtures were corrected and the inconsistent block was kept as a control of its own; `GREEN2` is the pass of harness 1. `GREEN3` and `GREEN4` were runs of harness 2 that still failed: in `GREEN3` a missing block and an early end of the output were reported as a move-list difference, a defect of the comparator that had just been changed to compare from the start (missing output is not a difference; corrected); in `GREEN4` one diagnostic did not yet name the missing output. `GREEN5` is the first pass of harness 2, made before every counted run. `RED4a` and `RED4` are the red runs of the report controls alone (four of them at first, then five); they start no engine. The last log in the table is the run that counts for the verdicts: a full run made after the last change to the report generator.

The reviews are recorded in `REVIEW_LOG.md`. The first one, by a read-only reviewer on another model at 19:41, found no way for a real difference to come out as equal, but it found gaps (how a probe build is bound to its switches, answers that were computed and thrown away, unlabelled transcripts, three controls that could not fail). All were fixed, the probes were rebuilt as harness 2, and every counted run was started again. The runs made before that are kept as an earlier run and are not added to any count (section 7). The second review, of the runners and the report generator, was started the same way at 20:09 and stopped at 20:34 on the owner's instruction to use no subagents, before it had reported anything. **It was then done by the author of the code, which is weaker than an independent review.** It changed the report generator (every gate is now tied to the frozen binaries, the self-test result is read from the newest log, the tie between probe and executable is a gate) and corrected descriptions in this file; it changed none of the six files that produced the counted fuzz rows.

## 4. Pins

Settings as recorded for the lock: Threads 1, Hash 16, OwnBook false, UseNNUE true or false; one process for the five net-on depths, one for the five net-off depths, one for the three perft pins. The lock was run first and reproduced all 13.

{{PINS_TABLE}}

## 5. Perft divide

Every root move's count was compared with the lock's, not only the total. The lock's totals equal the published values wherever one exists.

{{DIVIDE_TABLE}}

## 6. Edge suite, warm states, Threads

**Edge suite.** {{EDGE_SENTENCE}} Every entry has a category, a provenance and a predicate that an independent rules oracle checked (own Python code that shares nothing with the engine; validated on published perft counts and on deliberately wrong labels). The suite is `suite/edge_suite.tsv`. For every legal entry and for every position reached from it by one made move, all fields were compared on the probes; on the release executables the entry was asked `go perft 1` and `go perft 2`, and every position after one move `go perft 1`. The lock's move set (probe and executable) and its checkers (probe) were also compared with the oracle's. Entries that `set_fen` rejects, and entries it accepts although no legal game reaches them, are kept apart: they are robustness evidence, not legal-position evidence. For the rejected ones the engine's refusal text and the unchanged board were compared; the unreachable ones ran one process each.

{{EDGE_CATEGORIES}}

{{EDGE_TABLE}}

**Warm states.** One process per executable, Threads 1, in this order: twelve positions searched to depth 16 twice in a row (cold, then warm tables); four of them to depth 17 after `ucinewgame`; six with Hash 1 and six with Hash 64, without `ucinewgame`; twelve searches with the net off and four with it on again; four searches after `Clear Hash`, each followed by a perft 3; then a 40-ply game line searched to depth 12 at every ply with the tables kept; at the end `bench 13` must still be the pin. That is 101 searches. Every info line (depth, selective depth, score, nodes, hash fill, principal variation; without time and speed) and every bestmove must equal the lock's.

**Threads.** Six blocks per executable with Threads 2, 3, 4, 3, 2 and 4 and 16 MiB of hash per thread; each block has twelve searches of one million nodes and one `go infinite` ended by `stop`, and is followed by `ucinewgame` and `Clear Hash`: 78 searches. Checked are the exit code, a bestmove for every search, its legality, and the bench-13 pin afterwards at Threads 1. This shows stability only. **Multithreaded search is not deterministic, so these runs do not establish node identity.**

{{RELEASE_TABLE}}

## 7. Differential fuzz

**Corpus.** Random and semi-random legal playouts, generated by the lock probe. Seeds: the start position, the eight positions of the engine's `bench`, the 12,000 positions of `fens_12k_v2.txt` (md5 `e7dbf2c8151188c03ef52054557a531e`), and edge positions. Per playout the seed class is drawn 70 % fens12k, 20 % edge, 5 % bench, 5 % start position; half the playouts choose uniformly among the legal moves, half weight en passant 16, captures 4, promotions 8, castling 8, double pushes 2, king moves 2 and checks 6 (multiplied); the length is 8 to 80 plies, 20 to 160 from the start position and the bench seeds, or until there is no legal move. Master seed `4D47465A20261110`; the chunk seed is the master seed xor (chunk + 1) x `9E3779B97F4A7C15`, through SplitMix64 into xoshiro256**. A chunk is 100,000 visited positions. Chunks 0 to 99 use the seed file `v1` (33 edge positions known before the suite existed), chunks 100 to 199 use `v2` (all legal suite entries); both files are identified by sha256 in every ledger row (`evidence/corpus/`). Nothing of the corpus is stored: a chunk is regenerated from its definition, and the ledgers keep its sha256.

**What one comparison is.** On the auxiliary tier one position comparison is one record: the generated lists All, Captures and Quiets in order, `is_legal` and `gives_check` for every generated move in three king-line states, the legal lists, the checkers on four routes, the checkers after every legal move, `has_legal_move` twice, eight eval values (net off, net on by refresh and incrementally, raw net, uncached, and re-evaluations of the positions one and eight plies back), and the null-move child. The lock's transcript and the candidate's must be byte-identical after their identity frames. On the release executables one comparison is one `go perft 2` block reached by `position fen <parent> moves <move>`: the legal moves in order and the number of legal replies to each (one process per executable and chunk, options Threads 1, Hash 16, OwnBook false; perft does not use the net).

A chunk counts only with status OK, and one candidate and chunk counts once however often it is run. Excluded or failed comparisons are the rows in the "not OK" columns.

{{FUZZ_TABLE}}

{{CORPUS_SENTENCES}}

**Stale caches.** Inside every chunk the worker's pawn cache stays warm across playouts and is cleared at recorded points; every record also re-evaluates the positions one and eight plies back, which then meet cache entries written for later positions (often the same pawns with a king on another square). In addition, some chunks were replayed with two other cache histories:

{{VARIANTS_TABLE}}

**Earlier run.** Before the first review the same corpus had been run with harness 1, which recorded fewer fields. It found no difference either. It is listed for completeness and is not added to the counts above.

{{H1_TABLE}}

## 8. Supplementary evidence

**Do the inputs execute the changed lines?** The job forbids mutated engines, so sensitivity was shown another way: each candidate tree was also built with the compiler's source-based coverage (unchanged source, extra compiler flags), and the count of every instrumented line inside the candidate's `#if` region was read.

{{COVERAGE_TABLE}}

**WITNESS_NOPIN.** `has_legal_move` answers true almost everywhere, so random play says little about its shortcut. Its answer can only become wrong in a stalemate whose pawn pushes all belong to pinned pawns. Such positions were constructed for the king and pawn pairs on a common rank or diagonal, in both colours, and confirmed by the oracle. They are statically valid; whether a legal game reaches each one is not established, so they are reported here and not counted as fuzz or legal edge coverage.

{{WNP_TABLE}}

**Search output of the release executables.** The code of WITNESS_NOPIN and KING_PAWN_CACHE runs inside a release executable only during search. Search output does not stand in for move order, checkers or static eval; it is listed as supplementary evidence that those executables search identically.

{{SEARCHSIG_TABLE}}

**Probe against its own release executable.**

{{CROSSTIER_TABLE}}

## 9. Differences found

{{FIRST_MISMATCH}}

{{FAIL_FOLDERS}}

## 10. Limits

- **Finite testing.** Equivalence is shown on the positions tested, not for every position.
- **Two artifacts.** Checkers, `has_legal_move`, `is_legal`, `gives_check` and static eval were compared on auxiliary probes: the same source files, but compiled at `-O3` without link-time and profile-guided optimisation and with another `main`. A defect that only the release build's code generation introduces would have to show in what the release executables print: pins, perft divide, move lists and reply counts, warm transcripts, search signatures.
- **No planted faults.** Job 3 did not build mutated engines. That the comparator can fail is shown by the self-test's corrupted fixtures; that the inputs reach the patches is shown by line coverage. Job 2 ran mutants against its own harness.
- **WITNESS_NOPIN.** The positions that decide its answer are rare in play (see section 8) and the targeted set is constructed. Inside the release executable its code runs only during search, where a wrong answer at a stalemate node would most likely not change the printed output.
- **Threads.** The soak shows no crash, hang or illegal move; it does not show node identity.
- **The corpus** is what random and weighted playouts from the given seeds reach. The counts of distinct positions, checks, mates and special moves are in section 7.
- **The oracle** was validated on published perft counts to depth 3 or 4 and on wrong labels. It vouches for labels, move sets and checkers of the edge entries and the targets, not for move order.
- **The incremental accumulator path** was exercised one ply at a time inside windows of 64 plies; the multi-ply walk-back of the search was not, and no candidate changes that code.
- **Review.** A second model reviewed only the first version of the probe, the comparators and the UCI driver. The changes that made harness 2, the runners (`fuzz.py`, `checks_release.py`, `edge.py`), the oracle, the coverage and target tools and the report generator were reviewed by their author only (`REVIEW_LOG.md`). What stands in for that review is the self-test, whose controls ran against the final code.
- **Timing** was not measured and nothing here is a statement about speed.

## 11. Replay

Every ledger row can be replayed from its chunk number: `README.md` gives the commands. The probes report their identity (`mgprobe id`), and every transcript begins with it. After the counted runs some of their rows were run again from their definition (seeds file, master seed, chunk number), and every hash of the new run was compared with the row: the input, both outputs and both binaries.

{{REPLAY_TABLE}}

## 12. Evidence

`evidence/TABLES.md` holds all generated tables, `evidence/VERDICTS.json` the gates per candidate. Receipts: `evidence/freeze`, `probes`, `pins`, `divide`, `warm`, `soak`, `edge`, `crosstier`, `search_sig`, `coverage`, `wnp_targets`, `replay`; ledgers: `evidence/fuzz_aux`, `fuzz_uci`, `fuzz_warm`, and `h1_earlier_run`; logs: `evidence/logs`, `evidence/selftest`. `MANIFEST.tsv` lists every file of the pack and every artifact that stays on the PC under `D:\forge_jobs_20261109\fable2\out\job3`, with MD5 and SHA256.
