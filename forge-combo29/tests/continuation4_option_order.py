#!/usr/bin/env python3
"""Preserve legacy UCI order; resolve and change tunables strictly by name."""
import re
import sys
from equivalence_screen import Engine

EXPERIMENT = 'Continuation4Weight'


def snapshot(engine):
    engine.send('uci')
    lines = engine.until('uciok')
    options = {}
    for line in lines:
        match = re.fullmatch(r'option name (.+?) type (.+)', line)
        if match:
            name, declaration = match.groups()
            assert name not in options, ('duplicate option', name)
            options[name] = declaration
    return options


def check(baseline_path, experiment_path):
    baseline, experiment = [Engine(path, True) for path in [baseline_path, experiment_path]]
    try:
        original = snapshot(baseline)
        current = snapshot(experiment)
        assert EXPERIMENT not in original
        assert current[EXPERIMENT] == 'spin default 0 min 0 max 100'
        assert {name: value for name, value in current.items() if name != EXPERIMENT} == original
        # This sequence check is deliberately about advertisement order, not lookup.
        assert list(current) == list(original) + [EXPERIMENT], 'experiment must append after every existing option, including Clear Hash'
        named_changes = 0
        # Target tunables by their actual names, never by an ordinal/table index.
        for name, declaration in list(current.items()):
            if name in {'Hash', 'Threads', 'Move Overhead', 'Book Depth', 'Book Variety'}:
                continue
            match = re.fullmatch(r'spin default (-?\d+) min (-?\d+) max (-?\d+)', declaration)
            if not match:
                continue
            default, minimum, maximum = map(int, match.groups())
            replacement = minimum if minimum != default else maximum
            experiment.send(f'setoption name {name} value {replacement}')
            changed = snapshot(experiment)
            expected = dict(current)
            expected[name] = f'spin default {replacement} min {minimum} max {maximum}'
            assert changed == expected, ('name-based lookup changed another option', name)
            experiment.send(f'setoption name {name} value {default}')
            assert snapshot(experiment) == current, ('name-based restore', name)
            named_changes += 1
        print(f'PASS: legacy advertisement order preserved; experiment appended; {named_changes} tunables changed/restored by name')
    finally:
        baseline.close()
        experiment.close()


if __name__ == '__main__':
    check(*sys.argv[1:])
