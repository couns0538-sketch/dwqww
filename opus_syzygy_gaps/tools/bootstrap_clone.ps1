# Step 0: independent blobless clone from GitHub, baseline exe hash. Exits by itself.
Set-Location 'D:\'
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$logDir = Join-Path $JobOut 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir 'bootstrap.log'
function L($s) { Add-Content -Path $log -Value $s; Write-Output $s }
L ('start ' + (Get-ViennaNow) + ' ' + (Get-JobPinLine))
$exe = 'C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe'
$want = '4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0'
$h = (Get-FileHash -Algorithm SHA256 -Path $exe).Hash
L ("baseline_sha256 $h match=" + ($h -eq $want))
if (-not (Test-Path (Join-Path $JobRepo '.git'))) {
    cmd /c "git clone --filter=blob:none --no-checkout https://github.com/couns0538-sketch/dwqww `"$JobRepo`" > `"$logDir\clone.log`" 2>&1"
    L "clone_exit $LASTEXITCODE"
} else { L 'clone_exists' }
Set-Location $JobRepo
L ('repo ' + (Get-Location).Path)
L ('p6_tip ' + (git rev-parse origin/opus-r13-p6-syzygy))
L ('main_tip ' + (git rev-parse origin/main))
L ('branches ' + ((git branch -r | Measure-Object).Count))
L ('end ' + (Get-ViennaNow))
