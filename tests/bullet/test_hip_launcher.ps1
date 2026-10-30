# Windows PowerShell 5.1 behavioral regressions. This never runs HIP or Cargo.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$launcher = Join-Path $PSScriptRoot '..\..\tools\bullet\run_hip_smoke.ps1'
if (-not (Test-Path -LiteralPath $launcher)) { throw 'Missing HIP launcher' }
. $launcher

function Expect-Refusal([scriptblock]$Action) {
    $refused = $false
    try { & $Action } catch { $refused = $true }
    if (-not $refused) { throw 'Expected fail-closed refusal' }
}

Expect-Refusal { Assert-GpuIdleSample @() }
Expect-Refusal { Assert-GpuIdleSample @([pscustomobject]@{Name='gpu'; UtilizationPercentage=1}) }
Expect-Refusal { Assert-GpuIdleSample @([pscustomobject]@{Name='gpu'}) }
Expect-Refusal { Assert-GpuIdleSample @([pscustomobject]@{Name='gpu'; UtilizationPercentage=$null}) }
Expect-Refusal { Assert-GpuIdleSample @([pscustomobject]@{Name='gpu'; UtilizationPercentage=-1}) }
Expect-Refusal { Assert-GpuIdleSample @([pscustomobject]@{UtilizationPercentage=0}) }
Assert-GpuIdleSample @([pscustomobject]@{Name='gpu'; UtilizationPercentage=0})
Expect-Refusal { Assert-NoProductionProcess @() }
Expect-Refusal { Assert-NoProductionProcess @([pscustomobject]@{ProcessId=999; Name='python.exe'; CommandLine='python train.py'}) }
Expect-Refusal { Assert-NoProductionProcess @([pscustomobject]@{ProcessId=999; Name='forge.exe'; CommandLine='forge.exe'}) }
Expect-Refusal { Assert-NoProductionProcess @([pscustomobject]@{ProcessId=999; Name='worker.exe'; CommandLine='train_resid_v3b.py'}) }
Assert-NoProductionProcess @([pscustomobject]@{ProcessId=999; Name='explorer.exe'; CommandLine='explorer.exe'})
Expect-Refusal { Assert-ScratchPath -Path 'C:\temp' -RepoRoot 'C:\repo' }
Expect-Refusal { Assert-ScratchPath -Path 'F:\repo\run' -RepoRoot 'F:\repo' }
Assert-ScratchPath -Path 'F:\runs' -RepoRoot 'F:\repo'
Expect-Refusal { Assert-FreeBytes (20GB - 1) }
Assert-FreeBytes (20GB)
Expect-Refusal { ConvertTo-AffinityMask '0' }
Expect-Refusal { ConvertTo-AffinityMask 'garbage' }
if ((ConvertTo-AffinityMask '0x3').ToInt64() -ne 3) { throw 'Wrong affinity mask' }
$previousTarget = $env:CARGO_BUILD_TARGET
try {
    $env:CARGO_BUILD_TARGET = 'aarch64-pc-windows-msvc'
    $plan = Get-HipBuildPlan -TargetRoot 'F:\target' -Manifest 'C:\repo\Cargo.toml'
    $targetIndex = [Array]::IndexOf($plan.Arguments, '--target')
    if ($targetIndex -lt 0 -or $plan.Arguments[$targetIndex + 1] -ne 'x86_64-pc-windows-msvc') { throw 'Foreign inherited Cargo target was not overridden' }
    if ($plan.Executable -ne 'F:\target\x86_64-pc-windows-msvc\release\train_smoke.exe') { throw 'Executable path does not match explicit build target' }
} finally { $env:CARGO_BUILD_TARGET = $previousTarget }

# Invoke an actual native process which writes stderr successfully under Stop,
# then one which fails. Dedicated logs must preserve both streams and exit code.
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('bullet-launcher-test-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $testRoot
$self = [Diagnostics.Process]::GetCurrentProcess()
$oldPriority = $self.PriorityClass
$oldAffinity = $self.ProcessorAffinity
try {
    $self.PriorityClass = [Diagnostics.ProcessPriorityClass]::Idle
    $native = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $child = Join-Path $testRoot 'native.ps1'
    @'
param([string]$Value, [int]$Code)
[Console]::Out.WriteLine($Value)
[Console]::Error.WriteLine('normal native stderr')
exit $Code
'@ | Set-Content -LiteralPath $child -Encoding UTF8
    $argument = 'space and "quote" trailing\'
    $nativeArgs = @('-NoProfile', '-NonInteractive', '-File', $child, '-Value', $argument, '-Code', '0')
    $code = Invoke-NativeLogged -FilePath $native -Arguments $nativeArgs -LogPrefix (Join-Path $testRoot 'ok') -Affinity $oldAffinity -WorkingDirectory $testRoot
    if ($code -ne 0) { throw 'stderr caused native invocation failure' }
    if ((Get-Content -Raw (Join-Path $testRoot 'ok.stdout.log')).TrimEnd() -cne $argument) { throw 'Argument quoting changed argument' }
    if ((Get-Content -Raw (Join-Path $testRoot 'ok.stderr.log')).Trim() -ne 'normal native stderr') { throw 'stderr missing' }
    $preserved = (Get-FileHash -LiteralPath (Join-Path $testRoot 'ok.stdout.log')).Hash
    Expect-Refusal { Invoke-NativeLogged -FilePath $native -Arguments $nativeArgs -LogPrefix (Join-Path $testRoot 'ok') -Affinity $oldAffinity -WorkingDirectory $testRoot }
    if ((Get-FileHash -LiteralPath (Join-Path $testRoot 'ok.stdout.log')).Hash -ne $preserved) { throw 'Existing evidence overwritten' }
    $nativeArgs[-1] = '17'
    $code = Invoke-NativeLogged -FilePath $native -Arguments $nativeArgs -LogPrefix (Join-Path $testRoot 'fail') -Affinity $oldAffinity -WorkingDirectory $testRoot
    if ($code -ne 17) { throw 'Native failure exit code lost' }
    if ((Get-Content -Raw (Join-Path $testRoot 'fail.exit')).Trim() -ne '17') { throw 'Exit receipt missing' }
    $code = Invoke-NativeLogged -FilePath $native -Arguments @('-NoProfile', '-NonInteractive', '-File', $launcher) -LogPrefix (Join-Path $testRoot 'unscheduled') -Affinity $oldAffinity -WorkingDirectory $testRoot
    if ($code -ne 76) { throw 'Unscheduled launcher did not exit 76' }
    $code = Invoke-NativeLogged -FilePath $native -Arguments @('-NoProfile', '-NonInteractive', '-File', $launcher, '-GpuFreeSlotConfirmed') -LogPrefix (Join-Path $testRoot 'missing_affinity') -Affinity $oldAffinity -WorkingDirectory $testRoot
    if ($code -ne 76) { throw 'Missing affinity did not exit 76' }
    'PASS: preflight refusals, stderr under Stop, argument quoting, exit preservation'
    "Logs retained: $testRoot"
} finally {
    $self.PriorityClass = $oldPriority
    $self.ProcessorAffinity = $oldAffinity
}
