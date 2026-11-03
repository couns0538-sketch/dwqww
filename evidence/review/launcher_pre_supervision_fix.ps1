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
if ($RunName -notmatch '^[a-zA-Z0-9_-]+$') { throw 'Invalid run name' }
$scriptFull = [IO.Path]::GetFullPath($Script)
if (-not $scriptFull.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $scriptFull -PathType Leaf)) { throw 'Script outside owned root or missing' }
if ($RequiredBytes -lt 0 -or (Get-PSDrive D).Free -lt (50GB + $RequiredBytes)) { throw '50 GiB plus allocation admission refused' }
$run = Join-Path $root ('evidence\runs\' + $RunName)
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
$outStream=[IO.File]::Open((Join-Path $run 'output.log'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
$errStream=[IO.File]::Open((Join-Path $run 'stderr.log'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try {
    $process.PriorityClass='Idle'
    $process.ProcessorAffinity=[IntPtr](1L -shl $Cpu)
    if (-not $child.Start()) { throw 'Native creation failed' }
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
} finally {
    $outStream.Dispose()
    $errStream.Dispose()
    $process.ProcessorAffinity=$oldAffinity
    $process.PriorityClass=$oldPriority
}
$receipt=@{schema=1;script=$scriptFull;arguments=$ScriptArguments;python=$python;cpu=$Cpu;priority='Idle';threads=1;started=$started;finished=[DateTime]::UtcNow.ToString('o');exit_code=$nativeExit;stop_reason=$stopReason;free_bytes=(Get-PSDrive D).Free;required_bytes=$RequiredBytes;script_sha256_before=$scriptHash;script_sha256_after=(Get-FileHash -LiteralPath $scriptFull -Algorithm SHA256).Hash.ToLower();log='output.log';stderr='stderr.log'}
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $run 'receipt.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $run 'output.log') -Tail 22
Get-Content -LiteralPath (Join-Path $run 'stderr.log') -Tail 22
if ((Get-PSDrive D).Free -lt 50GB) { throw 'Disk floor breached; no next job' }
exit $nativeExit
