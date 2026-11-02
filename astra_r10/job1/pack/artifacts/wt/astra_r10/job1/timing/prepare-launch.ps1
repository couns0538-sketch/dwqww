$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity=[IntPtr]12
$base='D:\a10\wt\astra_r10\job1'; $t="$base\timing"
$reads=@('D:\a10\python\python.exe','D:\a10\python','D:\a10\pydeps',$t,"$base\build-proof01\REPORT.json","$base\smoke-01\REPORT.json","$base\sanitizer-01\REPORT.json","$base\parity\check-launch01\stdout.log","$base\host.json",'D:\a10\wt\astra_r9\evidence\c1-source.json','D:\a10\c1\src\nnue_weights.inc','D:\a10\kit\build_ltopgo.ps1','D:\a10\inputs','D:\a10\b\pc1-a\src_copy\forge_ltopgo_pc1-a.exe','D:\a10\parity-r1')
foreach($name in @('freeze','run')){
 $out="$t\$name-launch02"
 $argsList=if($name -eq 'freeze'){@('-B',"$t\freeze_protocol.py",'--threads','1')}else{@('-B',"$t\run_timing.py",'--threads','1','--protocol',"$t\protocol.json",'--out',"$t\run01")}
 $writes=if($name -eq 'freeze'){@($out,"$t\protocol.json")}else{@($out,"$t\run01")}
 $m=[ordered]@{schema=1;executable='D:\a10\python\python.exe';executable_sha256=(Get-FileHash D:\a10\python\python.exe).Hash;
 arguments=$argsList;working_directory=$t;output_directory=$out;read_paths=$reads;write_paths=$writes;
 logical_cpus=@(2,3);worker_threads=1;minimum_free_mib=51200;required_bytes=200000000}
 $path="$t\$name-launch02-manifest.json";if(Test-Path $path){throw 'manifest exists'}
 $m|ConvertTo-Json -Depth 4|Set-Content $path -Encoding UTF8
}
