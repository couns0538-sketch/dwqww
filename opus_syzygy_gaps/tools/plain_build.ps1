# plain_build.ps1 - plain -O3 build of a Forge tree, the R13 P6 plain flags token for token, plus --no-insert-timestamp
# so two builds compare byte for byte. Idle on CPUs 12-15. Refuses to overwrite an existing exe.
# usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File plain_build.ps1 -Src <tree> -Exe <out.exe> [-Defines 'A=1,B=1'] [-Extra '<flags>'] [-NoExpose]
param(
    [Parameter(Mandatory = $true)][string]$Src,
    [Parameter(Mandatory = $true)][string]$Exe,
    [string]$Defines = '',
    [string]$Extra = '',
    [string]$Units = 'bitboard,board,book,eval,eval_params,nnue,search,uci',
    [string]$MoreSources = '',
    [string]$Inc = '',
    [switch]$NoExpose
)
. 'D:\forge_jobs_20261107\opus1\env.ps1'
if (Test-Path -LiteralPath $Exe) { Write-Output "refusing: $Exe exists"; exit 2 }
$dir = Split-Path -Parent $Exe
if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
$flags = '-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread'
if (-not $NoExpose) { $flags += ' -DFORGE_EXPOSE_TUNABLES=1' }
foreach ($d in ($Defines -split ',')) { if ($d) { $flags += " -D$d" } }
if ($Extra) { $flags += " $Extra" }
foreach ($d in ($Inc -split ',')) { if ($d) { $flags += " -I$d" } }
$sources = (($Units -split ',') | ForEach-Object { "src/$_.cpp" }) -join ' '
if ($MoreSources) { $sources = "$MoreSources $sources" }
$log = $Exe + '.build.log'
$line = "g++ $flags -Iinclude $sources -Wl,--no-insert-timestamp -o `"$Exe`""
Set-Content -Path $log -Value ("# " + (Get-ViennaNow) + " " + (Get-JobPinLine) + " src=$Src`n# $line")
Set-Location -LiteralPath $Src
$rsp = Join-Path $dir ((Split-Path -Leaf $Exe) + '.cmd.txt')
Set-Content -Path $rsp -Value $line -Encoding ASCII
cmd /d /c "$line >> `"$log`" 2>&1"
$rc = $LASTEXITCODE
if ($rc -ne 0) { Write-Output "build FAILED exit $rc; see $log"; exit $rc }
$h = (Get-FileHash -Algorithm SHA256 -LiteralPath $Exe).Hash
Add-Content -Path $log -Value ("# done " + (Get-ViennaNow) + " sha256 $h")
Write-Output "built $Exe sha256 $h"
