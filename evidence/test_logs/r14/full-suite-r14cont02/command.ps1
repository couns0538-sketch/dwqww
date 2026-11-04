# Final R14-scope suite run at the tip (R14 finish; owner's fix list item 3): the same scope as
# full-suite-r14cont01\run3-r14-scope (every top-level D:\a14\tests\test_*.py plus tests\r14_native and
# tests\r14_qualification), launched through opus_lowrun.py --mask 0x2 (CPU 1, Idle priority, GPU hidden) once CPUs 0-1
# carry no kit-build / engine process; the first line of output.log is `git rev-parse HEAD` of the tree the suite ran on,
# then stdout+stderr of pytest merged by cmd.exe (raw bytes). command.txt holds the exact expanded command line;
# selected_files.txt the path list; timing.txt / exit.txt the clock and exit code.
$ErrorActionPreference = 'Continue'
$env:TEMP = 'D:\a14\tmp'
$env:TMP = 'D:\a14\tmp'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$dir = 'D:\a14\evidence\test_logs\r14\full-suite-r14cont02'
$files = @(Get-ChildItem -LiteralPath 'D:\a14\tests' -Filter 'test_*.py' -File | Sort-Object Name | ForEach-Object { $_.FullName })
$files += 'D:\a14\tests\r14_native'
$files += 'D:\a14\tests\r14_qualification'
$files -join "`n" | Set-Content -Path "$dir\selected_files.txt" -Encoding ascii
$quoted = ($files | ForEach-Object { '"' + $_ + '"' }) -join ' '
$command = "D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_lowrun.py --mask 0x2 -- D:\a14\runtime\python\python.exe -I -B -m pytest $quoted -q -p no:cacheprovider --basetemp $dir\tmp"
$sha = (git -C D:/a14 rev-parse HEAD).Trim()
@(
  "Environment: TEMP=TMP=D:\a14\tmp, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1; launcher = Idle on CPU 1 (mask 0x2), GPU hidden.",
  "Tree: git rev-parse HEAD = $sha (also the first line of output.log).",
  "Command (stdout+stderr merged into $dir\output.log by cmd.exe, appended after the HEAD line):",
  $command
) -join "`n" | Set-Content -Path "$dir\command.txt" -Encoding ascii
$start = Get-Date
"start=$($start.ToString('yyyy-MM-dd HH:mm:ss'))" | Set-Content -Path "$dir\timing.txt" -Encoding ascii
[IO.File]::WriteAllText("$dir\output.log", $sha + "`n")
cmd /c "$command >> $dir\output.log 2>&1"
$code = $LASTEXITCODE
$end = Get-Date
"end=$($end.ToString('yyyy-MM-dd HH:mm:ss'))" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
"exit=$code" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
"elapsed_s=$([int]($end - $start).TotalSeconds)" | Add-Content -Path "$dir\timing.txt" -Encoding ascii
"exit=$code" | Set-Content -Path "$dir\exit.txt" -Encoding ascii
