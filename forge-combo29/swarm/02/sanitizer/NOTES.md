# S02 sanitizer proofs (required before any "0 sanitizer lines" claim)

Build under test: /agent/repos/base/forge-combo29/build-asan/forge
  cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
           -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
  sha256 b109a0a5acce5b0ddad5707c04f8263fe51f48a890df4a7a2ea6ffcef8a43f99
  nm -C | grep -c __asan_ = 35 ; __ubsan_ = 15 ; __tsan_ = 0   (see sanitizer/build.meta)

PROOF 1 (nm): the exe carries the sanitizer runtime. See build.meta.

PROOF 2 (planted fault counted by the same runner): planted_proof.sh
  fault exe = scratch copy at /tmp/forge-fault (NEVER committed), two faults behind input I control:
    command "sanprobe" -> heap-buffer-over-read
    command "ubprobe"  -> signed integer overflow
  Same runner, same input file forge-combo29/swarm/02/sanitizer/probe.in:
    clean real engine   -> exit 0, sanitizer_lines 0
    fault build         -> exit 1, sanitizer_lines 3   (ASan heap-buffer-overflow + UBSan runtime error shown)
    fault build, probes removed from the input -> exit 0, sanitizer_lines 0  (control: the count is
      caused by the planted input, not by the runner being trigger-happy)
  Raw: sanitizer/{clean,fault,fault_control}.out, meta.txt, probe.in, probe_control.in, fault_first_lines.txt

The planted source edit (as text, it was applied to the scratch copy only):
  if (command == "sanprobe") {
      char* p = new char[4];  ... volatile char leak = p[4 + (std::rand() & 3)]; ...
  }
  if (command == "ubprobe") {
      volatile int big = 2147483647; int wrap = big + (std::rand() & 1); ...
  }

Env: every run uses `env -u ASAN_OPTIONS -u UBSAN_OPTIONS -u TSAN_OPTIONS` so a left-over option cannot hide lines.
