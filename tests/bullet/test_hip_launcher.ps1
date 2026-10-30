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

# Hand-picked WDDM instances: same engine across PIDs must aggregate, while
# separate engine IDs, physical adapters and LUIDs must not be added together.
function New-GpuSample([int]$ProcessId, [double]$Utilization, [int]$Engine = 0,
                       [string]$Kind = '3D', [int]$Physical = 0,
                       [string]$Luid = '0x00000000_0x0000D196') {
    [pscustomobject]@{ Name="pid_${ProcessId}_luid_${Luid}_phys_${Physical}_eng_${Engine}_engtype_${Kind}"; UtilizationPercentage=$Utilization }
}
Expect-Refusal { Assert-GpuIdleSample @() }
Expect-Refusal { Assert-GpuIdleSample @([pscustomobject]@{Name='gpu'; UtilizationPercentage=0}) }
Expect-Refusal { Assert-GpuIdleSample @([pscustomobject]@{Name='pid_999_luid_0x0_0x1_phys_0_eng_0_engtype_3D'}) }
Expect-Refusal { Assert-GpuIdleSample @([pscustomobject]@{Name='pid_999_luid_0x0_0x1_phys_0_eng_0_engtype_3D'; UtilizationPercentage=$null}) }
Expect-Refusal { Assert-GpuIdleSample @([pscustomobject]@{UtilizationPercentage=0}) }
foreach ($invalid in @(-1, 101, [double]::NaN, [double]::PositiveInfinity)) {
    Expect-Refusal { Assert-GpuIdleSample @((New-GpuSample 991 $invalid)) }
}
Assert-GpuIdleSample @((New-GpuSample 991 0))
Assert-GpuIdleSample @((New-GpuSample 991 1.99))
Assert-GpuIdleSample @((New-GpuSample 991 2))
Assert-GpuIdleSample @((New-GpuSample 991 1), (New-GpuSample 992 1))
Expect-Refusal { Assert-GpuIdleSample @((New-GpuSample 991 2.01)) }
Expect-Refusal { Assert-GpuIdleSample @((New-GpuSample 991 1.1), (New-GpuSample 992 1.1)) }
foreach ($kind in @('Compute', 'Compute0', 'Compute_0', 'Compute 1', 'Graphics', 'Graphics_0', 'Graphics_1', 'Graphics_12')) {
    Expect-Refusal { Assert-GpuIdleSample @((New-GpuSample 991 2.01 -Kind $kind)) }
    Assert-GpuIdleSample @((New-GpuSample 991 2 -Kind $kind))
}
Assert-GpuIdleSample @((New-GpuSample 991 1.9), (New-GpuSample 992 1.9 -Engine 1))
Assert-GpuIdleSample @((New-GpuSample 991 1.9), (New-GpuSample 992 1.9 -Physical 1))
Assert-GpuIdleSample @((New-GpuSample 991 1.9), (New-GpuSample 992 1.9 -Luid '0x00000000_0x0000D197'))
Expect-Refusal { Assert-GpuIdleSample @((New-GpuSample 991 1.9), (New-GpuSample 992 1.9 -Kind 'Compute')) }
Expect-Refusal { Assert-GpuIdleSample @((New-GpuSample 991 1.1 -Kind 'Graphics_1'), (New-GpuSample 992 1.1 -Kind 'Graphics_1')) }
Assert-GpuIdleSample @((New-GpuSample 991 100 -Kind 'Copy'), (New-GpuSample 992 90 -Kind 'VideoDecode'), (New-GpuSample 993 90 -Kind 'Video Decode'))
# Ignored engine types still require valid telemetry.
Expect-Refusal { Assert-GpuIdleSample @((New-GpuSample 991 -1 -Kind 'Copy')) }

function New-TestProcess([string]$Name, [string]$CommandLine, [string]$ExecutablePath = '') {
    [pscustomobject]@{ ProcessId=999999; Name=$Name; CommandLine=$CommandLine; ExecutablePath=$ExecutablePath }
}
Expect-Refusal { Assert-NoProductionProcess @() }
foreach ($command in @('python R:\nnue-pytorch\train.py', 'python -u -X utf8 -W ignore "R:\nnue-pytorch\train_resid_v3b.py"',
                       'python -- "R:\training jobs\nnue-pytorch\train.py"', 'py -3.11 R:\nnue-pytorch\train.py',
                       'python selfplay.py', 'python -u train_resid_v2.py', 'python .\TRAIN_RESID_V3B.PY',
                       'python R:\toy\train_resid_v3b.py', 'python -u r11_train_entry.py',
                       'python "R:\training jobs\R11_TRAIN_ENTRY.PY"', 'python r11_train_entry',
                       'python -uW ignore R:\nnue-pytorch\train.py',
                       'python -uX utf8 R:\nnue-pytorch\train.py', 'python -uWignore R:\nnue-pytorch\train.py',
                       'python -uXutf8 R:\nnue-pytorch\train.py', 'py -V:3.11 R:\nnue-pytorch\train.py', 'python -v R:\nnue-pytorch\train.py', 'python -x R:\nnue-pytorch\train.py',
                       '"R:\Python Env\python.exe" -u "R:\nnue-pytorch\train.py"')) {
    $name = if ($command.StartsWith('py ')) { 'py.exe' } else { 'python.exe' }
    Expect-Refusal { Assert-NoProductionProcess @((New-TestProcess $name $command)) }
}
foreach ($name in @('selfplay.exe', 'selfplay_worker.exe', 'fastchess.exe', 'cutechess.exe', 'cutechess-cli.exe', 'gate.exe', 'gate_candidate.exe', 'R11_TRAIN_ENTRY.EXE')) {
    Expect-Refusal { Assert-NoProductionProcess @((New-TestProcess $name $name)) }
}
foreach ($name in @('explorer.exe', 'python.exe', 'pythonw.exe', 'python3.11.exe', 'cargo.exe', 'rustc.exe', 'cmake.exe', 'ninja.exe', 'clang++.exe', 'cl.exe', 'hipcc.exe', 'forge.exe', 'stockfish.exe', 'gatekeeper.exe', 'editor.exe')) {
    Assert-NoProductionProcess @((New-TestProcess $name ($name + ' README_train.py nnue-pytorch selfplay fastchess cutechess')))
}
foreach ($command in @('python tools\convert.py --input train.py', 'python -c "print(''train.py'')"',
                       'python -m unittest train.py', 'python -uc "print(''train.py'')" R:\nnue-pytorch\train.py', 'python --version train.py', 'python train.py',
                       'python R:\toy\train_metrics.py', 'python -V R:\nnue-pytorch\train.py',
                       'python R:\nnue-pytorch\..\toy\train_metrics.py', 'python nnue-pytorch\..\toy\train_metrics.py',
                       'python "R:\nnue-pytorch\inspect.py"', 'python -W train.py tools\inspect.py')) {
    Assert-NoProductionProcess @((New-TestProcess 'python.exe' $command))
}
Assert-NoProductionProcess @((New-TestProcess 'python.exe' 'python.exe'))
foreach ($name in @('python.exe', 'worker.exe')) {
    Expect-Refusal { Assert-NoProductionProcess @([pscustomobject]@{ ProcessId=999999; Name=$name; CommandLine=$null }) }
    Expect-Refusal { Assert-NoProductionProcess @([pscustomobject]@{ ProcessId=999999; Name=$name }) }
    Expect-Refusal { Assert-NoProductionProcess @((New-TestProcess $name '')) }
    $denied = [pscustomobject]@{ ProcessId=999999; Name=$name }
    $denied | Add-Member ScriptProperty CommandLine { throw [UnauthorizedAccessException]::new('AccessDenied') }
    Expect-Refusal { Assert-NoProductionProcess @($denied) }
}
foreach ($command in @('python tools\inspect.py --guard-tag r11', 'python.exe --GUARD-TAG=production', 'worker.exe --guard-tag')) {
    Expect-Refusal { Assert-NoProductionProcess @((New-TestProcess 'worker.exe' $command)) }
}
Expect-Refusal { Assert-NoProductionProcess @((New-TestProcess 'python.exe' 'python "unterminated')) }
Assert-NoProductionProcess @((New-TestProcess 'worker.exe' 'train_resid_v3b.py'))
Expect-Refusal { Assert-NoProductionProcess @((New-TestProcess 'python.exe' 'python R:\forge\tools\nnue\train_resid_v3b.py')) -ProductionTrainScriptPaths @('R:\forge\tools\nnue\train_resid_v3b.py') }
Expect-Refusal { Assert-NoProductionProcess @((New-TestProcess 'python.exe' 'python R:\toy\train_resid_v3b.py')) -ProductionTrainScriptPaths @('R:\forge\tools\nnue\train_resid_v3b.py') }
Assert-NoProductionProcess @((New-TestProcess 'editor.exe' 'editor.exe "R:\nnue-pytorch\train.py"'))
Expect-Refusal { Assert-NoProductionProcess @((New-TestProcess 'FORGE.exe' 'forge.exe')) -GateExeNames @('forge.exe') }
foreach ($name in @('FORGE.exe', 'stockfish.exe')) {
    Expect-Refusal { Assert-NoProductionProcess @((New-TestProcess $name $name)) -GateExeNames ' forge.exe , stockfish.exe ' }
}
Assert-NoProductionProcess @((New-TestProcess 'forge_other.exe' 'forge_other.exe')) -GateExeNames ' forge.exe , stockfish.exe '
Assert-NoProductionProcess @((New-TestProcess 'forge_other.exe' 'forge_other.exe')) -GateExeNames @('forge.exe')
Expect-Refusal { Assert-NoProductionProcess @((New-TestProcess 'forge.exe' 'forge.exe' 'R:\gates\forge.exe')) -GateExePaths @('r:\GATES\forge.exe') }
Assert-NoProductionProcess @((New-TestProcess 'forge.exe' 'forge.exe' 'R:\analysis\forge.exe')) -GateExePaths @('R:\gates\forge.exe')
# An inaccessible ExecutablePath may be resolved from the actual argv[0].
Expect-Refusal { Assert-NoProductionProcess @((New-TestProcess 'forge.exe' '"R:\gates\forge.exe"')) -GateExePaths @('R:\gates\forge.exe') }
Assert-NoProductionProcess @((New-TestProcess 'editor.exe' 'editor.exe "R:\gates\forge.exe"')) -GateExePaths @('R:\gates\forge.exe')

Assert-ProcessPolicyOptions
Expect-Refusal { Assert-ProcessPolicyOptions -GateExeNames @('forge*.exe') }
Expect-Refusal { Assert-ProcessPolicyOptions -GateExeNames 'forge.exe,,stockfish.exe' }
Expect-Refusal { Assert-ProcessPolicyOptions -GateExeNames 'forge.exe,R:\gate.exe' }
Assert-ProcessPolicyOptions -GateExeNames ' forge.exe , stockfish.exe '
$normalizedNames = @(ConvertTo-GateExeNames @(' forge.exe , stockfish.exe ', 'candidate.exe'))
if ($normalizedNames.Count -ne 3 -or $normalizedNames[0] -cne 'forge.exe' -or $normalizedNames[1] -cne 'stockfish.exe' -or $normalizedNames[2] -cne 'candidate.exe') { throw 'Comma-separated gate names were not normalized' }
Expect-Refusal { Assert-ProcessPolicyOptions -GateExePaths @('forge.exe') }
Expect-Refusal { Assert-ProcessPolicyOptions -ProductionTrainScriptPaths @('R:\train*.py') }
Assert-ProcessPolicyOptions -GateExeNames @('forge.exe') -GateExePaths @('R:\gates\forge.exe') -ProductionTrainScriptPaths @('R:\forge\train.py')

# Fake only external telemetry/delay, exercising the real slot's sequencing.
# DriveInfo uses the explicit scratch drive in production; this test replaces its wrapper.
$diskCheck = ${function:Assert-HipDiskSpace}
$script:gpuReads = 0
$script:processReads = 0
$script:sleepCalls = 0
$script:busyAt = 0
$script:invalidAt = 0
$script:invalidMode = ''
try {
    function Assert-HipDiskSpace {
        param([string]$ScratchDrive)
        if ($ScratchDrive -cne 'R:\') { throw 'Disk check did not use the configured scratch drive' }
    }
    function Get-CimInstance {
        param([string]$ClassName, [string]$Namespace, [string]$ErrorAction)
        if ($ClassName -eq 'Win32_Process') {
            $script:processReads++
            return New-TestProcess 'explorer.exe' 'explorer.exe'
        }
        if ($ClassName -ne 'Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine' -or $Namespace -ne 'root\cimv2') { throw 'Unexpected telemetry query' }
        $script:gpuReads++
        if ($script:gpuReads -eq $script:invalidAt) {
            switch ($script:invalidMode) {
                'missing' { return $null }
                'malformed' { return [pscustomobject]@{ Name='invalid'; UtilizationPercentage=0 } }
                'no_utilization' { return [pscustomobject]@{ Name='pid_991_luid_0x0_0x1_phys_0_eng_0_engtype_3D' } }
                'denied' { throw [UnauthorizedAccessException]::new('GPU telemetry AccessDenied') }
            }
        }
        $util = if ($script:gpuReads -eq $script:busyAt) { 2.01 } else { 0 }
        return New-GpuSample 991 $util
    }
    function Start-Sleep {
        param([int]$Seconds)
        if ($Seconds -ne 1) { throw 'Wrong sample interval' }
        $script:sleepCalls++
    }
    Assert-HipSlot -ScratchDrive 'R:'
    if ($script:gpuReads -ne 5 -or $script:processReads -ne 5 -or $script:sleepCalls -ne 4) { throw 'Idle slot did not require five snapshots and four one-second delays' }
    foreach ($busyAt in 1..5) {
        $script:gpuReads = 0; $script:processReads = 0; $script:sleepCalls = 0; $script:busyAt = $busyAt
        Expect-Refusal { Assert-HipSlot -ScratchDrive 'R:' }
        if ($script:gpuReads -ne $busyAt) { throw 'Busy sample was not refused at its first occurrence' }
    }
    $script:busyAt = 0
    foreach ($mode in @('missing', 'malformed', 'no_utilization', 'denied')) {
        foreach ($invalidAt in 1..5) {
            $script:gpuReads = 0; $script:processReads = 0; $script:sleepCalls = 0
            $script:invalidAt = $invalidAt; $script:invalidMode = $mode
            Expect-Refusal { Assert-HipSlot -ScratchDrive 'R:' }
            if ($script:gpuReads -ne $invalidAt -or $script:processReads -ne $invalidAt -or $script:sleepCalls -ne ($invalidAt - 1)) { throw 'Invalid telemetry was retried or accepted' }
        }
    }
} finally {
    Set-Item Function:\Assert-HipDiskSpace $diskCheck
    Remove-Item Function:\Get-CimInstance, Function:\Start-Sleep
}
Expect-Refusal { Assert-ScratchPath -Path 'C:\temp' -RepoRoot 'C:\repo' -ScratchDrive 'R:' }
Expect-Refusal { Assert-ScratchPath -Path 'R:\repo\run' -RepoRoot 'R:\repo' -ScratchDrive 'R:' }
Assert-ScratchPath -Path 'R:\runs' -RepoRoot 'R:\repo' -ScratchDrive 'R:'
Assert-ScratchPath -Path 'S:\runs' -RepoRoot 'C:\repo' -ScratchDrive 's:\'
Expect-Refusal { Assert-ScratchPath -Path 'R:\runs' -RepoRoot 'C:\repo' -ScratchDrive 'S:' }
Expect-Refusal { Assert-ScratchPath -Path 'R:relative' -RepoRoot 'C:\repo' -ScratchDrive 'R:' }
Expect-Refusal { Assert-ScratchPath -Path '\\server\share\runs' -RepoRoot 'C:\repo' -ScratchDrive 'R:' }
foreach ($invalidDrive in @('', 'R', 'R:\runs', '\\server\share')) {
    Expect-Refusal { ConvertTo-ScratchDrive $invalidDrive }
}
if ((ConvertTo-ScratchDrive 'r:') -cne 'R:\' -or (ConvertTo-ScratchDrive 's:/') -cne 'S:\') { throw 'Scratch drive normalization failed' }
Expect-Refusal { Assert-FreeBytes (20GB - 1) }
Assert-FreeBytes (20GB)
Expect-Refusal { ConvertTo-AffinityMask '0' }
Expect-Refusal { ConvertTo-AffinityMask 'garbage' }
if ((ConvertTo-AffinityMask '0x3').ToInt64() -ne 3) { throw 'Wrong affinity mask' }
$previousTarget = $env:CARGO_BUILD_TARGET
try {
    $env:CARGO_BUILD_TARGET = 'aarch64-pc-windows-msvc'
    $plan = Get-HipBuildPlan -TargetRoot 'R:\target' -Manifest 'C:\repo\Cargo.toml'
    $targetIndex = [Array]::IndexOf($plan.Arguments, '--target')
    if ($targetIndex -lt 0 -or $plan.Arguments[$targetIndex + 1] -ne 'x86_64-pc-windows-msvc') { throw 'Foreign inherited Cargo target was not overridden' }
    if ($plan.Executable -ne 'R:\target\x86_64-pc-windows-msvc\release\train_smoke.exe') { throw 'Executable path does not match explicit build target' }
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
