# IDEA_SOURCE — S14 follow-up: no zero-fill of the move buffers

- **Idea:** Opus's own S14 finding (`opus_round1/sol_S14/REPORT.md` §4 item 2): in the AL1 lock exe every MovePicker
  construction zero-fills 3,328 bytes (2,048 B `moves_{}`, 1,024 B MoveList data because `Move` has default member
  initializers, 256 B `bad_captures_{}`), although the picker only reads entries it has written. Nothing is taken
  from another engine.
- **Storage technique:** standard C++20 implicit object creation (P0593R6, [intro.object]): an array of `std::byte`
  implicitly creates objects of implicit-lifetime types, and `std::launder` gives a pointer to them. `Move` itself is
  not changed, so no other use of `Move` changes behaviour.
- **Pick-order oracle:** adapted from Sol's S14 oracle
  (`17aa0cae:validation/forge_sol_pack31_20261025/forge_sol_S14_validation_prepared_20261026/forge_sol_S14_picker_oracle_20261026.cpp`):
  the history seed, the stack set-up and the six picker configurations are his; the storage patterns, the
  completeness check, the larger workload and the planted bugs are new. His allocation counter and fixed 20-row
  workload were not used.
- **Codegen tool:** extended from `opus_round1/O3/codegen_compare.sh` (branch `opus-O3`).
- **CI and NPS pattern:** `.github/workflows/opus-offguard-ci.yml` and `opus_round1/offguard/ci_offguard.sh` (branch
  `opus-offguard`); `nps_ab.py` is the unchanged copy used by S29, O3 and offguard (sha256 `bd8375b1…`).
- **Callgrind:** the run set-up follows O2's `opus-o2-perf.yml` (bench 13, Hash 16), with call-site attribution added.
