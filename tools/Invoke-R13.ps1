param(
    [Parameter(Mandatory=$true)][string]$Script,
    [string[]]$ScriptArguments = @(),
    [Parameter(Mandatory=$true)][string]$RunName,
    [ValidateRange(-1,15)][int]$Cpu = -1,
    [ValidateRange(1,10800)][int]$TimeoutSeconds = 1800,
    [long]$RequiredBytes = 134217728,
    [switch]$WithDatafilterRuntime
)
$ErrorActionPreference='Stop'
$root = 'D:\a13'
$python = 'D:\a11\runtime\python\python.exe'
function Assert-OwnedPath([string]$Candidate) {
    $full=[IO.Path]::GetFullPath($Candidate)
    if ($full -ne $root -and -not $full.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside owned root' }
    $walk=$full
    while ($walk) {
        if (Test-Path -LiteralPath $walk) {
            if ((Get-Item -Force -LiteralPath $walk).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse ancestor refused' }
        }
        $walk=[IO.Path]::GetDirectoryName($walk)
    }
}
function Get-SourceIdentity {
    $identities=@{}
    foreach ($folder in @('tools','tests','astra_r8\datafilter')) {
        Get-ChildItem -LiteralPath (Join-Path $root $folder) -Recurse -File | Where-Object { $_.Extension -in @('.py','.ps1') } | ForEach-Object {
            Assert-OwnedPath $_.FullName
            $identities[$_.FullName.Substring($root.Length+1).Replace('\','/')]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()
        }
    }
    return $identities
}
if ($RunName -notmatch '^[a-zA-Z0-9_-]+$') { throw 'Invalid run name' }
$scriptFull = [IO.Path]::GetFullPath($Script)
Assert-OwnedPath $scriptFull
if ([IO.Path]::GetExtension($scriptFull) -ne '.py') { throw 'Only Python entry points are supported' }
if (-not $scriptFull.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $scriptFull -PathType Leaf)) { throw 'Script outside owned root or missing' }
if ($RequiredBytes -lt 0 -or (Get-PSDrive D).Free -lt (50GB + $RequiredBytes)) { throw '50 GiB plus allocation admission refused' }
$run = Join-Path $root ('evidence\runs\' + $RunName)
Assert-OwnedPath $run
if (Test-Path -LiteralPath $run) { throw 'Refusing reused run directory' }
$samples = Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor
if ($Cpu -eq -1) {
    $usage = $samples | Where-Object Name -in @('0','1','2','3') | Sort-Object PercentProcessorTime | Select-Object -First 1
    $Cpu=[int]$usage.Name
} else { $usage = $samples | Where-Object Name -eq ([string]$Cpu) }
if (-not $usage -or [int]$usage.PercentProcessorTime -gt 70) { throw "CPU $Cpu admission refused: $($usage.PercentProcessorTime)% busy" }
New-Item -ItemType Directory -Path $run, (Join-Path $run 'tmp') | Out-Null
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONNOUSERSITE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:CUDA_VISIBLE_DEVICES='-1'
$env:HIP_VISIBLE_DEVICES='-1'
$env:ROCR_VISIBLE_DEVICES='-1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:NUMEXPR_NUM_THREADS='1'
$env:TEMP=Join-Path $run 'tmp'
$env:TMP=$env:TEMP
$env:TMPDIR=$env:TEMP
$env:TORCH_HOME=Join-Path $env:TEMP 'torch'
$env:TORCHINDUCTOR_CACHE_DIR=Join-Path $env:TEMP 'inductor'
$env:TRITON_CACHE_DIR=Join-Path $env:TEMP 'triton'
$env:PYTHONPYCACHEPREFIX=Join-Path $env:TEMP 'pycache'
$env:MPLCONFIGDIR=Join-Path $env:TEMP 'matplotlib'
$env:XDG_CACHE_HOME=Join-Path $env:TEMP 'xdg-cache'
$env:XDG_CONFIG_HOME=Join-Path $env:TEMP 'xdg-config'
$env:HF_HOME=Join-Path $env:TEMP 'huggingface'
$env:ASTRA_R13_CPU=[string]$Cpu
$env:ASTRA_R13_DEADLINE=([DateTimeOffset]::UtcNow.ToUnixTimeSeconds()+$TimeoutSeconds).ToString()
if ($WithDatafilterRuntime) {
    $env:PYTHONPATH='D:\a13\tools;F:\nnue_pytorch\venv\Lib\site-packages'
    $env:ASTRA_NPT_ROOT='F:\opus_scratch\r6\nnue-pytorch-amd'
    $env:NNUE_DATA_LOADER_LIB='F:\opus_scratch\r6\nnue-pytorch-amd\build\libtraining_data_loader.dll'
} else { $env:PYTHONPATH='D:\a13\tools' }
$process=[Diagnostics.Process]::GetCurrentProcess()
$oldPriority=$process.PriorityClass
$oldAffinity=$process.ProcessorAffinity
$started=[DateTime]::UtcNow.ToString('o')
$scriptHash=(Get-FileHash -LiteralPath $scriptFull -Algorithm SHA256).Hash.ToLower()
$sourcesBefore=Get-SourceIdentity
$stopReason=$null
$nativeExit=76
$child=[Diagnostics.Process]::new()
$child.StartInfo=[Diagnostics.ProcessStartInfo]::new()
$child.StartInfo.FileName=$python
$child.StartInfo.WorkingDirectory=$root
$child.StartInfo.UseShellExecute=$false
$child.StartInfo.CreateNoWindow=$true
$child.StartInfo.RedirectStandardOutput=$true
$child.StartInfo.RedirectStandardError=$true
$child.StartInfo.ArgumentList.Add('-B')
$child.StartInfo.ArgumentList.Add($scriptFull)
foreach ($argument in $ScriptArguments) { $child.StartInfo.ArgumentList.Add($argument) }
$outStream=$null
$errStream=$null
$childStarted=$false
$exceptionMessage=$null
try {
    $outStream=[IO.FileStream]::new((Join-Path $run 'output.log'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read,1,[IO.FileOptions]::WriteThrough)
    $errStream=[IO.FileStream]::new((Join-Path $run 'stderr.log'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read,1,[IO.FileOptions]::WriteThrough)
    $process.PriorityClass='Idle'
    $process.ProcessorAffinity=[IntPtr](1L -shl $Cpu)
    if (-not $child.Start()) { throw 'Native creation failed' }
    $childStarted=$true
    $copyOut=$child.StandardOutput.BaseStream.CopyToAsync($outStream)
    $copyErr=$child.StandardError.BaseStream.CopyToAsync($errStream)
    $watch=[Diagnostics.Stopwatch]::StartNew()
    while (-not $child.WaitForExit(1000)) {
        if ((Get-PSDrive D).Free -lt 50GB) { $stopReason='DISK_FLOOR' }
        if ($watch.Elapsed.TotalSeconds -ge $TimeoutSeconds) { $stopReason='DEADLINE' }
        if ($copyOut.IsFaulted -or $copyErr.IsFaulted) { $stopReason='CAPTURE_FAILED' }
        if ($stopReason) {
            # Only this freshly started Popen-equivalent process tree is stopped.
            $child.Kill($true)
            $child.WaitForExit()
            break
        }
    }
    $null=$copyOut.GetAwaiter().GetResult()
    $null=$copyErr.GetAwaiter().GetResult()
    $nativeExit=$child.ExitCode
    if ($stopReason) { $nativeExit=70 }
} catch {
    $nativeExit=70
    if (-not $stopReason) { $stopReason='SUPERVISOR_EXCEPTION' }
    $exceptionMessage=$_.Exception.Message
} finally {
    if ($childStarted -and -not $child.HasExited) {
        $child.Kill($true)
        $child.WaitForExit()
    }
    if ($copyOut) { try { $null=$copyOut.GetAwaiter().GetResult() } catch { $nativeExit=70; $stopReason='CAPTURE_FAILED' } }
    if ($copyErr) { try { $null=$copyErr.GetAwaiter().GetResult() } catch { $nativeExit=70; $stopReason='CAPTURE_FAILED' } }
    if ($outStream) { $outStream.Dispose() }
    if ($errStream) { $errStream.Dispose() }
    $process.ProcessorAffinity=$oldAffinity
    $process.PriorityClass=$oldPriority
}
$scriptAfter=$null
$sourcesAfter=@{}
if ((Get-PSDrive D).Free -lt 50GB) {
    Write-Output 'DISK_FLOOR: owned worker stopped; no receipt allocation or next job.'
    exit 70
}
try {
    $scriptAfter=(Get-FileHash -LiteralPath $scriptFull -Algorithm SHA256).Hash.ToLower()
    $sourcesAfter=Get-SourceIdentity
    if ($scriptAfter -ne $scriptHash -or $sourcesBefore.Count -ne $sourcesAfter.Count) { throw 'Source identity changed' }
    foreach ($name in $sourcesBefore.Keys) { if ($sourcesBefore[$name] -ne $sourcesAfter[$name]) { throw "Source identity changed: $name" } }
} catch { $nativeExit=70; $stopReason='SOURCE_CHANGED'; $exceptionMessage=$_.Exception.Message }
$receipt=@{schema=2;script=$scriptFull;arguments=$ScriptArguments;python=$python;cpu=$Cpu;priority='Idle';threads=1;started=$started;finished=[DateTime]::UtcNow.ToString('o');exit_code=$nativeExit;stop_reason=$stopReason;exception=$exceptionMessage;free_bytes=(Get-PSDrive D).Free;required_bytes=$RequiredBytes;script_sha256_before=$scriptHash;script_sha256_after=$scriptAfter;source_sha256_before=$sourcesBefore;source_sha256_after=$sourcesAfter;log='output.log';stderr='stderr.log'}
if ((Get-PSDrive D).Free -lt (50GB+1MB)) { Write-Output 'Receipt allocation reserve refused; no next job.'; exit 70 }
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $run 'receipt.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $run 'output.log') -Tail 22
Get-Content -LiteralPath (Join-Path $run 'stderr.log') -Tail 22
if ((Get-PSDrive D).Free -lt 50GB) { throw 'Disk floor breached; no next job' }
exit $nativeExit
