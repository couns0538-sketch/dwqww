# selftest_10min.ps1 - Opus 30-h job: 10-minute dry run of the SPSA tuner (tune_spsa.ps1 / tune_spsa.py).
#   1. a new run of configs\selftest.json (2 lock tunables, 1+0.01, UHO) with a deadline 5 minutes ahead,
#   2. the stop path: a second session resumed with a 4-minute deadline that is stopped with -Stop after 60 s,
#   3. a third session resumed for at most 1 batch (--max-pairs 2),
#   then checks: every session exited 0; iterations.jsonl records = history.csv data rows; the pair count k and the
#   batch numbers continue across sessions without gaps or repeats; theta in every record stays inside [min, max];
#   every game finished normally (no time loss / crash / illegal move in the terminations); config.json + params.csv
#   copies exist. Exit 0 = PASS, 1 = FAIL. -Out must be a new folder.
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File selftest_10min.ps1 -Out D:\o30\spsa\selftest_<tag>
param([Parameter(Mandatory = $true)][string]$Out)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Out) { [Console]::Error.WriteLine("selftest: $Out exists"); exit 2 }
$here = $PSScriptRoot
$wrap = Join-Path $here 'tune_spsa.ps1'
$cfg = Join-Path $here 'configs\selftest.json'
$py = 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
$fail = New-Object System.Collections.Generic.List[string]
function Run-Wrapper([string[]]$extra) {
    $args2 = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $wrap) + $extra
    $p = Start-Process -FilePath 'powershell.exe' -ArgumentList $args2 -NoNewWindow -PassThru -Wait
    return $p.ExitCode
}
$t1 = (Get-Date).AddMinutes(5).ToString('yyyy-MM-dd HH:mm')
$rc1 = Run-Wrapper @('-Config', $cfg, '-RunDir', $Out, '-Until', ('"' + $t1 + '"'))
if ($rc1 -ne 0) { $fail.Add("session 1 exit $rc1") }
$t2 = (Get-Date).AddMinutes(4).ToString('yyyy-MM-dd HH:mm')
$p2 = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $wrap, '-RunDir', $Out, '-Until', ('"' + $t2 + '"')) -NoNewWindow -PassThru
Start-Sleep -Seconds 60
$rcs = Run-Wrapper @('-RunDir', $Out, '-Stop')
if ($rcs -ne 0) { $fail.Add("stop command exit $rcs") }
$p2.WaitForExit()
if ($p2.ExitCode -ne 0) { $fail.Add("session 2 exit $($p2.ExitCode)") }
$rc3 = Run-Wrapper @('-RunDir', $Out, '-MaxPairs', '2')
if ($rc3 -ne 0) { $fail.Add("session 3 exit $rc3") }
$check = @'
import csv, json, sys
d = sys.argv[1]
recs = [json.loads(l) for l in open(d + '/iterations.jsonl', encoding='ascii') if l.strip()]
rows = list(csv.reader(open(d + '/history.csv', encoding='ascii')))[2:]
params = list(csv.DictReader(open(d + '/params.csv', encoding='utf-8')))
bad = []
if not recs: bad.append('no batches')
if len(rows) != len(recs): bad.append(f'history rows {len(rows)} != records {len(recs)}')
for i, r in enumerate(recs):
    if r['batch'] != i: bad.append(f'batch number {r["batch"]} at position {i}')
    if i and r['k_before'] != recs[i - 1]['k_after']: bad.append(f'pair count gap at batch {i}')
    for p in params:
        v = r['theta_after'][p['name']]
        if not float(p['min']) <= v <= float(p['max']): bad.append(f'{p["name"]} {v} outside range')
    other = {t: n for t, n in r['terminations'].items() if t != 'normal'}
    if other: bad.append(f'batch {i} terminations {other}')
print(f'{len(recs)} batches, {recs[-1]["k_after"] if recs else 0} pairs, sessions logged: '
      f'{sum(1 for l in open(d + "/tuner.log") if "] start:" in l)}')
for b in bad: print('FAIL', b)
sys.exit(1 if bad else 0)
'@
$checkFile = Join-Path $Out 'selftest_check.py'
Set-Content -LiteralPath $checkFile -Value $check -Encoding ascii
& $py -I -B $checkFile $Out
if ($LASTEXITCODE -ne 0) { $fail.Add('state checks') }
foreach ($f in @('config.json', 'params.csv')) { if (-not (Test-Path -LiteralPath (Join-Path $Out $f))) { $fail.Add("missing $f") } }
if ($fail.Count -eq 0) { Write-Output 'SELFTEST PASS'; exit 0 }
foreach ($m in $fail) { Write-Output "SELFTEST FAIL: $m" }
exit 1
