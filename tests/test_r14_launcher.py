"""Native child environment isolation regression checks."""
import json
import hashlib
from pathlib import Path
import subprocess
import time

import pytest
import psutil

ROOT = Path('D:/a14')
LAUNCHER = ROOT / 'tools/Invoke-R13.ps1'


def test_requires_seven_and_owns_runtime():
    source = LAUNCHER.read_text(encoding='utf-8-sig')
    assert source.startswith('#Requires -Version 7')
    assert 'F:\\nnue_pytorch' not in source
    assert 'D:\\a11\\runtime' not in source


def test_child_environment_and_parent_preserved(tmp_path):
    assert tmp_path.resolve().is_relative_to(ROOT)
    probe = tmp_path / 'probe with spaces.py'
    child_out = tmp_path / 'child.json'
    parent_out = tmp_path / 'parent.json'
    keys = ['CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES', 'TEMP', 'PYTHONPATH', 'ASTRA_R14_DEADLINE', 'ASTRA_R13_DEADLINE']
    probe.write_text('import os,json,sys\nfrom pathlib import Path\n'
                     f'Path({str(child_out)!r}).write_text(json.dumps(dict(executable=sys.executable,arguments=sys.argv[1:],env={{k:os.environ.get(k) for k in {keys!r}}})))\n'
                     + "print('native_stdout')\nprint('native_stderr',file=sys.stderr)\n", encoding='utf-8')
    harness = tmp_path / 'harness.ps1'
    run_name = 'launcher-' + hashlib.sha256(str(tmp_path).encode()).hexdigest()[:12]
    harness.write_text("$ErrorActionPreference='Stop'\n"
                       "[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'\n"
                       + ''.join(f"$env:{key}='{1 if key.endswith('DEADLINE') else 'sentinel-'+key}'\n" for key in keys)
                       + f"& '{LAUNCHER}' -Script '{probe}' -ScriptArguments @('space arg','quote\"arg','trail\\','') -RunName '{run_name}' -TimeoutSeconds 30\n"
                       + "$exit=$LASTEXITCODE\n"
                       + "$values=@{}\n"
                       + ''.join(f"$values['{key}']=$env:{key}\n" for key in keys)
                       + f"$values | ConvertTo-Json | Set-Content -LiteralPath '{parent_out}' -Encoding utf8\n"
                       + "exit $exit\n", encoding='utf-8')
    proc = subprocess.run(['pwsh', '-NoProfile', '-File', str(harness)], capture_output=True, text=True, timeout=45)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert 'native_stdout' in proc.stdout and 'native_stderr' in proc.stdout
    parent = json.loads(parent_out.read_text(encoding='utf-8-sig'))
    assert parent == {key: '1' if key.endswith('DEADLINE') else f'sentinel-{key}' for key in keys}
    child = json.loads(child_out.read_text(encoding='utf-8'))
    assert child['arguments'] == ['space arg', 'quote"arg', 'trail\\', '']
    assert Path(child['executable']).is_relative_to(ROOT / 'runtime')
    assert child['env']['CUDA_VISIBLE_DEVICES'] == '-1'
    assert child['env']['HIP_VISIBLE_DEVICES'] == '-1'
    assert Path(child['env']['TEMP']).is_relative_to(ROOT)
    assert child['env']['PYTHONPATH'] == str(ROOT / 'tools')
    assert child['env']['ASTRA_R14_DEADLINE'] == child['env']['ASTRA_R13_DEADLINE']
    assert time.time() < float(child['env']['ASTRA_R14_DEADLINE']) <= time.time() + 31


def test_storage_cap_rejects_before_child_and_preserves_parent(tmp_path):
    probe = tmp_path / 'probe.py'
    marker = tmp_path / 'started'
    probe.write_text(f'from pathlib import Path\nPath({str(marker)!r}).touch()\n', encoding='utf-8')
    harness = tmp_path / 'storage.ps1'
    harness.write_text("$ErrorActionPreference='Stop'\n"
                       "$env:TEMP='unchanged'\n"
                       "function Get-ChildItem { param($LiteralPath,[switch]$Recurse,[switch]$File,[switch]$Force)\n"
                       "[pscustomobject]@{Length=5000000000L}\n}\n"
                       f"try {{ & '{LAUNCHER}' -Script '{probe}' -RunName 'storage-test' -TimeoutSeconds 2; throw 'accepted' }}\n"
                       "catch { if ($_.Exception.Message -notmatch 'storage cap') { throw } }\n"
                       "if ($env:TEMP -ne 'unchanged') { throw 'parent environment changed' }\n", encoding='utf-8')
    run = subprocess.run(['pwsh', '-NoProfile', '-File', str(harness)], capture_output=True, text=True, timeout=15)
    assert run.returncode == 0, run.stdout + run.stderr
    assert not marker.exists()


@pytest.mark.parametrize('phase', ['during', 'after'])
def test_owned_cap_after_child_never_allocates_receipt(tmp_path, phase):
    probe = tmp_path / 'probe.py'
    marker = tmp_path / 'child-started'
    parent_out = tmp_path / 'parent.json'
    probe.write_text('from pathlib import Path\nimport time\n'
                     + f'Path({str(marker)!r}).touch()\n'
                     + ('time.sleep(20)\n' if phase == 'during' else ''), encoding='utf-8')
    run_name = 'cap-' + hashlib.sha256(str(tmp_path).encode()).hexdigest()[:12]
    run_directory = ROOT / 'evidence/test_logs/r14/launchers' / run_name
    harness = tmp_path / 'post-cap.ps1'
    keys = ['TEMP', 'PYTHONPATH', 'CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES']
    harness.write_text("$ErrorActionPreference='Stop'\n"
                       "[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'\n"
                       + ''.join(f"$env:{key}='sentinel-{key}'\n" for key in keys)
                       + "$global:fixtureGetChildItem=Get-Command Microsoft.PowerShell.Management\\Get-ChildItem\n"
                       + "function Get-ChildItem {\n[CmdletBinding()] param([string[]]$LiteralPath,[switch]$Recurse,[switch]$File,[switch]$Force)\n"
                       + f"if ($LiteralPath.Count -eq 1 -and $LiteralPath[0] -eq 'D:\\a14' -and (Test-Path -LiteralPath '{marker}')) {{\n"
                       + "return [pscustomobject]@{Length=5000000000L}\n}\n"
                       + "& $global:fixtureGetChildItem @PSBoundParameters\n}\n"
                       + f"& '{LAUNCHER}' -Script '{probe}' -RunName '{run_name}' -TimeoutSeconds 30\n"
                       + "$nativeExit=$LASTEXITCODE\n$values=@{}\n"
                       + ''.join(f"$values['{key}']=$env:{key}\n" for key in keys)
                       + f"@{{env=$values;priority=[string][Diagnostics.Process]::GetCurrentProcess().PriorityClass}} | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath '{parent_out}' -Encoding utf8\n"
                       + "exit $nativeExit\n", encoding='utf-8')
    process = subprocess.run(['pwsh', '-NoProfile', '-File', str(harness)], capture_output=True, text=True, timeout=45)
    assert marker.exists(), process.stdout + process.stderr
    assert process.returncode == 70, process.stdout + process.stderr
    assert 'OWNED_STORAGE_CAP' in process.stdout
    assert 'SOURCE_CHANGED' not in process.stdout
    assert not (run_directory / 'receipt.json').exists()
    parent = json.loads(parent_out.read_text(encoding='utf-8-sig'))
    assert parent['env'] == {key: f'sentinel-{key}' for key in keys}
    assert parent['priority'] == 'BelowNormal'


def test_exited_child_cannot_leave_descendant_holding_pipes(tmp_path):
    probe = tmp_path / 'pipe_probe.py'
    child_out = tmp_path / 'descendant.json'
    probe.write_text('import json,subprocess,sys,time\nfrom pathlib import Path\n'
                     "child=subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep(6)'],stdout=sys.stdout,stderr=sys.stderr)\n"
                     + f'Path({str(child_out)!r}).write_text(json.dumps(dict(pid=child.pid,started=time.monotonic())))\n', encoding='utf-8')
    name = 'pipes-' + hashlib.sha256(str(tmp_path).encode()).hexdigest()[:12]
    harness = tmp_path / 'pipes.ps1'
    harness.write_text("[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'\n"
                       + f"& '{LAUNCHER}' -Script '{probe}' -RunName '{name}' -TimeoutSeconds 2\nexit $LASTEXITCODE\n", encoding='utf-8')
    process = subprocess.Popen(['pwsh', '-NoProfile', '-File', str(harness)], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    admission_deadline = time.monotonic() + 12
    child = None
    while child is None and process.poll() is None and time.monotonic() < admission_deadline:
        try:
            child = json.loads(child_out.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.02)
    if child is None:
        stdout, stderr = process.communicate(timeout=15)
        pytest.fail(stdout + stderr + '\nchild marker missing')
    pid = child['pid']
    # Source hashing is outside child execution; measure the descendant itself.
    deadline = child['started'] + 3
    while psutil.pid_exists(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    stopped_in_time = not psutil.pid_exists(pid)
    stdout, stderr = process.communicate(timeout=15)
    assert process.returncode == 0, stdout + stderr
    assert stopped_in_time, 'descendant holding capture survived the bounded cleanup'
