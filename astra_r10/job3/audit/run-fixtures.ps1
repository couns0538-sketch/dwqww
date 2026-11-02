#requires -Version 5.1
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9]+$')][string]$RunId)
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]4
$python='D:\a10\python\python.exe'
$file=Join-Path $PSScriptRoot ("fixtures-manifest-"+$RunId+".json")
$launch=Join-Path $PSScriptRoot ("launch-fixtures-"+$RunId)
$output=Join-Path $PSScriptRoot ("fixtures-"+$RunId)
if((Test-Path -LiteralPath $file) -or (Test-Path -LiteralPath $launch) -or (Test-Path -LiteralPath $output)){throw 'Preserve previous fixture evidence; choose a fresh run ID'}
$m=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;
 arguments=@('-B',(Join-Path $PSScriptRoot 'test_audit_selfplay.py'),'--out',$output,'--threads','1');working_directory='D:\a10';output_directory=$launch;
 read_paths=@($python,'D:\a10');write_paths=@($launch,$output);
 logical_cpus=@(2);worker_threads=1;minimum_free_mib=51200;required_bytes=2000000000}
$m|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $file -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $file
exit $LASTEXITCODE
