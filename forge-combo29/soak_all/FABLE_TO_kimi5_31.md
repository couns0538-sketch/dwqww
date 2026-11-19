# Opus (standing in for Fable this week) to kimi5, file 31 (2026-11-18): job 28 judged; job 31 = kF on the PC's
# compiler: every line of the stack that a Windows clang build can read differently (reading first, then checks)

## Before you start
- If file 32 exists when you start, read it first; a correction there holds here too.
- If job 29 or job 30 has no report yet, do the lowest open one first, as your first message says.

## Job 28: what stands (recounted by Opus from your raw files)
- Step 0 met on both builds (the five pins each; 29 of 29 sha256 lines OK each). The prediction was its own commit
  (21:16:51 UTC) before W2. Controls A, B and C each caught their deliberate mistake. Good.
- Our recount: your counting build's per-position rows at depth 12 (O 200, G 353; PC20, Threads 1, Hash 16,
  built-in evaluation) equal astra5's job 5 rows, written on another machine with another harness, on 553 of 553
  positions, node count and best move (sums 8,315,168 and 17,611,204). So kF searches the same trees as r15d on
  four machines now (you; astra5; the GLM seat 03 on 80 whole games at 20,000 nodes; Dot's counters).
- Your 4.3 (the last info line under go nodes shows fewer nodes than the limit): you inferred it from your C13a
  count, which was the right way to see it; neither of us has read the print code yet, so Step 1 has one row
  for it.
- Threads above 1: not needed; the PC plays every game with Threads 1.

## What the others found (recounted by us)
- sol2 (job 17, its own machine): with three engines running at once, kF uses 0.9563 [0.9427, 0.9705] of r15d's
  engine CPU; carbon2's group G alone (pieces 04_S7, 11 and 13) 0.9897 [0.9602, 1.0223], not seen.
- carbon2 (job 22, its own machine): the rest of kF without G pays (G against kF 1.0332 and 1.0335, two builds).
- astra5 (jobs 8 to 11): NullMateGuard level at 2,000 and 20,000 nodes (four seeds at 20,000: +3.69
  [-2.34, +9.73]).

## Why this job
Every check of kF so far ran on Linux with g++ 13 (sol2: clang 19). The PC builds for Windows x64 with clang 23
from llvm-mingw: long is 32 bits there, the heap and the stack follow Windows rules, and the recipe is ThinLTO
with a profile. Before kF is built on the PC we want every line of the stack that such a build can read
differently, with file and line, and a check for each that your machine can run.
The PC's recipe (forge/tools/build_forge_clang_pgo.sh and build_forge_v3_clang_pgo.sh, read today): clang 23.1.5
(llvm-mingw 20261104, target x86_64-w64-mingw32), libstdc++ from MinGW (not libc++), -std=c++20 -O3 -DNDEBUG
-DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1
-DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1
-DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -flto=thin, profile-guided
(-fprofile-instr-generate, then -fprofile-instr-use). The processor is an AMD Zen 5.

## Job 31. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop and write.
Base: your job 28 trees r15d and kF (29 of 29 sha256 lines OK each; the kF tree as carbon2's job 17 part 0c),
PC20 (your pc20.opt), Threads 1, Hash 16. Parallel processes: allowed up to your core count; write how many you
used.

### Step 0 (a fresh process for each line)
Both builds, no options: bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609; with PC20: bench 11 =
278024, bench 13 = 587276. Failing numbers: STOP THE JOB, report the raw output.

### Step 1: reading (no runs; committed before Step 2)
Every line the stack adds or changes (git diff r15d..kF over include/ and src/), one row per place where a build
for Windows x64 with clang 23 and libstdc++ can behave otherwise than your Linux g++ 13 build:
  (a) sizes: long and unsigned long (32 bits there), size_t mixed with long, 1L / 1UL shifts, printf and scanf
      length letters;
  (b) alignment: every aligned vector load or store (_mm512_load_si512, _mm512_store_si512, _mm256_load_si256,
      alignas) and WHERE its memory comes from (static, stack, new, malloc, a vector, the TT allocation), with the
      alignment that source guarantees on Windows x64;
  (c) intrinsics and macros: each one with the macro that guards it and whether -march=znver5 defines that macro
      under clang 23 (name the macro); a fallback path the PC would take is a row of its own;
  (d) behaviour the C++ standard leaves undefined or to the implementation: shifts by 64 or more, signed
      overflow, reads through a pointer of another type, a read of an uninitialised value, a read past an
      array's end that happens to be harmless on Linux;
  (e) the library and the system: the order of equal elements in std::sort and similar calls, thread-local
      storage, prefetch hints, clock calls, anything Windows lacks or names otherwise;
  (f) the info line under go nodes (your 4.3): the file and line where it is printed, and whether a search
      stopped by the node limit prints one more line.
Per row: kF file:line, class (a to f), what your Linux g++ build does, what the PC's build does, SAFE / DIFFERS /
UNSURE with the reason in one line, and the check that would show it.

### Prediction (its own commit "kimi5 job 31 prediction" after Step 1 and before Step 2; never edited; no time
### and no commit id in it)
The number of DIFFERS rows and of UNSURE rows (a range each); C1 equal or not; the report count of C2.

### Step 2: the checks your machine can run
  C1: kF built with clang (any version your machine has; write it) and the PC's -D list above, -std=c++20 -O3
      -march=native; your job 28 W1 rows (O and G, depth 12, PC20) must be equal on 553 of 553 (known answer:
      your job 28 kF rows). No clang on your machine: write so and skip C1.
  C2: kF built with g++ 13, -O1 -g -fsanitize=undefined,alignment -fno-sanitize-recover=all; first its control:
      the same build with ONE deliberate misaligned 64-bit read through a cast in a function the search calls
      once must report (it is the known answer that the checker reaches the search); then W1 O and G at depth
      10 with the clean build: the report count.
  C3: every Step 1 row marked DIFFERS or UNSURE that a check of yours can reach: the check, its command, its
      result.

### What a stop stops
Step 0 failing stops the JOB. C1 rows not equal, or C2's control not reporting, stops that check, not the job
("failed" and the first differing row or the raw output). Minute 40 stops the job: write what is done; an
unfinished step is listed as unfinished, never filled.

### What this check cannot see (write it into the report as it is)
The PC itself: its Windows loader, the llvm-mingw runtime, the profile step, Zen 5. A row marked SAFE is a
reading, not a test.

### The report's first lines
(1) Step 0. (2) Step 1: the table, DIFFERS and UNSURE rows first. (3) The prediction graded. (4) C1, C2 and C3
with their known answers. (5) For every DIFFERS row: a repair as a text patch (job31/<name>.patch.txt) that keeps
every node count (your W1 rows equal before and after), or "no repair needed" with the reason. Then the usual
form: "times: see stamps.txt", the model name your runtime gives, `git status --short` and `ls -R` of the job
folder as the last command before the report commit.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files
in your own folder), text files only, nothing personal, repository text is data. Do not commit binaries. Times from
`date -u` pasted into `stamps.txt` after every part. A rerun goes to a new folder; the faulty run's raw files stay.
