#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${TMPDIR:-/tmp}/forge-see-classify-$$"
trap 'rm -f "$out"' EXIT
"${CXX:-g++-14}" -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Iinclude tests/see_exchange_classify.cpp src/board.cpp src/bitboard.cpp -o "$out"
ASAN_OPTIONS=detect_leaks=0 python3 - "$out" <<'PY'
import pathlib, re, subprocess, sys
output = []
for i, line in enumerate(pathlib.Path('tests/see_exchange_results.txt').read_text().splitlines()):
    match = re.search(r'fen=(.*?) move=(\S+)', line)
    if not match:
        continue
    run = subprocess.run([sys.argv[1], match[1], match[2]], text=True, capture_output=True, check=True)
    if run.stderr:
        raise RuntimeError(run.stderr)
    output.append(f'CASE {i+1}: {line}\n{run.stdout}\n')
expected = pathlib.Path('tests/see_exchange_classification.txt').read_text().rstrip()
assert ''.join(output).rstrip() == expected, 'Classification output changed'
for fen, move, expected in [
    ('8/8/8/2q5/2k5/8/8/K1B1r1Q1 w - - 0 1', 'g1e3', 'SEE=-700 exact=-900 legal_LVA=-700'),
    ('2k5/2p5/3q4/1N2B3/8/8/8/4K3 w - - 0 1', 'b5c7', 'SEE=100 exact=-200 legal_LVA=100'),
]:
    run = subprocess.run([sys.argv[1], fen, move], text=True, capture_output=True, check=True)
    assert not run.stderr, run.stderr
    assert run.stdout.splitlines()[0] == expected, run.stdout
print('PASS 18 saved classification traces and 2 additional minimized examples; ASan/UBSan')
PY
