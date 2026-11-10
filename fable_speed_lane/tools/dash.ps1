# dash.ps1 - one screen of where this job's runs stand (read-only; PowerShell 5.1 or 7, ASCII only).
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File dash.ps1 [-Since 15:00]
param([string]$Since = '00:00')
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess(); $me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]0x70
Write-Output ((NowVienna) + '  D: free ' + (DFree) + ' GiB')
$mine = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*forge_jobs_20261109\fable2*' -or $_.ExecutablePath -like 'D:\forge_jobs_20261109\fable2*' })
$bad = 0
foreach ($w in $mine) { $p = Get-Process -Id $w.ProcessId -ErrorAction SilentlyContinue; if ($p -and (([int64]$p.ProcessorAffinity -band (-bnot 0x78)) -ne 0 -or "$($p.PriorityClass)" -ne 'Idle')) { $bad++ } }
$cold = @($mine | Where-Object { $_.CommandLine -match 'spd_uci\.py"? cold' }).Count
$abba = @($mine | Where-Object { $_.CommandLine -match 'spd_uci\.py"? abba|pos_cycles\.py' }).Count
Write-Output ("processes of this job: {0} ({1} cold runs, {2} timing runs); outside CPU 3-6 or not Idle: {3}" -f $mine.Count, $cold, $abba, $bad)
Write-Output '--- identity lines'
Get-ChildItem (Join-Path $OUT 'id') -Directory | ForEach-Object {
    $q = Join-Path $_.FullName 'QUALIFY.log'
    if (Test-Path $q) { Get-Content $q | Where-Object { $_ -match '\[2026-11-1\d (\d\d:\d\d)' -and $Matches[1] -ge $Since } | ForEach-Object { $_.Substring(0, [Math]::Min(150, $_.Length)) } }
}
Write-Output '--- cold rows in progress (rows written so far)'
Get-ChildItem (Join-Path $OUT 'id') -Recurse -Filter '*.tsv.part' -ErrorAction SilentlyContinue | ForEach-Object { '{0}\{1}: {2}' -f $_.Directory.Name, $_.Name, @(Get-Content $_.FullName).Count }
Write-Output '--- timing'
Get-Content (Join-Path $OUT 'logs\timing2.log') | Where-Object { $_ -match 'by CPU cycles|^\[[^\]]+\] (start|FAILED|HOLD|GAVE)' -and $_ -match '\[2026-11-1\d (\d\d:\d\d)' -and $Matches[1] -ge $Since } | ForEach-Object { $_.Substring(0, [Math]::Min(170, $_.Length)) }
Get-ChildItem (Join-Path $OUT 'id') -Recurse -Filter 'abbarc_*.txt' | Where-Object { -not (Select-String -Path $_.FullName -Pattern 'ABBA INDICATIVE' -Quiet) } | ForEach-Object { '{0}\{1}: {2} blocks so far' -f $_.Directory.Name, $_.Name, @(Select-String -Path $_.FullName -Pattern 'ABBA block').Count }
Get-ChildItem (Join-Path $OUT 'regime') -Recurse -Filter 'pos_*.txt' -ErrorAction SilentlyContinue | ForEach-Object { $b = @(Select-String -Path $_.FullName -Pattern '^block \d+').Count; $f = @(Select-String -Path $_.FullName -Pattern 'POS_CYCLES BLOCKS').Line; '{0}\{1}: {2} blocks {3}' -f $_.Directory.Name, $_.Name, $b, ($f -join ' ') }
Write-Output '--- mutants'
foreach ($l in 'MUTANTS.log', 'MUTANTS_BUNDLE4.log', 'MUTANTS_BUNDLE3.log', 'MUTANTS_BUNDLE.log') {
    $p = Join-Path $OUT "id\mutants\$l"
    if (Test-Path $p) { $x = @(Get-Content $p); '{0}: {1} caught, {2} missed or error, {3} controls clean, {4} not clean{5}' -f $l, @($x | Where-Object { $_ -match '^MUTANT .*: CAUGHT;' }).Count, @($x | Where-Object { $_ -match '^MUTANT .*: (MISSED|ERROR)' }).Count, @($x | Where-Object { $_ -match '^CONTROL .*: clean;' }).Count, @($x | Where-Object { $_ -match 'NOT CLEAN' }).Count, $(if ($x | Where-Object { $_ -match '^SUMMARY' }) { '; SUMMARY written' } else { '' }) }
}
Write-Output '--- chain / runners (last lines)'
foreach ($f in 'chain.log', 'cold_singles.log') { $t = Get-Content (Join-Path $OUT "logs\$f") -Tail 1; Write-Output ($f + ': ' + $t.Substring(0, [Math]::Min(150, $t.Length))) }
