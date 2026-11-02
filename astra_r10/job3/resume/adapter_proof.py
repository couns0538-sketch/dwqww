"""Real FPOS/full-FEN converter restart proof. No engine, training or GPU.

Only this harness's directly created converter child can be terminated. Every
attempt, staging shard, orphan publication and original log is retained.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = Path('D:/a10')
FAULTS = ('before_publish', 'after_publish_before_checkpoint', 'after_checkpoint')
ROLES = {'text': 'rows.txt', 'bullet': 'rows.bullet', 'provenance': 'provenance.tsv'}


def hashes(path):
    path = Path(path)
    md5, sha = hashlib.md5(), hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(block); md5.update(block); sha.update(block)
    return {'bytes': size, 'md5': md5.hexdigest(), 'sha256': sha.hexdigest()}


def identity(path):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), **hashes(path)}


def pinned(item):
    if identity(item['path']) != item:
        raise ValueError('declared input/tool identity changed: ' + item['path'])


def owned(path):
    path = Path(path)
    root = ROOT.resolve(strict=True)
    if not path.is_absolute() or path.resolve() == root or not path.resolve().is_relative_to(root):
        raise ValueError('path must resolve strictly inside D:/a10: ' + str(path))
    return path.resolve()


def disk_guard():
    if os.name != 'nt':
        raise ValueError('this proof requires native Windows/NTFS')
    for drive, gib in (('C:/', 30), ('D:/', 50)):
        if shutil.disk_usage(drive).free < gib * 1024**3 + (32 * 1024**2 if drive == 'D:/' else 0):
            raise ValueError('storage floor violated: ' + drive)


def write_new(path, value):
    path = owned(path)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def source_tools():
    receipt = json.loads((HERE/'SOURCE_COPY.json').read_text(encoding='utf-8-sig'))
    if receipt['source_commit'] != 'd8982bc0':
        raise ValueError('unexpected original converter revision')
    original, candidate = [], []
    for item in receipt['files']:
        path = Path(receipt['source_root'])/item['source']
        bound = identity(path)
        if bound['sha256'].lower() != item['sha256'].lower():
            raise ValueError('frozen original source hash mismatch: ' + str(path))
        original.append(bound)
        candidate.append(identity(HERE/item['destination']))
    return original, candidate


def import_adapter(path):
    path = Path(path)
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('r10_real_converter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def worker(spec_path):
    spec_path = owned(spec_path)
    spec_bytes = spec_path.read_bytes()
    spec = json.loads(spec_bytes)
    spec_sha = hashlib.sha256(spec_bytes).hexdigest()
    logdir = owned(spec['logdir'])
    try:
        disk_guard()
        for item in spec['pinned']:
            pinned(item)
        out = owned(spec['out'])
        adapter = import_adapter(spec['adapter'])

        def fault_hook(point, context):
            if point != spec['fault'] or context['chunk_index'] != 1:
                return
            marker = dict(point=point, context=context, pid=os.getpid(),
                          spec_sha256=spec_sha, output=str(out))
            # Publish the marker only after the complete JSON is durable, so
            # the parent cannot observe a half-written signal file.
            pending = logdir/'fault-reached.json.pending'
            write_new(pending, marker)
            os.link(pending, logdir/'fault-reached.json')
            # A timeout is an error, never a successful interruption. The parent
            # owns the Popen handle and terminates only this newly created child.
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                time.sleep(.05)
            raise TimeoutError('parent did not interrupt the owned fault worker')

        if spec['action'] == 'verify':
            result = adapter.verify(out)
        else:
            argv = ['convert', '--pos', spec['pos'], '--input', spec['fen'],
                    '--sidecar-format', 'fen', '--out', str(out),
                    '--chunk-rows', str(spec['chunk_rows']), '--no-filters',
                    '--no-dedupe', '--min-free-mb', '51200']
            if spec['action'] == 'resume': argv.append('--resume')
            if spec['stop_after_chunks'] is not None:
                argv += ['--stop-after-chunks', str(spec['stop_after_chunks'])]
            args = adapter.parser().parse_args(argv)
            result = adapter.run(args, fault_hook=fault_hook) if spec['fault'] else adapter.run(args)
        for item in spec['pinned']:
            pinned(item)
        if hashlib.sha256(spec_path.read_bytes()).hexdigest() != spec_sha:
            raise ValueError('worker spec changed during execution')
        write_new(logdir/'worker-result.json', {'status': 'RETURNED', 'result': result})
    except BaseException as error:
        write_new(logdir/'worker-failure.json', {'status': 'FAILED',
                  'type': type(error).__name__, 'error': str(error)})
        raise


def role_manifest(out):
    """Hash stored payload bytes, without rebuilding or normalizing records."""
    out = Path(out)
    chunks = []
    concat = {role: (hashlib.md5(), hashlib.sha256(), 0) for role in ROLES}
    next_row = 0
    receipts = sorted(out.glob('chunk_*.json'))
    if not receipts:
        raise ValueError('proof needs committed chunks')
    for number, receipt in enumerate(receipts):
        if receipt.name != f'chunk_{number:06d}.json':
            raise ValueError('noncontiguous chunk receipts')
        chunk = json.loads(receipt.read_text())
        if chunk['start_row'] != next_row:
            raise ValueError('noncontiguous source offsets')
        next_row += chunk['input_rows']
        files = {}
        for relative, expected in chunk['files'].items():
            path = out/relative
            if not path.resolve().is_relative_to(out.resolve()):
                raise ValueError('escaped chunk manifest path')
            actual = hashes(path)
            if (actual['bytes'], actual['sha256']) != (expected['bytes'], expected['sha256']):
                raise ValueError('chunk payload differs from receipt')
            if path.name in files:
                raise ValueError('duplicate file role name')
            files[path.name] = actual
        if set(files) != set(ROLES.values()):
            raise ValueError('unexpected or missing output role; never silently omit it')
        roles = {}
        for role, filename in ROLES.items():
            path = out/chunk[role]
            if path.name != filename or chunk[role] not in chunk['files']:
                raise ValueError('invalid role binding')
            roles[role] = hashes(path)
            md5, sha, size = concat[role]
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    md5.update(block); sha.update(block); size += len(block)
            concat[role] = md5, sha, size
        chunks.append({'start_row': chunk['start_row'], 'input_rows': chunk['input_rows'],
                       'kept': chunk['kept'], 'counts': chunk['counts'],
                       'files': files, 'roles': roles})
    return {'chunks': chunks, 'input_rows': next_row,
            'concatenated_roles': {r: {'bytes': n, 'md5': m.hexdigest(), 'sha256': s.hexdigest()}
                                   for r, (m, s, n) in concat.items()}}


class Proof:
    def __init__(self, args):
        self.args = args
        self.out = owned(args.out)
        disk_guard()
        self.out.mkdir(parents=True, exist_ok=False)
        (self.out/'logs').mkdir()
        self.original, self.candidate = source_tools()
        self.harness = [identity(__file__), identity(HERE/'SOURCE_COPY.json')]
        self.inputs = [identity(args.pos), identity(args.fen), identity(args.input_provenance)]
        if self.inputs[0]['sha256'] != args.pos_sha256.lower() or self.inputs[1]['sha256'] != args.fen_sha256.lower():
            raise ValueError('specified input hashes do not match actual frozen inputs')
        if self.inputs[2]['sha256'] != args.provenance_sha256.lower():
            raise ValueError('specified provenance receipt hash does not match')
        provenance = json.loads(Path(args.input_provenance).read_text(encoding='utf-8-sig'))
        if provenance.get('schema') != 1 or provenance.get('upstream_scope') != args.upstream_scope:
            raise ValueError('provenance schema/scope mismatch')
        for role, actual in zip(('pos', 'fen'), self.inputs[:2]):
            recorded = provenance['outputs'][role]
            if (Path(recorded['path']).resolve(strict=True) != Path(actual['path'])
                    or recorded['sha256'].lower() != actual['sha256']):
                raise ValueError('provenance output binding mismatch: ' + role)
        upstream = provenance['evidence']
        upstream_identity = identity(owned(upstream['path']))
        if upstream_identity['sha256'] != upstream['sha256'].lower():
            raise ValueError('upstream evidence hash mismatch')
        self.inputs.append(upstream_identity)
        scope_evidence = provenance['scope_evidence']
        scope_identity = identity(owned(scope_evidence['path']))
        if scope_identity['sha256'] != scope_evidence['sha256'].lower():
            raise ValueError('upstream scope evidence hash mismatch')
        self.inputs.append(scope_identity)
        sys.path.insert(0, str(HERE/'data'))
        from forge_pos import PosReader
        with PosReader(args.pos) as reader:
            self.rows = len(reader)
        if not 3 <= self.rows <= 256 or not 1 <= args.chunk_rows < self.rows/2:
            raise ValueError('bounded proof requires 3..256 rows and at least three chunks')
        self.sequence = 0
        self.attempts = []
        write_new(self.out/'INPUTS.json', {'status': 'UNPROVEN', 'inputs': self.inputs,
                  'original_tools': self.original, 'candidate_tools': self.candidate,
                  'harness': self.harness, 'rows': self.rows, 'chunk_rows': args.chunk_rows,
                  'upstream_scope': args.upstream_scope, 'seed': None,
                  'scope': 'actual FPOS/full-FEN to bullet32+exact-sidecar converter; no native probe or training'})

    def launch(self, label, out, *, action='convert', original=False, fault=None,
               stop_after_chunks=None, inputs=None, error_contains=None):
        disk_guard()
        self.sequence += 1
        logdir = self.out/'logs'/f'{self.sequence:02d}_{label}'
        logdir.mkdir()
        tools = self.original if original else self.candidate
        adapter = next(item['path'] for item in tools if Path(item['path']).name == 'convert_dataset.py')
        pos, fen = inputs if inputs else (self.args.pos, self.args.fen)
        task = dict(action=action, adapter=adapter, out=str(owned(out)), logdir=str(logdir),
                    pos=str(owned(pos)), fen=str(owned(fen)), chunk_rows=self.args.chunk_rows,
                    fault=fault, stop_after_chunks=stop_after_chunks,
                    pinned=tools+self.harness+[identity(pos), identity(fen)])
        spec = logdir/'spec.json'
        write_new(spec, task)
        argv = [sys.executable, '-B', str(Path(__file__).resolve()), 'worker', '--spec', str(spec)]
        write_new(logdir/'command.json', {'argv': argv, 'spec': identity(spec)})
        env = os.environ.copy()
        env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
                   OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                   CUDA_VISIBLE_DEVICES='', HIP_VISIBLE_DEVICES='', ROCR_VISIBLE_DEVICES='',
                   TEMP=str(self.out), TMP=str(self.out))
        start = time.monotonic()
        proc = None
        interrupted = False
        observed = None
        timed_out = False
        try:
            with (logdir/'stdout.log').open('xb') as stdout, (logdir/'stderr.log').open('xb') as stderr:
                proc = subprocess.Popen(argv, cwd=str(HERE), env=env, stdout=stdout, stderr=stderr,
                                        creationflags=subprocess.IDLE_PRIORITY_CLASS)
                if fault:
                    marker = logdir/'fault-reached.json'
                    deadline = time.monotonic() + 35
                    while time.monotonic() < deadline and not marker.exists() and proc.poll() is None:
                        time.sleep(.05)
                    if not marker.exists() or proc.poll() is not None:
                        raise RuntimeError('worker did not wait at the declared fault point')
                    observed = json.loads(marker.read_text())
                    if (observed['point'] != fault or observed['pid'] != proc.pid
                            or observed['spec_sha256'] != identity(spec)['sha256']):
                        raise ValueError('fault marker identity mismatch')
                    context = observed['context']
                    actual_out = owned(out)
                    if owned(observed['output']) != actual_out or owned(context['out']) != actual_out:
                        raise ValueError('fault marker belongs to another output')
                    staging, published = owned(context['staging']), owned(context['published'])
                    if (staging.parent != actual_out or published.parent != actual_out
                            or not staging.name.startswith('.partial_data_')
                            or published.name != staging.name.removeprefix('.partial_')):
                        raise ValueError('fault marker has unexpected shard paths')
                    receipt = Path(out)/'chunk_000001.json'
                    if context['chunk_index'] != 1 or context['start_row'] != self.args.chunk_rows:
                        raise ValueError('wrong interrupted source boundary')
                    expected = {'before_publish': (True, False, False),
                                'after_publish_before_checkpoint': (False, True, False),
                                'after_checkpoint': (False, True, True)}[fault]
                    if (staging.exists(), published.exists(), receipt.exists()) != expected:
                        raise ValueError('filesystem does not match declared fault boundary')
                    payload = staging if staging.exists() else published
                    observed['payload_directory'] = str(payload)
                    observed['retained_files'] = {p.name: hashes(p) for p in payload.iterdir() if p.is_file()}
                    if set(observed['retained_files']) != set(ROLES.values()):
                        raise ValueError('fault point lacks actual converter output roles')
                    observed['committed_receipts'] = {p.name: hashes(p) for p in actual_out.glob('chunk_*.json')}
                    proc.terminate()
                    proc.wait(timeout=10)
                    interrupted = proc.returncode != 0
                    if not interrupted:
                        raise ValueError('normal completion cannot count as interruption')
                else:
                    proc.wait(timeout=90)
        except subprocess.TimeoutExpired:
            timed_out = True
            raise
        finally:
            if proc is not None and proc.poll() is None:
                # The object is our live Popen handle, never a looked-up PID.
                proc.kill(); proc.wait(timeout=10)
            receipt = {'label': label, 'pid': proc.pid if proc else None,
                       'exit_code': proc.returncode if proc else None,
                       'owned_process_only': True, 'interrupted': interrupted,
                       'timed_out': timed_out, 'fault': fault, 'observed': observed,
                       'elapsed_seconds': time.monotonic()-start, 'spec': identity(spec)}
            write_new(logdir/'process.json', receipt)
            self.attempts.append(receipt)
        for item in tools+self.harness:
            pinned(item)
        if fault:
            return receipt
        if error_contains:
            failure_path = logdir/'worker-failure.json'
            failure = json.loads(failure_path.read_text()) if failure_path.exists() else {}
            if proc.returncode == 0 or error_contains not in failure.get('error', ''):
                raise ValueError('negative control was not detected for its intended reason: ' + label)
            return {'status': 'DETECTED', 'expected_error': error_contains, 'failure': failure,
                    'process': receipt}
        if proc.returncode != 0:
            raise ValueError('real adapter failed: ' + label)
        result = json.loads((logdir/'worker-result.json').read_text())
        if result['status'] != 'RETURNED':
            raise ValueError('missing actual converter result')
        expected_statuses = {'CHECKPOINT'} if stop_after_chunks is not None else {'PASS', 'COMPLETE'}
        if result['result'].get('status') not in expected_statuses:
            raise ValueError('unexpected actual converter completion status')
        if stop_after_chunks is None and not (Path(out)/'COMPLETE.json').is_file():
            raise ValueError('successful converter result has no completion receipt')
        return result

    def verify_retained(self, interruption):
        observed = interruption['observed']
        output = owned(observed['output'])
        payload = owned(observed['payload_directory'])
        if payload.parent != output or not payload.is_dir():
            raise ValueError('interrupted shard directory was removed or moved')
        files = {p.name: hashes(p) for p in payload.iterdir() if p.is_file()}
        if files != observed['retained_files']:
            raise ValueError('interrupted shard bytes were changed by resume')
        for name, original in observed['committed_receipts'].items():
            if hashes(output/name) != original:
                raise ValueError('previously committed receipt was changed by resume')
        return {'status': 'PASS', 'payload_directory': str(payload),
                'files': files, 'original_committed_receipts': observed['committed_receipts']}

    def run(self):
        original = self.out/'original'
        self.launch('original_no_fault', original, original=True)
        original_roles = role_manifest(original)
        baseline = self.out/'uninterrupted'
        self.launch('candidate_no_fault', baseline)
        baseline_roles = role_manifest(baseline)
        if original_roles != baseline_roles:
            raise ValueError('default converter payload bytes changed versus frozen d8982bc0')
        comparisons = []
        for fault in FAULTS:
            output = self.out/fault
            interruption = self.launch(fault, output, fault=fault)
            self.launch(fault+'_resume', output, action='resume')
            resumed = role_manifest(output)
            retained_after_resume = self.verify_retained(interruption)
            if resumed != baseline_roles:
                raise ValueError('resumed payload bytes differ: ' + fault)
            self.launch(fault+'_resume_again', output, action='resume')
            retained_after_repeat = self.verify_retained(interruption)
            if role_manifest(output) != resumed:
                raise ValueError('completed resume changed payload bytes: ' + fault)
            comparisons.append({'fault': fault, 'status': 'PASS', 'interruption': interruption,
                                'baseline': baseline_roles, 'resumed': resumed,
                                'retained_after_resume': retained_after_resume,
                                'retained_after_repeat': retained_after_repeat})

        corrupted = self.out/'corrupted_committed_copy'
        shutil.copytree(baseline, corrupted)
        first = json.loads((corrupted/'chunk_000000.json').read_text())
        victim = owned(corrupted/first['bullet'])
        before = identity(victim)
        with victim.open('r+b') as stream:
            byte = stream.read(1)
            if not byte: raise ValueError('negative-control shard is empty')
            stream.seek(0); stream.write(bytes((byte[0] ^ 1,))); stream.flush(); os.fsync(stream.fileno())
        corruption = {'before': before, 'after': identity(victim)}
        corruption['verify'] = self.launch('corrupt_verify', corrupted, action='verify',
                                             error_contains='sealed chunk hash mismatch:')
        corruption['resume'] = self.launch('corrupt_resume', corrupted, action='resume',
                                             error_contains='sealed chunk hash mismatch:')

        changed = self.out/'changed_input'
        changed.mkdir()
        pos, fen = changed/'source.pos', changed/'source.fen'
        shutil.copyfile(self.args.pos, pos); shutil.copyfile(self.args.fen, fen)
        self.launch('changed_input_checkpoint', changed/'output', inputs=(pos, fen), stop_after_chunks=1)
        input_before = identity(fen)
        lines = fen.read_text(encoding='utf-8').splitlines()
        fields = lines[0].split()
        if len(fields) != 6: raise ValueError('expected six-field FEN negative input')
        fields[-1] = str(int(fields[-1])+1)
        lines[0] = ' '.join(fields)
        # This is an explicitly named disposable negative-control copy only.
        with fen.open('w', encoding='utf-8', newline='\n') as stream:
            stream.write('\n'.join(lines)+'\n'); stream.flush(); os.fsync(stream.fileno())
        changed_result = self.launch('changed_input_resume', changed/'output', action='resume',
                                    inputs=(pos, fen), error_contains='resume config/source/tool identity mismatch')
        for item in self.inputs+self.original+self.candidate+self.harness:
            pinned(item)
        report = {'status': 'PASS', 'strength': 'UNPROVEN', 'real_adapter': True,
                  'upstream_scope': self.args.upstream_scope, 'training': 'NOT_RUN',
                  'native_probe': 'NOT_RUN_BY_THIS_HARNESS',
                  'scope': 'three deterministic converter output roles; no .hce output claim',
                  'rows': self.rows, 'source_regression': {'status': 'PASS',
                      'original': original_roles, 'modified': baseline_roles},
                  'faults': comparisons, 'corrupted_shard': corruption,
                  'changed_input': {'before': input_before, 'after': identity(fen),
                                    'detection': changed_result}, 'attempts': self.attempts,
                  'excluded_from_byte_identity': ['UUID directory names', 'receipt path strings',
                                                'operational elapsed reports', 'disposable indexes']}
        write_new(self.out/'RESTART_PROOF.json', report)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    child = commands.add_parser('worker'); child.add_argument('--spec', type=Path, required=True)
    proof = commands.add_parser('proof')
    proof.add_argument('--threads', type=int, choices=[1], required=True)
    for name in ('out', 'pos', 'fen', 'input-provenance'):
        proof.add_argument('--'+name, type=Path, required=True)
    for name in ('pos-sha256', 'fen-sha256', 'provenance-sha256'):
        proof.add_argument('--'+name, required=True)
    proof.add_argument('--upstream-scope', choices=('native-relabel', 'relabel-with-fixture-probe',
                                                   'frozen-fpos-sidecar'), required=True)
    proof.add_argument('--chunk-rows', type=int, default=1)
    args = parser.parse_args()
    if args.command == 'worker':
        worker(args.spec)
        return
    run = None
    out_preexisted = True
    try:
        out_preexisted = owned(args.out).exists()
        run = Proof(args)
        report = run.run()
        print(json.dumps({'status': report['status'], 'rows': report['rows'],
                          'real_adapter': True, 'upstream_scope': args.upstream_scope}))
    except BaseException as error:
        if run is not None:
            write_new(run.out/'FAILURE.json', {'status': 'FAIL', 'type': type(error).__name__,
                                             'error': str(error), 'attempts': run.attempts})
        elif not out_preexisted and owned(args.out).is_dir():
            write_new(owned(args.out)/'INITIAL_FAILURE.json', {'status': 'FAIL',
                      'type': type(error).__name__, 'error': str(error)})
        raise


if __name__ == '__main__':
    main()
