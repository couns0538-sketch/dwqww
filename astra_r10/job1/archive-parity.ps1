$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity=[IntPtr]12
$base='D:\a10\wt\astra_r10\job1';$out="$base\launch-archive01"
$m=[ordered]@{schema=1;executable='D:\a10\python\python.exe';executable_sha256=(Get-FileHash D:\a10\python\python.exe).Hash;
arguments=@('-B',"$base\archive_parity.py",'--threads','1');working_directory='D:\a10';output_directory=$out;
read_paths=@('D:\a10\python\python.exe',"$base\archive_parity.py",'D:\a10\parity-r1','D:\a10\c1','D:\a10\parity-negative','D:\a10\parity-compiler-probe01');write_paths=@($out,"$base\native-parity");logical_cpus=@(2,3);worker_threads=1;minimum_free_mib=51200;required_bytes=200000000}
$path="$base\manifest-archive01.json";if(Test-Path $path){throw 'manifest exists'}
$m|ConvertTo-Json -Depth 4|Set-Content $path -Encoding UTF8
