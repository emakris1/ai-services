param
(
    [ValidateSet("pwsh","powershell")]
    [string]$Shell
)

$splatParams = @{}
if ($Shell)
{
    $splatParams['Shell'] = $Shell
}

& $PSScriptRoot\services\uv-run-services.ps1 @splatParams
& $PSScriptRoot\ui\run-ui.ps1
