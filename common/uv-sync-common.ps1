if (-not (Get-Command uv -ErrorAction SilentlyContinue))
{
    Write-Error "The command 'uv' was not found on PATH. Please install it and/or add it to PATH."
    exit 127
}

$PackageDir = Get-Item -Path $PSScriptRoot
Write-Host "Syncing packages for $($PackageDir.Name)" -ForegroundColor Cyan
# ai-rmq is a non-editable path dependency, so force a reinstall to pick up any source changes made to it
uv sync --directory $PackageDir.FullName --reinstall-package ai-rmq
