#requires -Version 5.1
param([Parameter(Mandatory=$true)][ValidateSet('Seal','Verify')][string]$Mode,
      [Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9]+$')][string]$RunId,
      [string]$SealRequest)
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]8
$python='D:\a10\python\python.exe'
$pack='D:\a10\wt\astra_r10\job3\pack'
$label=$Mode.ToLowerInvariant()+'-'+$RunId
$file=Join-Path $PSScriptRoot ($label+'.manifest.json')
$launch=Join-Path $PSScriptRoot ($label+'-launch')
if((Test-Path -LiteralPath $file) -or (Test-Path -LiteralPath $launch)){throw 'Preserve prior phase evidence'}
if($Mode -eq 'Seal'){
 if([string]::IsNullOrWhiteSpace($SealRequest) -or (Test-Path -LiteralPath $pack)){throw 'Fresh pack and reviewed seal request required'}
 $argv=@('-B','D:\a10\wt\skills\gate-handover-pack\scripts\seal_evidence.py',$SealRequest,'--out',$pack,'--purpose','incomplete-data','--threads','1')
 $writes=@($launch,$pack);$reservation=1000000000
}else{
 if(-not (Test-Path -LiteralPath $pack -PathType Container)){throw 'Existing sealed pack required'}
 $argv=@('-B',(Join-Path $PSScriptRoot 'verify_job3_pack.py'),'--pack',$pack,'--threads','1')
 $writes=@($launch);$reservation=10000000
}
$phaseSpec=@{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;
 arguments=$argv;working_directory='D:\a10';output_directory=$launch;
 read_paths=@($python,'D:\a10');write_paths=$writes;
 logical_cpus=@(3);worker_threads=1;minimum_free_mib=51200;required_bytes=$reservation}
$phaseSpec|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $file -Encoding UTF8
& 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $file
exit $LASTEXITCODE
