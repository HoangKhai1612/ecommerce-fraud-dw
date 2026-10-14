
$ErrorActionPreference = "Continue"

$ProjectRoot = "C:\Users\Administrator\Documents\ecommerce-fraud-dw"
$EvidenceDir = Join-Path $ProjectRoot "evidence\phase_26"
$LogFile = Join-Path $EvidenceDir "environment_report.txt"

New-Item -ItemType Directory -Path $EvidenceDir -Force |
    Out-Null

"PHASE 26 ENVIRONMENT DIAGNOSTICS" |
    Set-Content -Path $LogFile -Encoding utf8

"Timestamp: $(Get-Date -Format o)" |
    Add-Content -Path $LogFile -Encoding utf8

"Computer: $env:COMPUTERNAME" |
    Add-Content -Path $LogFile -Encoding utf8

"`n--- Docker Compose services ---" |
    Add-Content -Path $LogFile -Encoding utf8

Push-Location $ProjectRoot
try {
    docker compose ps 2>&1 |
        Out-String |
        Add-Content -Path $LogFile -Encoding utf8
}
finally {
    Pop-Location
}

"`n--- Port checks ---" |
    Add-Content -Path $LogFile -Encoding utf8

foreach ($Port in @(5432, 8000, 3000, 8080, 11434)) {
    $Listeners = @(
        Get-NetTCPConnection `
            -LocalPort $Port `
            -State Listen `
            -ErrorAction SilentlyContinue
    )

    if ($Listeners.Count -gt 0) {
        "PORT $Port : LISTENING" |
            Add-Content -Path $LogFile -Encoding utf8

        $Listeners |
            Select-Object LocalAddress, LocalPort, OwningProcess |
            Format-Table -AutoSize |
            Out-String |
            Add-Content -Path $LogFile -Encoding utf8
    }
    else {
        "PORT $Port : NO LISTENER FOUND" |
            Add-Content -Path $LogFile -Encoding utf8
    }
}

"`n--- Required project files ---" |
    Add-Content -Path $LogFile -Encoding utf8

$RequiredPaths = @(
    ".env",
    "dbt\dbt_project.yml",
    "ml\models\xgboost.pkl",
    "ml\models\feature_columns.json"
)

foreach ($RelativePath in $RequiredPaths) {
    $FullPath = Join-Path $ProjectRoot $RelativePath

    if (Test-Path $FullPath) {
        "PASS: $RelativePath" |
            Add-Content -Path $LogFile -Encoding utf8
    }
    else {
        "WARN: $RelativePath not found" |
            Add-Content -Path $LogFile -Encoding utf8
    }
}

"`n--- Docker disk usage ---" |
    Add-Content -Path $LogFile -Encoding utf8

docker system df 2>&1 |
    Out-String |
    Add-Content -Path $LogFile -Encoding utf8

Write-Host "Diagnostics completed."
Write-Host "Report: $LogFile"
