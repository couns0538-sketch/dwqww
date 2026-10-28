#!/usr/bin/env python3
"""Planted bugs for the S12 null-edge accumulator alias port (FORGE_NNUE_LAZY_ACC).
Each mutant: copy src/ include/ tests/ of this tree to <out>/<name>/, replace one exact snippet (it must occur once),
build Sol's v2 regression test and the extra tests (tests/s12_lazyacc_extra_tests.cpp) with the switch ON (release
flags, -DNDEBUG like CTest Release) and run both; either failing catches the mutant. The
"option_not_wired" mutant only breaks the UCI/search wiring, which the unit test bypasses, so for it the engine is
built and alias_stats.py must report no alias activity. A mutant is CAUGHT when its detector exits non-zero.
usage: mutation_check_alias.py <tree> <out_dir>      (Windows PC: MSYS2 ucrt64 g++ on PATH)
"""
import shutil
import subprocess
import sys
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
GPP = 'C:/msys64/ucrt64/bin/g++.exe'
FLAGS = ['-std=c++20', '-O2', '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-ffp-contract=off', '-fno-fast-math',
         '-march=znver5', '-static', '-pthread', '-DFORGE_NNUE_LAZY_ACC=1']
CORE = ['src/bitboard.cpp', 'src/board.cpp', 'src/book.cpp', 'src/eval.cpp', 'src/eval_params.cpp', 'src/nnue.cpp',
        'src/search.cpp']
TESTS = [('Sol v2 regression test', 'tests/forge_sol_S12_lazyacc_native_regression_v2_20261027.cpp'),
         ('extra tests', 'tests/s12_lazyacc_extra_tests.cpp')]

MUTANTS = [
    ('stale_alias_after_real_move', 'src/search.cpp',
     '    (ss + 1)->accumulator_owner = nullptr;\n#endif\n}\n\nvoid Worker::record_null_move',
     '#endif\n}\n\nvoid Worker::record_null_move'),
    ('stale_alias_after_null_move', 'src/search.cpp',
     '    (ss + 1)->runtime_psqt.valid = false;\n#if FORGE_NNUE_LAZY_ACC\n    (ss + 1)->accumulator_owner = nullptr;\n'
     '#endif\n}\n\nint Worker::corrected_eval',
     '    (ss + 1)->runtime_psqt.valid = false;\n#if FORGE_NNUE_LAZY_ACC\n#endif\n}\n\nint Worker::corrected_eval'),
    ('update_from_physical_parent', 'src/search.cpp',
     'nnue::update(owner->accumulator, child->accumulator, child->dirty);',
     'nnue::update((child - 1)->accumulator, child->accumulator, child->dirty);'),
    ('alias_across_real_edges', 'src/search.cpp',
     'if (child->dirty.count == 0) {',
     'if (child->dirty.count >= 0) {'),
    ('local_psqt_at_alias', 'src/search.cpp',
     'evaluator_.evaluate_runtime(board, owner->runtime_psqt) + network',
     'evaluator_.evaluate_runtime(board, ss->runtime_psqt) + network'),
    ('owner_not_validated', 'src/search.cpp',
     'return owner != nullptr && owner < frame && owner->accumulator.valid\n'
     '        && owner->accumulator_owner == nullptr ? owner : nullptr;',
     'return owner;'),
    ('option_not_wired', 'src/search.cpp',
     'shared_.lazy_acc_enabled = lazy_acc::requested.load(std::memory_order_relaxed)',
     'shared_.lazy_acc_enabled = false && lazy_acc::requested.load(std::memory_order_relaxed)'),
]


def run(cmd, cwd, log):
    with open(log, 'w', encoding='utf-8', newline='\n') as f:
        return subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT).returncode


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    caught = 0
    for name, rel, old, new in MUTANTS:
        d = OUT / name
        if d.exists():
            sys.exit('refusing to reuse %s (no deletes on this PC; pick a new out_dir)' % d)
        for sub in ('src', 'include', 'tests'):
            shutil.copytree(TREE / sub, d / sub)
        shutil.copy2(TREE / 'opus_round1/sol_S12/followup_nullalias/alias_stats.py', d / 'alias_stats.py')
        f = d / rel
        text = f.read_bytes().decode('utf-8')
        n = text.count(old)
        if n != 1:
            sys.exit('%s: pattern occurs %d times' % (name, n))
        f.write_bytes(text.replace(old, new).encode('utf-8'))
        if name == 'option_not_wired':
            rc = run([GPP, *FLAGS, '-Iinclude', *CORE, 'src/uci.cpp', '-o', 'forge_mut.exe'], d, d / 'build.log')
            if rc != 0:
                print('%-30s BUILD FAILED (see %s)' % (name, d / 'build.log'), flush=True)
                continue
            rc = run([sys.executable, '-I', '-B', 'alias_stats.py', str(d / 'forge_mut.exe'), '13'], d, d / 'run.log')
            detector = 'alias_stats.py d13'
            logs = [d / 'run.log']
        else:
            # core objects once, then each test linked against them
            rc = run([GPP, *FLAGS, '-Iinclude', '-c', *CORE], d, d / 'build_core.log')
            if rc != 0:
                print('%-30s BUILD FAILED (see %s)' % (name, d / 'build_core.log'), flush=True)
                continue
            objs = [Path(c).with_suffix('.o').name for c in CORE]
            rc, detector, logs = 0, [], []
            for i, (label, test) in enumerate(TESTS):
                exe, log = 'test%d_mut.exe' % i, d / ('run%d.log' % i)
                if run([GPP, *FLAGS, '-Iinclude', test, *objs, '-o', exe], d, d / ('build%d.log' % i)) != 0:
                    print('%-30s BUILD FAILED (see %s)' % (name, d / ('build%d.log' % i)), flush=True)
                    rc = None
                    break
                r = run([str(d / exe)], d, log)
                logs.append(log)
                if r != 0:
                    rc = r
                    detector.append(label)
            if rc is None:
                continue
            detector = ' + '.join(detector) or 'neither test'
        fails = [ln for log in logs for ln in log.read_text(encoding='utf-8', errors='replace').splitlines()
                 if ln.startswith('FAIL') or 'no alias activity' in ln or ln.startswith('CHECK')]
        verdict = 'CAUGHT' if rc != 0 else 'SURVIVED'
        caught += rc != 0
        print('%-30s %-8s by %s (exit %d); first lines: %s' % (name, verdict, detector, rc, ' | '.join(fails[:3])),
              flush=True)
    print('CAUGHT %d/%d' % (caught, len(MUTANTS)))


if __name__ == '__main__':
    main()
