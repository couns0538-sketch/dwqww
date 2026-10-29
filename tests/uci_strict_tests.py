#!/usr/bin/env python3
"""B4: advertised tunables and truthful UCI option diagnostics on the real engine."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from uci_regression import Engine


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('engine', type=Path)
    ap.add_argument('--log', type=Path, required=True)
    ap.add_argument('--debug-hooks', action='store_true')
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    # R3 F4 explicitly narrows the old B4 policy to fields owned by BundlePreset.
    owned = {'CorrHistPlus', 'HistRework', 'CuckooRep', 'CorrHistV2', 'LmrTableV2', 'TtPruneV2', 'SingularV2'}
    source = (root / 'src/search/tune.inc').read_text()
    defaults = dict(re.findall(r'^int (\w+) = (-?\d+);', source, re.M))
    registry = re.findall(r'\{"(\w+)", &(\w+), (-?\d+), (-?\d+)\}', source)
    if not registry or len({r[0] for r in registry}) != len(registry):
        raise RuntimeError('tunable registry is empty or ambiguous')
    e = Engine(args.engine)
    checks, failures = 0, []
    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)
            print('FAIL:', label)
    def command(text):
        e.send(text)
        e.send('isready')
        return e.until(lambda s: s == 'readyok', 30)[:-1]
    def option(name, value, changed=None):
        out = command(f'setoption name {name}' + ('' if value is None else f' value {value}'))
        if changed is not None:
            overrides = [s for s in out if s.startswith('info string override ')]
            expected = [f'info string override {name} after preset'] if changed else []
            check(overrides == expected, f'{name}={value}: override {overrides} == {expected}')
        return out
    try:
        e.send('uci')
        uci = e.until(lambda s: s == 'uciok', 30)
        names = [m.group(1) for s in uci if (m := re.match(r'^option name (.+?) type ', s))]
        check(len(names) == len(set(names)), 'no duplicate UCI options')
        for name, variable, low, high in registry:
            want = f'option name {name} type spin default {defaults[variable]} min {low} max {high}'
            check(uci.count(want) == 1, 'registered tunable metadata: ' + name)
        hook = 'option name DebugSearchDelayMs type spin default 0 min 0 max 10000'
        check((hook in uci) == args.debug_hooks, 'debug hook advertised exactly when compiled')
        out = option('NoSuchOption', '5')
        check(out == ['info string unknown option NoSuchOption'], 'unknown name is reported exactly')
        for text in ('setoption', 'setoption name', 'setoption foo bar'):
            check(command(text) == ['info string unknown option'], 'empty unknown name: ' + text)
        option('RazorDepth', '3', False)  # No preset yet.
        option('RazorDepth', defaults['RazorDepth'], False)
        option('BundlePreset', 'B1', False)
        option('CorrHistPlus', '4', True)
        option('CorrHistPlus', '4', False)
        out = option('CorrHistPlus', 'abc', False)
        check('info string invalid value for option CorrHistPlus' in out, 'invalid value is still rejected')
        out = option('CorrHistV2', 'true', False)
        check(any('CorrHistV2 refused' in s for s in out), 'exclusive option remains refused')
        for name, new, same, reset in (
            ('Hash', '16', '16', '32'), ('Threads', '2', '2', '1'),
            ('Move Overhead', '20', '20', '10'), ('RazorDepth', '3', '3', defaults['RazorDepth']),
            ('Ponder', 'true', 'true', 'false'), ('UseNNUE', 'false', 'false', 'true'),
            ('Book Depth', '20', '20', '30'), ('Book Variety', '10', '10', '30'),
            ('SmpBestThread', 'true', 'true', 'false'), ('SyzygyProbeDepth', '2', '2', '1'),
            ('Syzygy50MoveRule', 'false', 'false', 'true'), ('HardDeadline', '1', '1', '0'),
            ('CorrMargins', '1', '1', '0'), ('CorrExt', '1', '1', '0'),
            ('MaterialKeyTable', 'true', 'true', 'false'), ('NetScale', '101', '101', '100'),
            ('IntendedThreefold', 'true', 'true', 'false'), ('LmrTableV2', 'true', 'true', 'false'),
        ):
            option(name, new, name in owned); option(name, same, False); option(name, reset, name in owned)
        option('Hash', '0', False)
        option('Hash', '-5', False)  # Both clamp to one; requested text is not an actual change.
        option('Hash', '32', False)
        option('CuckooRep', 'false', True)
        option('CuckooRep', 'false', False)
        option('Book File', '/definitely/missing/astra2_book.bin', False)
        option('Clear Hash', None, False)
        out = option('NoSuchOption', '6', False)
        check(out == ['info string unknown option NoSuchOption'], 'unknown after preset is not an override')
        option('BundlePreset', 'invalid', False)
        option('HistRework', '3', True)  # Invalid preset must not disarm tracking.
        if args.debug_hooks:
            option('DebugSearchDelayMs', '1', False)
            option('DebugSearchDelayMs', '1', False)
            option('DebugSearchDelayMs', '0', False)
            out = option('DebugSearchDelayMs', 'abc', False)
            check('info string invalid value for option DebugSearchDelayMs' in out, 'invalid debug option rejected')
        option('BundlePreset', 'OFF', False)
        option('RazorDepth', '3', False)
        option('RazorDepth', defaults['RazorDepth'], False)
        option('CorrHistPlus', '4', False)
        option('CorrHistPlus', '0', False)
        e.send('position startpos'); e.send('go depth 3')
        answer = e.until(lambda s: s.startswith('bestmove '), 30)
        check(bool(re.fullmatch(r'bestmove [a-h][1-8][a-h][1-8][qrbn]?(?: ponder .+)?', answer[-1])), 'search still answers')
    except Exception as exc:
        check(False, f'{type(exc).__name__}: {exc}')
    finally:
        try: e.close()
        except Exception as exc: check(False, f'close: {exc}')
        args.log.parent.mkdir(parents=True, exist_ok=True)
        args.log.write_text('\n'.join(e.transcript) + '\n')
    print(json.dumps({'status': 'PASS' if not failures else 'FAIL', 'checks': checks,
                      'registry_count': len(registry), 'failures': failures}, indent=2))
    return bool(failures)

if __name__ == '__main__':
    raise SystemExit(main())
