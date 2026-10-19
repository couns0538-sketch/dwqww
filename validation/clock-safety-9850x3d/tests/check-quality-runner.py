#!/usr/bin/env python3
"""Regression checks for accepting native statistical output; launches no engines."""
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode = True
runner = Path(__file__).resolve().parents[1] / 'run-quality-sprt.py'
spec = importlib.util.spec_from_file_location('quality_runner', runner)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for token in ('nan', 'inf', '-inf', 'bogus'):
    fixture = f'LLR: 0.50\nLLR: {token}\nSPRT completed - H1 was accepted'
    try:
        module.native_acceptance(fixture)
    except RuntimeError:
        pass
    else:
        raise AssertionError(f'accepted invalid final LLR {token}')
for label, value in (('H1', '2.95'), ('H0', '-2.95')):
    assert module.native_acceptance(f'LLR: {value} (95%)\nSPRT completed - {label} was accepted') == label + '_accepted'
assert module.native_acceptance('LLR: 1.5') is None
for fixture in ('SPRT completed - H1 was accepted',
                'LLR: 3\nSPRT completed - H1 was accepted\nSPRT completed - H0 was accepted'):
    try:
        module.native_acceptance(fixture)
    except RuntimeError:
        pass
    else:
        raise AssertionError('accepted missing likelihood or ambiguous native decision')
print('Native decision audit regression checks passed')
