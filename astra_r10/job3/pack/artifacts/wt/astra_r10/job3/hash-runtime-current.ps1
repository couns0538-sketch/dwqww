#requires -Version 5.1
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]8
$python='D:\a10\python\python.exe'
$file=Join-Path $PSScriptRoot 'runtime-current.manifest.json'
$launch=Join-Path $PSScriptRoot 'launch-runtime-current'
if((Test-Path -LiteralPath $file) -or (Test-Path -LiteralPath $launch) -or (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'RUNTIME_CURRENT_HASHES.json'))){throw 'Preserve prior runtime receipts'}
$runtimeHashManifest=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;
 arguments=@('-B',(Join-Path $PSScriptRoot 'hash_runtime_current.py'),'--threads','1');working_directory='D:\a10';output_directory=$launch;
 read_paths=@($python,'D:\a10');write_paths=@($launch,(Join-Path $PSScriptRoot 'RUNTIME_CURRENT_HASHES.json'));
 logical_cpus=@(3);worker_threads=1;minimum_free_mib=51200;required_bytes=20000000}
$runtimeHashManifest|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $file -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $file
exit $LASTEXITCODE
