STATE: IN PROGRESS

# b2_pickbest: FORGE_SPD_PICKBEST (card T05D-02: branch-free first-maximum scan in MovePicker::pick_best)

Worker b2mg (fable), job B part 2, branch opus-speed-20261105. Source edits 09:37-09:40 PC clock (`date`).
Patch: `F:/ospd/wt/opus_speed/patches/b2_pickbest.patch` (50 lines; file search.cpp only; applies with `patch -p1` to a fresh
lock copy and reproduces `F:/ospd/src/b2_pickbest`: apply test in `F:/ospd/src/b2_applytest_pickbest`). One switch line
`#define FORGE_SPD_PICKBEST 0` in search.cpp. Verify variant (not for stacking): `F:/ospd/src/b2_pickbest_verify`.

## Design (own words)
The lock's `pick_best` (search.cpp:488-503) scans [index_, count_) with a strict `>` and keeps the FIRST maximum, then swaps it
to index_ (only for the first 4 picks per stage; later picks come from one std::sort, untouched here). The switch replaces
only the scan: key_i = (uint32(score_i) << 32) | (0xFFFFFFFF - i) read as a signed int64. The high half orders by score
(signed), the low half by inverted index (unsigned, index < 256 fits), and no two keys are equal, so max_i key_i names the
element with the highest score and, among equal scores, the lowest index: exactly the lock's `best`. The loop is a plain
`best_key = std::max(best_key, key_i)` chain (cmov, no data-dependent branch), `best = 0xFFFFFFFF - uint32(best_key)`, and the
swap plus everything after it is the lock's text, so the array that std::sort later receives is byte-identical. Portable
C++ (no intrinsics); GCC may or may not vectorise the max reduction (counted in the codegen section). Lists are at least one
element long at every call (the callers test index_ < count_), so the first key is valid.

## Lines touched (lock numbering)
- src/search.cpp: switch block before `class MovePicker` (:319); the helper `pick_key` under the switch before :486; :491-494
  (the scan) under `#if` / lock scan under `#else`; :495 swap and the rest untouched.
- Switch 0: `g++ -E -P` of src/search.cpp is byte-identical to the lock's (`F:/ospd/jobb/b2/pickbest/pp/`).

## Checks
(a), (b), (c) verify build (both scans at every pick over bench d16 + 12k FENs), codegen: PENDING (chain C, after chain B).

## Risks
- Gain unknown (card: +1 to +3 % UNPROVEN, a static guess); the ABBA decides. The scalar key chain trades the lock's
  mispredicted "new maximum" branches for a 1-cycle cmov dependency per element.
