if (-not (Get-Command uv -ErrorAction SilentlyContinue))
{
    Write-Error "The command 'uv' was not found on PATH. Please install it and/or add it to PATH."
    exit 127
}

$CoreDir = Get-Item -Path $PSScriptRoot
Write-Host "Syncing packages for $($CoreDir.Name)" -ForegroundColor Cyan
uv sync --directory $CoreDir.FullName
