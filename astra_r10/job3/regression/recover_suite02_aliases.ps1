#requires -Version 5.1
# Bounded recovery from owned pytest aliases rejected by the normal launcher.
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]4
$r10ProtectedRoots=@('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
$helper='D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1'
if((Get-FileHash -LiteralPath $helper -Algorithm SHA256).Hash -ne '17205767AE3EA35A5CCB5A7965BC4988BAE26B4F2260C821411A657C9979C787'){throw 'Reviewed helper changed'}
. $helper
$base='D:\a10\job3\regression-runs\suite02\pytest-temp'
$out='D:\a10\wt\astra_r10\job3\regression\suite02-alias-recovery'
$null=Assert-R10WritePath $base $r10ProtectedRoots
$null=Assert-R10WritePath $out $r10ProtectedRoots
if(Test-Path -LiteralPath $out){throw 'Fresh recovery evidence required'}
if([IO.DriveInfo]::new('C:\').AvailableFreeSpace -lt 30GB -or [IO.DriveInfo]::new('D:\').AvailableFreeSpace -lt 50GB){throw 'Disk floor'}
$null=New-Item -ItemType Directory -Path $out
$env:TEMP=$out;$env:TMP=$out;$env:TMPDIR=$out
function Assert-OwnChild([string]$Path){
 $lexical=[IO.Path]::GetFullPath($Path)
 if(-not $lexical.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Alias/target escaped exact suite02 pytest-temp lexical boundary'}
 return $lexical
}
function Target-Hashes([string]$Target){
 $pending=New-Object 'System.Collections.Generic.Stack[System.IO.DirectoryInfo]'
 $pending.Push([IO.DirectoryInfo]::new($Target));$rows=New-Object System.Collections.Generic.List[object]
 while($pending.Count){
  $dir=$pending.Pop()
  if($dir.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Nested reparse target refused'}
  foreach($entry in $dir.EnumerateFileSystemInfos()){
   $null=Assert-OwnChild $entry.FullName
   if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Nested reparse target refused'}
   if($entry -is [IO.DirectoryInfo]){$pending.Push($entry)}else{$rows.Add([pscustomobject]@{path=$entry.FullName;bytes=$entry.Length;sha256=(Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash})}
  }
 }
 return @($rows.ToArray()|Sort-Object path)
}
$aliases=@(Get-ChildItem -LiteralPath $base -Force|Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint})
if($aliases.Count -ne 29){throw 'Expected exact29 owned pytest convenience aliases; inspect before recovery'}
$inventory=@()
foreach($alias in $aliases){
 $link=Assert-OwnChild $alias.FullName
 if([IO.Path]::GetDirectoryName($link) -ne $base -or $alias.Name -notlike '*current' -or $alias.LinkType -ne 'SymbolicLink' -or @($alias.Target).Count -ne 1){throw 'Not an expected direct owned pytest alias'}
 $target=Assert-OwnChild ([string](@($alias.Target)[0]))
 $null=Assert-DPath $target $r10ProtectedRoots
 $resolved=(Resolve-Path -LiteralPath $target -ErrorAction Stop).ProviderPath
 $null=Assert-OwnChild $resolved
 if(-not (Get-Item -LiteralPath $resolved -Force).PSIsContainer){throw 'Alias target must be real directory'}
 $inventory += [pscustomobject]@{link=$link;type=$alias.LinkType;target=$target;resolved_target=$resolved;files=@(Target-Hashes $resolved)}
}
$scope=[ordered]@{scope='Exact29 owned pytest convenience aliases only; normal launcher workspace guard is obstructed by these reparse points. No guard relaxation, no target deletion, no recursive delete.';helper_sha256=(Get-FileHash -LiteralPath $helper -Algorithm SHA256).Hash;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash;start_utc=[DateTime]::UtcNow.ToString('o');priority=[string]$self.PriorityClass;affinity=$self.ProcessorAffinity.ToInt64();protected_roots=$r10ProtectedRoots;links=$inventory}
$scope|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'BEFORE.json') -Encoding UTF8
$removed=@()
foreach($item in $inventory){
 $current=Get-Item -LiteralPath $item.link -Force
 if($current.LinkType -ne 'SymbolicLink' -or @($current.Target).Count -ne 1 -or [string](@($current.Target)[0]) -ne $item.target){throw 'Alias changed after inventory'}
 $null=Assert-OwnChild $current.FullName
 # The DirectoryInfo was acquired with -LiteralPath and revalidated above.
 # Parameterless Delete is nonrecursive and unlinks only this directory symlink.
 # Avoid PowerShell5.1 Remove-Item's historical directory-symlink behavior.
 $current.Delete()
 $removed += $item.link
 $removed|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $out 'REMOVED.json') -Encoding UTF8
 if(Test-Path -LiteralPath $item.link){throw 'Alias still exists'}
}
foreach($item in $inventory){
 $after=@(Target-Hashes $item.resolved_target)
 if(($after|ConvertTo-Json -Depth 5 -Compress) -cne ($item.files|ConvertTo-Json -Depth 5 -Compress)){throw 'Target bytes or file set changed during alias removal'}
}
$workspaceBytes=Get-R10WorkspaceBytes
Assert-R10StorageBudget -CFreeBytes ([IO.DriveInfo]::new('C:\').AvailableFreeSpace) -DFreeBytes ([IO.DriveInfo]::new('D:\').AvailableFreeSpace) -WorkspaceBytes $workspaceBytes -RequiredBytes 0 -MinimumMiB 51200
[ordered]@{status='PASS';removed_aliases=$removed.Count;all_target_files_and_hashes_unchanged=$true;workspace_bytes=$workspaceBytes;finished_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $out 'AFTER.json') -Encoding UTF8
Get-Content -LiteralPath (Join-Path $out 'AFTER.json')
