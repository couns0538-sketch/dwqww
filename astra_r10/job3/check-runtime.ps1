$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]8
$env:TEMP='D:\a10\tmp';$env:TMP=$env:TEMP;$env:PYTHONDONTWRITEBYTECODE='1';$env:PYTHONNOUSERSITE='1';$env:PYTHONPATH='D:\a10\job3\runtime\packages'
$env:CUDA_VISIBLE_DEVICES='';$env:HIP_VISIBLE_DEVICES='';$env:ROCR_VISIBLE_DEVICES=''
$python='D:\a10\job3\runtime\python\python.exe';$launch=Join-Path $PSScriptRoot 'launch-runtime01';$path=Join-Path $PSScriptRoot 'runtime-manifest01.json'
if(Test-Path -LiteralPath $path){throw 'Fresh manifest required'}
@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;arguments=@('-B',(Join-Path $PSScriptRoot 'check_runtime.py'),'--threads','1');working_directory='D:\a10';output_directory=$launch;read_paths=@($python,'D:\a10\job3\runtime',(Join-Path $PSScriptRoot 'check_runtime.py'));write_paths=@($launch,'D:\a10\tmp');logical_cpus=@(3);worker_threads=1;minimum_free_mib=51200;required_bytes=10000000} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $path -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $path
exit $LASTEXITCODE
