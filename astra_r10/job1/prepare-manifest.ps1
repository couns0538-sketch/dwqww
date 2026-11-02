param([Parameter(Mandatory=$true)][ValidatePattern('^pc[12](-[a-z0-9]+)?$')][string]$Tag)
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity=[IntPtr]12
$out="D:\a10\wt\astra_r10\job1\launch-$Tag"
$m=[ordered]@{
 schema=1
 executable='D:\a10\python\python.exe'
 executable_sha256=(Get-FileHash D:\a10\python\python.exe -Algorithm SHA256).Hash
 arguments=@('-B','D:\a10\wt\astra_r10\job1\run_build.py','--threads','2','--tag',$Tag)
 working_directory='D:\a10'
 output_directory=$out
 read_paths=@('D:\a10\python\python.exe','D:\a10\python','D:\a10\pydeps','D:\a10\wt\astra_r10\job1\run_build.py','D:\a10\wt\astra_r9\evidence\c1-source.json','D:\a10\c1','D:\a10\kit')
 write_paths=@($out,'D:\a10\b','D:\a10\kit',"D:\a10\wt\astra_r10\job1\build-$Tag",'D:\a10\tmp')
 logical_cpus=@(2,3)
 worker_threads=2
 minimum_free_mib=51200
 required_bytes=1000000000
}
$path="D:\a10\wt\astra_r10\job1\manifest-$Tag.json"
if(Test-Path $path){throw 'manifest exists'}
$m | ConvertTo-Json -Depth 5 | Set-Content $path -Encoding UTF8
