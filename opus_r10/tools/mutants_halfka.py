"""R10: planted-bug check of tests/halfka_tests.cpp. For the control and each mutant: copy src/ and include/ of the repo
into a fresh folder under <scratch dir>, replace one line of src/nnue_halfka.cpp (the pattern must occur exactly once),
build the test with the box flags against that tree (build_tool.py), run it on the committed smoke net, and record the
exit code and the FAIL lines. The control must pass, every mutant should fail.
usage: python -I -B run_pinned.py --mask 0x0FF0 -- mutants_halfka.py <repo root> <scratch dir>"""
import os
import shutil
import subprocess
import sys

root, scratch = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
PY = sys.executable
TOOLS = os.path.join(root, "opus_r10", "tools")
MUTANTS = [
    ("control", None, None),
    ("apply_add_sub_swapped",  # one-pass update (AVX-512 path): adds become subtractions and back
     "a = adds[static_cast<std::size_t>(c)] ? _mm512_add_epi16(a, w) : _mm512_sub_epi16(a, w);",
     "a = adds[static_cast<std::size_t>(c)] ? _mm512_sub_epi16(a, w) : _mm512_add_epi16(a, w);"),
    ("block_kernel_skips_first_group",  # block kernel (VNNI): outputs 0..15 never accumulate
     "for (int q = 0; q < NQ; ++q) acc[q] = _mm512_dpbusd_epi32(acc[q], xb, _mm512_loadu_si512(w + q * 64));",
     "for (int q = 1; q < NQ; ++q) acc[q] = _mm512_dpbusd_epi32(acc[q], xb, _mm512_loadu_si512(w + q * 64));"),
    ("block_kernel_half_chunk",  # a final 64-byte chunk is scanned as 32 bytes: nonzero blocks are lost
     "unsigned mask = in - c >= 64 ?", "unsigned mask = in - c > 64 ?"),
    ("refresh_row_sub_for_add",  # refresh (AVX-512 row kernel) subtracts instead of adding
     "_mm512_storeu_si512(acc + j, _mm512_add_epi16(a, b));", "_mm512_storeu_si512(acc + j, _mm512_sub_epi16(a, b));"),
    ("scalar_layer_drops_bias",  # scalar reference path: bias missing
     "s[k] = b[static_cast<std::size_t>(k)] + dot(w.data() + static_cast<std::size_t>(k) * static_cast<std::size_t>(in), x, in);",
     "s[k] = dot(w.data() + static_cast<std::size_t>(k) * static_cast<std::size_t>(in), x, in);"),
    ("square_epsilon_dropped",  # l1 squared activation without the trainer's +1e-5 (rare effect: may survive 300 positions)
     "x[static_cast<std::size_t>(k)] = sqr(s1[static_cast<std::size_t>(k)], 21, 20);",
     "x[static_cast<std::size_t>(k)] = sqr(s1[static_cast<std::size_t>(k)], 21, 0);"),
]
os.makedirs(scratch, exist_ok=True)
rows = []
for name, old, new in MUTANTS:
    tree = os.path.join(scratch, name)
    if os.path.exists(tree):
        raise SystemExit(f"{tree} exists: use a fresh scratch dir")
    for d in ("src", "include"):
        shutil.copytree(os.path.join(root, d), os.path.join(tree, d))
    if old is not None:
        p = os.path.join(tree, "src", "nnue_halfka.cpp")
        text = open(p, "rb").read().decode("utf-8").replace("\r\n", "\n")
        assert text.count(old) == 1, (name, text.count(old))
        open(p, "wb").write(text.replace(old, new).encode("utf-8"))
    exe = os.path.join(tree, "halfka_tests.exe")
    b = subprocess.run([PY, "-I", "-B", os.path.join(TOOLS, "build_tool.py"), tree, os.path.join(root, "tests", "halfka_tests.cpp"), exe],
                       capture_output=True, text=True)
    if b.returncode != 0:
        rows.append((name, "BUILD FAILED", b.stdout[-300:] + b.stderr[-300:]))
        continue
    r = subprocess.run([exe, os.path.join(root, "opus_r10", "nets", "smoke_k32h3_l64.nnue"),
                        os.path.join(root, "tests", "halfka_smoke_expected.txt"), tree], capture_output=True, text=True, timeout=900)
    fails = [l for l in r.stdout.splitlines() if l.startswith("FAIL: ")]
    last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    rows.append((name, f"exit {r.returncode}", f"{len(fails)} FAIL lines; {last[:160]}; first: {fails[0][:160] if fails else '-'}"))
    print(f"{name}: exit {r.returncode}, {len(fails)} FAIL lines", flush=True)
ok = rows[0][1] == "exit 0" and all(r[1] not in ("exit 0", "BUILD FAILED") for r in rows[1:])
print()
for r in rows:
    print(" | ".join(r))
killed = sum(1 for r in rows[1:] if r[1].startswith("exit") and r[1] != "exit 0")
print(f"control {'PASS' if rows[0][1] == 'exit 0' else 'FAIL'}; mutants killed {killed}/{len(rows) - 1}")
sys.exit(0 if ok else 1)
