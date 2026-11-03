"""Native setup regression fixtures; never install packages or use the network."""
import json
from pathlib import Path
import subprocess
import time

import pytest
import psutil

ROOT = Path('D:/a14')
SETUP = ROOT / 'tools/Setup-R14Runtime.ps1'
PYTHON = ROOT / 'runtime/python/python.exe'
KEYS = ['TEMP', 'TMP', 'PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE',
        'CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES', 'OMP_NUM_THREADS',
        'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'PIP_CACHE_DIR']


def quoted(path):
    return "'" + str(path).replace("'", "''") + "'"


def run_fixture(tmp_path, *, child_exit=0, guard_after=0, delay=0, timeout=30,
                descendant=False, descendant_delay=30, unset=False, explicit=True):
    assert tmp_path.resolve().is_relative_to(ROOT)
    parent = tmp_path / 'parent.json'
    child = tmp_path / 'child.json'
    probe = tmp_path / 'probe.py'
    probe.write_text('import json,os,sys,time,subprocess,psutil\nfrom pathlib import Path\n'
                     + f'values={{k:os.environ.get(k) for k in {KEYS!r}}}\n'
                     + "values['_pid']=os.getpid()\nvalues['_priority']=int(psutil.Process().nice())\n"
                     + (f"values['_descendant']=subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep({descendant_delay})'],stdout=sys.stdout,stderr=sys.stderr).pid\n" if descendant else '')
                     + f'Path({str(child)!r}).write_text(json.dumps(values))\n'
                     + f'time.sleep({delay})\nsys.exit({child_exit})\n', encoding='utf-8')
    source = SETUP.read_text(encoding='utf-8-sig')
    mock = ''
    if '[switch]$Fixture' in source:
        invocation = (f'& {quoted(SETUP)} ' + ('-Fixture ' if explicit else '')
                      + f'-FixtureScript {quoted(probe)} -FixtureFailGuardAfter {guard_after} -ChildTimeoutSeconds {timeout}')
    else:
        # The baseline has no test entrypoint. Redirect its literal owned root
        # into this fixture, then replace its pip command with one native probe.
        old_root = "$root='D:\\a14'"
        assert source.count(old_root) == 1, 'baseline fixture adapter no longer applies'
        isolated = tmp_path / 'setup.ps1'
        isolated.write_text(source.replace(old_root, '$root=' + quoted(tmp_path)), encoding='utf-8')
        local_python = tmp_path / 'runtime/python/python.exe'
        local_python.parent.mkdir(parents=True)
        local_python.write_bytes(b'not executable; shadowed by fixture function')
        downloads = tmp_path / 'runtime/downloads'
        downloads.mkdir()
        (downloads / 'python-3.12.10-embed-amd64.zip').write_bytes(b'fixture')
        (downloads / 'get-pip.py').write_text('# fixture\n', encoding='ascii')
        mock = (f'function global:{local_python} {{ & {quoted(PYTHON)} -I -B {quoted(probe)}; '
                '$global:LASTEXITCODE=$LASTEXITCODE }\n')
        invocation = f'& {quoted(isolated)}'
    harness = tmp_path / 'harness.ps1'
    harness.write_text("$ErrorActionPreference='Stop'\n"
                       "[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'\n"
                       + ''.join((f"Remove-Item -LiteralPath 'Env:{key}' -ErrorAction SilentlyContinue\n" if unset else
                                  f"$env:{key}='sentinel-{key}'\n") for key in KEYS)
                       + mock + "$failure=$null\ntry {\n" + invocation
                       + "\n} catch { $failure=$_.Exception.Message }\n$values=@{}\n"
                       + ''.join(f"$values['{key}']=$env:{key}\n" for key in KEYS)
                       + f"@{{env=$values;failure=$failure;priority=[string][Diagnostics.Process]::GetCurrentProcess().PriorityClass}} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath {quoted(parent)} -Encoding utf8\n", encoding='utf-8')
    process = subprocess.run(['pwsh', '-NoProfile', '-File', str(harness)], capture_output=True,
                             text=True, timeout=40)
    assert process.returncode == 0, process.stdout + process.stderr
    return json.loads(parent.read_text(encoding='utf-8-sig')), child


@pytest.mark.parametrize('exit_code', [0, 7])
def test_setup_preserves_caller_environment_and_priority(tmp_path, exit_code):
    parent, child_path = run_fixture(tmp_path, child_exit=exit_code)
    assert parent['env'] == {key: f'sentinel-{key}' for key in KEYS}
    assert parent['priority'] == 'BelowNormal'
    assert bool(parent['failure']) is bool(exit_code)
    child = json.loads(child_path.read_text(encoding='utf-8'))
    assert child['CUDA_VISIBLE_DEVICES'] == child['HIP_VISIBLE_DEVICES'] == '-1'
    assert child['OMP_NUM_THREADS'] == child['OPENBLAS_NUM_THREADS'] == child['MKL_NUM_THREADS'] == '1'
    assert Path(child['TEMP']).is_relative_to(ROOT)
    assert child['_priority'] == int(psutil.IDLE_PRIORITY_CLASS)


def test_unset_caller_environment_is_restored(tmp_path):
    parent, _ = run_fixture(tmp_path, unset=True)
    assert parent['env'] == dict.fromkeys(KEYS)
    assert parent['failure'] is None


@pytest.mark.parametrize('kind', ['guard', 'timeout'])
def test_live_refusal_stops_only_owned_process_tree(tmp_path, kind):
    parent, path = run_fixture(tmp_path, guard_after=1 if kind == 'guard' else 0,
                               timeout=1 if kind == 'timeout' else 30, delay=30, descendant=True)
    assert ('resource refusal' if kind == 'guard' else 'timeout') in parent['failure']
    assert parent['env'] == {key: f'sentinel-{key}' for key in KEYS}
    child = json.loads(path.read_text(encoding='utf-8'))
    assert not psutil.pid_exists(child['_pid'])
    deadline = time.monotonic() + 2
    while psutil.pid_exists(child['_descendant']) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not psutil.pid_exists(child['_descendant'])


def test_fixture_options_cannot_activate_without_explicit_switch(tmp_path):
    parent, child = run_fixture(tmp_path, explicit=False)
    assert 'require explicit -Fixture' in parent['failure']
    assert not child.exists()
    assert parent['env'] == {key: f'sentinel-{key}' for key in KEYS}


def test_direct_exit_cannot_leave_descendant_holding_capture(tmp_path):
    started = time.monotonic()
    parent, path = run_fixture(tmp_path, descendant=True, descendant_delay=6, delay=0, timeout=1)
    elapsed = time.monotonic() - started
    assert elapsed < 4, f'capture ignored timeout after direct child exit: {elapsed:.2f}s'
    child = json.loads(path.read_text(encoding='utf-8'))
    deadline = time.monotonic() + 2
    while psutil.pid_exists(child['_descendant']) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not psutil.pid_exists(child['_descendant'])
    assert parent['env'] == {key: f'sentinel-{key}' for key in KEYS}


def test_resource_boundaries_and_allocation_reserve(tmp_path):
    source = SETUP.read_text(encoding='utf-8-sig')
    assert '[switch]$Fixture' in source
    probe = tmp_path / 'probe.py'
    probe.write_text('pass\n', encoding='ascii')
    harness = tmp_path / 'resource-boundaries.ps1'
    report = tmp_path / 'boundaries.json'
    harness.write_text("$ErrorActionPreference='Stop'\n"
                       "[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'\n"
                       + f'. {quoted(SETUP)} -Fixture -FixtureScript {quoted(probe)}\n'
                       + "$script:dFree=50GB;$script:cFree=30GB;$script:owned=0\n"
                       + "function Get-PSDrive([string]$Name) { if ($Name -eq 'D') { return @{Free=$script:dFree} }; return @{Free=$script:cFree} }\n"
                       + "function Get-R14OwnedBytes { return $script:owned }\n"
                       + "$results=@{}\n"
                       + "try { Assert-R14Resources; $results['exact_floors']='PASS' } catch { $results['exact_floors']=$_.Exception.Message }\n"
                       + "try { Assert-R14Resources 1; $results['d_reserve']='BAD' } catch { $results['d_reserve']=$_.Exception.Message }\n"
                       + "$script:dFree=80GB;$script:cFree=30GB-1\n"
                       + "try { Assert-R14Resources; $results['c_floor']='BAD' } catch { $results['c_floor']=$_.Exception.Message }\n"
                       + "$script:cFree=30GB;$script:owned=4999999999\n"
                       + "try { Assert-R14Resources 1; $results['owned_cap']='BAD' } catch { $results['owned_cap']=$_.Exception.Message }\n"
                       + f'$results | ConvertTo-Json | Set-Content -LiteralPath {quoted(report)} -Encoding utf8\n', encoding='utf-8')
    result = subprocess.run(['pwsh', '-NoProfile', '-File', str(harness)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    values = json.loads(report.read_text(encoding='utf-8-sig'))
    assert values['exact_floors'] == 'PASS'
    assert 'D:' in values['d_reserve']
    assert 'C:' in values['c_floor']
    assert '5 GB' in values['owned_cap']
