$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$env:TEMP='D:\a10\tmp';$env:TMP=$env:TEMP;$env:PYTHONDONTWRITEBYTECODE='1'
$python='D:\a10\python\python.exe'
$out=Join-Path $PSScriptRoot 'launch'
$m=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;arguments=@('-B',(Join-Path $PSScriptRoot 'recompute.py'),'--threads','1');working_directory=$PSScriptRoot;output_directory=$out;read_paths=@($python,'D:\a10\wt','D:\a10\inputs','D:\a10\c1','D:\a10\kit','D:\a10\b','D:\a10\parity-r1');write_paths=@($out,$PSScriptRoot);logical_cpus=@(2);worker_threads=1;minimum_free_mib=51200;required_bytes=10485760}
$path=Join-Path $PSScriptRoot 'manifest.json'
if (Test-Path -LiteralPath $path) {throw 'Review manifest exists'}
$m | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $path -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $path
exit $LASTEXITCODE
