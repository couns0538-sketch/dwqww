"""Native PowerShell resource-guard regressions with controlled disk observations."""
from pathlib import Path
import json
import hashlib
import subprocess

ROOT = Path('D:/a14')
PS5 = r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'


def test_observation_has_monotonic_clock_on_ps51(tmp_path):
    name = 'ps51-' + hashlib.sha256(str(tmp_path).encode()).hexdigest()[:12]
    run = subprocess.run([PS5, '-NoProfile', '-File', str(ROOT / 'tools/Observe-R14.ps1'), '-Name', name],
                         capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stdout + run.stderr
    receipt = json.loads((ROOT / f'evidence/r14/health-{name}.json').read_text())
    assert receipt.get('monotonic_ticks', 0) > 0
    assert receipt.get('monotonic_frequency', 0) > 0


def test_floor_breach_after_hash_writes_no_receipt(tmp_path):
    # Execute the original script body with only its owned-output root relocated.
    # The controlled hash cmdlet makes the floor fail immediately after hashing.
    source = (ROOT / 'tools/Verify-R14Inputs.ps1').read_text()
    source = source.replace("$root='D:\\a14'", f"$root='{tmp_path}'")
    prefix = """
Import-Module Microsoft.PowerShell.Utility, Microsoft.PowerShell.Management
$script:hashed=$false
function Get-PSDrive { param([string]$Name)
    [pscustomobject]@{Free=$(if($script:hashed){0L}else{100GB})}
}
function Get-FileHash { param($Algorithm,$LiteralPath)
    $script:hashed=$true
    [pscustomobject]@{Hash='78d231a89ca346bbe669f2242ae6329e'}
}
"""
    # Keep the parameter declaration as the first statement.
    first, rest = source.split('\n', 1)
    script = tmp_path / 'post_hash_breach.ps1'
    script.write_text(first + '\n' + prefix + rest, encoding='utf-8')
    (tmp_path / 'evidence/r14').mkdir(parents=True)
    run = subprocess.run([PS5, '-NoProfile', '-File', str(script)], capture_output=True, text=True, timeout=30)
    assert run.returncode != 0
    receipt = tmp_path / 'evidence/r14/input-pins-small.jsonl'
    assert not receipt.exists(), 'A receipt was allocated after the disk floor failed'
