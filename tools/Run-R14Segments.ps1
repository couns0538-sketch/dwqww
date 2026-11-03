param(
    [ValidateSet('production','jobA')][string]$Mode,
    [ValidateRange(0,3)][int]$Cpu=3,
    [ValidateRange(60,18000)][int]$Seconds=10800,
    [Parameter(Mandatory=$true)][string]$Name
)
$ErrorActionPreference='Stop'
if ($Name -notmatch '^[a-z0-9_-]+$') { throw 'Invalid run name' }
if (-not $Mode) { throw 'Explicit scan mode required' }
$root='D:\a14'
$out=Join-Path $root ('sep\segments-'+$Name)
$log=Join-Path $root ('evidence\r14\segments-'+$Name+'.log')
if ((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $log)) { throw 'Existing run refused' }
if ((Get-PSDrive D).Free -lt (50GB+32MB) -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk admission refused' }
$ownedBytes=(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Measure-Object -Property Length -Sum).Sum
if ([long]$ownedBytes+32MB -ge 5000000000L) { throw 'Owned storage admission refused before log allocation' }
$process=[Diagnostics.Process]::GetCurrentProcess()
$oldPriority=$process.PriorityClass
$names=@('TEMP','TMP','CUDA_VISIBLE_DEVICES','HIP_VISIBLE_DEVICES','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','ASTRA_R14_DEADLINE','ASTRA_R13_DEADLINE')
$saved=@{}
foreach ($name in $names) { $saved[$name]=[Environment]::GetEnvironmentVariable($name,'Process') }
try {
    $process.PriorityClass='Idle'
    $env:TEMP=Join-Path $root 'tmp'
    $env:TMP=$env:TEMP
    $env:CUDA_VISIBLE_DEVICES='-1'
    $env:HIP_VISIBLE_DEVICES='-1'
    $env:OMP_NUM_THREADS='1'
    $env:OPENBLAS_NUM_THREADS='1'
    $env:MKL_NUM_THREADS='1'
    $env:ASTRA_R14_DEADLINE=([DateTimeOffset]::UtcNow.ToUnixTimeSeconds()+$Seconds).ToString()
    $env:ASTRA_R13_DEADLINE=$env:ASTRA_R14_DEADLINE
    # The scanner guards bounded native requests, owned child cleanup and sealing.
    & D:\a14\runtime\python\python.exe -I -B D:\a14\tools\r14_segments.py --mode $Mode --cpu $Cpu --seconds $Seconds --qualification D:\a14\sep\qualification-million01\REPORT.json --qualification-md5 b91461a33503289c3025b5723d202d72 --out $out *> $log
    $code=$LASTEXITCODE
} finally {
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$saved[$name],'Process') }
    $process.PriorityClass=$oldPriority
}
Get-Content -LiteralPath $log -Tail 8
exit $code
