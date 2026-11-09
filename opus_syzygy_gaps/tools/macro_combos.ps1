# macro_combos.ps1 -Src <tree> - every on/off combination of the three candidate macros must compile (g++ -fsyntax-only, kit flags, -Wall -Wextra listed for the new lines only).
# Exit 0 when all eight compile. Writes one line per combination.
param([Parameter(Mandatory = $true)][string]$Src)
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
$F = '-std=c++20 -O1 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -fsyntax-only'
$bad = 0
Push-Location -LiteralPath $Src
foreach ($a in 0, 1) { foreach ($b in 0, 1) { foreach ($c in 0, 1) {
    $d = "-DFORGE_SYZYGY_TB_BOUNDS=$a -DFORGE_SYZYGY_ROOT_EXACT=$b -DFORGE_SYZYGY_RULE50=$c"
    foreach ($u in 'search', 'uci') {
        $err = Join-Path $JobTmp "combo_$a$b${c}_$u.err"
        cmd /d /c "g++ $F $d src/$u.cpp 2> `"$err`""
        $rc = $LASTEXITCODE
        if ($rc -ne 0) { $bad++; Write-Output "FAIL $a$b$c $u"; Get-Content -LiteralPath $err -TotalCount 6 | ForEach-Object { Write-Output "  $_" } }
        else { Write-Output "ok $a$b$c $u" }
    }
} } }
Pop-Location
Write-Output ("macro_combos " + $(if ($bad -eq 0) { 'ALL COMPILE' } else { "BAD $bad" }))
exit $(if ($bad -eq 0) { 0 } else { 1 })
