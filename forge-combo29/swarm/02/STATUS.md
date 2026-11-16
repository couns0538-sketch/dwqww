seat 02
area 2 (UCI COMMANDS under ASan + UBSan)
branch for-fable-and-opus/swarm-02
seed 201

## 2026-11-16T21:10Z

Done since start:
- STEP 1 seat claimed: SEAT 02, branch for-fable-and-opus/swarm-02, folder forge-combo29/swarm/02/.
- Repository check: `git remote get-url origin` -> https://github.com/couns0538-sketch/dwqww (ends in couns0538-sketch/dwqww). Correct repo.
- STEP 2 release build: worktree /agent/repos/base at 6b98f217, cmake Release with g++-13, plain `cmake .. -DCMAKE_BUILD_TYPE=Release`.
  Machine has avx512f/bw/dq/vl/bmi2, so no -DFORGE_PORTABLE needed. Exe: build/forge
  sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
- HONESTY PASS: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609.
  Raw: forge-combo29/swarm/02/honesty/{bench11,bench13,bench16,perft5}.txt, numbers.txt; harness run_honesty.sh.
  NOTE for others: this engine has NO argv handling (main() is just uci_loop(std::cin)); `forge bench 13`
  on the command line prints nothing and exits 0. Send `bench 13` on stdin instead.

Running now: ASan+UBSan build at /agent/repos/base/forge-combo29/build-asan (cmake -fsanitize=address,undefined).

Next: verify the ASan build's sanitizer symbols (nm -C | grep -c __asan_), plant a fault on a scratch copy and prove
the runner counts its sanitizer line, then AREA 2 job 1 (2,000 random UCI command sequences).

Exact next command:
  tail -3 /agent/repos/base/forge-combo29/build-asan/build.log
