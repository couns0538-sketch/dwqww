#!/usr/bin/env python3
"""Controls for the NNUE parity harness (AVX2 kernels): planted bugs in src/nnue.cpp must make the
parity test FAIL; reassociated accumulator kernels must still PASS (exact arithmetic, see below);
the unmutated tree must PASS.
usage: mutation_check.py <repo_dir> <scratch_dir> <build_script> "<cxx flags>"
(build_script: a CMake wrapper taking <src> <build> "<flags>" <targets...>, e.g. cmake_build_flags.sh)"""
import pathlib
import shutil
import subprocess
import sys

repo, scratch, build_script, flags = sys.argv[1:5]
NL = "\n"
# name: (pattern, replacement, must_fail). The reassociations must PASS: every w1/b1 value is an int16
# divided by 4096, so accumulator sums are exact (see REPORT.md) and their order cannot change a bit.
# The real bugs (wrong column, skipped change, unwritten lanes, missing clamp, reordered output sum)
# must FAIL.
QUIET = "vec_store(out + h, vec_add(vec_sub(vec_load(in + h), vec_load(r + h)), vec_load(a + h)));"
CAPTURE = "vec_add(vec_sub(vec_sub(vec_load(in + h), vec_load(r0 + h)), vec_load(r1 + h)), vec_load(a + h))"
CASTLE = ("vec_add(vec_sub(vec_add(vec_sub(vec_load(in + h), vec_load(r0 + h)), vec_load(a0 + h))," + NL +
          "                                           vec_load(r1 + h)),")
MUTATIONS = {
    "none": None,
    "quiet_reassociate": (QUIET, "vec_store(out + h, vec_add(vec_load(in + h), vec_sub(vec_load(a + h), vec_load(r + h))));",
                          False),
    "capture_reassociate": (CAPTURE, "vec_add(vec_sub(vec_load(in + h), vec_add(vec_load(r0 + h), vec_load(r1 + h))), vec_load(a + h))",
                            False),
    "castle_reassociate": (CASTLE, "vec_add(vec_add(vec_sub(vec_load(in + h), vec_load(r0 + h)), vec_sub(vec_load(a0 + h)," + NL +
                           "                                           vec_load(r1 + h))),", False),
    "refresh_reverse_order": ("const float* source = columns[c] + base;",
                              "const float* source = columns[count - 1 - c] + base;", False),
    "quiet_wrong_column": (QUIET, "vec_store(out + h, vec_add(vec_sub(vec_load(in + h), vec_load(r + h)), vec_load(r + h)));",
                           True),
    "capture_skips_second_removal": (CAPTURE, "vec_add(vec_sub(vec_load(in + h), vec_load(r0 + h)), vec_load(a + h))", True),
    "castle_swaps_rook_squares": ("                                   vec_load(a1 + h)));",
                                  "                                   vec_load(r1 + h)));", True),
    "refresh_drops_last_piece": ("for (std::size_t c = 0; c < count; ++c) {" + NL + "            const float* source = columns[c] + base;",
                                 "for (std::size_t c = 0; c + 1 < count; ++c) {" + NL + "            const float* source = columns[c] + base;",
                                 True),
    "quiet_last_vector_unwritten": ("    for (int h = 0; h < HiddenSize; h += VecWidth)" + NL + "        " + QUIET,
                                    "    for (int h = 0; h + VecWidth < HiddenSize; h += VecWidth)" + NL + "        " + QUIET, True),
    "output_no_upper_clamp": ("const __m256 a = _mm256_min_ps(_mm256_max_ps(_mm256_load_ps(ours.data() + base), zero), one);",
                              "const __m256 a = _mm256_max_ps(_mm256_load_ps(ours.data() + base), zero);", True),
    "output_sum_reverse": ("for (int j = 0; j < Lanes; ++j) out += lanes[j];",
                           "for (int j = Lanes - 1; j >= 0; --j) out += lanes[j];", True),
}

if __name__ == "__main__":
    source_text = (pathlib.Path(repo) / "src" / "nnue.cpp").read_text(encoding="utf-8")
    for name, edit in MUTATIONS.items():
        if edit and source_text.count(edit[0]) != 1:
            raise SystemExit(f"{name}: pattern found {source_text.count(edit[0])} times, expected once")
    results = []
    for name, edit in MUTATIONS.items():
        src = pathlib.Path(scratch) / f"src_{name}"
        if src.exists():
            shutil.rmtree(src)
        shutil.copytree(repo, src, ignore=shutil.ignore_patterns(".git", "opus_round1", "__pycache__"))
        if edit:
            path = src / "src" / "nnue.cpp"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace(edit[0], edit[1]), encoding="utf-8", newline="\n")
        build = pathlib.Path(scratch) / f"build_{name}"
        subprocess.run(["bash", build_script, str(src), str(build), flags, "forge_nnue_parity_tests"], check=True,
                       stdout=subprocess.DEVNULL)
        exe = build / "forge_nnue_parity_tests.exe"
        if not exe.exists():
            exe = build / "forge_nnue_parity_tests"
        run = subprocess.run([str(exe), "--fens", str(src / "tests" / "data" / "nnue_selfplay_sample_916.txt")],
                             capture_output=True, text=True)
        last = (run.stdout.strip().splitlines() or ["(no output)"])[-1]
        expected_fail = edit is not None and edit[2]
        ok = (run.returncode != 0) == expected_fail
        results.append(ok)
        print(f"{name}: expect {'FAIL' if expected_fail else 'PASS'}, exit {run.returncode} -> "
              f"{'caught' if run.returncode else 'passed'} ({'OK' if ok else 'UNEXPECTED'}): {last[:200]}", flush=True)
        shutil.rmtree(src)
        shutil.rmtree(build)
    print("ALL AS EXPECTED: planted bugs caught, reassociations and the clean tree pass" if all(results)
          else "MUTATION CHECK FAILED")
    sys.exit(0 if all(results) else 1)
