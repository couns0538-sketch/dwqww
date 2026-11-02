param([ValidateSet('smoke','sanitizer')][string]$Kind)
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity=[IntPtr]12
$base='D:\a10\wt\astra_r10\job1'
$out="$base\$Kind-01"; $launch="$base\launch-$Kind-01"
$exe=if($Kind -eq 'smoke'){'D:\a10\b\pc1-a\src_copy\forge_ltopgo_pc1-a.exe'}else{'D:\a10\inputs\forge_san_c1.exe'}
$m=[ordered]@{schema=1;executable='D:\a10\python\python.exe';executable_sha256=(Get-FileHash D:\a10\python\python.exe).Hash;
 arguments=@('-B',"$base\validation\run_checks.py",'--threads','1','--out',$out,'--exe',$exe,'--kind',$Kind);
 working_directory='D:\a10';output_directory=$launch;
 read_paths=@('D:\a10\python\python.exe','D:\a10\python','D:\a10\pydeps',"$base\validation",'D:\a10\inputs','D:\a10\wt\astra_r9\evidence\c1-source.json','D:\a10\wt\astra_r9\evidence\auxiliary-build-provenance.json',$exe);
 write_paths=@($out,$launch,'D:\a10\tmp');logical_cpus=@(2,3);worker_threads=1;minimum_free_mib=51200;required_bytes=50000000}
$file="$base\manifest-$Kind-01.json"
if(Test-Path $file){throw 'existing manifest'}
$m | ConvertTo-Json -Depth 4 | Set-Content $file -Encoding UTF8
