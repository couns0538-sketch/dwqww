"""CPU-only qualification of the existing copied datafilter tests. UNPROVEN.

NPT stays an external, explicitly declared read-only runtime. No training loop
or optimizer update is permitted. Missing/incompatible dependencies are errors,
never skips or substitute fixture passes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import toolchain_binding
import runtime_binding

sys.dont_write_bytecode = True
ROOT = Path('D:/a10')
HERE = Path(__file__).resolve().parent
RUNTIME = ROOT/'job3/runtime312'
NPT = Path('D:/grok-pc-data/npt/nnue-pytorch-amd')
DLL = NPT/'build/libtraining_data_loader.dll'
NPT_SOURCE_TREES = ('data_loader', 'ddp_utils', 'model', 'trainer')


def own(path):
    path = Path(path)
    if not path.is_absolute() or path.resolve() == ROOT.resolve() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('write/output path must resolve strictly under D:/a10')
    return path.resolve()


def identity(path):
    path = Path(path).resolve(strict=True)
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            sha.update(block)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha.hexdigest()}


def write_new(path, value):
    with own(path).open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def write_guard(event, args):
    # This is a Python-I/O fail-safe, not an OS sandbox for native libraries.
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, int):
            return  # descriptor was obtained through its earlier checked open
        writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        writing = writing or isinstance(mode, str) and any(c in mode for c in 'wax+')
        if writing:
            own(os.path.abspath(os.fsdecode(path)))
    elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.utime'):
        if not isinstance(args[0], int):
            own(os.path.abspath(os.fsdecode(args[0])))
    elif event in ('os.rename', 'os.link', 'os.symlink'):
        for path in args[:2]:
            own(os.path.abspath(os.fsdecode(path)))


def code_inputs():
    record = json.loads((HERE/'SOURCE_COPY.json').read_text(encoding='utf-8-sig'))
    if record['source_commit'] != 'd8982bc0':
        raise ValueError('wrong frozen regression source')
    pinned = [identity(__file__), identity(HERE/'SOURCE_COPY.json'), identity(HERE/'toolchain_binding.py'), identity(HERE/'runtime_binding.py')]
    for item in record['final_files']:
        actual = identity(item['path'])
        if actual['sha256'].lower() != item['sha256'].lower():
            raise ValueError('copied suite changed: '+item['path'])
        pinned.append(actual)
    for item in record['reviewed_overlays']:
        actual = identity(item['target'])
        if actual['sha256'].lower() != item['sha256'].lower():
            raise ValueError('reviewed overlay changed: '+item['target'])
    pinned.append(identity(HERE/'full_state.py'))
    return pinned


def imported_npt_identity():
    files = {str(DLL.resolve(strict=True))}
    for module in list(sys.modules.values()):
        file = getattr(module, '__file__', None)
        if file and Path(file).resolve().is_relative_to(NPT.resolve()):
            files.add(str(Path(file).resolve(strict=True)))
    return {path: identity(path) for path in sorted(files)}


def prebind_npt_sources():
    """Hash external code only; never copy or edit GPL runtime sources."""
    files = set(NPT.glob('*.py'))
    for name in NPT_SOURCE_TREES:
        tree = NPT/name
        if not tree.is_dir():
            raise ValueError('declared NPT source tree missing: '+str(tree))
        for folder, directories, filenames in os.walk(tree, followlinks=False):
            for entry in [Path(folder), *(Path(folder)/name for name in directories)]:
                if entry.is_symlink() or getattr(entry.lstat(), 'st_file_attributes', 0) & 0x400:
                    raise ValueError('reparse source path refused: '+str(entry))
            files.update(Path(folder)/name for name in filenames if name.endswith('.py'))
    files.add(DLL)
    for path in files:
        if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('reparse source file refused: '+str(path))
        if not path.resolve(strict=True).is_relative_to(NPT.resolve(strict=True)):
            raise ValueError('NPT source escaped declared root')
    return {str(path.resolve(strict=True)): identity(path) for path in sorted(files)}


def verify_npt_binding(bound):
    imported = imported_npt_identity()
    for path, item in imported.items():
        if path not in bound:
            raise ValueError('imported NPT file was not bound before import: '+path)
        if bound[path] != item:
            raise ValueError('imported NPT file differs from pre-import binding: '+path)
    current = prebind_npt_sources()
    if current != bound:
        raise ValueError('declared NPT source set or bytes changed during checks')
    return imported


class Results:
    def __init__(self):
        self.collected = []
        self.reports = []
        self.exitstatus = None

    def pytest_collection_finish(self, session):
        self.collected = [item.nodeid for item in session.items]

    def pytest_runtest_logreport(self, report):
        self.reports.append({'nodeid': report.nodeid, 'when': report.when,
                             'outcome': report.outcome, 'duration': report.duration})

    def pytest_sessionfinish(self, session, exitstatus):
        self.exitstatus = int(exitstatus)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threads', type=int, choices=[2], required=True,
                        help='maximum: existing filter tests exercise workers=2; Torch/BLAS stay1')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--preflight-only', action='store_true')
    parser.add_argument('--runtime-manifest-sha256', required=True)
    args = parser.parse_args()
    out = own(args.out)
    if not out.is_relative_to(ROOT/'job3/regression-runs'):
        raise ValueError('native runtime cache/output must stay outside Git under D:/a10/job3/regression-runs')
    out.mkdir(parents=True, exist_ok=False)
    for name in ('cache', 'temp', 'runtime_receipts', 'pycache'):
        (out/name).mkdir()
    for volume, reserve in (('C:/',30*1024**3), ('D:/',50*1024**3+128*1024**2)):
        if shutil.disk_usage(volume).free < reserve:
            raise ValueError('disk floor/reservation unavailable: '+volume)
    package_path = str(RUNTIME/'packages')
    os.environ.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
        PYTHONPATH=os.pathsep.join((package_path, str(HERE/'datafilter'), str(HERE))),
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', ASTRA_REGRESSION_OUTPUT=str(out),
        PYTHONPYCACHEPREFIX=str(out/'pycache'),
        ASTRA_NPT_ROOT=str(NPT), NNUE_DATA_LOADER_LIB=str(DLL),
        CUDA_VISIBLE_DEVICES='', HIP_VISIBLE_DEVICES='', ROCR_VISIBLE_DEVICES='',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
        NUMEXPR_NUM_THREADS='1', TORCHINDUCTOR_COMPILE_THREADS='1', MAX_JOBS='1',
        WORLD_SIZE='1', RANK='0', LOCAL_RANK='0',
        TEMP=str(out/'temp'), TMP=str(out/'temp'), TMPDIR=str(out/'temp'),
        XDG_CACHE_HOME=str(out/'cache'), MPLCONFIGDIR=str(out/'cache/matplotlib'),
        TORCH_HOME=str(out/'cache/torch'), TORCHINDUCTOR_CACHE_DIR=str(out/'cache/inductor'),
        TRITON_CACHE_DIR=str(out/'cache/triton'), NUMBA_CACHE_DIR=str(out/'cache/numba'))
    sys.path[:0] = [package_path, str(HERE/'datafilter'), str(HERE)]
    # A fresh cache prefix forces source reads instead of preexisting unbound
    # external .pyc files. Bytecode writes remain disabled, including children.
    sys.pycache_prefix = str(out/'pycache')
    sys.addaudithook(write_guard)
    started = time.time()
    stage = 'source-binding'
    reports = Results()
    before = {}
    toolchain_before = {}
    code = []
    step_handle = None
    trainer_type = old_fit = None
    optimizer_calls = []
    try:
        if Path(sys.executable).resolve() != (RUNTIME/'python/python.exe').resolve(strict=True):
            raise ValueError('wrong CPU interpreter')
        if sys.version_info < (3, 12):
            raise ValueError('external NPT requires Python3.12 or newer')
        code = code_inputs()
        stage = 'private-runtime-binding'
        runtime_before = runtime_binding.verify(RUNTIME, args.runtime_manifest_sha256)
        write_new(out/'RUNTIME_BOUND_BEFORE.json',runtime_before)
        stage = 'external-readonly-prebinding'
        before = prebind_npt_sources()
        write_new(out/'NPT_SOURCES_BEFORE.json', {'scope':{'root_python_files':str(NPT/'*.py'),
            'python_trees':list(NPT_SOURCE_TREES), 'native_library':str(DLL)}, 'files':before})
        stage = 'readonly-toolchain-binding'
        compiler_environment = toolchain_binding.environment(RUNTIME/'python')
        toolchain_before = toolchain_binding.snapshot()
        write_new(out/'TOOLCHAIN_BEFORE.json', {'environment':compiler_environment, 'files':toolchain_before})
        stage = 'cpu-dependency-import'
        import numpy
        import pytest
        import torch
        import chess
        import psutil
        torch.set_num_threads(1); torch.set_num_interop_threads(1)
        if torch.version.cuda is not None or torch.version.hip is not None or '+cpu' not in torch.__version__:
            raise ValueError('CPU-only Torch is required')
        for module in (numpy, pytest, torch, chess, psutil):
            if not Path(module.__file__).resolve().is_relative_to(RUNTIME.resolve()):
                raise ValueError('dependency escaped declared private D runtime: '+module.__name__)
        proc = psutil.Process()
        if proc.nice() != psutil.IDLE_PRIORITY_CLASS or len(proc.cpu_affinity()) > 2:
            raise ValueError('Idle and at most2 explicit CPUs required')
        runtime = {'python':sys.version, 'torch':torch.__version__, 'numpy':numpy.__version__,
                   'pytest':pytest.__version__, 'threads':torch.get_num_threads(),
                   'interop_threads':torch.get_num_interop_threads(), 'affinity':proc.cpu_affinity(),
                   'priority':'Idle', 'cuda':torch.version.cuda, 'hip':torch.version.hip,
                   'historical_runtime':'DIFFERENT; this is the newly isolated Python3.12 CPU runtime; versions recorded above',
                   'external_npt_root':str(NPT), 'external_loader':identity(DLL)}
        write_new(out/'CPU_RUNTIME.json', runtime)
        stage = 'external-readonly-import'
        import npt_adapter
        import train
        if npt_adapter.NPT != NPT.resolve():
            raise ValueError('wrong external NPT runtime')
        initial_imported = verify_npt_binding(before)
        write_new(out/'NPT_IMPORTED_INITIAL.json', initial_imported)

        # These tests deliberately intercept fit to prove construction/checkpoint
        # integration. A hidden call to the real training loop must fail closed.
        trainer_type = train.SimpleTrainer
        old_fit = trainer_type.fit
        def forbidden_fit(*unused_args, **unused_kwargs):
            raise RuntimeError('training loop is forbidden in regression qualification')
        trainer_type.fit = forbidden_fit
        from torch.optim.optimizer import register_optimizer_step_pre_hook
        def forbid_optimizer_step(optimizer, positional, keyword):
            optimizer_calls.append(type(optimizer).__name__)
            raise RuntimeError('optimizer update is forbidden in regression qualification')
        step_handle = register_optimizer_step_pre_hook(forbid_optimizer_step)
        if args.preflight_only:
            stage = 'preflight-complete'
            exitcode = 0
        else:
            stage = 'existing-regression-suite'
            argv = ['-q', '--maxfail=1', '-p', 'no:cacheprovider',
                    '--basetemp', str(out/'pytest-temp'), '--rootdir', str(HERE/'datafilter'),
                    '--confcutdir', str(HERE/'datafilter/tests'), str(HERE/'datafilter/tests')]
            write_new(out/'PYTEST_COMMAND.json', {'argv':argv, 'source_commit':'d8982bc0',
                       'test_modifications':'fixture output path only; test assertions unchanged',
                       'historical_fixture_seeds':'unchanged deterministic unit-test inputs; no new training/experiment seed'})
            exitcode = int(pytest.main(argv, plugins=[reports]))
        after = verify_npt_binding(before)
        write_new(out/'NPT_IMPORTED_AFTER.json', after)
        write_new(out/'NPT_SOURCES_AFTER.json', {'files':prebind_npt_sources()})
        stage = 'final-toolchain-binding'
        toolchain_after = toolchain_binding.snapshot()
        write_new(out/'TOOLCHAIN_AFTER.json', {'files':toolchain_after})
        if toolchain_after != toolchain_before:
            raise ValueError('installed read-only compiler/header/library input changed during checks')
        stage = 'final-private-runtime-binding'
        runtime_after = runtime_binding.verify(RUNTIME, args.runtime_manifest_sha256)
        write_new(out/'RUNTIME_BOUND_AFTER.json',runtime_after)
        if runtime_after != runtime_before:
            raise ValueError('private CPU runtime changed during checks')
        for item in code:
            if identity(item['path']) != item:
                raise ValueError('copied regression input changed during checks')
        if optimizer_calls:
            raise ValueError('forbidden optimizer step was attempted')
        calls = [r for r in reports.reports if r['when']=='call']
        failures = [r for r in reports.reports if r['outcome']=='failed']
        skips = [r for r in reports.reports if r['outcome']=='skipped']
        passing = sum(r['outcome']=='passed' for r in calls)
        qualified = exitcode == 0 and not failures and not skips
        if not args.preflight_only:
            qualified = qualified and len(reports.collected) >= 73 and passing == len(reports.collected)
        result = dict(status=('PREFLIGHT_PASS' if args.preflight_only else 'PASS') if qualified else 'FAIL',
            classification='UNPROVEN', stage=stage, preflight_only=args.preflight_only,
            pytest_exitcode=exitcode, collected=len(reports.collected), passed=passing,
            failures=len(failures), skipped=len(skips), nodeids=reports.collected, reports=reports.reports,
            elapsed_seconds=time.time()-started, runtime=runtime,
            external_runtime_unchanged=True, optimizer_updates=0, training_loops=0,
            toolchain_unchanged=True, compiler_environment=compiler_environment,
            private_runtime_unchanged=True, private_runtime_binding=runtime_before,
            external_binding_scope='all declared NPT Python sources and loader DLL bound before any import, all observed imported NPT files required prebound, all declared files rechecked afterward',
            write_guard_scope='Python audit hook in this process; not inherited by children and not an OS sandbox. Reviewed child commands inherit D-only cache/output and bytecode-disabled environment.',
            limits='CPU only; max2 filter workers, Torch/interop/BLAS1; no GPU; external GPL sources remain external',
            source_binding=identity(HERE/'SOURCE_COPY.json'))
        write_new(out/'RESULT.json', result)
        print(json.dumps({k:result[k] for k in ('status','stage','collected','passed','failures','skipped')}))
        return 0 if qualified else 1
    except BaseException as error:
        write_new(out/'FAILURE.json', {'status':'FAIL', 'classification':'UNPROVEN', 'stage':stage,
            'type':type(error).__name__, 'error':str(error), 'collected':len(reports.collected),
            'reports':reports.reports, 'elapsed_seconds':time.time()-started,
            'compatibility_note':'No historical73-test PASS is claimed; CPU/runtime compatibility must be assessed.'})
        raise
    finally:
        if step_handle is not None: step_handle.remove()
        if trainer_type is not None: trainer_type.fit = old_fit


if __name__ == '__main__':
    raise SystemExit(main())
