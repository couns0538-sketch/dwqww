#Requires -Version 7
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
$root = 'D:\a14'
$python = 'D:\a14\runtime\python\python.exe'
. (Join-Path $root 'tools\R14-OwnedJob.ps1')
function Assert-OwnedStorage([long]$NextBytes=0) {
    $used=(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Measure-Object -Property Length -Sum).Sum
    if ($NextBytes -lt 0 -or ([long]$used+$NextBytes) -ge 5000000000L) { throw 'Owned storage cap admission refused' }
}
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
if ($RequiredBytes -lt 0 -or (Get-PSDrive D).Free -lt (50GB + $RequiredBytes) -or (Get-PSDrive C).Free -lt 30GB) { throw '50 GiB plus allocation admission refused' }
Assert-OwnedStorage $RequiredBytes
$run = Join-Path $root ('evidence\test_logs\r14\launchers\' + $RunName)
Assert-OwnedPath $run
if (Test-Path -LiteralPath $run) { throw 'Refusing reused run directory' }
$samples = Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor
if ($Cpu -eq -1) {
    $usage = $samples | Where-Object Name -in @('0','1','2','3') | Sort-Object PercentProcessorTime | Select-Object -First 1
    $Cpu=[int]$usage.Name
} else { $usage = $samples | Where-Object Name -eq ([string]$Cpu) }
if (-not $usage -or [int]$usage.PercentProcessorTime -gt 70) { throw "CPU $Cpu admission refused: $($usage.PercentProcessorTime)% busy" }
New-Item -ItemType Directory -Path $run, (Join-Path $run 'tmp') | Out-Null
$childEnvironment=@{}
$childEnvironment['PYTHONDONTWRITEBYTECODE']='1'
$childEnvironment['PYTHONNOUSERSITE']='1'
$childEnvironment['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
$childEnvironment['CUDA_VISIBLE_DEVICES']='-1'
$childEnvironment['HIP_VISIBLE_DEVICES']='-1'
$childEnvironment['ROCR_VISIBLE_DEVICES']='-1'
$childEnvironment['OMP_NUM_THREADS']='1'
$childEnvironment['MKL_NUM_THREADS']='1'
$childEnvironment['OPENBLAS_NUM_THREADS']='1'
$childEnvironment['NUMEXPR_NUM_THREADS']='1'
$childEnvironment['TEMP']=Join-Path $run 'tmp'
$childEnvironment['TMP']=$childEnvironment['TEMP']
$childEnvironment['TMPDIR']=$childEnvironment['TEMP']
$childEnvironment['TORCH_HOME']=Join-Path $childEnvironment['TEMP'] 'torch'
$childEnvironment['TORCHINDUCTOR_CACHE_DIR']=Join-Path $childEnvironment['TEMP'] 'inductor'
$childEnvironment['TRITON_CACHE_DIR']=Join-Path $childEnvironment['TEMP'] 'triton'
$childEnvironment['PYTHONPYCACHEPREFIX']=Join-Path $childEnvironment['TEMP'] 'pycache'
$childEnvironment['MPLCONFIGDIR']=Join-Path $childEnvironment['TEMP'] 'matplotlib'
$childEnvironment['XDG_CACHE_HOME']=Join-Path $childEnvironment['TEMP'] 'xdg-cache'
$childEnvironment['XDG_CONFIG_HOME']=Join-Path $childEnvironment['TEMP'] 'xdg-config'
$childEnvironment['HF_HOME']=Join-Path $childEnvironment['TEMP'] 'huggingface'
$childEnvironment['ASTRA_R13_CPU']=[string]$Cpu
$childEnvironment['ASTRA_R13_DEADLINE']=([DateTimeOffset]::UtcNow.ToUnixTimeSeconds()+$TimeoutSeconds).ToString()
$childEnvironment['ASTRA_R14_DEADLINE']=$childEnvironment['ASTRA_R13_DEADLINE']
if ($WithDatafilterRuntime) { throw 'Protected runtime access is forbidden' }
$childEnvironment['PYTHONPATH']='D:\a14\tools'
$process=[Diagnostics.Process]::GetCurrentProcess()
$oldPriority=$process.PriorityClass
$oldAffinity=$process.ProcessorAffinity
$started=((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+' Vienna')
$scriptHash=(Get-FileHash -LiteralPath $scriptFull -Algorithm SHA256).Hash.ToLower()
$sourcesBefore=Get-SourceIdentity
$stopReason=$null
$nativeExit=76
$child=[Diagnostics.Process]::new()
$child.StartInfo=[Diagnostics.ProcessStartInfo]::new()
$child.StartInfo.FileName=$python
$child.StartInfo.WorkingDirectory=$root
$child.StartInfo.UseShellExecute=$false
foreach ($key in $childEnvironment.Keys) { $child.StartInfo.Environment[$key]=[string]$childEnvironment[$key] }
$child.StartInfo.CreateNoWindow=$true
$child.StartInfo.RedirectStandardOutput=$true
$child.StartInfo.RedirectStandardError=$true
$child.StartInfo.ArgumentList.Add('-B')
$child.StartInfo.ArgumentList.Add($scriptFull)
foreach ($argument in $ScriptArguments) { $child.StartInfo.ArgumentList.Add($argument) }
$job=Initialize-R14JobChild $child $run $python (@('-B',$scriptFull)+$ScriptArguments)
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
    Release-R14JobChild $job $child
    $watch=[Diagnostics.Stopwatch]::StartNew()
    while (-not $child.WaitForExit(1000)) {
        if ((Get-PSDrive D).Free -lt 50GB -or (Get-PSDrive C).Free -lt 30GB) { $stopReason='DISK_FLOOR' }
        try { Assert-OwnedStorage 1MB } catch { $stopReason='OWNED_STORAGE_CAP' }
        if (-not $stopReason -and $watch.Elapsed.TotalSeconds -ge $TimeoutSeconds) { $stopReason='DEADLINE' }
        if (-not $stopReason -and ($copyOut.IsFaulted -or $copyErr.IsFaulted)) { $stopReason='CAPTURE_FAILED' }
        if ($stopReason) {
            # Only this freshly started Popen-equivalent process tree is stopped.
            $job.Dispose()
            if (-not $child.WaitForExit(5000)) { throw 'Owned child did not exit after job closure' }
            break
        }
    }
    Complete-R14JobCapture $job $child @($copyOut,$copyErr) {
        if ((Get-PSDrive D).Free -lt 50GB -or (Get-PSDrive C).Free -lt 30GB) { $script:stopReason='DISK_FLOOR'; throw 'Disk floor during capture' }
        try { Assert-OwnedStorage 1MB } catch { $script:stopReason='OWNED_STORAGE_CAP'; throw }
    }
    $nativeExit=$child.ExitCode
    if ($stopReason) { $nativeExit=70 }
} catch {
    $nativeExit=70
    if (-not $stopReason) { $stopReason='SUPERVISOR_EXCEPTION' }
    $exceptionMessage=$_.Exception.Message
} finally {
    if ($childStarted -and -not $child.HasExited) {
        try { Stop-R14JobChild $job $child $childStarted }
        catch { $nativeExit=70; if (-not $stopReason) { $stopReason='CHILD_EXIT_TIMEOUT' } }
    }
    try { Complete-R14JobCapture $job $child @($copyOut,$copyErr) $null }
    catch { $nativeExit=70; if (-not $stopReason) { $stopReason='CAPTURE_FAILED' } }
    if ($outStream) { $outStream.Dispose() }
    if ($errStream) { $errStream.Dispose() }
    $process.ProcessorAffinity=$oldAffinity
    $process.PriorityClass=$oldPriority
}
$scriptAfter=$null
$sourcesAfter=@{}
if ($stopReason -eq 'OWNED_STORAGE_CAP') {
    Write-Output 'OWNED_STORAGE_CAP: owned worker stopped; no receipt allocation or next job.'
    exit 70
}
if ((Get-PSDrive D).Free -lt 50GB -or (Get-PSDrive C).Free -lt 30GB) {
    Write-Output 'DISK_FLOOR: owned worker stopped; no receipt allocation or next job.'
    exit 70
}
try { Assert-OwnedStorage 1MB } catch {
    Write-Output 'OWNED_STORAGE_CAP: post-child reserve refused; no receipt allocation or next job.'
    exit 70
}
try {
    $scriptAfter=(Get-FileHash -LiteralPath $scriptFull -Algorithm SHA256).Hash.ToLower()
    $sourcesAfter=Get-SourceIdentity
    if ($scriptAfter -ne $scriptHash -or $sourcesBefore.Count -ne $sourcesAfter.Count) { throw 'Source identity changed' }
    foreach ($name in $sourcesBefore.Keys) { if ($sourcesBefore[$name] -ne $sourcesAfter[$name]) { throw "Source identity changed: $name" } }
} catch { $nativeExit=70; $stopReason='SOURCE_CHANGED'; $exceptionMessage=$_.Exception.Message }
$receipt=@{schema=2;script=$scriptFull;arguments=$ScriptArguments;python=$python;cpu=$Cpu;priority='Idle';threads=1;started=$started;finished=((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+' Vienna');exit_code=$nativeExit;stop_reason=$stopReason;exception=$exceptionMessage;free_bytes=(Get-PSDrive D).Free;required_bytes=$RequiredBytes;script_sha256_before=$scriptHash;script_sha256_after=$scriptAfter;source_sha256_before=$sourcesBefore;source_sha256_after=$sourcesAfter;log='output.log';stderr='stderr.log'}
if ((Get-PSDrive D).Free -lt (50GB+1MB) -or (Get-PSDrive C).Free -lt 30GB) { Write-Output 'Receipt allocation reserve refused; no next job.'; exit 70 }
try { Assert-OwnedStorage 1MB } catch {
    Write-Output 'OWNED_STORAGE_CAP: receipt reserve refused; no receipt allocation or next job.'
    exit 70
}
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $run 'receipt.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $run 'output.log') -Tail 22
Get-Content -LiteralPath (Join-Path $run 'stderr.log') -Tail 22
if ((Get-PSDrive D).Free -lt 50GB -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk floor breached; no next job' }
exit $nativeExit
