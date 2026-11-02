$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity=[IntPtr]12
$base='D:\a10\wt\astra_r10\job1'
if(Test-Path D:\a10\inputs\gcc-15.2-gpp.exe){throw 'compiler copy exists'}
Copy-Item C:\msys64\ucrt64\bin\g++.exe D:\a10\inputs\gcc-15.2-gpp.exe
if((Get-FileHash D:\a10\inputs\gcc-15.2-gpp.exe).Hash -ne '08C11FAA4F15A460AF8D90A2FD90F658658938C94051BDE8BABFBECCE3304C6C'){throw 'compiler identity'}
$text=[IO.File]::ReadAllText('D:\a10\wt\astra_r9\tools\host_metadata.py')
$text=$text.Replace('D:/a9/pydeps','D:/a10/pydeps')
$text=$text.Replace("pathlib.Path(__file__).parents[1]/'evidence/host.json'","pathlib.Path('D:/a10/wt/astra_r10/job1/host.json')")
$prefix="import argparse`np=argparse.ArgumentParser(); p.add_argument('--threads',type=int,choices=[1],required=True); p.parse_args()`n"
[IO.File]::WriteAllText("$base\host_metadata.py",$prefix+$text)
$out="$base\launch-host01"
$m=[ordered]@{schema=1;executable='D:\a10\python\python.exe';executable_sha256=(Get-FileHash D:\a10\python\python.exe).Hash;
arguments=@('-B',"$base\host_metadata.py",'--threads','1');working_directory='D:\a10';output_directory=$out;
read_paths=@('D:\a10\python\python.exe','D:\a10\python','D:\a10\pydeps',"$base\host_metadata.py");write_paths=@($out,"$base\host.json");logical_cpus=@(2,3);worker_threads=1;minimum_free_mib=51200;required_bytes=1000000}
$m|ConvertTo-Json -Depth 4|Set-Content "$base\manifest-host01.json" -Encoding UTF8
