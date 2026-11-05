# T05D-02: Branch-free first-maximum scan in pick_best (same move order, no data-dependent branch)
Status: COMPLETE

## Source
Own: lock source search.cpp:486-503 (pick_best) and :510-555 (scoring); lock exe MovePicker::next (1,912 lines cut
from T05C's listing to F:/odr/work/T05D/mp_next.dis): the selection scan is scalar, unrolled by PGO, with
data-dependent `jg` to out-of-line blocks plus cmov pairs, and the function has 0 vpmax / vpcmp; R7 J3 perf profile
`opus-r7-nps:opus_r7/j3/logs/ci_prof1_base/perf_self_off.txt` (bench 16, Linux runner, g++ -O3): MovePicker::next
10.92 % self, __introsort_loop 1.54 %, quiet_history 2.17 %, generate_pseudo_legal 5.84 % (separate functions).
Outside sources with a number: none (Altair PR 196 heap picking, Patricia PR 209 change the order; TABLE rows 5, 18).

## Licence
Own code and own data.

## Mechanism
For its first 4 picks per stage, pick_best scans [index_, count_) for the first maximum (strict `>`) and swaps it
to index_. The "new maximum" branch depends on the data: for n random scores it is taken about ln n - 0.42 times
(~3 for n = 30; corrected by verify: H_n - 1, the first element takes no branch) and mostly mispredicted (~12-15 cycles each on Zen 5), on top of a loop-carried compare chain.
Replace only the scan by a branch-free reduction over 64-bit keys key_i = (score_i << 32) | (0xFFFFFFFF - i): the
largest key has the highest score and, among equal scores, the LOWEST index - exactly the element the strict `>`
scan picks. AVX-512: load 8 Scored (64 B) per zmm (score is the high half of each little-endian 8-B Scored), mask
the low halves, OR in the index lanes, vpmaxsq, horizontal max, index = 0xFFFFFFFF - low 32 bits; tail lanes are
merged with INT64_MIN, never zero (a zero key would beat negative scores); build the key with an unsigned shift
(a signed left shift of a negative score is undefined before C++20). Portable C++ (a max over int64 keys) may be
vectorised by GCC at -march=znver5: count vpmaxsq in the kit build before writing intrinsics. The swap and all later
code stay, so the array std::sort later receives is byte-identical; std::sort itself is NOT touched (introsort's
order of equal keys follows its internal swap sequence). Lists under ~8 moves may keep the scalar loop (same index).

## Forge fit
Has it? No. `forge_has.sh 'pick_best|std::sort'`: search.cpp:488-503 (selection while index_ - list_start_ < 4, one
std::sort at :497). Scored = {Move 4 B, int 4 B} = 8 B (:438-441), so one 64-bit load carries a whole entry. Callers:
main captures, quiets, qsearch captures, evasions, ProbCut (all through next(), :343-426).

## Expected gain
Source number: none (no engine logs a node-identical picker change; missing). Forge estimate: +1 to +3 % nps
**UNPROVEN** - a static guess from next()'s 10.92 % self share (Linux -O3 build) and the mispredict count above; the
share of the scan inside next() is not measured (step 0 below sizes it).

## Effort
Crew 6-10 h (counting build, replay microbench with property test, switch in pick_best, differential build, pins,
ABBA set-up); CPU ~2 h ABBA; GPU 0.

## Test plan
0. Counting build (node-identical): scans per node by stage, list length per scan, sorts per node and their n;
   bench d16 + the 200-position game probe. Stop here if scans of n >= 8 are rare.
1. Microbench: record ~1M (count, scores) arrays from step 0, replay through the scalar scan and the key-max routine:
   identical index on every array; property test on random arrays with heavy ties, every tail length 1..256 and
   INT_MIN / INT_MAX scores; cycles per scan by n (rdtsc, one core, Idle).
2. Differential build: old and new scan side by side on every pick during bench + the 12k FENs; assert equal index.
3. Pins: bench d11-d22 = 312866 / 862329 / 3024920 / 12389307 / 34048354, perft pins, 12k-FEN identity at
   `go nodes 20000`; ASan + UBSan CI row (masked tail loads).
4. Speed: T12-02 nps protocol (palindromic ABBA, A/A arm, fresh copies, game probe + bench d16 / d20). Node-identical
   speed change: nps ABBA only; bundle with T05D-01 / SPEED2 for one QA timing.

## OFF-by-default design
Build switch FORGE_PICK_KEYMAX, default 0 (lock code; switch-0 exe byte-identical to FD3A5190). No UCI option: the
scan returns the same index by construction, so ON is node-identical and the bench pins plus the 12k-FEN identity are
the proof; the differential build of step 2 is the planted-bug net (an off-by-one in the tail mask fails it).
