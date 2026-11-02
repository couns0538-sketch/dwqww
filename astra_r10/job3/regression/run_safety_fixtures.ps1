#requires -Version 5.1
$ErrorActionPreference='Stop'
$self=[Diagnostics.Process]::GetCurrentProcess();$self.PriorityClass='Idle';$self.ProcessorAffinity=[IntPtr]4
$root='D:\a10\wt\astra_r10\job3\regression'
$launcher='D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1'
if((Get-FileHash -LiteralPath $launcher -Algorithm SHA256).Hash -ne 'A78C49C5134A53493C193E26D848062F9FF7F74B03FC48BCE01E1C32BE49F4D4'){throw 'Reviewed helper changed'}
$out=Join-Path $root 'safety-fixtures01'
if(Test-Path -LiteralPath $out){throw 'Fresh evidence required'}
$null=New-Item -ItemType Directory -Path $out
$env:TEMP=$out;$env:TMP=$out;$env:TMPDIR=$out
$rows=@()
foreach($test in @([pscustomobject]@{name='original19';script=(Join-Path $root 'Test-OriginalSafety.ps1')},[pscustomobject]@{name='readonly';script='D:\a10\wt\skills\grok-pc-safe-run\tests\Test-ReadOnlyRuntime.ps1'})){
 $start=[DateTime]::UtcNow.ToString('o')
 & powershell -NoProfile -File $test.script -Launcher $launcher -Evidence (Join-Path $out $test.name) *> (Join-Path $out ($test.name+'.log'))
 $native=$LASTEXITCODE
 $rows += [pscustomobject]@{name=$test.name;script_sha256=(Get-FileHash -LiteralPath $test.script -Algorithm SHA256).Hash;started=$start;finished=[DateTime]::UtcNow.ToString('o');exit_code=$native}
 if($native -ne 0){break}
}
$report=[ordered]@{status=$(if(@($rows|Where-Object exit_code -ne 0).Count){'FAIL'}else{'PASS'});launcher_sha256=(Get-FileHash -LiteralPath $launcher -Algorithm SHA256).Hash;priority=[string]$self.PriorityClass;affinity=$self.ProcessorAffinity.ToInt64();runs=$rows}
$report|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $out 'RECEIPT.json') -Encoding UTF8
$report|ConvertTo-Json -Depth 6
if($report.status -ne 'PASS'){exit 1}
