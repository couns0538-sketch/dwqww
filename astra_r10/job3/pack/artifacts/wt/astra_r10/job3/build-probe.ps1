$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]8
$env:TEMP='D:\a10\tmp';$env:TMP=$env:TEMP;$env:PYTHONDONTWRITEBYTECODE='1'
$python='D:\a10\python\python.exe';$out='D:\a10\job3\probe01';$launch=Join-Path $PSScriptRoot 'launch-probe01';$path=Join-Path $PSScriptRoot 'probe-manifest01.json'
if(Test-Path -LiteralPath $path){throw 'Fresh manifest required'}
@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;arguments=@('-B',(Join-Path $PSScriptRoot 'build_probe.py'),'--threads','1','--out',$out);working_directory='D:\a10';output_directory=$launch;read_paths=@($python,'D:\a10');write_paths=@($out,$launch,'D:\a10\tmp');logical_cpus=@(3);worker_threads=1;minimum_free_mib=51200;required_bytes=300000000} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $path -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $path
exit $LASTEXITCODE
