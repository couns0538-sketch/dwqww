# run_baseline.ps1 - first checks of the P6 parent (plain build): C1's own suite and the pins. Exits by itself.
param([string]$Exe = 'D:\forge_jobs_20261107\opus1\out\exe\p6_plain.exe', [string]$Tag = 'p6_plain')
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$out = Join-Path $JobOut "base\$Tag"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$py = 'C:\Python315\python.exe'
$tools = Join-Path $JobRepo 'opus_syzygy_gaps\tools'
$pins = Join-Path $tools 'pins.py'
Set-Content -Path "$out\RUN.txt" -Value ('start ' + (Get-ViennaNow) + ' ' + (Get-JobPinLine) + " exe $Exe")
$c1 = Join-Path $JobOut 'exe\p6_c1tests.exe'
if ($Tag -eq 'p6_plain') {
    $s = Start-Process -FilePath 'cmd.exe' -ArgumentList "/d /c `"`"$c1`" D:\forge_jobs_20261107\opus1\out\src\p6_c1tests\syzygy_fixtures.tsv D:\forge_jobs_20261107\opus1\out\src\p6_c1tests\syzygy_reference.tsv D:\syzygy345 > `"$out\c1_full.out`" 2>&1`"" -PassThru -NoNewWindow
    $t = Start-Process -FilePath 'cmd.exe' -ArgumentList "/d /c `"`"$c1`" D:\forge_jobs_20261107\opus1\out\src\p6_c1tests\syzygy_fixtures.tsv D:\forge_jobs_20261107\opus1\out\src\p6_c1tests\syzygy_reference.tsv D:\forge_jobs_20261107\opus1\out\tb\man34 > `"$out\c1_man34.out`" 2>&1`"" -PassThru -NoNewWindow
}
$a = Start-Process -FilePath 'cmd.exe' -ArgumentList "/d /c `"`"$py`" -I -B `"$pins`" `"$Exe`" `"$out\pins_off.json`" --expect lock > `"$out\pins_off.out`" 2>&1`"" -PassThru -NoNewWindow
$b = Start-Process -FilePath 'cmd.exe' -ArgumentList "/d /c `"`"$py`" -I -B `"$pins`" `"$Exe`" `"$out\pins_tb.json`" --expect p6path --tables D:\syzygy345 --no-net-off > `"$out\pins_tb.out`" 2>&1`"" -PassThru -NoNewWindow
foreach ($p in @($s, $t, $a, $b)) { if ($p) { $p.WaitForExit() } }
Add-Content -Path "$out\RUN.txt" -Value ('end ' + (Get-ViennaNow))
