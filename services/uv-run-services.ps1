if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "The 'uv' command was not found on PATH. Please install it or add it to PATH."
    exit 127
}

$WtArgs = @()

# List service folder names you want to skip
$ExcludedServices = @("test_services")

# Get all directories, then filter out excluded ones
$Services = Get-ChildItem -Path $PSScriptRoot -Directory | Where-Object { 
    $ExcludedServices -notcontains $_.Name 
}

foreach ($Service in $Services) {
    $ServicePath = $Service.FullName
    Write-Host "Preparing tab for $($Service.Name)" -ForegroundColor Cyan

    $TabArgs = @(
        "new-tab",
        "--title", $Service.Name,
        "--startingDirectory", $ServicePath,
        "powershell",
        "-NoExit",
        "-Command",
        "uv run $($Service.Name).py;"
    )

    $WtArgs += $TabArgs
}

Start-Process wt -ArgumentList $WtArgs
