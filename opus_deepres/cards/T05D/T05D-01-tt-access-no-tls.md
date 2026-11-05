# T05D-01: TT probe / store without the per-access emulated-TLS lookup (port R7TtExclusive to the lock)
Status: COMPLETE

## Source
Own records: R7 J3 report `opus-r7-nps:opus_r7/j3/REPORT.md` (option R7TtExclusive, engine commit 2d9889cf, NPS
logs/nps_ci_pooled.txt, callgrind logs/ci_prof2_options/option_sets.log); tried gate R7-TTX (passed H1, never ported;
notes/TRIED_GATES.md line 87); lock exe forge_ltopgo_x_al1s198_v23.exe (sha256 fd3a51903e73dc1f..., re-hashed by
T05D), static listing F:/odr/work/T05C/lock_v23.dis. No outside source needed. Details: notes/T05D/sources.md L2-L5.

## Licence
Own code, own measurements, own exe: free to reuse inside Forge.

## Mechanism
The PC toolchain emulates `thread_local`: every read of TranspositionTable::active_lease_ calls __emutls_get_address,
which calls the threads library's getspecific: GetLastError, a once check, TlsGetValue, a spin lock taken with `xchg`
on memory (a locked instruction = full fence: younger loads wait, the store buffer drains), the unlock, SetLastError.
lock_stripe() reads it through has_exclusive_access() on EVERY probe and store, although a one-worker UCI `go` or
bench holds the ExclusiveLease and the returned lock is a deferred (unlocked) one. In the LTO+PGO lock exe the call
sits inside the inlined probe, between the cluster index (mulq, shl 6) and the first key32 compare: on the TT load's
critical path. Fix (own design): Searcher::search already knows the lease is taken (Exclusive and one worker);
hand that to the Worker as a plain bool once per search, and let the Worker call probe / store bodies without
lock_stripe while it is set. Entry selection, aging, replacement and the store's handle checks (owner, epoch, key,
cluster, slot) stay as they are, so the same entries are read and written in the same order.

## Forge fit
Has it? No. `forge_has.sh 'has_exclusive_access|lock_stripe|thread_local'`: search.hpp:153-155, search.cpp:184,
:211-216, :218-228, probe :249, store :289, hashfull :308. Lock exe call sites of __emutls_get_address: Worker::search
0x1400ee166 and 0x1400f2152 (two PGO copies of the inlined probe), Worker::qsearch 0x1400facc5 (inlined probe), and
the out-of-line TranspositionTable::store 0x1400fe605 (called from 3 sites in search, 2 in qsearch).
R7's probe_exclusive / store_exclusive are not in the lock and not in SPEED2 (de20653c = prefetch sites, MovePicker
hoist, table piece_type). Correction: notes/T05/SPEED_LIST.md line 34 ("R7TtExclusive is in the lock") is wrong - the
lock skips only the stripe mutex, not the TLS read. R7's tree has another layout (tt.hpp, thread_data.hpp), so the
change is re-written for search.hpp with the forge-lock-port recipe, not cherry-picked.

## Expected gain
Source number (own, R7 J3, PC, plain -O3 znver5 build of opus-r5d-matefix 5882c383 - not the lock; fresh process per
run, rotated order, PC 73 % busy, 95 % t-intervals): +3.59 % [+1.38, +5.84] d16 wall and +3.97 % [+1.23, +6.77] d20
wall nps over 15 runs (A/A -0.02 % [-2.24, +2.25] / -0.98 % [-2.51, +0.57]); second exe +1.54 % [-2.23, +5.45] d16,
+5.45 % [+3.31, +7.63] d20 (6 runs); callgrind bench 13 -1.26 % instructions on Linux (native TLS there, so no fence).
Gate R7-TTX, non-regression SPRT [-10, 0]: 2,534 games, +3.84 Elo, LLR 2.96, H1 (same R7 tree).
Forge estimate on the LTO+PGO lock: +2 to +4 % nps **UNPROVEN** (same four opaque calls; PGO cannot remove them).

## Effort
Crew 6-8 h (switch, plain + kit pc1 = pc2, pins, 12k identity, objdump, CI row, ABBA); CPU ~2 h ABBA, no SPRT; GPU 0.

## Test plan
1. Codegen: switch-1 exe has no __emutls_get_address call in Worker::search, Worker::qsearch or the store path (only
   the lease constructor / destructor and hashfull keep it); switch-0 kit build = FD3A5190 byte for byte (as SPEED2).
2. Pins: bench d11 / d13 / d16 / d20 / d22 = 312866 / 862329 / 3024920 / 12389307 / 34048354; perft startpos 5 =
   4,865,609, kiwipete 5 = 193,690,690; the 12k gate FENs at `go nodes 20000`: bestmove, score, nodes equal.
3. Threads 2 / 4 bench and the TSan CI row: helpers still take stripe locks (the flag exists only under the lease).
4. Speed: T12-02 protocol - palindromic ABBA, fresh exe copies per slot, A/A arm first, the 200-position game probe
   (`go movetime 200`) plus bench d16 / d20; keep at a point estimate >= +1 % with A/A containing 0; then QA timing
   together with SPEED2. Node-identical speed change: nps ABBA only, no Elo SPRT.

## OFF-by-default design
Build switch FORGE_TT_NOTLS, default 0 (the lock's code path; switch-0 exe = FD3A5190 byte for byte). With 1 the bool
is true only while the Searcher holds the ExclusiveLease (one worker, TTAccess::Exclusive: UCI go and bench); helpers,
Threads > 1, diagnostics and hashfull keep lock_stripe. No UCI option: ON reads and writes the same TT entries in the
same order, so the bench pins and the 12k-FEN identity are the proof.
