#Requires -Version 7
param(
    [Parameter(Mandatory=$true)][string]$Output,
    [Parameter(Mandatory=$true)][ValidateRange(0,15)][int]$Cpu,
    [ValidateRange(1,1800)][int]$TimeoutSeconds=600,
    [ValidateRange(4096,67108864)][long]$LogBytes=33554432,
    [string]$FixtureJson,
    [switch]$CollectOnly
)
$ErrorActionPreference='Stop'
$root='D:\a14'
$python=Join-Path $root 'runtime\python\python.exe'
$worker=Join-Path $root 'tools\r14_suite.py'
$configuration=Join-Path $root 'tools\r14_suite.ini'
$native=Join-Path $root 'tools\r14_native\build\chain_native_r03.exe'
$run=[IO.Path]::GetFullPath($Output)
function Assert-OutputPath([string]$Path) {
    $full=[IO.Path]::GetFullPath($Path)
    if (-not ($full.StartsWith($root+'\evidence\test_logs\',[StringComparison]::OrdinalIgnoreCase) -or $full.StartsWith($root+'\tmp\',[StringComparison]::OrdinalIgnoreCase))) { throw 'Output must be owned test evidence' }
    $walk=$full
    while ($walk) {
        if (Test-Path -LiteralPath $walk) {
            if ((Get-Item -LiteralPath $walk -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Redirected output path' }
        }
        $walk=[IO.Path]::GetDirectoryName($walk)
    }
}
function Assert-Resources([long]$Reserve=1048576) {
    if ((Get-PSDrive D).Free -lt (50GB+$Reserve) -or (Get-PSDrive C).Free -lt 30GB) { throw 'DISK_FLOOR' }
    $used=(Get-ChildItem -LiteralPath $root -Recurse -Force -File | Measure-Object Length -Sum).Sum
    if ([long]$used+$Reserve -ge 5000000000L) { throw 'OWNED_STORAGE_CAP' }
}
function Get-CandidateIdentity {
    $map=@{}
    foreach ($path in @($python,$worker,$configuration,$native,$PSCommandPath,(Join-Path $root 'tools\R14-OwnedJob.ps1'),(Join-Path $root 'tools\R14-ChildGate.ps1'))) {
        $map[$path]=(Get-FileHash -LiteralPath $path -Algorithm MD5).Hash.ToLower()
    }
    return $map
}
Assert-OutputPath $run
if (Test-Path -LiteralPath $run) { throw 'Existing output refused' }
$usage=Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor | Where-Object Name -eq ([string]$Cpu)
if (-not $usage -or [int]$usage.PercentProcessorTime -gt 70) { throw 'CPU admission refused' }
Assert-Resources ($LogBytes+8MB)
$before=Get-CandidateIdentity
if ($before[$python] -ne '0cfdf7db1b81d067d3dad75f6abb312b') { throw 'Runtime executable identity changed' }
if ($before[$configuration] -ne 'b9d12b7f4027e03000d178ccb2a49077') { throw 'Suite configuration identity changed' }
if ($before[$native] -ne '91427a99870d6b3775595db55f0a82e8') { throw 'Native candidate identity changed' }
New-Item -ItemType Directory -Path $run,(Join-Path $run 'tmp') | Out-Null
$owner=[Diagnostics.Process]::GetCurrentProcess()
$oldPriority=$owner.PriorityClass
$oldAffinity=$owner.ProcessorAffinity
$compileEnvironment=@{}
foreach ($name in @('TEMP','TMP')) { $compileEnvironment[$name]=@{present=(Test-Path -LiteralPath ('Env:'+$name));value=[Environment]::GetEnvironmentVariable($name,'Process')} }
$child=$null
$job=$null
$started=$false
$stopReason=$null
$exception=$null
$nativeExit=76
$outStream=$null
$errStream=$null
$copyOut=$null
$copyErr=$null
$began=(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+' Vienna'
try {
    $owner.PriorityClass='Idle'
    $owner.ProcessorAffinity=[IntPtr](1L -shl $Cpu)
    $env:TEMP=Join-Path $run 'tmp'
    $env:TMP=$env:TEMP
    . (Join-Path $root 'tools\R14-OwnedJob.ps1')
    if (-not ('R14SuiteCapture' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
public sealed class R14SuiteCapture : Stream {
    readonly FileStream file; readonly long limit;
    public R14SuiteCapture(string path,long cap) { file=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read); limit=cap; }
    public override bool CanRead { get { return false; } }
    public override bool CanSeek { get { return false; } }
    public override bool CanWrite { get { return true; } }
    public override long Length { get { return file.Length; } }
    public override long Position { get { return file.Position; } set { throw new NotSupportedException(); } }
    public override void Flush() { file.Flush(true); }
    public override void Write(byte[] data,int offset,int count) { if(count>limit-file.Position) throw new IOException("LOG_CAP"); file.Write(data,offset,count); }
    public override Task WriteAsync(byte[] data,int offset,int count,CancellationToken token) { Write(data,offset,count); return Task.CompletedTask; }
    public override int Read(byte[] data,int offset,int count) { throw new NotSupportedException(); }
    public override long Seek(long offset,SeekOrigin origin) { throw new NotSupportedException(); }
    public override void SetLength(long value) { throw new NotSupportedException(); }
    protected override void Dispose(bool disposing) { if(disposing) file.Dispose(); base.Dispose(disposing); }
}
'@
    }
    $arguments=@('-I','-B',$worker,'--out',$run,'--seconds',[string]$TimeoutSeconds)
    if ($CollectOnly) { $arguments+='--collect-only' }
    if ($FixtureJson) { $arguments+=@('--fixture-json',$FixtureJson) }
    $child=[Diagnostics.Process]::new()
    $child.StartInfo=[Diagnostics.ProcessStartInfo]::new()
    $child.StartInfo.WorkingDirectory=$root
    $child.StartInfo.UseShellExecute=$false
    $child.StartInfo.CreateNoWindow=$true
    $child.StartInfo.RedirectStandardOutput=$true
    $child.StartInfo.RedirectStandardError=$true
    foreach ($name in @('ASTRA_R13_CPU','ASTRA_R14_CPU','ASTRA_R13_DEADLINE','ASTRA_R14_DEADLINE','PYTHONPATH')) { $null=$child.StartInfo.Environment.Remove($name) }
    foreach ($name in @($child.StartInfo.Environment.Keys)) { if ($name.StartsWith('PYTEST_',[StringComparison]::OrdinalIgnoreCase)) { $null=$child.StartInfo.Environment.Remove($name) } }
    foreach ($name in @('CUDA_VISIBLE_DEVICES','HIP_VISIBLE_DEVICES','ROCR_VISIBLE_DEVICES')) { $child.StartInfo.Environment[$name]='-1' }
    foreach ($name in @('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')) { $child.StartInfo.Environment[$name]='1' }
    foreach ($name in @('TEMP','TMP','TMPDIR')) { $child.StartInfo.Environment[$name]=Join-Path $run 'tmp' }
    foreach ($name in @('PYTHONDONTWRITEBYTECODE','PYTHONNOUSERSITE','PYTEST_DISABLE_PLUGIN_AUTOLOAD')) { $child.StartInfo.Environment[$name]='1' }
    $child.StartInfo.Environment['R14_SUITE_CHILD']=$run
    $child.StartInfo.Environment['R14_NATIVE_EXE']=$native
    $job=Initialize-R14JobChild $child $run $python $arguments
    $outStream=[R14SuiteCapture]::new((Join-Path $run 'output.log'),[long]($LogBytes/2))
    $errStream=[R14SuiteCapture]::new((Join-Path $run 'stderr.log'),[long]($LogBytes/2))
    if (-not $child.Start()) { throw 'Child creation failed' }
    $started=$true
    $copyOut=$child.StandardOutput.BaseStream.CopyToAsync($outStream)
    $copyErr=$child.StandardError.BaseStream.CopyToAsync($errStream)
    Release-R14JobChild $job $child
    $watch=[Diagnostics.Stopwatch]::StartNew()
    $nextStorage=0.0
    while (-not $child.WaitForExit(100)) {
        if ($copyOut.IsFaulted -or $copyErr.IsFaulted) { throw 'LOG_CAP_OR_CAPTURE_FAILED' }
        if ($watch.Elapsed.TotalSeconds -ge $TimeoutSeconds) { throw 'DEADLINE' }
        if ($watch.Elapsed.TotalSeconds -ge $nextStorage) { Assert-Resources; $nextStorage=$watch.Elapsed.TotalSeconds+2 }
    }
    Complete-R14JobCapture $job $child @($copyOut,$copyErr) {
        if ($watch.Elapsed.TotalSeconds -ge $TimeoutSeconds) { throw 'DEADLINE' }
        Assert-Resources
    }
    if ($watch.Elapsed.TotalSeconds -ge $TimeoutSeconds) { throw 'DEADLINE' }
    $nativeExit=$child.ExitCode
} catch {
    $exception=$_.Exception.Message
    $stopReason=if ($exception -match 'LOG_CAP') {'LOG_CAP'} elseif ($exception -match 'DEADLINE') {'DEADLINE'} elseif ($exception -match 'DISK_FLOOR|OWNED_STORAGE_CAP') {$Matches[0]} else {'SUPERVISOR_EXCEPTION'}
    $nativeExit=70
} finally {
    try { if ($job) { Stop-R14JobChild $job $child $started }; Complete-R14JobCapture $job $child @($copyOut,$copyErr) $null }
    catch { if (-not $stopReason) { $stopReason='CAPTURE_FAILED'; $exception=$_.Exception.Message }; $nativeExit=70 }
    foreach ($stream in @($outStream,$errStream)) { if ($stream) { try { $stream.Dispose() } catch { $stopReason='CAPTURE_CLOSE_FAILED';$nativeExit=70;$exception=$_.Exception.Message } } }
    $owner.ProcessorAffinity=$oldAffinity
    $owner.PriorityClass=$oldPriority
    foreach ($name in $compileEnvironment.Keys) {
        if ($compileEnvironment[$name].present) { [Environment]::SetEnvironmentVariable($name,$compileEnvironment[$name].value,'Process') }
        else { [Environment]::SetEnvironmentVariable($name,[NullString]::Value,'Process') }
    }
}
$supervision=@{started=$began;finished=((Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+' Vienna');cpu=$Cpu;priority='Idle';threads=1;native_exit=$nativeExit;stop_reason=$stopReason;exception=$exception;log_bytes_limit=$LogBytes;candidate_before=$before}
try {
    Assert-Resources 8MB
    $after=Get-CandidateIdentity
    $supervision.candidate_after=$after
    foreach ($path in $before.Keys) { if ($before[$path] -ne $after[$path]) { throw 'Candidate identity changed' } }
    if ($stopReason) { throw $stopReason }
    if ($nativeExit -notin @(0,1,2)) { throw 'Unexpected worker exit' }
    $receipt=Get-Content -LiteralPath (Join-Path $run 'worker-result.json.part') -Raw | ConvertFrom-Json -AsHashtable
    if (($nativeExit -eq 0) -ne ($receipt.status -in @('PASS','COLLECTED'))) { throw 'Worker status/exit mismatch' }
    $receipt.supervision=$supervision
    $pending=Join-Path $run 'REPORT.json.part'
    $payload=[Text.UTF8Encoding]::new($false).GetBytes(($receipt | ConvertTo-Json -Depth 20))
    $sink=[IO.FileStream]::new($pending,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    try { $sink.Write($payload,0,$payload.Length);$sink.Flush($true) } finally { $sink.Dispose() }
    Assert-Resources 1MB
    Assert-OutputPath $run
    [IO.File]::Move($pending,(Join-Path $run 'REPORT.json'))
} catch {
    $supervision.stop_reason=if ($stopReason) {$stopReason} else {'PUBLICATION_REFUSED'}
    $supervision.exception=$_.Exception.Message
    $nativeExit=70
}
$supervision | ConvertTo-Json -Depth 6 -Compress | Write-Output
exit $nativeExit
