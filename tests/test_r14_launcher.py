"""Native child environment isolation regression checks."""
import json
import hashlib
from pathlib import Path
import subprocess

ROOT = Path('D:/a14')
LAUNCHER = ROOT / 'tools/Invoke-R13.ps1'


def test_requires_seven_and_owns_runtime():
    source = LAUNCHER.read_text(encoding='utf-8-sig')
    assert source.startswith('#Requires -Version 7')
    assert 'F:\\nnue_pytorch' not in source
    assert 'D:\\a11\\runtime' not in source


def test_child_environment_and_parent_preserved(tmp_path):
    assert tmp_path.resolve().is_relative_to(ROOT)
    probe = tmp_path / 'probe.py'
    child_out = tmp_path / 'child.json'
    parent_out = tmp_path / 'parent.json'
    keys = ['CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES', 'TEMP', 'PYTHONPATH']
    probe.write_text('import os,json,sys\nfrom pathlib import Path\n'
                     f'Path({str(child_out)!r}).write_text(json.dumps(dict(executable=sys.executable,env={{k:os.environ.get(k) for k in {keys!r}}})))\n', encoding='utf-8')
    harness = tmp_path / 'harness.ps1'
    run_name = 'launcher-' + hashlib.sha256(str(tmp_path).encode()).hexdigest()[:12]
    harness.write_text("$ErrorActionPreference='Stop'\n"
                       "[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'\n"
                       + ''.join(f"$env:{key}='sentinel-{key}'\n" for key in keys)
                       + f"& '{LAUNCHER}' -Script '{probe}' -RunName '{run_name}' -TimeoutSeconds 30\n"
                       + "$exit=$LASTEXITCODE\n"
                       + "$values=@{}\n"
                       + ''.join(f"$values['{key}']=$env:{key}\n" for key in keys)
                       + f"$values | ConvertTo-Json | Set-Content -LiteralPath '{parent_out}' -Encoding utf8\n"
                       + "exit $exit\n", encoding='utf-8')
    proc = subprocess.run(['pwsh', '-NoProfile', '-File', str(harness)], capture_output=True, text=True, timeout=45)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    parent = json.loads(parent_out.read_text(encoding='utf-8-sig'))
    assert parent == {key: f'sentinel-{key}' for key in keys}
    child = json.loads(child_out.read_text(encoding='utf-8'))
    assert Path(child['executable']).is_relative_to(ROOT / 'runtime')
    assert child['env']['CUDA_VISIBLE_DEVICES'] == '-1'
    assert child['env']['HIP_VISIBLE_DEVICES'] == '-1'
    assert Path(child['env']['TEMP']).is_relative_to(ROOT)
    assert child['env']['PYTHONPATH'] == str(ROOT / 'tools')
