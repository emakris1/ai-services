param
(
    [switch]$DeleteAceCache
)

if ($DeleteAceCache)
{
    $CachePath = "$env:LOCALAPPDATA\ace"
    $CacheDir = Get-Item -Path $CachePath -ErrorAction SilentlyContinue
    if ($CacheDir)
    {
        Write-Host "Deleting ACE cache at $CacheDir" -ForegroundColor Yellow
        Remove-Item -Recurse -Force -Path $CacheDir -ErrorAction SilentlyContinue
    }
    else
    {
        Write-Host "No ACE cache to delete at $CachePath" -ForegroundColor Yellow
    }
}

& $PSScriptRoot\core\uv-sync-core.ps1
& $PSScriptRoot\services\uv-sync-services.ps1
& $PSScriptRoot\ui\flutter-build-ui.ps1
