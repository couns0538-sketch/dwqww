$ErrorActionPreference = 'Stop'
$proofProc = [System.Diagnostics.Process]::GetCurrentProcess()
$proofProc.PriorityClass = 'Idle'
$proofProc.ProcessorAffinity = [IntPtr]8
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONNOUSERSITE = '1'
$env:CUDA_VISIBLE_DEVICES = ''
$env:HIP_VISIBLE_DEVICES = ''
$env:ROCR_VISIBLE_DEVICES = ''
$protectedRoots = @('D:\forge_nnue_train','D:\forge_nnue_train_old','D:\forge_j1_data','D:\forge_j1_data_astra','D:\forge_push\locks','D:\grok-pc-data\forge_push\locks','D:\grok-pc-data\forge_push\nnue_data','D:\grok-pc-data\forge_push\nnue_cand','D:\grok-pc-data\npt','D:\grok-pc-data\nnue','D:\grok-pc-data\r11_nnue','D:\grok-pc-data\lichess','D:\syzygy','D:\syzygy345','C:\Users\Administrator\grok-pc\forge_push','C:\o13','F:\')
$archivedLauncher = 'D:\a10\wt\astra_r10\job3\regression\launcher_before_readonly\Invoke-GrokPcSafeRun.ps1'
$launcherSha = '842D6520058EB9F5C14D7426CA3BAD92F080AFB5F5684F1C43AB1A56FE38C21D'
if ((Get-FileHash -LiteralPath $archivedLauncher -Algorithm SHA256).Hash -ne $launcherSha) { throw 'Archived reviewed launcher changed' }
$manifestPath = 'D:\a10\wt\astra_r10\job3\resume\proof03.manifest.json'
$bindingPath = 'D:\a10\wt\astra_r10\job3\resume\proof03-launcher-binding.json'
if (Test-Path -LiteralPath $bindingPath) { throw 'Refusing existing launcher binding receipt' }
$binding = [ordered]@{command_start_utc=[DateTime]::UtcNow.ToString('o');archived_launcher=$archivedLauncher;sha256=$launcherSha;manifest=$manifestPath;manifest_sha256=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash;wrapper=$PSCommandPath;wrapper_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash}
[IO.File]::WriteAllText($bindingPath, ($binding | ConvertTo-Json -Depth 4), (New-Object System.Text.UTF8Encoding($false)))
& $archivedLauncher -Manifest $manifestPath -ProtectedRoots $protectedRoots
if ($LASTEXITCODE -ne 0) { throw "Resume proof launcher exit $LASTEXITCODE; preserve evidence and inspect before retry" }
if ((Get-FileHash -LiteralPath $archivedLauncher -Algorithm SHA256).Hash -ne $launcherSha) { throw 'Archived reviewed launcher changed during proof' }
