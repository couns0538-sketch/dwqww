#pragma once

#include <atomic>
#include <cstdint>
#include <string>

// Runtime search options set over UCI (src/uci.cpp). Every option defaults to
// OFF; with all options OFF the search is the AL1 s198 search. Options are
// written only while no search runs (the UCI loop stops the search first).
namespace forge::options {

// UCI SmpExactNodes (check, default false); acts only with Threads > 1.
// Resets every worker's published node count before the helper threads start
// (otherwise the main thread reads the previous search's counts until each
// helper has started: `go nodes N` can stop at once and the first info lines
// over-report nodes/nps), and reports the exact total after the helpers stop.
extern bool smp_exact_nodes;

// UCI SmpBestThread (check, default false); acts only with Threads > 1.
// Reports the best move, ponder move, PV and score of the worker with the
// deepest completed iteration (ties: higher score) instead of always thread 0.
extern bool smp_best_thread;

// UCI SmpProtectProvenScore (check, default false): while tablebases are
// loaded, rank winning TB scores by score rather than helper depth. Acts only
// with SmpBestThread. Set while the UCI loop has stopped and joined search.
extern bool smp_protect_proven_score;

// UCI LocklessTT (check, default false). The transposition table is probed and
// written without its striped locks: each entry is two 64-bit atomic words and
// the first carries the key tag mixed with a hash of all data bits, so a read
// that combines two writes fails the key check and counts as a miss
// (src/search/tt_lockless.inc). Read once per search by Searcher::search;
// changing it clears the table. Same table contents and rules as the locked
// table, so a search with Threads=1 is unchanged.
extern bool lockless_tt;

// UCI SmpHelpersPastDepth (check, default false; R3-6); acts only with Threads > 1
// and a `go depth N` limit. Without it a helper thread returns as soon as it has
// completed iteration N, and its core sits idle until the main thread completes
// N too. With it a helper keeps deepening (up to depth 64) until the main thread
// raises the stop flag; the iterations past N only fill the shared table, and the
// helper still returns its result of iteration N (src/search/iterative.inc), so
// SmpBestThread chooses among the same depths as before. Searches without a
// depth limit (clocked, infinite, node: helpers already run to depth 64 there)
// and `go mate` searches are unchanged.
extern bool smp_helpers_past_depth;
// Syzygy tablebases (job C1). The master switch is UCI SyzygyPath (string,
// default empty = no tables, forge/syzygy.hpp); the two options below only act
// while tables are loaded.
// UCI SyzygyProbeDepth (spin 1-10, default 1): positions with as many pieces
// as the largest loaded tables are probed inside the search only at this
// remaining depth or more (fewer pieces: at every depth).
extern int syzygy_probe_depth;
// UCI Syzygy50MoveRule (check, default true): cursed wins and blessed losses
// (decided only beyond the 50-move rule) count as draws.
extern bool syzygy_50_move_rule;

// UCI CorrHistPlus (spin 0-7, default 0): extra correction-history keys, a
// bitmask of forge::corrplus::{Continuation = 1, MinorPiece = 2, NonPawn = 4}
// (forge/correction_plus.hpp). 0 keeps the AL1 s198 pawn + material
// correction only; each bit is meant to be gated on its own. One byte so that
// the default-path test in the hot corrected_eval is a single compare with
// memory that needs no register.
extern std::uint8_t corr_hist_plus;

// UCI HardDeadline (spin 0-1000 ms, default 0 = off). When N > 0, every search
// with a clock or movetime gets a watchdog thread that sleeps until the hard
// time limit + N ms (ponder searches: counted from ponderhit). If the search has
// not answered by then, the watchdog stops it and sends `bestmove` with the best
// move of the last completed iteration (published by the main worker), so a
// starved or delayed search thread cannot make the engine miss its deadline.
extern int hard_deadline_ms;

// HardDeadline runtime slot: best move (low 32 bits) and ponder move (high 32
// bits) of the main worker's last completed iteration, packed so the pair is
// consistent (forge::pack_move). Process-wide and constant-initialised (no
// constructor code): one UCI search runs at a time; the UCI thread resets it to
// 0 before each clocked search, the main worker writes it, the watchdog reads it.
extern std::atomic<std::uint64_t> published_moves;

// UCI NNUEKingBuckets (spin 0-32, default 0) together with UCI NNUEFile
// (string): evaluate with a v2 network (king-bucketed input layer, see
// forge/nnue.hpp nnue::v2) loaded from NNUEFile. N > 0 selects the loaded net
// when it has exactly N king buckets.
extern int nnue_king_buckets;

// UCI NNUEOutputBuckets (spin 0-16, default 0) together with NNUEFile (C5):
// N > 0 selects the loaded v2 net when it has exactly N output buckets (output
// row chosen by the piece count). The two counts combine: a net with king and
// output buckets needs both options; 0 means "this net has none" (one output
// bucket; for king buckets: one unmirrored bucket).
//
// Fail-loud rule (no silent fall-back to the compiled-in network). The user
// requests a v2 net with a non-empty NNUEFile, NNUEKingBuckets > 0 or
// NNUEOutputBuckets > 0. A request that cannot be honoured (file missing or
// unreadable, wrong size, bad header or checksum, a king or output bucket
// count that does not match the loaded net, both counts 0 while a file is
// loaded, a count > 0 without a loaded file) is an error: the UCI layer prints
// `info string ERROR NNUE v2: <reason>` at once, and if the request is still
// unsatisfied at the next `isready`, `go` or `bench` it prints the error again
// and exits with status 2. Not errors: `UseNNUE false` (every network off on
// purpose; the request is ignored while it lasts) and NNUEFile `<empty>` (clears
// the file part of the request). With no NNUE option set nothing new is printed
// and the engine is the AL1 s198 engine.
extern int nnue_output_buckets;

// UCI NNUEThreats (spin 0-1, default 0; O6; "true" / "false" are accepted as
// well): 1 = evaluate with a v2 net that has threat inputs (header feature_set
// bit 0; forge/nnue_v2.hpp ThreatFeatures), loaded with NNUEFile; with
// NNUEKingBuckets 0 that net must have one king bucket, with NNUEKingBuckets
// N > 0 exactly N. The header and the option must agree both ways: NNUEThreats 1
// with a net without threat inputs, and NNUEThreats 0 with a threat net, are
// fail-loud errors (rule above). NNUEThreats 1 is itself a v2 request (an error
// without a usable net); UseNNUE false still wins.
extern int nnue_threats;

// UCI NNUEPawnPairs (spin 0-1, default 0; O7; "true" / "false" accepted as
// well): 1 = evaluate with a v2 net that has pawn-pair inputs (header
// feature_set bit 1; forge/nnue_v2.hpp PawnPairFeatures). Same rules as
// NNUEThreats: with NNUEKingBuckets 0 a one-bucket net, the header bit and the
// option must agree both ways (fail-loud otherwise), it is a v2 request of its
// own, UseNNUE false wins. NNUEThreats and NNUEPawnPairs are independent: a net
// with both blocks needs both options.
extern int nnue_pawn_pairs;

// UCI PureNnue (spin 0-1, default 0; O4; "true" / "false" are accepted as
// well): 1 = the evaluation is the network alone, without the hand-crafted
// evaluation (HCE). It needs a stand-alone v2 net (header flag residual = 0,
// trainer --pure) loaded with NNUEFile; with NNUEKingBuckets 0 that net must
// have one king bucket (the compiled-in input layer), with NNUEKingBuckets
// N > 0 exactly N. The header flag and the option must agree both ways:
// PureNnue 1 with a residual net, and PureNnue 0 with a stand-alone net, are
// fail-loud errors (rule above), so the HCE is skipped exactly when PureNnue
// is 1. PureNnue 1 is itself a v2 request (an error without a usable net);
// UseNNUE false still wins.
extern bool pure_nnue;

// Derived switch read by Worker::static_evaluate: true while a v2 network is
// active. Written only by apply_nnue_v2().
extern bool nnue_v2;

// Re-selects the evaluation network after NNUEFile, NNUEKingBuckets,
// NNUEOutputBuckets or UseNNUE changed and returns whether a v2 network is now
// active. The caller clears the hash afterwards (stored static evals may belong
// to another network).
// `message` (optional) receives a one-line description of the state.
bool apply_nnue_v2(std::string* message);

// The fail-loud rule above: why the current v2 request cannot be honoured, or
// "" when it is honoured, when nothing is requested or when UseNNUE is false.
// `file` is the NNUEFile value ("" = none) and `load_error` why it did not
// load ("" = it loaded). Call after apply_nnue_v2().
std::string nnue_v2_problem(const std::string& file, const std::string& load_error);

// UCI CorrMargins (spin 0-1, default 0): correction-size pruning margins
// (forge/corr_margins.hpp, weights tune::Corr*Pct). Read once per iteration at
// the root, which then searches with the CorrMargins instance of the main
// search (Worker::search_corr_margins, src/search/alphabeta.inc); with 0 no
// node tests it and the search is the AL1 s198 search.
extern std::uint8_t corr_margins;

// UCI CorrExt (spin 0-1, default 0): correction-history extensions
// (forge/corr_ext.hpp, weights tune::CorrExt*). Read once per iteration at the
// root, which then searches with the CorrExt instance of the main search
// (Worker::search_corr_ext, src/search/alphabeta.inc); with 0 no node tests it
// and the search is the AL1 s198 search.
extern std::uint8_t corr_ext;

// UCI CuckooRep (check, default false): upcoming-repetition draw bound. At
// every non-root node of the main and quiescence search whose alpha is below
// the draw score, Board::upcoming_repetition() asks whether the side to move
// can reach a search-level repetition draw with one reversible move; if so,
// the draw score is a lower bound for the node (src/search/cuckoo.inc). Read
// once per iteration at the root, which then searches with the CuckooRep
// instances of the search functions; with the option off no node tests it.
extern bool cuckoo_rep;

// UCI MaterialKeyTable (check, default false), job S11 (node-exact speed).
// The material-correction key (src/search.cpp material_key) is computed from
// the contribution table of forge/material_key_table.hpp (ten table loads and
// additions) instead of the ten dependent Horner multiplications. Both give the
// same 64-bit key for every board, so the search (nodes, scores, moves) is
// unchanged; only the speed can differ.
extern bool material_key_table;

// UCI IntendedThreefold (check, default false), S-IT. FIDE 9.2.1 lets the side to move
// claim a draw before a legal move that would create the third occurrence; with
// the option on, non-root search and quiescence treat that right as a floor at
// the draw score, without TT score cutoffs or stores at those nodes.
extern bool intended_threefold;

} // namespace forge::options
