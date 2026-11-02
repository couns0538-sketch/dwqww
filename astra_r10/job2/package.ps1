$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]12
$env:TEMP='D:\a10\tmp';$env:TMP=$env:TEMP;$env:PYTHONDONTWRITEBYTECODE='1'
$python='D:\a10\python\python.exe'
$sealer='D:\a10\wt\skills\gate-handover-pack\scripts\seal_evidence.py'
$verifier='D:\a10\wt\astra_r10\job1\packaging\verify_pack.py'
$sources=@((Join-Path $PSScriptRoot 'REPORT.md'),(Join-Path $PSScriptRoot 'recover_inputs.py'),(Join-Path $PSScriptRoot 'recover.ps1'),(Join-Path $PSScriptRoot 'recover-manifest01.json'),$PSCommandPath)
foreach($folder in @('inputs01','recovery','launch-recover01')) {
    $sources+=@(rg --files (Join-Path $PSScriptRoot $folder))
    if($LASTEXITCODE){throw 'Input listing failed'}
}
$artifacts=@($sources | Sort-Object -Unique | ForEach-Object {@{role='original_evidence';path=([IO.Path]::GetFullPath($_).Substring($PSScriptRoot.Length+1).Replace('\','/'));sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $_).Hash.ToLowerInvariant()}})
foreach($line in @('rule50','optimism')) {
    $pack=Join-Path $PSScriptRoot ('pack_'+$line)
    $request=Join-Path $PSScriptRoot ('request_'+$line+'.json')
    if((Test-Path -LiteralPath $pack) -or (Test-Path -LiteralPath $request)){throw 'Fresh pack/request required'}
    @{schema=1;source_root=$PSScriptRoot;artifacts=$artifacts;blockers=@('Required CR129d440e cannot be recovered; no substitute patch applied.','Original PGN hashes and exact fitting inputs unavailable in permitted frozen copies.',('Separate '+$line+' widened-range fit and candidate proof UNVERIFIED; no executable or fitted value delivered.'),'No fresh gate inventory or seed availability proof. P4 also blocked on1e7b5d20/cc826b0a.')} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $request -Encoding UTF8
    foreach($action in @('seal','verify')) {
        $output=Join-Path $PSScriptRoot ('launch-'+$action+'-'+$line)
        $manifest=Join-Path $PSScriptRoot ('manifest-'+$action+'-'+$line+'.json')
        if(Test-Path -LiteralPath $manifest){throw 'Fresh launch manifest required'}
        $arguments=@('-B',$sealer,$request,'--purpose','incomplete-engine','--out',$pack,'--threads','1')
        $writes=@($output,$pack)
        if($action -eq 'verify'){$arguments=@('-B',$verifier,'--pack',$pack,'--threads','1');$writes=@($output)}
        @{schema=1;executable=$python;executable_sha256=(Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash;arguments=$arguments;working_directory='D:\a10';output_directory=$output;read_paths=@($python,'D:\a10\python',$PSScriptRoot,$sealer,$verifier);write_paths=$writes;logical_cpus=@(2);worker_threads=1;minimum_free_mib=51200;required_bytes=10000000} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifest -Encoding UTF8
        & 'D:\a10\wt\astra_r10\launch.ps1' -Manifest $manifest
        if($LASTEXITCODE){throw ('Pack '+$action+' failed for '+$line+'; retain attempt')}
    }
}
