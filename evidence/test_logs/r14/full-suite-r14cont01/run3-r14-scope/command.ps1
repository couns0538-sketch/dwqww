# Triage run 3 (independent reviewer): the R14 scope that the R14 runtime can collect - every top-level
# D:\a14\tests\test_*.py (the six inherited a13 files + test_r14_* + test_opus_*) plus tests\r14_native and
# tests\r14_qualification. Excluded: astra_r8\datafilter\tests (needs torch, absent from the R14 runtime),
# tests\data and tests\data2 (module-name collisions with astra_r8\datafilter and R14-runtime-bound subprocess tests).
# Same environment and launcher as ..\command.ps1.
$ErrorActionPreference = 'Continue'
$env:TEMP = 'D:\a14\tmp'
$env:TMP = 'D:\a14\tmp'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$dir = 'D:\a14\evidence\test_logs\r14\full-suite-r14cont01\run3-r14-scope'
$files = @(Get-ChildItem -LiteralPath 'D:\a14\tests' -Filter 'test_*.py' -File | Sort-Object Name | ForEach-Object { $_.FullName })
$files += 'D:\a14\tests\r14_native'
$files += 'D:\a14\tests\r14_qualification'
$files -join "`n" | Set-Content -Path "$dir\selected_files.txt" -Encoding ascii
$start = Get-Date
"start=$($start.ToString('yyyy-MM-dd HH:mm:ss'))" | Set-Content -Path "$dir\timing.txt" -Encoding ascii
$quoted = ($files | ForEach-Object { '"' + $_ + '"' }) -join ' '
cmd /c "D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_lowrun.py --mask 0x4 -- D:\a14\runtime\python\python.exe -I -B -m pytest $quoted -q -p no:cacheprovider --basetemp $dir\tmp > $dir\output.log 2>&1"
$code = $LASTEXITCODE
$end = Get-Date
"end=$($end.ToString('yyyy-MM-dd HH:mm:ss'))" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
"exit=$code" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
"elapsed_s=$([int]($end - $start).TotalSeconds)" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
