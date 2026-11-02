# Small evidence-only bundle. Never qualifies data, training, or native tests.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidatePattern('^r11-blocked[0-9]+$')][string]$Tag)
$ErrorActionPreference='Stop'
$repo='D:\a11\wt'
$helper="$repo\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1"
function Owned([string]$Path) {
    . $helper
    $full=Assert-DPath $Path @('D:\a10','F:\')
    if(-not $full.StartsWith('D:\a11\',[StringComparison]::OrdinalIgnoreCase)){throw 'Outside owned root'}
    return $full
}
function Files([string]$Root) {
    $pending=[Collections.Generic.Stack[string]]::new();$pending.Push((Owned $Root))
    while($pending.Count){
        $directory=Owned $pending.Pop()
        foreach($item in Get-ChildItem -LiteralPath $directory -Force){
            $checked=Owned $item.FullName
            if($item.PSIsContainer){$pending.Push($checked)}else{$checked}
        }
    }
}
function Digest([string]$Path,[string]$Algorithm){(Get-FileHash -LiteralPath (Owned $Path) -Algorithm $Algorithm).Hash.ToLowerInvariant()}
function Write-New([string]$Path,[string]$Text){
    $checked=Owned $Path
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes($Text)
    $stream=[IO.File]::Open($checked,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
$out=Owned "D:\a11\handoff\$Tag"
if(Test-Path -LiteralPath $out){throw 'Fresh bundle directory required'}
if([IO.DriveInfo]::new('C:\').AvailableFreeSpace -lt 30GB -or [IO.DriveInfo]::new('D:\').AvailableFreeSpace -lt (50GB+100MB)){throw 'Storage floor/reservation'}
$paths=@(Files "$repo\astra_r11")
$paths+=@("$repo\AGENTS.md","$repo\skills\gate-handover-pack\SKILL.md","$repo\skills\grok-pc-safe-run\SKILL.md",$helper,"$repo\skills\grok-pc-safe-run\references\launcher-contract.md","$repo\skills\grok-pc-safe-run\tests\Test-R11Paths.ps1","$repo\skills\npt-data-holdout-check\SKILL.md")
$paths=@($paths|Sort-Object -Unique)
$inventory=@();$total=0L
foreach($path in $paths){
    $checked=Owned $path
    if(-not $checked.StartsWith($repo+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Source outside worktree'}
    $relative=$checked.Substring($repo.Length+1).Replace('\','/')
    if($relative -match '(?i)\.nnue$|(^|/)(STOP|PAUSE|forge_queue_state\.json)$'){throw 'Forbidden artifact'}
    $size=(Get-Item -LiteralPath $checked).Length;$total+=$size
    if($total -gt 90MB -or $inventory.Count -ge 10000){throw 'Evidence bundle exceeds source budget; 10MB reserved for metadata'}
    $inventory+=[ordered]@{path=$relative;bytes=$size;sha256=(Digest $checked 'SHA256')}
}
$tip=(& git -C $repo rev-parse HEAD).Trim()
if($LASTEXITCODE -ne 0){throw 'Git identity failed'}
$dirty=@(& git -C $repo status --porcelain)
if($LASTEXITCODE -ne 0 -or $dirty.Count){throw 'Commit the reviewed evidence before sealing'}
[IO.Directory]::CreateDirectory((Owned (Split-Path -Parent $out)))|Out-Null
New-Item -ItemType Directory -Path (Owned $out) -ErrorAction Stop|Out-Null
foreach($entry in $inventory){
    $source=Owned (Join-Path $repo $entry.path);$target=Owned (Join-Path $out $entry.path)
    [IO.Directory]::CreateDirectory((Owned (Split-Path -Parent $target)))|Out-Null
    if(Test-Path -LiteralPath $target){throw 'Unexpected target exists'}
    $input=[IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try {
        $output=[IO.File]::Open((Owned $target),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
        try{$input.CopyTo($output);$output.Flush($true)}finally{$output.Dispose()}
    }finally{$input.Dispose()}
    if((Digest $target 'SHA256') -cne $entry.sha256 -or (Digest $source 'SHA256') -cne $entry.sha256){throw 'Source/copy drift'}
}
$status=[ordered]@{schema=1;status='SEALED_BLOCKED_EVIDENCE';classification='UNPROVEN';source_commit=$tip;data_pack_qualified=$false;training_clearance='BLOCKED';authentic_mappings_recovered=0;population_rows_inherited_r10=17388528;filtered_train_rows_inherited_r10=999953;holdout_rows_inherited_r10=16388575;traceable_rows_established=0;row_trace_scan='UNRUN';untraceable_rows_measured=$null;train_games=$null;holdout_games=$null;game_overlap=$null;current_full_input_hashes='UNRUN';original_73_tests='UNRUN';new_python_fixtures='UNRUN';note='Counts inherited from R10. No new data pack or overlap proof. Checksum verification certifies evidence bytes only.'}
Write-New "$out\PACK_STATUS.json" (($status|ConvertTo-Json -Depth 8)+"`n")
Write-New "$out\ARTIFACTS.json" (([ordered]@{source_commit=$tip;files=$inventory}|ConvertTo-Json -Depth 8)+"`n")
$payload=@(Files $out|Sort-Object)
foreach($algorithm in @('MD5','SHA256')){
    $lines=@(foreach($path in $payload){(Digest $path $algorithm)+'  '+$path.Substring($out.Length+1).Replace('\','/')})
    Write-New "$out\${algorithm}SUMS" (($lines -join "`n")+"`n")
}
$expected=@(@($inventory.path)+@('PACK_STATUS.json','ARTIFACTS.json','MD5SUMS','SHA256SUMS')|Sort-Object)
$actual=@(Files $out|ForEach-Object{$_.Substring($out.Length+1).Replace('\','/')}|Sort-Object)
if(($expected -join "`n") -cne ($actual -join "`n")){throw 'Unexpected final artifact census; preserve failed output'}
$finalBytes=0L;foreach($path in Files $out){$finalBytes+=(Get-Item -LiteralPath $path).Length}
if($finalBytes -gt 100MB -or [IO.DriveInfo]::new('C:\').AvailableFreeSpace -lt 30GB -or [IO.DriveInfo]::new('D:\').AvailableFreeSpace -lt 50GB){throw 'Final size/storage check failed; preserve output'}
Write-Output $out
Write-Output 'Created evidence bundle only. Independently verify both manifests and exact census before reporting sealed bytes.'
