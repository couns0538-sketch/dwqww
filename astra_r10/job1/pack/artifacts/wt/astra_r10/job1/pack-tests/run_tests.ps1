#requires -Version 5.1
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$Tag)
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]4
$out=Join-Path $PSScriptRoot $Tag
$file=Join-Path $PSScriptRoot ($Tag+'.manifest.json')
if ((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $file)) {throw 'Preserve previous evidence'}
$python='D:\a10\python\python.exe'
$test=Join-Path $PSScriptRoot 'test_seal_evidence.py'
$sealer='D:\a10\wt\skills\gate-handover-pack\scripts\seal_evidence.py'
$manifest=[ordered]@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;
 arguments=@('-B',$test,'--threads','1');working_directory=$PSScriptRoot;output_directory=$out;
 read_paths=@($python,'D:\a10\python',$test,$sealer);write_paths=@($out);logical_cpus=@(2);worker_threads=1;minimum_free_mib=51200;required_bytes=10000000}
$manifest|ConvertTo-Json -Depth 4|Set-Content -LiteralPath $file -Encoding UTF8
& 'D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1' -Manifest $file -ProtectedRoots @('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
exit $LASTEXITCODE
