#!/usr/bin/env python3
"""port_sf26split.py - R13 P3 step 1: split Sf26Bundle bits 2, 4, 8 into their own options (lock tree + sf26bundle_al1.patch).

New tunables (all default 0 = off; Sf26Bundle keeps working unchanged):
  Sf26NmpPrior     (0/1)  = bit 2: NMP static-eval guard relief per earlier sibling null fail high
  Sf26LmrGap       (0/1)  = bit 4: one extra LMR ply for quiet moves whose static eval is Sf26LmrAlphaGap below alpha
  Sf26MulticutCorr (0/1)  = bit 8: singular multicut teaches the correction history
  Sf26NmpPriorCap  (1-8, default 3) = bit 2's count cap (the original constant 3), a margin tunable like the others
Each switch is ORed with its bit, so Sf26NmpPrior=1 searches exactly like Sf26Bundle=2 (and so on); every margin keeps
its original default. Every anchor must match exactly once; LF bytes.
usage: python -I -B port_sf26split.py <scratch repo>
"""
import sys

root = sys.argv[1]


def edit(rel, pairs):
    p = f'{root}/{rel}'
    s = open(p, 'rb').read().decode()
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, f'{rel}: anchor found {n}x: {old[:90]!r}'
        s = s.replace(old, new)
    open(p, 'wb').write(s.encode())


edit('include/forge/search.hpp', [
    ('extern int Sf26LmrAlphaGap;        // bit 4: static eval this far below alpha adds one LMR ply to quiet moves\n',
     'extern int Sf26LmrAlphaGap;        // bit 4: static eval this far below alpha adds one LMR ply to quiet moves\n'
     '// R13 P3: bits 2 / 4 / 8 as their own switches (0 = off; each is ORed with its Sf26Bundle bit) + bit 2\'s cap.\n'
     'extern int Sf26NmpPrior;           // = Sf26Bundle bit 2\n'
     'extern int Sf26LmrGap;             // = Sf26Bundle bit 4\n'
     'extern int Sf26MulticutCorr;       // = Sf26Bundle bit 8\n'
     'extern int Sf26NmpPriorCap;        // bit 2: earlier sibling null fail highs counted, at most this many (original 3)\n'),
])
edit('src/search.cpp', [
    ('int Sf26LmrAlphaGap = 260;\n',
     'int Sf26LmrAlphaGap = 260;\nint Sf26NmpPrior = 0;\nint Sf26LmrGap = 0;\nint Sf26MulticutCorr = 0;\nint Sf26NmpPriorCap = 3;\n'),
    ('        {"Sf26NmpPriorBonus", &Sf26NmpPriorBonus, 0, 100},       {"Sf26LmrAlphaGap", &Sf26LmrAlphaGap, 50, 1000},\n',
     '        {"Sf26NmpPriorBonus", &Sf26NmpPriorBonus, 0, 100},       {"Sf26LmrAlphaGap", &Sf26LmrAlphaGap, 50, 1000},\n'
     '        {"Sf26NmpPrior", &Sf26NmpPrior, 0, 1},                   {"Sf26LmrGap", &Sf26LmrGap, 0, 1},\n'
     '        {"Sf26MulticutCorr", &Sf26MulticutCorr, 0, 1},           {"Sf26NmpPriorCap", &Sf26NmpPriorCap, 1, 8},\n'),
    ('        const int sf26_nmp_bonus = (tune::Sf26Bundle & 2) != 0 ? std::min(ss->null_cut_count, 3) * tune::Sf26NmpPriorBonus : 0;\n',
     '        const int sf26_nmp_bonus = ((tune::Sf26Bundle & 2) != 0 || tune::Sf26NmpPrior != 0)\n'
     '                                       ? std::min(ss->null_cut_count, tune::Sf26NmpPriorCap) * tune::Sf26NmpPriorBonus : 0;\n'),
    ('                if ((tune::Sf26Bundle & 8) != 0 && !in_check && !is_mate_score(singular_beta) &&\n',
     '                if (((tune::Sf26Bundle & 8) != 0 || tune::Sf26MulticutCorr != 0) && !in_check && !is_mate_score(singular_beta) &&\n'),
    ('            if ((tune::Sf26Bundle & 4) != 0 && quiet && !in_check && ss->static_eval + tune::Sf26LmrAlphaGap < alpha) r += 1;\n',
     '            if (((tune::Sf26Bundle & 4) != 0 || tune::Sf26LmrGap != 0) && quiet && !in_check &&\n'
     '                ss->static_eval + tune::Sf26LmrAlphaGap < alpha) r += 1;\n'),
])
print('port_sf26split: all anchors applied')
