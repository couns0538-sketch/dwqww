#requires -Version 5.1
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]4
$root='D:\a10\wt\astra_r10\job3\regression'
$out=Join-Path $root 'reviewed-runner2383'
if(Test-Path -LiteralPath $out){throw 'No source archive overwrite'}
$null=New-Item -ItemType Directory -Path $out
$bound=Get-Content -LiteralPath (Join-Path $root 'suite02-inputs.json') -Raw|ConvertFrom-Json
$rows=@()
foreach($item in $bound){
 if((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash -ne $item.sha256){throw ('Original input changed before archival: '+$item.path)}
 $target=Join-Path $out ([IO.Path]::GetFileName($item.path))
 Copy-Item -LiteralPath $item.path -Destination $target -ErrorAction Stop
 $sha=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
 if($sha -ne $item.sha256){throw 'Archive copy identity mismatch'}
 $rows += [pscustomobject]@{source=$item.path;archive=$target;sha256=$sha}
}
[ordered]@{scope='exact suite02 inputs before historical NumPy runtime alignment and pytest convenience-alias suppression';utc=[DateTime]::UtcNow.ToString('o');files=$rows}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $out 'ARCHIVE.json') -Encoding UTF8
$rows|Select-Object source,sha256
