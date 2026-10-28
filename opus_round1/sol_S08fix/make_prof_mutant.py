#!/usr/bin/env python3
"""Planted bugs for the S08-2 tests, applied to a COPY of the source tree (one exact replacement each; the
pattern must occur once). The mutant build must make tests/prof_tests.cpp fail.
  merge_main_only : Searcher::profile_snapshot() returns only the main worker's bank (no merge of the helpers)
  shared_bank     : every worker counts into the main worker's bank (the pre-S08-2 sharing, now without atomics)
usage: make_prof_mutant.py <copied_src_root> <merge_main_only|shared_bank>"""
from pathlib import Path
import sys

MUTANTS = {
    'merge_main_only': ('src/search.cpp',
                        '    for (const auto& worker : workers_) prof::merge(total, worker->profile_bank().snapshot_quiescent());',
                        '    prof::merge(total, workers_.front()->profile_bank().snapshot_quiescent());'),
    'shared_bank': ('src/search.cpp',
                    '    prof::Scope profile_scope(shared_.profile_active ? &profile_bank_ : nullptr);',
                    '    prof::Scope profile_scope(shared_.profile_active ? '
                    'const_cast<prof::Bank*>(&(*all.front()).profile_bank()) : nullptr);'),
}

root, name = Path(sys.argv[1]), sys.argv[2]
rel, old, new = MUTANTS[name]
path = root / rel
text = path.read_text(encoding='utf-8')
if text.count(old) != 1:
    raise SystemExit(f'{name}: pattern found {text.count(old)} times, expected 1')
path.write_text(text.replace(old, new), encoding='utf-8')
print(f'mutant {name} written to {path}')
