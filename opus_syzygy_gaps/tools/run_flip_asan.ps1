# run_flip_asan.ps1 -Tag <san tag> - tb_root under MSVC ASan with exact-size heap copies on every damaged table folder (out\tb\flip_NN, rejected, nodtz, nochild, dtzonly).
# Body damage may give wrong values: this run asks only that the reader neither crashes nor reads out of range. Output: out\san\<tag>\flips\SUMMARY.txt
param([Parameter(Mandatory = $true)][string]$Tag)
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$dir = Join-Path $JobOut "san\$Tag"
$runs = Join-Path $dir 'flips'
New-Item -ItemType Directory -Force -Path $runs | Out-Null
$sum = Join-Path $runs 'SUMMARY.txt'
Add-Content -Path $sum -Value ('start ' + (Get-ViennaNow) + ' ' + (Get-JobPinLine))
foreach ($l in Get-Content (Join-Path $dir 'vcenv.txt')) { $i = $l.IndexOf('='); if ($i -gt 0) { Set-Item -Path ('env:' + $l.Substring(0, $i)) -Value $l.Substring($i + 1) } }
$env:TEMP = $JobTmp; $env:TMP = $JobTmp
$env:ASAN_OPTIONS = 'halt_on_error=1:detect_leaks=0'
$env:TB_HEAP = '1'
$fen = Join-Path $JobOut 'exp\partial\mix.fens'
$opt = 'SyzygyRootExact=3'
$bad = 0; $n = 0
foreach ($d in Get-ChildItem (Join-Path $JobOut 'tb') -Directory | Where-Object { $_.Name -like 'flip_*' -or $_.Name -in 'rejected', 'nodtz', 'nochild', 'dtzonly' }) {
    cmd /d /c "`"$dir\tb_root_asan.exe`" `"$($d.FullName)`" `"$fen`" 1 $opt > `"$runs\$($d.Name).out`" 2> `"$runs\$($d.Name).err`""
    $rc = $LASTEXITCODE
    $n++
    if ($rc -ne 0) { $bad++ }
    Add-Content -Path $sum -Value ("$($d.Name) exit $rc " + (Get-Content "$runs\$($d.Name).err" -TotalCount 1))
}
Add-Content -Path $sum -Value ("runs $n non-zero $bad end " + (Get-ViennaNow))
Write-Output "runs $n non-zero $bad"
