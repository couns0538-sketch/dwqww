#requires -Version 5.1
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9]+$')][string]$RunId)
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]8
$python='D:\a10\python\python.exe'
$file=Join-Path $PSScriptRoot ('runtime-integration-'+$RunId+'.manifest.json')
$launch=Join-Path $PSScriptRoot ('runtime-integration-'+$RunId+'-launch')
if((Test-Path -LiteralPath $file) -or (Test-Path -LiteralPath $launch)){throw 'Preserve fixture attempt'}
$testSpec=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;
 arguments=@('-B',(Join-Path $PSScriptRoot 'test_collector_runtime.py'),'--threads','1');working_directory='D:\a10';output_directory=$launch;
 read_paths=@($python,'D:\a10');write_paths=@($launch,'D:\a10\tmp');
 logical_cpus=@(3);worker_threads=1;minimum_free_mib=51200;required_bytes=10000000}
$testSpec|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $file -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $file
exit $LASTEXITCODE
