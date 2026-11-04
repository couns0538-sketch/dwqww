"""Runner fixtures use only owned synthetic inputs and the independent runtime."""
import json
import os
from pathlib import Path
import subprocess

import psutil
import pytest

ROOT = Path('D:/a14')


def test_selected_suite_excludes_training_collection():
    import r14_suite
    paths = r14_suite.selected_files()
    assert ROOT/'tests/test_r14_chain_evidence.py' in paths
    assert ROOT/'tests/test_r14_joba.py' in paths
    assert ROOT/'tests/test_r14_suite.py' in paths
    assert len(paths) == len(set(paths))
    assert all(path.is_relative_to(ROOT/'tests') for path in paths)
    assert not any('datafilter' in str(path) or path.parent.name in ('data', 'data2') for path in paths)
    assert not any(ROOT/'tests'/name in paths for name in r14_suite.DEFERRED_TESTS)


def test_pytest_controls_are_isolated_and_empty_configuration_is_pinned(tmp_path, monkeypatch):
    import r14_suite
    control = {'PYTEST_ADDOPTS': '-k nothing', 'PYTEST_PLUGINS': 'unwanted_fixture_plugin',
               'PYTEST_DEBUG': '1', 'R14_NATIVE_EXE': str(ROOT/'tools/r14_native/build/chain_native.exe')}
    monkeypatch.setattr(r14_suite.os, 'environ', control)
    configuration, native = r14_suite.prepare_configuration()
    assert control.get('PYTEST_ADDOPTS') is None
    assert control.get('PYTEST_PLUGINS') is None
    assert control.get('PYTEST_DEBUG') is None
    assert control['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] == '1'
    assert Path(control['R14_NATIVE_EXE']).name == 'chain_native_r03.exe'
    assert native['md5'] == '91427a99870d6b3775595db55f0a82e8'
    assert Path(configuration['path']).read_bytes() == b'[pytest]\n'
    bad = tmp_path/'changed.ini'
    bad.write_text('[pytest]\npython_functions = hidden_*\n')
    monkeypatch.setattr(r14_suite, 'CONFIGURATION', bad)
    with pytest.raises(ValueError, match='configuration identity'):
        r14_suite.prepare_configuration()


def test_changed_native_candidate_is_refused_before_collection(tmp_path, monkeypatch):
    import r14_suite
    candidate = tmp_path/'changed.exe'
    candidate.write_bytes(b'wrong candidate; never executed')
    monkeypatch.setattr(r14_suite, 'NATIVE', candidate)
    monkeypatch.setattr(r14_suite.os, 'environ', {})
    with pytest.raises(ValueError, match='native candidate identity'):
        r14_suite.prepare_configuration()


def test_missing_selected_file_cannot_pass_with_other_tests_green():
    import r14_suite
    results = r14_suite.Results()
    results.nodeids = ['tests/test_one.py::test_one']
    results.reports = [dict(nodeid=results.nodeids[0], when='call', outcome='passed', duration=0, kind='test')]
    files = [dict(path=str(ROOT/'tests/test_one.py')), dict(path=str(ROOT/'tests/test_two.py'))]
    report = r14_suite.assemble_report(results, 0, files, files, collect_only=False)
    assert report['status'] == 'UNVERIFIED'
    assert report['selected_file_coverage']['missing'] == [str(ROOT/'tests/test_two.py')]


def test_fixture_selection_cannot_use_source_or_external_paths():
    import r14_suite
    for path in (ROOT/'tools/r14_suite.py', Path('D:/a13/test_fixture.py')):
        with pytest.raises(ValueError):
            r14_suite.selected_files([str(path)])


def test_import_guard_refuses_training_modules_without_loading_them():
    import r14_suite
    guard = r14_suite.ImportGuard()
    for name in ('train', 'npt_adapter', 'train_adapter', 'torch', 'model.nnue', 'trainer.callbacks',
                 'NPT_ADAPTER', 'MODEL.nnue'):
        with pytest.raises(ImportError):
            guard.find_spec(name)
    assert guard.find_spec('chess') is None


def test_file_identity_change_is_incomplete(tmp_path):
    import r14_suite
    source = tmp_path/'test_fixture.py'
    source.write_text('def test_one(): pass\n')
    before = r14_suite.identities([source])
    source.write_text('def test_two(): pass\n')
    results = r14_suite.Results()
    results.nodeids = ['fixture::test_two']
    report = r14_suite.assemble_report(results, 0, before, r14_suite.identities([source]),
                                      collect_only=True)
    assert report['status'] == 'UNVERIFIED'
    assert report['files_unchanged'] is False


def test_postrun_identity_error_preserves_pytest_exit_code(tmp_path, monkeypatch):
    import sys
    import tempfile
    import r14_suite
    source = tmp_path/'test_fixture.py'
    source.write_text('def test_one(): pass\n')
    out = tmp_path/'run'
    (out/'tmp').mkdir(parents=True)
    original = r14_suite.identities
    selected_reads = 0

    def late_read_failure(paths):
        nonlocal selected_reads
        if paths == [source]:
            selected_reads += 1
            if selected_reads == 2:
                raise OSError('fixture post-run identity failure')
        return original(paths)

    monkeypatch.setattr(r14_suite, 'identities', late_read_failure)
    monkeypatch.setattr(r14_suite, 'selected_files', lambda fixtures: [source])
    monkeypatch.setattr(r14_suite, 'Resources', lambda seconds: lambda reserve=0: None)
    monkeypatch.setattr(r14_suite, 'install_boundary', lambda output: None)
    monkeypatch.setattr(r14_suite, 'prepare_configuration', lambda: ({'path': 'fixture.ini'}, {'path': 'fixture.exe'}))
    monkeypatch.setattr(tempfile, 'tempdir', tempfile.gettempdir())
    monkeypatch.setenv('R14_SUITE_CHILD', str(out))
    monkeypatch.setattr(sys, 'argv', ['r14_suite.py', '--out', str(out), '--seconds', '20'])
    monkeypatch.setattr(pytest, 'main', lambda *args, **kwargs: 0)
    assert r14_suite.main() == 2
    receipt = json.loads((out/'worker-result.json.part').read_text())
    assert receipt['status'] == 'UNVERIFIED'
    assert receipt['pytest_exit_code'] == 0
    assert receipt['selected_after'] is None
    assert 'post-run identity failure' in receipt['error']


FIXTURE = '''import os, sys
from pathlib import Path
import pytest

def test_pass():
    assert sys.executable.lower().replace('\\\\','/') == 'd:/a14/runtime/python/python.exe'
    assert os.environ['CUDA_VISIBLE_DEVICES'] == os.environ['HIP_VISIBLE_DEVICES'] == '-1'
    assert os.environ['OMP_NUM_THREADS'] == '1'

def test_fail():
    assert False, 'intentional runner fixture'

@pytest.mark.skip(reason='intentional runner fixture')
def test_skip(): pass

@pytest.fixture
def broken():
    raise RuntimeError('intentional setup error')

def test_error(broken): pass

def test_subcases(subtests):
    for value in (0, 1):
        with subtests.test(value=value):
            assert value == 0

def test_boundaries():
    for name in ('train','npt_adapter','torch'):
        with pytest.raises(ImportError): __import__(name)
    with pytest.raises(PermissionError):
        sys.audit('open', 'F:/nnue_pytorch/forbidden.py', 'r', os.O_RDONLY)
    with pytest.raises(PermissionError):
        sys.audit('open', 'C:/r14-forbidden-fixture.txt', 'w', os.O_WRONLY|os.O_CREAT)
    with open(os.devnull, 'w') as sink: sink.write('allowed sink')
'''


@pytest.mark.parametrize('collect_only', [False, True])
def test_real_pytest_receipts_are_exact_and_fixture_scoped(tmp_path, collect_only):
    source = tmp_path/'test_runner_fixture.py'
    source.write_text(FIXTURE)
    (tmp_path/'pytest.ini').write_text('[pytest]\npython_functions = test_pass\n')
    out = tmp_path/'run'
    command = ['pwsh', '-NoProfile', '-File', str(ROOT/'tools/Invoke-R14Suite.ps1'),
               '-Output', str(out), '-Cpu', str(psutil.Process().cpu_affinity()[0]),
               '-TimeoutSeconds', '45', '-FixtureJson', json.dumps([str(source)])]
    if collect_only:
        command.append('-CollectOnly')
    hostile = dict(os.environ, PYTEST_ADDOPTS='-k test_pass')
    hostile.pop('PYTEST_PLUGINS', None)
    child = subprocess.run(command, capture_output=True, text=True, timeout=65, env=hostile)
    assert child.returncode == (0 if collect_only else 1), child.stdout+child.stderr
    assert (out/'REPORT.json').is_file(), child.stdout+child.stderr
    report = json.loads((out/'REPORT.json').read_text())
    assert report['scope'] == 'runner_fixture'
    assert report['collected'] == 6
    assert report['files_unchanged'] is True
    assert report['selected_before'] == report['selected_after']
    assert report['configuration']['path'] == str(ROOT/'tools/r14_suite.ini')
    assert report['pytest_arguments'][report['pytest_arguments'].index('-c')+1] == report['configuration']['path']
    assert report['native']['md5'] == '91427a99870d6b3775595db55f0a82e8'
    assert report['supervision']['candidate_before'][report['native']['path']] == report['native']['md5']
    assert report['supervision']['candidate_after'][report['native']['path']] == report['native']['md5']
    assert report['supervision']['stop_reason'] is None
    assert report['started'].endswith(' Vienna') and report['finished'].endswith(' Vienna')
    if collect_only:
        assert report['status'] == 'COLLECTED'
        assert report['test_counts']['not_run'] == 6
        assert not report['reports']
    else:
        assert report['status'] == 'FAIL'
        assert report['test_counts'] == dict(passed=3, failed=1, skipped=1, error=1, not_run=0)
        assert report['subtest_counts'] == dict(passed=1, failed=1, skipped=0)
        assert report['pytest_exit_code'] == 1
    assert not (out/'REPORT.json.part').exists()


@pytest.mark.parametrize('failure', ['deadline', 'log_cap'])
def test_supervisor_stops_only_fixture_job_without_publishing(tmp_path, failure):
    source = tmp_path/'test_bounded_fixture.py'
    if failure == 'deadline':
        source.write_text('def test_wait():\n import time\n time.sleep(30)\n')
    else:
        source.write_text("def test_noise():\n while True: print('x'*512, flush=True)\n")
    out = tmp_path/'run'
    command = ['pwsh', '-NoProfile', '-File', str(ROOT/'tools/Invoke-R14Suite.ps1'),
               '-Output', str(out), '-Cpu', str(psutil.Process().cpu_affinity()[0]),
               '-TimeoutSeconds', '2' if failure == 'deadline' else '20',
               '-LogBytes', '4096', '-FixtureJson', json.dumps([str(source)])]
    child = subprocess.run(command, capture_output=True, text=True, timeout=40)
    assert child.returncode == 70, child.stdout+child.stderr
    assert ('DEADLINE' if failure == 'deadline' else 'LOG_CAP') in child.stdout
    assert not (out/'REPORT.json').exists()
    assert sum(path.stat().st_size for path in out.glob('*.log')) <= 4096
