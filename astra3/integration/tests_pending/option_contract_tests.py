#!/usr/bin/env python3
"""A1 native advertised-option / active-echo contract; no bench or strength claim.

Reuses tools/uci_regression.py's Engine response/deadline protocol and the repo's
FORGENN2 writer. See COVERAGE.md for explicit exclusions and evidence limits.
Every invocation preserves fresh, original binary stdin/stdout/stderr streams.
"""
from __future__ import annotations

import argparse
from array import array
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time

# This file lives at <repo>/astra3/integration/tests_pending/. No installed module
# or external chess implementation supplies the driver or fixtures.
ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True  # Imports must not write outside this owned folder.
sys.path.insert(0, str(ROOT / 'tools'))
from uci_regression import Engine  # noqa: E402


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    # Exclusive creation protects partial evidence from an earlier run.
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


class RawEngine(Engine):
    """Engine's protocol waits with byte-exact separate stream capture.

    Reader threads flush original bytes before decoding. A decoding failure is
    an error, never replacement text. Only this instance's own child is stopped.
    """
    def __init__(self, executable: Path, directory: Path):
        directory.mkdir()
        self.directory = directory
        self.lines = queue.Queue()
        self.transcript = []
        self.reader_errors = []
        self.stdin_log = (directory / 'stdin.bin').open('xb')
        self.stdout_log = (directory / 'stdout.bin').open('xb')
        self.stderr_log = (directory / 'stderr.bin').open('xb')
        self.process = subprocess.Popen(
            [str(executable.resolve())], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        self.reader = threading.Thread(target=self._read_raw, daemon=True)
        self.stderr_reader = threading.Thread(target=self._read_stderr, daemon=True)
        self.reader.start()
        self.stderr_reader.start()
        self.closed = False

    def _read_raw(self):
        try:
            for raw in iter(self.process.stdout.readline, b''):
                self.stdout_log.write(raw)
                self.stdout_log.flush()
                line = raw.decode('utf-8').rstrip('\r\n')
                self.transcript.append('< ' + line)
                self.lines.put(line)
        except Exception as error:
            self.reader_errors.append(repr(error))
        finally:
            self.lines.put(None)

    def _read_stderr(self):
        try:
            for raw in iter(lambda: self.process.stderr.read(65536), b''):
                self.stderr_log.write(raw)
                self.stderr_log.flush()
        except Exception as error:
            self.reader_errors.append(repr(error))

    def send(self, command: str):
        raw = (command + '\n').encode('utf-8')
        self.stdin_log.write(raw)
        self.stdin_log.flush()
        self.transcript.append('> ' + command)
        self.process.stdin.write(raw)
        self.process.stdin.flush()

    def command(self, text: str):
        self.send(text)
        self.send('isready')
        return self.until(lambda s: s == 'readyok', 15)[:-1]

    def option(self, name: str, value: str | None):
        return self.command('setoption name ' + name +
                            ('' if value is None else ' value ' + value))

    def handshake(self):
        self.send('uci')
        return self.until(lambda s: s == 'uciok', 15)

    def short_search(self):
        self.send('position startpos')
        self.send('go nodes 1 searchmoves e2e4')
        lines = self.until(lambda s: s.startswith('bestmove '), 15)
        require(lines[-1].split()[1] == 'e2e4', 'restricted search must answer e2e4')
        self.send('isready')
        tail = self.until(lambda s: s == 'readyok', 15)
        require(not any(s.startswith('bestmove ') for s in tail), 'duplicate bestmove')
        return lines + tail

    def drain_exit(self, timeout=15):
        deadline = time.monotonic() + timeout
        out = []
        while True:
            remaining = deadline - time.monotonic()
            require(remaining > 0, 'child did not exit before deadline')
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty as error:
                raise AssertionError('child did not exit before deadline') from error
            if line is None:
                return out
            out.append(line)

    def close(self, allowed_codes=(0,)):
        if self.closed:
            return
        self.closed = True
        cleanup_error = None
        try:
            if self.process.poll() is None:
                try:
                    self.send('quit')
                except BrokenPipeError:
                    pass
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()  # Our own subprocess only.
                    self.process.wait(timeout=5)
                    cleanup_error = 'own child ignored quit; killed after deadline'
            self.reader.join(timeout=5)
            self.stderr_reader.join(timeout=5)
            if self.reader.is_alive() or self.stderr_reader.is_alive():
                cleanup_error = 'capture reader did not finish'
        finally:
            for stream in (self.stdin_log, self.stdout_log, self.stderr_log):
                stream.close()
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                stream.close()
            write_json(self.directory / 'exit.json', {
                'returncode': self.process.returncode, 'allowed_codes': list(allowed_codes),
                'reader_errors': self.reader_errors, 'cleanup_error': cleanup_error})
        require(cleanup_error is None, str(cleanup_error))
        require(not self.reader_errors, 'raw-capture error: ' + repr(self.reader_errors))
        require(self.process.returncode in allowed_codes,
                f'child exit {self.process.returncode}, expected {allowed_codes}')


@dataclass(frozen=True)
class Option:
    name: str
    kind: str
    default: str | None = None
    minimum: int | None = None
    maximum: int | None = None
    variants: tuple[str, ...] = ()

    def nondefault(self) -> str:
        if self.kind == 'check':
            return 'false' if self.default == 'true' else 'true'
        if self.kind == 'spin':
            n = int(self.default)
            if n < self.maximum:
                return str(n + 1)
            require(n > self.minimum, self.name + ' has no legal nondefault value')
            return str(n - 1)
        raise AssertionError(self.name + ': requires dedicated fixture or whitelist')


def parse_options(lines: list[str]) -> dict[str, Option]:
    options = {}
    for line in lines:
        if not line.startswith('option '):
            continue
        match = re.fullmatch(r'option name (.+?) type (check|spin|combo|string|button)(.*)', line)
        require(match is not None, 'malformed advertisement: ' + line)
        name, kind, tail = match.groups()
        require(name not in options, 'duplicate advertised option: ' + name)
        if kind == 'button':
            require(tail == '', 'unexpected button metadata: ' + line)
            option = Option(name, kind)
        elif kind == 'check':
            m = re.fullmatch(r' default (true|false)', tail)
            require(m is not None, 'invalid check metadata: ' + line)
            option = Option(name, kind, m.group(1))
        elif kind == 'spin':
            m = re.fullmatch(r' default (-?\d+) min (-?\d+) max (-?\d+)', tail)
            require(m is not None, 'invalid spin metadata: ' + line)
            default, minimum, maximum = map(int, m.groups())
            require(minimum <= default <= maximum, 'invalid spin range: ' + line)
            option = Option(name, kind, str(default), minimum, maximum)
        elif kind == 'combo':
            require(tail.startswith(' default '), 'missing combo default: ' + line)
            pieces = tail[len(' default '):].split(' var ')
            require(len(pieces) >= 2 and pieces[0] in pieces[1:], 'invalid combo: ' + line)
            require(len(pieces[1:]) == len(set(pieces[1:])), 'duplicate combo choices: ' + line)
            option = Option(name, kind, pieces[0], variants=tuple(pieces[1:]))
        else:
            require(tail.startswith(' default '), 'missing string default: ' + line)
            option = Option(name, kind, tail[len(' default '):])
        options[name] = option
    require(bool(options), 'no UCI options advertised')
    return options


# These names cannot truthfully represent active search-algorithm overrides.
# Exact names only: a new advertised option must be covered, not silently exempted.
WHITELIST = {
    'Hash': 'resource allocation; active search-algorithm line intentionally excludes it',
    'Threads': 'worker resource count; independent SMP behavior flags are tested',
    'Move Overhead': 'protocol clock overhead, outside the active-search-options contract',
    'Ponder': 'protocol capability; go ponder behavior is outside this echo test',
    'OwnBook': 'opening-book selection, disabled for these search probes',
    'Book File': 'external opening-book path; no book dataset is supplied',
    'Book Depth': 'opening-book lookup control, not an active search option',
    'Book Variety': 'opening-book selection control, not an active search option',
    'Clear Hash': 'stateless button: there is no nondefault value to echo',
    'Profile': 'build-time optional instrumentation, not search behavior',
    'DebugSearchDelayMs': 'build-time optional test scheduling instrumentation',
    'BundlePreset': 'macro; all advertised variants are checked by expanded-option assertions',
}
OWNED = ('CorrHistPlus', 'HistRework', 'CuckooRep', 'CorrHistV2',
         'LmrTableV2', 'TtPruneV2', 'SingularV2')
PRESETS = {
    'OFF': {},
    'B1': {'CorrHistPlus': '1', 'HistRework': '2', 'CuckooRep': 'true', 'TtPruneV2': 'true'},
    'B2': {'CorrHistV2': 'true', 'LmrTableV2': 'true', 'CuckooRep': 'true', 'TtPruneV2': 'true'},
    'B3': {'CorrHistPlus': '1', 'LmrTableV2': 'true', 'CuckooRep': 'true', 'TtPruneV2': 'true'},
    'B4': {'CorrHistV2': 'true', 'HistRework': '2', 'CuckooRep': 'true', 'TtPruneV2': 'true'},
    'N1': {'CorrHistPlus': '4', 'SingularV2': '1'},
}
NEW_OPTIONS = {'SmpV2': ('check', 'false'), 'TmSoftHardClamp': ('check', 'false'),
               'SingularV2': ('spin', '0')}
NNUE_OPTIONS = {'NNUEFile', 'NNUEKingBuckets', 'NNUEOutputBuckets',
                'NNUEThreats', 'NNUEPawnPairs', 'PureNnue'}


class Suite:
    def __init__(self, args):
        self.args = args
        args.output_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        self.run_dir = Path(tempfile.mkdtemp(prefix='option-contract-' + stamp + '-',
                                            dir=args.output_root.resolve()))
        self.binary_sha = sha256(args.engine)
        self.cases = []
        self.options = {}
        self.coverage = {}
        self.fixtures = {}
        self.owned_children = []
        print('Evidence:', self.run_dir, flush=True)
        write_json(self.run_dir / 'invocation.json', {
            'argv': sys.argv, 'engine': str(args.engine.resolve()), 'engine_sha256': self.binary_sha,
            'source_root': str(ROOT), 'hidden_size': args.hidden, 'start_utc': stamp,
            'driver_sha256': sha256(Path(__file__)),
            'reused_files': {str(p.relative_to(ROOT)): sha256(p) for p in (
                ROOT / 'tools/uci_regression.py', ROOT / 'tools/nnue/forge_nnue_v2.py')}})

    def run_case(self, label, function):
        self.owned_children = []
        started = time.monotonic()
        errors = []
        try:
            function()
        except Exception as error:
            errors.append(type(error).__name__ + ': ' + str(error))
        finally:
            for engine, allowed in self.owned_children:
                try:
                    engine.close(allowed)
                except Exception as error:
                    errors.append('cleanup ' + type(error).__name__ + ': ' + str(error))
        result = {'case': label, 'status': 'FAIL' if errors else 'PASS', 'errors': errors,
                  'seconds': time.monotonic() - started}
        self.cases.append(result)
        with (self.run_dir / 'cases.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(result, sort_keys=True) + '\n')
            stream.flush()
        print(result['status'] + ': ' + label + (': ' + '; '.join(errors) if errors else ''), flush=True)
        return not errors

    def engine(self, *, allowed=(0,)) -> RawEngine:
        directory = self.run_dir / f'case-{len(self.cases):03d}-child-{len(self.owned_children):02d}'
        engine = RawEngine(self.args.engine, directory)
        self.owned_children.append((engine, allowed))
        engine.handshake()
        engine.option('Hash', '16')
        engine.option('Threads', '1')
        engine.option('OwnBook', 'false')
        return engine

    def active(self, lines) -> dict[str, str]:
        records = [line[len('info string active: '):] for line in lines
                   if line.startswith('info string active: ')]
        require(len(records) <= 1, 'more than one active line in one search: ' + repr(records))
        if not records:
            return {}
        text = records[0]
        pattern = re.compile(r'(?<!\S)(' + '|'.join(re.escape(x) for x in
                             sorted(self.options, key=len, reverse=True)) + r')=')
        matches = list(pattern.finditer(text))
        require(matches and matches[0].start() == 0, 'unparseable active line: ' + text)
        values = {}
        for i, match in enumerate(matches):
            name = match.group(1)
            require(name not in values, 'duplicate active field: ' + name)
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            values[name] = text[match.end():end].rstrip()
        return values

    def expected_active(self, engine, expected):
        got = self.active(engine.short_search())
        require(got == expected, f'active fields {got!r} != {expected!r}')

    def discover(self):
        engine = self.engine()
        self.options = parse_options(engine.handshake())
        for name, (kind, default) in NEW_OPTIONS.items():
            require(name in self.options, 'required integrated option missing: ' + name)
            option = self.options[name]
            require((option.kind, option.default) == (kind, default), 'new option metadata: ' + name)
        require((self.options['SingularV2'].minimum, self.options['SingularV2'].maximum) == (0, 1),
                'SingularV2 must remain spin 0..1')
        require('BundlePreset' in self.options and set(self.options['BundlePreset'].variants) == set(PRESETS),
                'BundlePreset variants require an explicit expansion assertion')
        for name, option in self.options.items():
            if name in WHITELIST:
                classification = {'kind': 'explicit-whitelist', 'reason': WHITELIST[name]}
            elif name == 'SyzygyPath':
                classification = {'kind': 'external-path-failure-fixture',
                                  'reason': 'Missing-path truth tested; actual table load UNVERIFIED (no TB files)'}
            elif name in NNUE_OPTIONS:
                classification = {'kind': 'fixture-activation-and-reset'}
            else:
                require(option.kind in ('spin', 'check'), 'unclassified option: ' + name)
                classification = {'kind': 'nondefault-activation-and-reset'}
            self.coverage[name] = classification
        write_json(self.run_dir / 'advertisements.json', {k: vars(v) for k, v in self.options.items()})
        write_json(self.run_dir / 'coverage.json', self.coverage)
        self.expected_active(engine, {})

    def generate_fixtures(self):
        spec = importlib.util.spec_from_file_location('forge_nnue_v2_contract',
                                                     ROOT / 'tools/nnue/forge_nnue_v2.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        directory = self.run_dir / 'fixture nets'
        directory.mkdir()
        hidden = self.args.hidden
        for name, residual, feature_set in (
            ('residual', True, 0), ('standalone', False, 0),
            ('threats', True, module.FEATURE_SET_THREATS),
            ('pawnpairs', True, module.FEATURE_SET_PAWN_PAIRS)):
            path = directory / (name + '.fnn2')
            kwargs = {}
            if feature_set & module.FEATURE_SET_THREATS:
                kwargs['wt'] = array('h', [0]) * (module.THREAT_FEATURES * hidden)
            if feature_set & module.FEATURE_SET_PAWN_PAIRS:
                kwargs['wp'] = array('h', [0]) * (module.PAWN_PAIR_FEATURES * hidden)
            module.write_v2(path, hidden=hidden, king_buckets=1, residual=residual, mirror=False,
                            king_map=[0] * 64, output_map=[0] * 33, output_buckets=1,
                            w1=array('h', [0]) * (module.INPUTS * hidden), b1=array('h', [0]) * hidden,
                            w2=array('h', [0]) * (2 * hidden), b2=array('h', [0]),
                            feature_set=feature_set, **kwargs)
            checked = module.read_v2(path)
            require(checked['hidden'] == hidden, 'fixture reader rejected hidden size')
            self.fixtures[name] = path
        write_json(directory / 'fixtures.json', {
            name: {'path': str(path), 'sha256': sha256(path), 'bytes': path.stat().st_size}
            for name, path in self.fixtures.items()})

    def activation(self, name):
        engine = self.engine()
        option = self.options[name]
        value = option.nondefault()
        out = engine.option(name, value)
        require(not any('invalid value' in x or ' refused' in x or 'unknown option' in x for x in out),
                name + ': legal value was rejected: ' + repr(out))
        self.expected_active(engine, {name: value})
        engine.option(name, option.default)
        self.expected_active(engine, {})

    def nnue_activation(self, name):
        engine = self.engine()
        selected = {'NNUEThreats': 'threats', 'NNUEPawnPairs': 'pawnpairs',
                    'PureNnue': 'standalone'}.get(name, 'residual')
        path = self.fixtures[selected]
        values = {'NNUEFile': str(path), name: '1'} if name != 'NNUEFile' else {
            'NNUEFile': str(path), 'NNUEKingBuckets': '1'}
        # NNUEFile alone is not a valid selection. Send the complete compatible
        # set before isready; the existing loader rejects incomplete selections.
        for field, value in values.items():
            engine.send(f'setoption name {field} value {value}')
        engine.send('isready')
        engine.until(lambda s: s == 'readyok', 15)
        self.expected_active(engine, values)
        for field in values:
            engine.send(f'setoption name {field} value {self.options[field].default}')
        engine.send('isready')
        engine.until(lambda s: s == 'readyok', 15)
        self.expected_active(engine, {})

    @staticmethod
    def overrides(lines):
        return [x for x in lines if x.startswith('info string override ')]

    @staticmethod
    def warnings(lines):
        return [x for x in lines if x.startswith('info string warning: CorrMargins=')]

    def presets(self):
        engine = self.engine()
        # Independent flags must survive every preset, including OFF.
        engine.option('SmpV2', 'true')
        engine.option('TmSoftHardClamp', 'true')
        independent = {'SmpV2': 'true', 'TmSoftHardClamp': 'true'}
        for preset, expanded in PRESETS.items():
            out = engine.option('BundlePreset', preset)
            require(any(x.startswith(f'info string BundlePreset {preset}:') for x in out),
                    'preset acknowledgement missing: ' + preset)
            require(not self.overrides(out), 'preset must not report individual overrides')
            require(not self.warnings(out), 'unexpected combination warning with CorrMargins OFF')
            self.expected_active(engine, expanded | independent)
        engine.option('BundlePreset', 'OFF')
        engine.option('SmpV2', 'false')
        engine.option('TmSoftHardClamp', 'false')
        self.expected_active(engine, {})

    def owned_overrides(self):
        for name in OWNED:
            engine = self.engine()
            # N1 owns SingularV2=1; B1 owns the other options even when a field is
            # zero. Turn the exclusion partner off before switching CorrHistV2.
            engine.option('BundlePreset', 'N1' if name == 'SingularV2' else 'B1')
            if name == 'CorrHistV2':
                engine.option('CorrHistPlus', '0')
            values = {'CorrHistPlus': '4', 'HistRework': '3', 'CuckooRep': 'false',
                      'CorrHistV2': 'true', 'LmrTableV2': 'true', 'TtPruneV2': 'false',
                      'SingularV2': '0'}
            value = values[name]
            out = engine.option(name, value)
            require(self.overrides(out) == [f'info string override {name} after preset'],
                    name + ': changed owned value must report exactly one override: ' + repr(out))
            require(not self.overrides(engine.option(name, value)), name + ': noop reported override')
            require(not self.overrides(engine.option(name, 'not-a-value')), name + ': invalid reported override')
            engine.option('BundlePreset', 'OFF')
            require(not self.overrides(engine.option(name, self.options[name].nondefault())),
                    name + ': OFF must disarm preset override attribution')
            engine.close()

    def nonowned_overrides(self):
        engine = self.engine()
        engine.option('BundlePreset', 'B1')
        changed = [('Hash', '17'), ('Threads', '2'), ('Move Overhead', '11'), ('Ponder', 'true'),
                   ('Book Depth', '29'), ('Book Variety', '29'), ('UseNNUE', 'false'),
                   ('SyzygyProbeDepth', '2'), ('CorrMargins', '1'), ('NetScale', '101'),
                   ('SmpV2', 'true'), ('TmSoftHardClamp', 'true')]
        # Dynamically include every non-owned generic tunable/search switch, not
        # merely the formerly reported Hash/LmrQuietBase examples.
        already = {x[0] for x in changed}
        for name, option in self.options.items():
            if name not in already and name not in OWNED and name not in WHITELIST and name not in NNUE_OPTIONS:
                if option.kind in ('check', 'spin'):
                    changed.append((name, option.nondefault()))
        for name, value in changed:
            require(not self.overrides(engine.option(name, value)), 'non-owned override reported: ' + name)
        require(not self.overrides(engine.option('Clear Hash', None)), 'button reported override')
        require(not self.overrides(engine.option('NoSuchOptionContract', '1')), 'unknown reported override')

    def attribution_and_warnings(self):
        engine = self.engine()
        engine.option('CorrMargins', '1')
        out = engine.option('BundlePreset', 'B1')
        warning = self.warnings(out)
        require(len(warning) == 1 and '(BundlePreset B1)' in warning[0], 'valid preset warning/attribution missing')
        ack = next(i for i, x in enumerate(out) if x.startswith('info string BundlePreset B1:'))
        require(out.index(warning[0]) > ack, 'warning must follow preset acknowledgement outside its lock')
        engine.option('TtPruneV2', 'true')  # No-op must preserve the originating preset.
        engine.option('CorrMargins', '0')
        warning = self.warnings(engine.option('CorrMargins', '1'))
        require(len(warning) == 1 and '(BundlePreset B1)' in warning[0], 'noop TtPruneV2 erased attribution')
        invalid = engine.option('BundlePreset', 'bogus')
        require(any('invalid value for option BundlePreset' in x for x in invalid), 'invalid preset not rejected')
        require(not self.warnings(invalid) and not self.overrides(invalid), 'invalid preset emitted mutation warning')
        self.expected_active(engine, PRESETS['B1'] | {'CorrMargins': '1'})
        engine.option('CorrExt', '1')
        refused = engine.option('BundlePreset', 'N1')
        require(any('refused' in x and 'N1' in x for x in refused), 'N1 with CorrExt must be refused')
        require(not self.warnings(refused) and not self.overrides(refused), 'refused preset emitted mutation warning')
        self.expected_active(engine, PRESETS['B1'] | {'CorrMargins': '1', 'CorrExt': '1'})
        engine.option('CorrExt', '0')
        engine.option('TtPruneV2', 'false')
        warning = self.warnings(engine.option('TtPruneV2', 'true'))
        require(len(warning) == 1 and '(BundlePreset ' not in warning[0], 'explicit TtPruneV2 change kept stale attribution')

    def syzygy_failed_path(self):
        engine = self.engine()
        path = self.run_dir / 'definitely absent tablebases'
        require(not path.exists(), 'negative Syzygy fixture unexpectedly exists')
        out = engine.option('SyzygyPath', str(path))
        require(any('0 WDL and 0 DTZ' in x for x in out), 'missing path did not report zero loaded tables')
        active = self.active(engine.short_search())
        require(active == {} or (set(active) == {'SyzygyPath'} and
                active['SyzygyPath'].startswith(str(path)) and
                active['SyzygyPath'][len(str(path)):].strip() == '(failed)'),
                'unloaded SyzygyPath appeared active without (failed): ' + repr(active))
        engine.option('SyzygyPath', '<empty>')
        self.expected_active(engine, {})

    def nnue_failed_path(self):
        engine = self.engine(allowed=(2,))
        path = self.run_dir / 'definitely absent net.fnn2'
        require(not path.exists(), 'negative NNUE fixture unexpectedly exists')
        engine.send(f'setoption name NNUEFile value {path}')
        engine.send('go nodes 1')
        out = engine.drain_exit()
        require(any('ERROR NNUE v2:' in x and str(path) in x for x in out), 'missing net failure not reported')
        active = self.active(out)
        require(active == {} or (set(active) == {'NNUEFile'} and
                active['NNUEFile'].startswith(str(path)) and
                active['NNUEFile'][len(str(path)):].strip() == '(failed)'),
                'unloaded NNUEFile appeared active without (failed): ' + repr(active))
        require(not any(x.startswith('bestmove ') for x in out), 'unusable net silently searched fallback')

    def finish(self):
        unchanged = sha256(self.args.engine) == self.binary_sha
        if not unchanged:
            self.cases.append({'case': 'binary-immutable', 'status': 'FAIL', 'errors': ['binary changed during tests']})
        failures = [x for x in self.cases if x['status'] != 'PASS']
        summary = {'status': 'FAIL' if failures else 'PASS', 'case_count': len(self.cases),
                   'failed_case_count': len(failures), 'failures': failures, 'cases': self.cases,
                   'advertised_count': len(self.options), 'coverage': self.coverage,
                   'binary_sha256': self.binary_sha, 'binary_unchanged': unchanged,
                   'unverified': ['Successful real Syzygy table loading (no tables supplied)',
                                  'Algorithmic effect, bench identity, multiworker races, speed and playing strength',
                                  'Build-time options absent from this executable are not exercised']}
        write_json(self.run_dir / 'summary.json', summary)
        # Hash original streams and fixture files, not a reconstructed transcript.
        files = sorted(p for p in self.run_dir.rglob('*') if p.is_file())
        with (self.run_dir / 'SHA256SUMS.txt').open('x', encoding='utf-8') as stream:
            for path in files:
                stream.write(sha256(path) + '  ' + str(path.relative_to(self.run_dir)) + '\n')
        print(json.dumps({'status': summary['status'], 'cases': len(self.cases),
                          'failures': len(failures), 'evidence': str(self.run_dir)}, sort_keys=True))
        return bool(failures)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('engine', type=Path)
    parser.add_argument('--output-root', type=Path, default=Path(__file__).resolve().parent / 'runs')
    parser.add_argument('--hidden', type=int, default=256,
                        help='FORGE_NNUE_HIDDEN of tested binary; integration recipe is 256')
    args = parser.parse_args()
    require(args.engine.is_file(), 'engine is missing')
    require(args.hidden in (128, 256), 'set hidden to the actual supported build width')
    suite = Suite(args)
    try:
        if not suite.run_case('discover-duplicates-classification-defaults', suite.discover):
            return suite.finish()
        fixtures_ok = suite.run_case('repo-writer-fixture-reader-roundtrip', suite.generate_fixtures)
        for name in suite.options:
            if name in WHITELIST or name == 'SyzygyPath':
                continue
            if name in NNUE_OPTIONS:
                if fixtures_ok:
                    suite.run_case('echo-' + name, lambda name=name: suite.nnue_activation(name))
            else:
                suite.run_case('echo-' + name, lambda name=name: suite.activation(name))
        suite.run_case('preset-expanded-values-and-independent-flags', suite.presets)
        suite.run_case('changed-owned-only-noop-invalid-and-off-overrides', suite.owned_overrides)
        suite.run_case('nonowned-options-never-report-preset-override', suite.nonowned_overrides)
        suite.run_case('preset-warnings-refusals-and-tt-noop-attribution', suite.attribution_and_warnings)
        suite.run_case('syzygy-missing-path-truth', suite.syzygy_failed_path)
        suite.run_case('nnue-missing-path-fails-closed', suite.nnue_failed_path)
    except KeyboardInterrupt:
        suite.cases.append({'case': 'interrupted', 'status': 'FAIL', 'errors': ['KeyboardInterrupt; raw logs retained']})
    return suite.finish()


if __name__ == '__main__':
    raise SystemExit(main())
