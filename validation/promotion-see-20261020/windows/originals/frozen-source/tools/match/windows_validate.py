#!/usr/bin/env python3
"""Offline native-Windows Forge validation; run with runtime/python.exe -I -B.

Bundle manifest schema (version 1): ``files`` maps relative POSIX filenames to
SHA-256 strings. It must cover this runner, pgn_stats.py, both engine/*.exe,
fastchess/fastchess.exe, runtime/python.exe, and openings/{aa,pilot,sprt}.epd.
``provenance`` contains fastchess_source (the full PIN below), and nonempty
candidate/original objects recording source/archive, compiler, flags and build
evidence. Include all runtime/DLL/license/provenance files in ``files`` too.
Manifest itself is frozen separately, avoiding a self-referential checksum.

No network access, resume, retry, game pooling, adjudication or automatic upload.
An accepted H1 is evidence for this opponent/control; it does not prove +5 Elo.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import signal
import subprocess
import sys
import time
import uuid
import zipfile

sys.dont_write_bytecode = True
PIN = '60d7a7a26c6b0582a15c112fb29a1829bef2adb3'
ZERO_BIN_REGULARIZATION = 0.001
PRINTED_LLR_TOLERANCE = 0.005000001  # Pinned native format is {:.2f}.
BOUNDARY_NUMERIC_TOLERANCE = 1e-10
PHASES = {'aa': (4, 2), 'pilot': (8, 1), 'sprt': (5000, 1)}
REQUIRED = {'windows_validate.py', 'pgn_stats.py', 'engine/candidate.exe',
            'engine/original-6.4.exe', 'fastchess/fastchess.exe', 'runtime/python.exe',
            'openings/aa.epd', 'openings/pilot.epd', 'openings/sprt.epd'}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def ascii_path(path):
    if not str(path).isascii():
        raise ValueError('Use an ASCII-only bundle/results path: pinned Fastchess uses CreateProcessA')


def fen(line):
    return ' '.join(line.split()[:4])


def selected(root, phase):
    lines = (root / 'openings' / (phase + '.epd')).read_text(encoding='utf-8').splitlines()
    positions = [fen(line) for line in lines if line.strip()]
    if len(positions) != PHASES[phase][0] or len(set(positions)) != len(positions):
        raise ValueError(f'{phase}: openings must have exactly {PHASES[phase][0]} unique positions')
    if any(len(p.split()) != 4 or p.split()[3] != '-' for p in positions):
        raise ValueError('Opening eligibility requires four FEN fields and EP target -')
    return positions


def verify_hashes(root, frozen):
    # Runtime import/DLL search must not acquire an unfrozen dependency. Results
    # directories may grow; the four immutable dependency trees may not.
    immutable = [p for directory in ('runtime', 'engine', 'fastchess', 'openings')
                 for p in (root / directory).rglob('*') if p.is_file()]
    immutable += [p for p in root.iterdir() if p.is_file() and p.name != 'manifest.json']
    for path in immutable:
        name = path.relative_to(root).as_posix()
        if name not in frozen:
            raise ValueError(f'Unlisted bundle dependency: {name}')
    for name, expected in frozen.items():
        path = root / name
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f'input checksum changed: {name}')


def load_bundle(root):
    ascii_path(root)
    root = root.resolve(strict=True)
    ascii_path(root)
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    files = manifest.get('files', {})
    provenance = manifest.get('provenance', {})
    if manifest.get('schema_version') != 1 or not REQUIRED <= files.keys():
        raise ValueError('Manifest schema_version=1 and all required files are required')
    if provenance.get('fastchess_source') != PIN or not all(
            isinstance(provenance.get(key), dict) and provenance[key] for key in ('candidate', 'original')):
        raise ValueError('Manifest requires pinned Fastchess and candidate/original source/build provenance')
    lower = set()
    for name, digest in files.items():
        relative = PurePosixPath(name)
        if (not name.isascii() or '\\' in name or ':' in name or relative.is_absolute()
                or '..' in relative.parts or name != relative.as_posix() or name in ('', '.')
                or name.lower() in lower or name.lower() == 'manifest.json'):
            raise ValueError(f'Unsafe or ambiguous relative manifest path: {name}')
        lower.add(name.lower())
        path = root / name
        if not path.resolve().is_relative_to(root) or any(
                item.is_symlink() for item in (path, *path.parents) if item.is_relative_to(root)):
            raise ValueError(f'Manifest path escapes bundle or uses a symlink: {name}')
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError(f'Invalid SHA-256 for {name}')
    frozen = dict(files, **{'manifest.json': sha(root / 'manifest.json')})
    verify_hashes(root, frozen)
    for name in ('engine/candidate.exe', 'engine/original-6.4.exe',
                 'fastchess/fastchess.exe', 'runtime/python.exe'):
        with (root / name).open('rb') as stream:
            if stream.read(2) != b'MZ':
                raise ValueError(f'Native Windows PE required: {name}')
    openings = [p for phase in PHASES for p in selected(root, phase)]
    if len(openings) != len(set(openings)):
        raise ValueError('A/A, pilot and SPRT openings must be disjoint')
    return manifest, frozen


def runner_version(root):
    completed = subprocess.run([str(root / 'fastchess/fastchess.exe'), '-version'],
                               cwd=root, capture_output=True, text=True, timeout=30, check=True)
    version = completed.stdout.strip()
    if PIN[:7] not in version:
        raise ValueError('Fastchess runtime version does not match frozen source pin')
    return version


def phase_command(root, out, phase):
    pairs, concurrency = PHASES[phase]
    # Relative, space-free engine commands avoid this pinned runner's unquoted
    # CreateProcessA command line. Fastchess itself runs with cwd=bundle root.
    candidate = 'original-6.4.exe' if phase == 'aa' else 'candidate.exe'
    command = [str(root / 'fastchess/fastchess.exe'), '-config', f'outname={out / "state.json"}',
               '-engine', f'cmd=engine/{candidate}', 'name=Candidate',
               '-engine', 'cmd=engine/original-6.4.exe', 'name=Baseline',
               '-each', 'proto=uci', 'tc=inf' if phase == 'aa' else 'tc=10+0.1',
               'option.Threads=1', 'option.Hash=32', 'option.OwnBook=false',
               'option.Ponder=false', 'option.Move Overhead=100', 'restart=on']
    if phase == 'aa':
        command.append('nodes=10000')
    command += ['-openings', f'file={root / "openings" / (phase + ".epd")}',
                'format=epd', 'order=sequential', '-rounds', str(pairs), '-games', '2',
                '-concurrency', str(concurrency), '-srand', '20261019', '-report', 'penta=true',
                '-ratinginterval', '2', '-autosaveinterval', '2', '-pgnout',
                f'file={out / "games.pgn"}', 'append=false', 'notation=uci', 'nodes=true',
                'timeleft=true', '-log', f'file={out / "fastchess.log"}', 'level=trace',
                'engine=true', 'realtime=false', 'append=false', '-strict']
    if phase == 'sprt':
        command += ['-sprt', 'elo0=0', 'elo1=5', 'alpha=0.05', 'beta=0.05', 'model=logistic']
    return command


def console_text(out):
    path = out / 'console.txt'
    return re.sub(r'\x1b\[[0-9;]*m', '', path.read_text(encoding='utf-8', errors='replace')) if path.exists() else ''


def final_llr(console):
    tokens = re.findall(r'LLR:\s*(\S+)', console)
    if not tokens:
        raise ValueError('Missing final native likelihood')
    try:
        llr = float(tokens[-1].rstrip(',;'))
    except ValueError as error:
        raise ValueError('Unparseable final native LLR') from error
    if not math.isfinite(llr):
        raise ValueError('Native acceptance has non-finite final LLR')
    return llr


def native_acceptance(console):
    decisions = re.findall(r'SPRT[^\n]*completed - (H[01]) was accepted', console)
    if not decisions:
        return None
    if len(decisions) != 1:
        raise ValueError('Acceptance requires exactly one native decision')
    final_llr(console)
    return decisions[0] + '_accepted'


def logistic_llr(penta, elo0, elo1):
    """Constrained multinomial MLE, independent of pinned Fastchess's ITP.

    Reused from tests/audit-quality-result.py. Maximizing sum(n_i log(q_i))
    with sum(q_i)=1 and sum(a_i q_i)=s gives
    q_i=p_i/(1+theta*(a_i-s)). Its scalar constraint equation is strictly
    decreasing, so bisection finds theta without the native implementation.
    """
    if len(penta) != 5 or any(type(n) is not int or n < 0 for n in penta) or not sum(penta):
        raise ValueError('invalid pentanomial counts')
    counts = [float(n) if n else ZERO_BIN_REGULARIZATION for n in penta]
    total = math.fsum(counts)
    probabilities = [n / total for n in counts]
    scores = [0.0, 0.25, 0.5, 0.75, 1.0]

    def constrained_mle(elo):
        score = 1.0 / (1.0 + 10.0 ** (-elo / 400.0))
        if not 0.0 < score < 1.0:
            raise ValueError('hypothesis score is outside the MLE domain')
        lower, upper = -1.0 / (1.0 - score), 1.0 / score
        theta = 0.0
        for _ in range(100):
            theta = (lower + upper) / 2.0
            value = math.fsum(p * (a - score) / (1.0 + theta * (a - score))
                              for p, a in zip(probabilities, scores))
            if value == 0.0:
                break
            if value > 0.0:
                lower = theta
            else:
                upper = theta
        fitted = [p / (1.0 + theta * (a - score)) for p, a in zip(probabilities, scores)]
        if (any(not math.isfinite(q) or q <= 0 for q in fitted)
                or abs(math.fsum(fitted) - 1.0) > 1e-9
                or abs(math.fsum(a * q for a, q in zip(scores, fitted)) - score) > 1e-9):
            raise ValueError('constrained MLE failed its normalization/mean checks')
        return fitted

    q0, q1 = constrained_mle(elo0), constrained_mle(elo1)
    llr = math.fsum(n * math.log(b / a) for n, a, b in zip(counts, q0, q1))
    if not math.isfinite(llr):
        raise ValueError('independently recomputed likelihood is not finite')
    return llr


def audit_likelihood(console, penta, pairs, cap):
    decision = native_acceptance(console)
    native_llr = final_llr(console)
    independent_llr = logistic_llr(penta, 0, 5)
    lower, upper = -math.log(19), math.log(19)
    if abs(native_llr - independent_llr) > PRINTED_LLR_TOLERANCE:
        raise ValueError('Independent likelihood disagrees with native two-decimal likelihood')
    if decision == 'H1_accepted':
        if independent_llr < upper - BOUNDARY_NUMERIC_TOLERANCE:
            raise ValueError('Native H1 acceptance lacks independent upper-bound crossing')
    elif decision == 'H0_accepted':
        if independent_llr > lower + BOUNDARY_NUMERIC_TOLERANCE:
            raise ValueError('Native H0 acceptance lacks independent lower-bound crossing')
    elif pairs != cap:
        raise ValueError('SPRT stopped before cap without a native boundary')
    elif not lower < independent_llr < upper:
        raise ValueError('Cap lacks native acceptance despite independent boundary crossing')
    else:
        decision = 'inconclusive_at_pair_cap'
    return decision, {
        'method': 'Independent constrained multinomial MLE; 100-step bisection',
        'zero_bin_regularization': ZERO_BIN_REGULARIZATION,
        'native_printed_llr': native_llr, 'independent_llr': independent_llr,
        'printed_llr_tolerance': PRINTED_LLR_TOLERANCE,
        'lower_bound': lower, 'upper_bound': upper,
        'boundary_numeric_tolerance': BOUNDARY_NUMERIC_TOLERANCE}


def audit_phase(root, out, phase):
    console = console_text(out)
    if re.search(r'^\s*(?:warning|error|fatal)\b', console, re.I | re.M):
        raise ValueError('Fastchess console contains a warning/error')
    with (out / 'fastchess.log').open(encoding='utf-8', errors='replace') as log:
        if any(re.search(r'\[(?:WARN|ERR|FATAL)\s*\]', line) for line in log):
            raise ValueError('Fastchess trace contains a warning/error')
    spec = importlib.util.spec_from_file_location('bundle_pgn_stats', root / 'pgn_stats.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    text = (out / 'games.pgn').read_text(encoding='utf-8')
    stats = checker.summarize(text, require_identical_pairs=phase == 'aa')
    pairs = stats['pairs']
    if not 1 <= pairs <= PHASES[phase][0]:
        raise ValueError('Invalid completed-pair count')
    expected = selected(root, phase)[:pairs]
    grouped = {}
    for tags, _ in checker.games(text):
        grouped.setdefault(tags['Round'], fen(tags['FEN']))
    # Check round numbers too: set membership alone can hide a skipped prefix.
    if set(grouped) != {str(i) for i in range(1, pairs + 1)} or any(
            grouped[str(i)] != position for i, position in enumerate(expected, 1)):
        raise ValueError('Played openings are not the exact scheduled prefix')
    penta = re.findall(r'Ptnml\(0-2\):\s*\[([^\]]+)\]', console)
    if not penta or [int(v.strip()) for v in penta[-1].split(',')] != stats['pentanomial_0_half_1_1half_2']:
        raise ValueError('Native pentanomial counts are missing or disagree with PGN')
    decision = native_acceptance(console)
    likelihood_audit = None
    if phase != 'sprt':
        if pairs != PHASES[phase][0] or decision:
            raise ValueError('Calibration/pilot must finish its complete fixed schedule without SPRT')
        status = phase + '_passed'
    else:
        decision, likelihood_audit = audit_likelihood(
            console, stats['pentanomial_0_half_1_1half_2'], pairs, PHASES[phase][0])
        status = 'completed'
    return {'status': status, 'sprt_decision': decision, 'statistics': stats,
            'likelihood_audit': likelihood_audit,
            'equal_clock_gain_established': phase == 'sprt' and decision == 'H1_accepted',
            'claim_scope': 'Specified native Windows opponent/control only; H1 does not prove gain >=5 Elo; no Stockfish claim'}


def progress(out, started):
    console = console_text(out)
    return {'elapsed_seconds': round(time.monotonic() - started, 3),
            'finished_game_messages': len(re.findall(r'^Finished game ', console, re.M)),
            'latest_llr_lines': [line for line in console.splitlines() if 'LLR:' in line][-2:]}


def stop_child(process):
    if process.poll() is not None:
        return
    try:
        process.send_signal(signal.CTRL_BREAK_EVENT if os.name == 'nt' else signal.SIGINT)
        process.wait(timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        # Kill only this owned process tree if graceful Fastchess cleanup stalls.
        if os.name == 'nt':
            subprocess.run([str(Path(os.environ['SystemRoot']) / 'System32/taskkill.exe'),
                            '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=30)
        process.kill()
        process.wait(timeout=30)


def run_phase(root, out, phase, frozen):
    verify_hashes(root, frozen)
    out.mkdir()
    command = phase_command(root, out, phase)
    write(out / 'command.json', {'argv': command, 'cwd': str(root)})
    result = {'status': 'running', 'phase': phase, 'equal_clock_gain_established': False}
    started = time.monotonic()
    process = None
    try:
        with (out / 'console.txt').open('x', encoding='utf-8') as console:
            process = subprocess.Popen(command, cwd=root, stdout=console, stderr=subprocess.STDOUT,
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
            result['pid'] = process.pid
            while True:
                result['progress'] = progress(out, started)
                write(out / 'result.json', result)
                print(f'{phase}: {result["progress"]}', flush=True)
                try:
                    result['exit_code'] = process.wait(timeout=10)
                    break
                except subprocess.TimeoutExpired:
                    pass
        if result['exit_code']:
            raise ValueError(f'Fastchess exited {result["exit_code"]}')
        verify_hashes(root, frozen)
        result.update(audit_phase(root, out, phase))
    except (Exception, KeyboardInterrupt) as error:
        if process is not None:
            try:
                stop_child(process)
            except Exception as cleanup_error:
                result['cleanup_error'] = str(cleanup_error)
        result.update(status='failed_or_interrupted', error=str(error) or type(error).__name__,
                      equal_clock_gain_established=False)
    finally:
        result['progress'] = progress(out, started)
        result['outputs_sha256'] = {p.name: sha(p) for p in out.iterdir()
                                    if p.is_file() and p.name != 'result.json'}
        write(out / 'result.json', result)
    return result


def host_info():
    cpu_registry = {}
    if os.name == 'nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
                for name in ('ProcessorNameString', 'Identifier', 'VendorIdentifier', '~MHz'):
                    try:
                        cpu_registry[name] = winreg.QueryValueEx(key, name)[0]
                    except OSError:
                        pass
        except OSError as error:
            cpu_registry['unavailable'] = str(error)
    return {'platform': platform.platform(), 'machine': platform.machine(),
            'processor': platform.processor(), 'logical_cpu_count': os.cpu_count(),
            'cpu_registry': cpu_registry, 'wine_detected': is_wine(),
            'python': sys.version, 'python_executable': sys.executable,
            'processor_environment': {key: os.environ.get(key) for key in
                                      ('PROCESSOR_IDENTIFIER', 'PROCESSOR_ARCHITECTURE', 'NUMBER_OF_PROCESSORS')}}


def is_wine():
    if os.name != 'nt':
        return False
    import ctypes
    try:
        return bool(ctypes.WinDLL('ntdll').wine_get_version)
    except AttributeError:
        return False


def run_validation(root, out, aa_only=False):
    root, out = root.resolve(), out.resolve()
    ascii_path(root)
    ascii_path(out)
    out.mkdir(parents=True, exist_ok=False)
    result = {'status': 'running', 'equal_clock_gain_established': False, 'phases': {}}
    frozen = {}
    try:
        manifest, frozen = load_bundle(root)
        version = runner_version(root)
        write(out / 'protocol.json', {
            'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'manifest': manifest, 'input_sha256': frozen, 'host': host_info(),
            'fastchess_version': version, 'fastchess_source': PIN,
            'settings': {'threads': 1, 'hash_mib': 32, 'ownbook': False, 'ponder': False,
                         'move_overhead_ms': 100, 'restart': True, 'strict': True,
                         'adjudication': None, 'aa_pairs': 4, 'aa_nodes': 10000,
                         'pilot_pairs': 8, 'timed_control': '10+0.1', 'sprt_max_pairs': 5000,
                         'sprt': {'elo0': 0, 'elo1': 5, 'alpha': .05, 'beta': .05, 'model': 'logistic'},
                         'concurrency': {'aa': 2, 'pilot': 1, 'sprt': 1}},
            'opening_eligibility': 'Disjoint unique FEN first four fields; original EP target - only',
            'commands': {phase: {'argv': phase_command(root, out / phase, phase), 'cwd': str(root)}
                         for phase in (('aa',) if aa_only else PHASES)},
            'policy': 'One fresh attempt; no retry/resume/pooling. All games retained. Any fault invalidates attempt.',
            'claim_scope': 'Native Windows candidate versus exact original; conditional timed strength only, no Stockfish claim'})
        for phase in (('aa',) if aa_only else PHASES):
            result['active_phase'] = phase
            write(out / 'result.json', result)
            phase_result = run_phase(root, out / phase, phase, frozen)
            result['phases'][phase] = phase_result
            if phase_result['status'] == 'failed_or_interrupted':
                raise ValueError(f'{phase} gate failed: {phase_result.get("error", "unknown error")}')
        verify_hashes(root, frozen)
        result.update(status='aa_passed' if aa_only else 'completed',
                      equal_clock_gain_established=False if aa_only else
                      result['phases']['sprt']['equal_clock_gain_established'])
    except (Exception, KeyboardInterrupt) as error:
        result.update(status='failed_or_interrupted', error=str(error) or type(error).__name__,
                      equal_clock_gain_established=False)
    finally:
        result['final_input_sha256'] = {name: sha(root / name) if (root / name).is_file() else None
                                        for name in frozen}
        result['claim_scope'] = 'Specified opponent/control only; accepted H1 does not prove >=5 Elo; no Stockfish claim'
        write(out / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--out', type=Path, help='New results directory; an existing directory is never resumed')
    parser.add_argument('--aa-only', action='store_true', help='Only deterministic fixed-node readiness calibration')
    parser.add_argument('--zip-results', action='store_true', help='Package all retained results after final status is written')
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('Run with bundled runtime/python.exe on native Windows (Wine is readiness only)')
    if Path(sys.executable).resolve() != (args.bundle / 'runtime/python.exe').resolve():
        parser.error('Use this bundle\'s runtime/python.exe -I -B windows_validate.py')
    if not sys.flags.isolated or not sys.flags.dont_write_bytecode:
        parser.error('Launch bundled Python with both -I and -B')
    if is_wine() and not args.aa_only:
        parser.error('Wine supports --aa-only readiness; run timed strength validation on native Windows')
    out = args.out or args.bundle / 'results' / (datetime.datetime.now().strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8])
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f'received signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    result = run_validation(args.bundle, out, args.aa_only)
    print(json.dumps(result, indent=2), flush=True)
    if args.zip_results:
        target = out.parent / (out.name + '.zip')
        with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(out.rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(out))
        print(f'Results archive: {target}', flush=True)
    return 0 if result['status'] in ('completed', 'aa_passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
