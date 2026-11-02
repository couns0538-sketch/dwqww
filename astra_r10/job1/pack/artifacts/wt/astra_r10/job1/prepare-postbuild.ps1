$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity=[IntPtr]12
$base='D:\a10\wt\astra_r10\job1'
function Make-Manifest($Name,$Script,$Arguments,$Reads,$Writes,$Bytes){
 $out="$base\launch-$Name"
 $m=[ordered]@{schema=1;executable='D:\a10\python\python.exe';executable_sha256=(Get-FileHash D:\a10\python\python.exe).Hash;
 arguments=(@('-B',$Script,'--threads','1')+$Arguments);working_directory='D:\a10';output_directory=$out;
 read_paths=(@('D:\a10\python\python.exe','D:\a10\python','D:\a10\pydeps',$Script)+$Reads);
 write_paths=(@($out,'D:\a10\tmp')+$Writes);logical_cpus=@(2,3);worker_threads=1;minimum_free_mib=51200;required_bytes=$Bytes}
 $p="$base\manifest-$Name.json"; if(Test-Path $p){throw 'existing manifest'}
 $m | ConvertTo-Json -Depth 4 | Set-Content $p -Encoding UTF8
}
Make-Manifest 'build-proof01' "$base\collect_build_proof.py" @('--out',"$base\build-proof01") @('D:\a10\b','D:\a10\c1',"$base\build-pc1-a","$base\build-pc2-a",'D:\a10\wt\astra_r9\evidence\c1-source.json') @("$base\build-proof01") 500000000
Make-Manifest 'validation-tests01' "$base\validation\test_checks.py" @() @("$base\validation") @() 1000000
