param
(
    [switch]$DeleteAceCache
)

if ($DeleteAceCache)
{
    $CachePath = "$env:LOCALAPPDATA\cgt_ace"
    $CacheDir = Get-Item -Path $CachePath -ErrorAction SilentlyContinue
    if ($CacheDir)
    {
        Write-Host "Deleting CGT ACE cache at $CacheDir" -ForegroundColor Yellow
        Remove-Item -Recurse -Force -Path $CacheDir -ErrorAction SilentlyContinue
    }
    else
    {
        Write-Host "No CGT ACE cache to delete at $CachePath" -ForegroundColor Yellow
    }
}

& $PSScriptRoot\core\uv-sync-core.ps1
& $PSScriptRoot\services\uv-sync-services.ps1
& $PSScriptRoot\ui\flutter-build-ui.ps1
