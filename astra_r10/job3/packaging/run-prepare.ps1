#requires -Version 5.1
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9]+$')][string]$RunId,
      [Parameter(Mandatory=$true)][string]$FinalReceipt)
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]8
$python='D:\a10\python\python.exe'
$file=Join-Path $PSScriptRoot ("prepare-"+$RunId+".manifest.json")
$launch=Join-Path $PSScriptRoot ("prepare-"+$RunId+"-launch")
$output=Join-Path $PSScriptRoot ("prepare-"+$RunId)
if((Test-Path -LiteralPath $file) -or (Test-Path -LiteralPath $launch) -or (Test-Path -LiteralPath $output)){throw 'Preserve prior evidence; fresh preparation ID required'}
$argv=@('-B',(Join-Path $PSScriptRoot 'prepare_job3_pack.py'),'--final-receipt',$FinalReceipt,'--out',$output,'--launcher-output',$launch,'--threads','1')
$m=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;
 arguments=$argv;working_directory='D:\a10';output_directory=$launch;
 read_paths=@($python,'D:\a10');write_paths=@($launch,$output);
 logical_cpus=@(3);worker_threads=1;minimum_free_mib=51200;required_bytes=200000000}
$m|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $file -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $file
exit $LASTEXITCODE
