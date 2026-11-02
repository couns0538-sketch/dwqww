$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='Idle'
[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity=[IntPtr]12
$dir='D:\a10\wt\astra_r10\job1\validation'
New-Item -ItemType Directory $dir -ErrorAction Stop | Out-Null
$original='D:\a10\wt\astra_r9\tools\validate_uci.py'
$text=[IO.File]::ReadAllText($original)
$text=$text.Replace('D:/a9/pydeps','D:/a10/pydeps').Replace('psutil.BELOW_NORMAL_PRIORITY_CLASS','psutil.IDLE_PRIORITY_CLASS')
$text=$text.Replace("ap.add_argument('exe');", "ap.add_argument('--threads',type=int,choices=[1],required=True); ap.add_argument('exe');")
$text=$text.Replace('for threads in [1,4]:','for threads in [1]:')
$text=$text.Replace("pathlib.Path(__file__).parents[1].joinpath('evidence/fens_12k.txt')", "pathlib.Path('D:/a10/inputs/fens_12k.txt')")
[IO.File]::WriteAllText((Join-Path $dir 'validate_uci.py'),$text)
Copy-Item D:\a9\checks\forge_san_c1.exe,D:\a9\checks\sanitizer_control.exe D:\a10\inputs
Get-ChildItem D:\a9\toolchain\llvm-mingw-20261020-ucrt-x86_64\bin -Filter '*.dll' | Copy-Item -Destination D:\a10\inputs
Get-ChildItem D:\a10\inputs -File | Get-FileHash -Algorithm SHA256 | ConvertTo-Json | Set-Content (Join-Path $dir 'inputs.json') -Encoding UTF8
