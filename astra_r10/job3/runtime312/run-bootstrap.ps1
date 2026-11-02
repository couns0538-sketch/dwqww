#requires -Version 5.1
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]8
$python='D:\a10\python\python.exe'
$file=Join-Path $PSScriptRoot 'bootstrap.manifest.json'
$launch=Join-Path $PSScriptRoot 'bootstrap-launch'
if((Test-Path -LiteralPath $file) -or (Test-Path -LiteralPath $launch)){throw 'Preserve bootstrap attempt'}
$bootstrapSpec=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;
 arguments=@('-B',(Join-Path $PSScriptRoot 'bootstrap.py'),'--threads','1');working_directory='D:\a10';output_directory=$launch;
 read_paths=@($python,'D:\a10');write_paths=@($launch,(Join-Path $PSScriptRoot 'BOOTSTRAP.json'),'D:\a10\job3\runtime312');
 logical_cpus=@(3);worker_threads=1;minimum_free_mib=51200;required_bytes=500000000}
$bootstrapSpec|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $file -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $file
exit $LASTEXITCODE
