# S49 box run on a GitHub-hosted Windows runner (a quiet "box" without gates; labelled box-only). It exercises the
# Windows path of pc_speed_ci_20261027.ps1 end to end: CIM load probes, .NET process affinity and Idle priority,
# per-slot sampling, ABBA slots and the bootstrap. The exes come from ci_s49_build_windows.sh (MSYS2 UCRT64, static).
#   1. identity of both exes (uci_check.py), -SelfTest, the Python tests;
#   2. A/A: lock vs lock, 40 pairs + control pairs per depth -> the CI must contain 1.00;
#   3. A/B: lock vs the TEST-ONLY synthetic 5% slowdown -> the CI must exclude 1.00 (nodes A = B).
# usage: pwsh -File opus_round1/sol_S49/ci_s49_box_windows.ps1 -Out ci_out
param([string]$Out = 'ci_out')
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$J = Join-Path $root 'opus_round1\sol_S49'
$tool = Join-Path $J 'pc_speed_ci_20261027.ps1'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$Out = (Resolve-Path $Out).Path
$status = 0
$lock = Join-Path $Out 'build_lock\forge.exe'
$slow = Join-Path $Out 'build_slow\forge.exe'
$cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name
"== runner: $([Environment]::ProcessorCount) logical CPUs; $cpu; $([Environment]::OSVersion.VersionString); pwsh $($PSVersionTable.PSVersion)" |
    Tee-Object -FilePath (Join-Path $Out 'runner_windows.log')
foreach ($pair in @(@('lock', $lock), @('slow', $slow))) {
    python (Join-Path $root 'opus_round1\ci\uci_check.py') $pair[1] 2>&1 | Tee-Object -FilePath (Join-Path $Out "identity_$($pair[0])_windows.log")
    if ($LASTEXITCODE -ne 0) { $status = 1 }
}
pwsh -NoProfile -File $tool -SelfTest 2>&1 | Tee-Object -FilePath (Join-Path $Out 'selftest_windows.log')
if ($LASTEXITCODE -ne 0) { $status = 1 }
$env:PWSH = 'pwsh'
python -I -B (Join-Path $J 'tests\test_pc_speed_ci.py') *> (Join-Path $Out 'tests_windows.log')
if ($LASTEXITCODE -ne 0) { $status = 1 }
Get-Content (Join-Path $Out 'tests_windows.log') -Tail 4
$common = @('-Depths', '13,16', '-Pairs', '40', '-ControlEvery', '4', '-BoxOnly', '-ReservedCores', '0', '-AllowNoTemperature')
pwsh -NoProfile -File $tool -ExeA $lock -ExeB $lock @common -OutDir (Join-Path $Out 'run_aa') -Label 'box-only A/A (GitHub Windows runner)' 2>&1 |
    Tee-Object -FilePath (Join-Path $Out 'run_aa_windows.log')
if ($LASTEXITCODE -ne 0) { $status = 1 }
pwsh -NoProfile -File $tool -ExeA $lock -ExeB $slow @common -OutDir (Join-Path $Out 'run_slow5') -Label 'box-only synthetic 5% slowdown (GitHub Windows runner)' 2>&1 |
    Tee-Object -FilePath (Join-Path $Out 'run_slow5_windows.log')
if ($LASTEXITCODE -ne 0) { $status = 1 }
python -I -B (Join-Path $J 's49_box_verdict.py') $Out 2>&1 | Tee-Object -FilePath (Join-Path $Out 'verdict_windows.log')
if ($LASTEXITCODE -ne 0) { $status = 1 }
"ci_s49_box_windows status=$status"
exit $status
