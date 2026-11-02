$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity=[IntPtr]12
$base='D:\a10\wt\astra_r10\job1\timing'
$out="$base\test-launch01"
$m=[ordered]@{schema=1;executable='D:\a10\python\python.exe';executable_sha256=(Get-FileHash D:\a10\python\python.exe).Hash;
arguments=@('-B',"$base\test_timing.py",'--threads','1','--out',"$base\tests01");working_directory='D:\a10';output_directory=$out;
read_paths=@('D:\a10\python\python.exe','D:\a10\python','D:\a10\pydeps',$base,'D:\a10\inputs','D:\a10\wt\astra_r9\evidence\c1-source.json');
write_paths=@($out,"$base\tests01");logical_cpus=@(2,3);worker_threads=1;minimum_free_mib=51200;required_bytes=10000000}
$m|ConvertTo-Json -Depth 4|Set-Content "$base\test-launch01-manifest.json" -Encoding UTF8
