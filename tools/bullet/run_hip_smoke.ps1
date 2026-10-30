#requires -Version 5.1
<# A future, explicitly scheduled GPU-free slot only. Windows/HIP UNVERIFIED.
   Dot-source without arguments to load helpers for tests; no job is launched.
   No process is stopped or killed by this launcher. #>
[CmdletBinding()]
param(
    [string]$CpuAffinityMask,
    [string]$PythonExe,
    [string]$PythonSha256,
    [string]$InputDir,
    [string]$RunRoot = 'F:\astra_bullet_smoke',
    [string]$TargetDir = 'F:\astra_bullet_cargo_target',
    [switch]$GpuFreeSlotConfirmed
)

function ConvertTo-AffinityMask([string]$Value) {
    if ($Value -notmatch '^(?:0x)?[0-9a-fA-F]+$') { throw 'Explicit nonzero hexadecimal CPU affinity mask required' }
    $mask = [Convert]::ToInt64(($Value -replace '^0x', ''), 16)
    if ($mask -le 0) { throw 'CPU affinity mask must be nonzero and fit a signed native pointer' }
    return [IntPtr]$mask
}

function Assert-ScratchPath([string]$Path, [string]$RepoRoot) {
    $full = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    $repo = [IO.Path]::GetFullPath($RepoRoot).TrimEnd('\')
    if (-not $full.StartsWith('F:\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Scratch, target and TEMP must be on F:' }
    if ($full.Equals($repo, [StringComparison]::OrdinalIgnoreCase) -or $full.StartsWith($repo + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Run, target and TEMP must be outside the repository' }
    # Reject junction/symlink ancestors, which could redirect writes off F:.
    $parent = $full
    while ($parent) {
        if (Test-Path -LiteralPath $parent) {
            $item = Get-Item -LiteralPath $parent -Force -ErrorAction Stop
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point is not an approved scratch path: $parent" }
        }
        $parent = [IO.Path]::GetDirectoryName($parent)
    }
}

function Assert-FreeBytes([long]$Available) {
    if ($Available -lt 20GB) { throw 'F: requires at least 20 GiB free; refusing work' }
}

function Assert-GpuIdleSample([object[]]$Samples) {
    if (-not $Samples -or $Samples.Count -eq 0) { throw 'GPU telemetry unavailable or empty; no idle claim is possible' }
    foreach ($sample in $Samples) {
        if ($null -eq $sample.PSObject.Properties['Name'] -or [string]::IsNullOrWhiteSpace([string]$sample.Name)) { throw 'GPU counter identity unavailable' }
        $property = $sample.PSObject.Properties['UtilizationPercentage']
        if ($null -eq $property -or $null -eq $property.Value) { throw 'GPU utilization is unavailable' }
        $util = 0.0
        if (-not [double]::TryParse([string]$property.Value, [ref]$util) -or [double]::IsNaN($util) -or [double]::IsInfinity($util) -or $util -lt 0 -or $util -gt 100) { throw 'Invalid GPU telemetry' }
        if ($util -gt 0) { throw "GPU busy: $($sample.Name) utilization=$util" }
    }
}

function Assert-NoProductionProcess([object[]]$Processes) {
    if (-not $Processes -or $Processes.Count -eq 0) { throw 'Process telemetry unavailable or empty' }
    foreach ($process in $Processes) {
        if ($null -eq $process.PSObject.Properties['ProcessId'] -or $null -eq $process.PSObject.Properties['Name'] -or [string]::IsNullOrWhiteSpace([string]$process.Name)) { throw 'Incomplete process telemetry' }
        if ([int]$process.ProcessId -eq $PID) { continue }
        $name = [string]$process.Name
        # Broad refusal is intentional: a dedicated slot must have no trainer,
        # self-play, match, compiler or Python worker alongside the smoke.
        if ($name -match '(?i)^(python(?:w|\d+(?:\.\d+)*)?|cargo|rustc|cmake|ninja|clang(?:\+\+)?|cl|hipcc|fastchess|cutechess(?:-cli)?|forge[^.]*|stockfish[^.]*|train[^.]*)\.exe$') { throw "Production/build process present: $name PID $($process.ProcessId)" }
        if ($null -ne $process.PSObject.Properties['CommandLine'] -and [string]$process.CommandLine -match '(?i)(nnue-pytorch|train[^\\/\s]*\.py|selfplay|fastchess|cutechess)') { throw "Production command present: PID $($process.ProcessId)" }
    }
}

function Assert-HipSlot {
    Assert-FreeBytes ([IO.DriveInfo]::new('F:\').AvailableFreeSpace)
    # Missing/denied WDDM/CIM counters are a refusal, never interpreted as zero.
    # Two snapshots are an additional check, not a substitute for scheduling.
    for ($sampleIndex = 0; $sampleIndex -lt 2; $sampleIndex++) {
        Assert-NoProductionProcess @(Get-CimInstance Win32_Process -ErrorAction Stop)
        Assert-GpuIdleSample @(Get-CimInstance -Namespace root\cimv2 -ClassName Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine -ErrorAction Stop)
        if ($sampleIndex -eq 0) { Start-Sleep -Seconds 1 }
    }
}

function ConvertTo-NativeArgument([string]$Value) {
    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') { return $Value }
    # Windows CommandLineToArgvW / CRT quoting, including trailing backslashes.
    $quoted = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $quoted = [regex]::Replace($quoted, '(\\+)$', '$1$1')
    return '"' + $quoted + '"'
}

function Write-NewLogText([string]$Path, [string]$Text) {
    $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
    $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
}

function Get-HipBuildPlan([string]$TargetRoot, [string]$Manifest) {
    # Bind the output path to the exact CLI target, overriding both inherited
    # CARGO_BUILD_TARGET and global Cargo build.target configuration.
    $rustTarget = 'x86_64-pc-windows-msvc'
    return [pscustomobject]@{
        Arguments = @('build', '--release', '--locked', '-j2', '--target', $rustTarget, '--features', 'rocm', '--manifest-path', $Manifest, '--bin', 'train_smoke')
        Executable = Join-Path $TargetRoot ($rustTarget + '\release\train_smoke.exe')
    }
}

function Invoke-NativeLogged {
    param([string]$FilePath, [string[]]$Arguments, [string]$LogPrefix,
          [IntPtr]$Affinity, [string]$WorkingDirectory)
    $parent = [Diagnostics.Process]::GetCurrentProcess()
    if ($parent.PriorityClass -ne [Diagnostics.ProcessPriorityClass]::Idle -or $parent.ProcessorAffinity -ne $Affinity) { throw 'Idle priority and explicit CPU affinity must be set before process creation' }
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName = $FilePath
    $info.Arguments = (($Arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' ')
    $info.WorkingDirectory = $WorkingDirectory
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $commandJson = @{executable=$FilePath; arguments=$Arguments; cwd=$WorkingDirectory; affinity=$Affinity.ToInt64(); priority='Idle'; TEMP=$env:TEMP; TMP=$env:TMP; CARGO_TARGET_DIR=$env:CARGO_TARGET_DIR} | ConvertTo-Json -Depth 4
    Write-NewLogText -Path ($LogPrefix + '.command.json') -Text $commandJson
    $process = New-Object Diagnostics.Process
    $process.StartInfo = $info
    $stdout = $null
    $stderr = $null
    try {
        # Claim both logs exclusively before spawning. A log error must not
        # leave a running child with unconsumed redirected streams.
        $stdout = [IO.File]::Open($LogPrefix + '.stdout.log', [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
        $stderr = [IO.File]::Open($LogPrefix + '.stderr.log', [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
        if (-not $process.Start()) { throw 'Native process failed to start' }
        # The child inherits Idle priority and affinity at creation; avoid a
        # racy post-start setter on short-lived rustc/Python/native children.
        # Concurrent stream copies avoid pipe deadlock and preserve raw
        # stderr without PowerShell 5.1 NativeCommandError conversion.
        $outCopy = $process.StandardOutput.BaseStream.CopyToAsync($stdout)
        $errCopy = $process.StandardError.BaseStream.CopyToAsync($stderr)
        $process.WaitForExit()
        $outCopy.GetAwaiter().GetResult()
        $errCopy.GetAwaiter().GetResult()
        $code = $process.ExitCode
        Write-NewLogText -Path ($LogPrefix + '.exit') -Text ([string]$code)
        return $code
    } finally {
        if ($null -ne $stdout) { $stdout.Dispose() }
        if ($null -ne $stderr) { $stderr.Dispose() }
        $process.Dispose()
    }
}

if ($MyInvocation.InvocationName -eq '.') { return }
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$run = $null
$phase = 'preflight'
try {
    if (-not $GpuFreeSlotConfirmed) { throw 'GPU-free scheduled slot must be explicitly confirmed; never run alongside the live AMD trainer' }
    if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitProcess) { throw 'Requires 64-bit Windows PowerShell 5.1 or newer' }
    $affinity = ConvertTo-AffinityMask $CpuAffinityMask
    $repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
    Assert-ScratchPath -Path $RunRoot -RepoRoot $repo
    Assert-ScratchPath -Path $TargetDir -RepoRoot $repo
    Assert-HipSlot
    if ($PythonSha256 -notmatch '^[0-9a-fA-F]{64}$' -or -not [IO.Path]::IsPathRooted($PythonExe)) { throw 'Supply absolute pinned venv PythonExe and its expected SHA256' }
    $python = (Resolve-Path -LiteralPath $PythonExe).Path
    if ([IO.Path]::GetFileName($python) -ine 'python.exe' -or [IO.Path]::GetFileName([IO.Path]::GetDirectoryName($python)) -ine 'Scripts' -or -not (Test-Path -LiteralPath (Join-Path ([IO.Path]::GetDirectoryName([IO.Path]::GetDirectoryName($python))) 'pyvenv.cfg'))) { throw 'PythonExe must identify an existing Windows venv Scripts\python.exe' }
    if ((Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash -ine $PythonSha256) { throw 'Pinned venv Python hash mismatch' }
    if (-not $InputDir) { $InputDir = Join-Path $repo 'validation\astra-bullet-export\bullet_gpu_input' }
    $inputRoot = (Resolve-Path -LiteralPath $InputDir).Path
    $inputFile = Join-Path $inputRoot 'input.fbs'
    $expected = (Get-Content -Raw -LiteralPath (Join-Path $inputRoot 'manifest.json') | ConvertFrom-Json).input_sha256
    if ($expected -notmatch '^[0-9a-fA-F]{64}$' -or (Get-FileHash -LiteralPath $inputFile -Algorithm SHA256).Hash -ine $expected) { throw 'Smoke input hash mismatch' }
    if (-not $env:HIP_PATH -or -not (Test-Path -LiteralPath $env:HIP_PATH) -or -not $env:GCN_ARCH_NAME) { throw 'Configure installed HIP_PATH and verified GCN_ARCH_NAME before this launcher' }
    $cargo = (Get-Command cargo.exe -CommandType Application -ErrorAction Stop).Source
    $rustc = (Get-Command rustc.exe -CommandType Application -ErrorAction Stop).Source
    $self = [Diagnostics.Process]::GetCurrentProcess()
    $self.PriorityClass = [Diagnostics.ProcessPriorityClass]::Idle
    $self.ProcessorAffinity = $affinity
    $run = Join-Path $RunRoot ([guid]::NewGuid().ToString('N'))
    $tempDir = Join-Path $run 'temp'
    Assert-ScratchPath -Path $tempDir -RepoRoot $repo
    $null = New-Item -ItemType Directory -Path $run -ErrorAction Stop
    $null = New-Item -ItemType Directory -Path $tempDir -ErrorAction Stop
    $null = New-Item -ItemType Directory -Path $TargetDir -Force -ErrorAction Stop
    $env:CARGO_TARGET_DIR = [IO.Path]::GetFullPath($TargetDir)
    $env:TEMP = $tempDir
    $env:TMP = $tempDir
    $env:CARGO_BUILD_JOBS = '2'
    $env:OMP_NUM_THREADS = '1'
    $env:OPENBLAS_NUM_THREADS = '1'
    $env:MKL_NUM_THREADS = '1'
    @{utc=[DateTime]::UtcNow.ToString('o'); input_sha256=$expected; python=$python; python_sha256=$PythonSha256; HIP_PATH=$env:HIP_PATH; GCN_ARCH_NAME=$env:GCN_ARCH_NAME; gpu_free_slot_confirmed=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $run 'preflight.json') -Encoding UTF8
    Write-Host "Logs and outputs: $run"
    $phase = 'native'
    $code = Invoke-NativeLogged -FilePath $rustc -Arguments @('--version') -LogPrefix (Join-Path $run 'rustc_version') -Affinity $affinity -WorkingDirectory $run
    if ($code -ne 0) { throw "rustc --version exited $code" }
    $version = Get-Content -Raw -LiteralPath (Join-Path $run 'rustc_version.stdout.log')
    if ($version -notmatch '^rustc (\d+)\.(\d+)\.(\d+)' -or [version]($Matches[0].Substring(6)) -lt [version]'1.87.0') { throw 'Rust 1.87 or newer is required (1.85 fails)' }
    $code = Invoke-NativeLogged -FilePath $python -Arguments @('-c', 'import sys, numpy; print(sys.executable); print(sys.version); print(numpy.__version__)') -LogPrefix (Join-Path $run 'python_version') -Affinity $affinity -WorkingDirectory $run
    if ($code -ne 0) { throw "Pinned venv/NumPy check exited $code" }
    $manifest = Join-Path $repo 'tools\bullet\lock_graph\Cargo.toml'
    $code = Invoke-NativeLogged -FilePath $cargo -Arguments @('fetch', '--locked', '--manifest-path', $manifest) -LogPrefix (Join-Path $run 'cargo_fetch') -Affinity $affinity -WorkingDirectory $run
    if ($code -ne 0) { throw "cargo fetch --locked exited $code" }
    $phase = 'preflight'
    Assert-HipSlot
    $phase = 'native'
    $output = Join-Path $run 'checkpoint'
    $buildPlan = Get-HipBuildPlan -TargetRoot $env:CARGO_TARGET_DIR -Manifest $manifest
    $code = Invoke-NativeLogged -FilePath $cargo -Arguments $buildPlan.Arguments -LogPrefix (Join-Path $run 'cargo_build') -Affinity $affinity -WorkingDirectory $run
    if ($code -ne 0) { throw "Bullet HIP build exited $code" }
    $trainingExe = $buildPlan.Executable
    $trainingHash = (Get-FileHash -LiteralPath $trainingExe -Algorithm SHA256).Hash
    Write-NewLogText -Path (Join-Path $run 'train_smoke.sha256') -Text $trainingHash
    $phase = 'preflight'
    Assert-HipSlot
    $phase = 'native'
    $code = Invoke-NativeLogged -FilePath $trainingExe -Arguments @($inputFile, $output, '128') -LogPrefix (Join-Path $run 'original_training') -Affinity $affinity -WorkingDirectory $run
    if ($code -ne 0) { throw "Bullet GPU smoke exited $code; partial outputs retained" }
    if (-not (Test-Path -LiteralPath (Join-Path $output 'COMPLETE.txt'))) { throw 'Training completion marker missing' }
    $phase = 'preflight'
    Assert-FreeBytes ([IO.DriveInfo]::new('F:\').AvailableFreeSpace)
    $phase = 'native'
    $weights = Join-Path $output 'weights.bin'
    $exportManifest = Join-Path $run 'export_manifest.json'
    $exporter = Join-Path $repo 'tools\bullet\lock_export.py'
    $code = Invoke-NativeLogged -FilePath $python -Arguments @($exporter, 'manifest', '--checkpoint', $weights, '--out', $exportManifest, '--provenance', "Actual Bullet GPU smoke; original logs in $run") -LogPrefix (Join-Path $run 'export_manifest') -Affinity $affinity -WorkingDirectory $run
    if ($code -ne 0) { throw "Checkpoint manifest exited $code" }
    $code = Invoke-NativeLogged -FilePath $python -Arguments @($exporter, 'export', '--checkpoint', $weights, '--manifest', $exportManifest, '--out', (Join-Path $run 'nnue_weights.inc')) -LogPrefix (Join-Path $run 'export_include') -Affinity $affinity -WorkingDirectory $run
    if ($code -ne 0) { throw "Include export exited $code" }
    [IO.File]::WriteAllText((Join-Path $run 'LAUNCHER_COMPLETE.txt'), 'Smoke and export completed; native 12k parity and strength remain unverified.')
    exit 0
} catch {
    $code = if ($phase -eq 'preflight') { 76 } else { 1 }
    $message = "REFUSED/FAILED (exit $code): $($_.Exception.Message)"
    [Console]::Error.WriteLine($message)
    if ($run -and (Test-Path -LiteralPath $run)) { [IO.File]::WriteAllText((Join-Path $run 'launcher_failure.log'), $message) }
    exit $code
}
