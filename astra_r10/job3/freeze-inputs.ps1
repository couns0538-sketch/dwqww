#requires -Version 5.1
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$python='D:\a10\python\python.exe';$file=Join-Path $PSScriptRoot 'freeze-manifest01.json';$launch=Join-Path $PSScriptRoot 'launch-freeze01'
if(Test-Path -LiteralPath $file){throw 'preserve manifest'}
$m=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;
 arguments=@('-B',(Join-Path $PSScriptRoot 'freeze_inputs.py'),'--threads','1');working_directory='D:\a10';output_directory=$launch;
 read_paths=@($python,'D:\a10','D:\grok-pc-data\dwqww\astra8_data','D:\grok-pc-data\selfplay_out');write_paths=@($launch,(Join-Path $PSScriptRoot 'freeze01'),'D:\a10\job3\inputs');
 logical_cpus=@(2,3);worker_threads=1;minimum_free_mib=51200;required_bytes=1936978153}
$m|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $file -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $file
exit $LASTEXITCODE
