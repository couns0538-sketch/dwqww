$ErrorActionPreference='Stop'
if ($PSVersionTable.PSVersion.ToString() -ne '7.5.4') { throw 'Unexpected portable runtime version' }
[ordered]@{
 PSVersionTable=$PSVersionTable
 Framework=[System.Runtime.InteropServices.RuntimeInformation]::FrameworkDescription
 Architecture=[System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString()
 Culture=[System.Globalization.CultureInfo]::GetCultureInfo('en-US').DisplayName
 SHA256=[System.Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData([System.Text.Encoding]::UTF8.GetBytes('forge-portable-runtime')))
 LanguageMode=$ExecutionContext.SessionState.LanguageMode.ToString()
} | ConvertTo-Json -Depth 6 -Compress
