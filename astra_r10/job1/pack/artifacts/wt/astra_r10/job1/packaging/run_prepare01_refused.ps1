$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$env:TEMP='D:\a10\tmp';$env:TMP=$env:TEMP;$env:PYTHONDONTWRITEBYTECODE='1'
$python='D:\a10\python\python.exe'
$launchOut='D:\a10\wt\astra_r10\job1\launch-preparepack01'
$prepared=Join-Path $PSScriptRoot 'prepared01'
$path=Join-Path $PSScriptRoot 'prepare-launch01.json'
if((Test-Path -LiteralPath $path) -or (Test-Path -LiteralPath $prepared) -or (Test-Path -LiteralPath $launchOut)){throw 'Fresh preparation output required'}
$m=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;arguments=@('-B',(Join-Path $PSScriptRoot 'prepare_pack.py'),'--threads','1','--out',$prepared,'--launcher-output',$launchOut);working_directory='D:\a10';output_directory=$launchOut;read_paths=@('D:\a10');write_paths=@($launchOut,$prepared);logical_cpus=@(2);worker_threads=1;minimum_free_mib=51200;required_bytes=10000000}
$m | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $path -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $path
exit $LASTEXITCODE
