$ErrorActionPreference='Stop'
foreach ($path in $args) {
    $tokens=$null; $errors=$null
    $null=[System.Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
    if ($errors.Count -ne 0) { $errors | Format-List | Out-String | Write-Output; exit 1 }
    "PASS AST: $path"
}
'Linux PowerShell 7 parser only; Windows 5.1 behavior is UNVERIFIED.'
