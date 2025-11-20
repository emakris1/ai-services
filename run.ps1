param
(
    [ValidateSet("pwsh","powershell")]
    [string]$Shell
)

$RunParams = @{}
if ($Shell)
{
    $RunParams['Shell'] = $Shell
}

& $PSScriptRoot\services\uv-run-services.ps1 @RunParams
& $PSScriptRoot\ui\run-ui.ps1
