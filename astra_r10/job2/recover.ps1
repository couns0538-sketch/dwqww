$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$env:TEMP='D:\a10\tmp';$env:TMP=$env:TEMP;$env:PYTHONDONTWRITEBYTECODE='1'
$python='D:\a10\python\python.exe'
$launchOut=Join-Path $PSScriptRoot 'launch-recover01'
$snapshot=Join-Path $PSScriptRoot 'inputs01'
$path=Join-Path $PSScriptRoot 'recover-manifest01.json'
if(Test-Path -LiteralPath $path){throw 'Fresh manifest required'}
$m=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;arguments=@('-B',(Join-Path $PSScriptRoot 'recover_inputs.py'),'--threads','1','--out',$snapshot);working_directory='D:\a10';output_directory=$launchOut;read_paths=@($python,'D:\a10');write_paths=@($launchOut,$snapshot,'D:\a10\repo','D:\a10\tmp');logical_cpus=@(2,3);worker_threads=1;minimum_free_mib=51200;required_bytes=1000000000}
$m | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $path -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $path
exit $LASTEXITCODE
