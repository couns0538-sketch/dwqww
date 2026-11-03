param([ValidateSet(0,3)][int]$Cpu=0,[Parameter(Mandatory=$true)][string]$Name)
$ErrorActionPreference='Stop'
if ($Name -notmatch '^[a-z0-9_-]+$') { throw 'Invalid run name' }
$root='D:\a14'
$out=Join-Path $root ('sep\joba-map-'+$Name)
$log=Join-Path $root ('evidence\r14\joba-map-'+$Name+'.log')
if ((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $log)) { throw 'Existing run refused' }
if ((Get-PSDrive D).Free -lt (50GB+32MB) -or (Get-PSDrive C).Free -lt 30GB) { throw 'Disk admission refused' }
$used=(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Measure-Object -Property Length -Sum).Sum
if ([long]$used+32MB -ge 5000000000L) { throw 'Owned storage admission refused' }
$process=[Diagnostics.Process]::GetCurrentProcess()
$priority=$process.PriorityClass
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
    $env:ASTRA_R14_DEADLINE=([DateTimeOffset]::UtcNow.ToUnixTimeSeconds()+300).ToString()
    $env:ASTRA_R13_DEADLINE=$env:ASTRA_R14_DEADLINE
    # A single-process bounded source join; no native child or training import.
    & D:\a14\runtime\python\python.exe -I -B D:\a14\tools\r14_joba.py --scan D:\a14\sep\segments-joba01\REPORT.json --scan-md5 77b76a460e569e50196da08f083e95d4 --out $out --cpu $Cpu --seconds 300 *> $log
    $code=$LASTEXITCODE
} finally {
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$saved[$name],'Process') }
    $process.PriorityClass=$priority
}
Get-Content -LiteralPath $log -Tail 6
exit $code
