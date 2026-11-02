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
& 'D:\a10\wt\skills\grok-pc-safe-run\scripts\Invoke-GrokPcSafeRun.ps1' -Manifest 'D:\a10\wt\astra_r10\job3\resume\proof02.manifest.json' -ProtectedRoots $protectedRoots
if ($LASTEXITCODE -ne 0) { throw "Resume proof launcher exit $LASTEXITCODE; preserve evidence and inspect before retry" }
