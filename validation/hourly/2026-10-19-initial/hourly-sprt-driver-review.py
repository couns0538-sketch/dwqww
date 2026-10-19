#!/usr/bin/env python3
"""Bounded validator review; does not launch any engine or match."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'tools/match'))
import run_hourly_sprt as driver
from pgn_stats import games

checks = []
def ok(name, fn):
    fn()
    checks.append({'name': name, 'pass': True})
def equal(a, b):
    assert a == b, (a, b)
def rejects(name, fn):
    try:
        fn()
    except (RuntimeError, ValueError, KeyError):
        checks.append({'name': name, 'pass': True})
    else:
        raise AssertionError(name + ': invalid input accepted')

fixture = REPO / driver.RUN / 'matches/resume-aa'
original = fixture / 'resumed/checkpoint-0004.json'
original_hash = driver.digest(original)
cfg = json.loads(original.read_text())
out = fixture / 'resumed'
selected = fixture / 'selected.epd'
pgn = out / 'games.pgn'
actual = driver.verify_outcomes(pgn, cfg, selected, 4, False)
ok('Real naturally completed A/A prefix: 4 pairs / 8 games', lambda: equal((actual['complete_pairs'], actual['all_pgn_games']), (4, 8)))
ok('Native six-bin scoreboard reconciles real PGN', lambda: equal(actual['penta6']['WL'], 4))

# Adapt only protocol metadata, without claiming these fixed-node A/A games
# constitute a strength test. This checks the observed native JSON schema.
verified = copy.deepcopy(cfg)
verified.update(seed=20261019, games=2, concurrency=6, sprt=driver.SPRT)
for engine, kind in zip(verified['engines'], ('candidate', 'baseline')):
    engine['cmd'] = str(REPO / driver.INPUTS[kind][0])
    engine['limit']['nodes'] = 0
ok('Observed native JSON schema matches frozen strength protocol',
   lambda: driver.check_config(verified, {}, {REPO}, {fixture, out}))
for name, mutate in (
    ('Changed clock rejected', lambda c: c['engines'][0]['limit']['tc'].update(increment=101)),
    ('Changed binary path rejected', lambda c: c['engines'][0].update(cmd='/wrong/binary')),
    ('Changed engine count rejected', lambda c: c['engines'].append(copy.deepcopy(c['engines'][0]))),
    ('Changed SPRT model rejected', lambda c: c['sprt'].update(model='normalized')),
    ('Changed opening start rejected', lambda c: c['opening'].update(start=2)),
    ('Enabled adjudication rejected', lambda c: c['draw'].update(enabled=True)),
    ('Changed option value rejected', lambda c: c['engines'][0]['options'][0].__setitem__(1,'16')),
):
    changed = copy.deepcopy(verified)
    mutate(changed)
    rejects(name, lambda: driver.check_config(changed, {}, {REPO}, {fixture, out}))

bad_cfg = copy.deepcopy(cfg)
bad_cfg['stats']['Candidate vs Baseline']['wins'] += 1
rejects('Native WDL mismatch rejected', lambda: driver.verify_outcomes(pgn, bad_cfg, selected, 4, False))
bad_cfg = copy.deepcopy(cfg)
bad_cfg['stats']['Candidate vs Baseline']['penta_WL'] -= 1
rejects('Native pentanomial mismatch rejected', lambda: driver.verify_outcomes(pgn, bad_cfg, selected, 4, False))

ok('Final LLR, not earlier LLR, is returned', lambda: equal(driver.native_sprt_status('LLR: 0.00 (0%)\nLLR: 0.42 (1%)\n'), (None, .42)))
ok('Pinned H1 terminal marker recognized', lambda: equal(driver.native_sprt_status('LLR: 3.01 (100%)\nSPRT (0.00, 5.00) completed - H1 was accepted\n'), ('H1', 3.01)))
ok('ANSI-colored H0 terminal marker recognized', lambda: equal(driver.native_sprt_status('\x1b[31mLLR: -3.01 (100%)\x1b[0m\nSPRT (0.00, 5.00) completed - H0 was accepted\n'), ('H0', -3.01)))
for final in ('nan', '-nan', 'inf', '-inf'):
    rejects('Nonfinite final LLR rejected: ' + final, lambda: driver.native_sprt_status('LLR: 0.0 (0%)\nLLR: ' + final + ' (0%)\n'))
rejects('Missing LLR rejected', lambda: driver.native_sprt_status('Finished match'))
rejects('Conflicting terminal markers rejected', lambda: driver.native_sprt_status('LLR: 3.0 (100%)\nSPRT () completed - H0 was accepted\nSPRT () completed - H1 was accepted'))

ok('Original completed checkpoint stayed immutable', lambda: equal(driver.digest(original), original_hash))
result = {'status': 'pass', 'checks': checks, 'check_count': len(checks),
          'driver_sha256': driver.digest(REPO / 'tools/match/run_hourly_sprt.py'),
          'fixture_checkpoint_sha256': original_hash, 'strength_games_launched': 0,
          'scope': 'Real native A/A fixture schema/PGN bookkeeping plus synthetic invalid-input and native-output checks; no separate legality or Elo implementation.'}
print(json.dumps(result, indent=2))
