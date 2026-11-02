#requires -Version 5.1
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess(); $self.PriorityClass='Idle'; $self.ProcessorAffinity=[IntPtr]4
$root='D:\a10\wt\astra_r10\job3\regression'
$out=Join-Path $root 'reviewed-draft01'
if(Test-Path -LiteralPath $out){throw 'Do not overwrite reviewed draft'}
$null=New-Item -ItemType Directory -Path $out
$files=@((Join-Path $root 'run_regression.py'),'D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1')
$rows=@()
foreach($file in $files){
 $target=Join-Path $out ([IO.Path]::GetFileName($file))
 Copy-Item -LiteralPath $file -Destination $target
 $rows += [pscustomobject]@{source=$file;target=$target;sha256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash}
}
$rows | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $out 'ARCHIVE.json') -Encoding UTF8
$rows
