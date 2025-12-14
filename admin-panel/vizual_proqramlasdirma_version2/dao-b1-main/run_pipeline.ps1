# E2E Pipeline Orchestration Script for Sprint 2
# Starts Hardhat node, deploys contract, runs indexer and backfill

param(
    [string]$HardhatLocalPath = "c:\Users\Qurban\OneDrive\Desktop\dao-b1-main\dao-b1-main\hardhat_local",
    [string]$ProjectRoot = "c:\Users\Qurban\OneDrive\Desktop\dao-b1-main\dao-b1-main",
    [int]$MetricsPort = 8003,
    [string]$RpcUrl = "http://127.0.0.1:8545"
)

Write-Host "=== Sprint 2 E2E Pipeline Orchestration ===" -ForegroundColor Green

# Function to wait for RPC to be ready
function Wait-ForRpc {
    param([string]$Url, [int]$TimeoutSeconds = 30)
    $start = Get-Date
    Write-Host "Waiting for RPC at $Url to be ready..." -ForegroundColor Cyan
    while ((Get-Date) - $start -lt [TimeSpan]::FromSeconds($TimeoutSeconds)) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method POST -Body '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' -ContentType 'application/json' -ErrorAction Stop
            Write-Host "RPC is ready!" -ForegroundColor Green
            return $true
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    Write-Host "RPC did not become ready within $TimeoutSeconds seconds" -ForegroundColor Red
    return $false
}

# Step 1: Clean DB (optional)
Write-Host "`n[Step 1] Optionally resetting database..." -ForegroundColor Yellow
$dbPath = Join-Path $ProjectRoot "db.sqlite3"
if (Test-Path $dbPath) {
    Write-Host "Removing existing db.sqlite3..." -ForegroundColor Cyan
    Remove-Item -Path $dbPath -Force
}

# Step 2: Seed database
Write-Host "`n[Step 2] Seeding database..." -ForegroundColor Yellow
Push-Location $ProjectRoot
python backend\seed_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Seed failed! Exiting." -ForegroundColor Red
    exit 1
}
Pop-Location
Write-Host "Seed completed successfully." -ForegroundColor Green

# Step 3: Start Hardhat node in background
Write-Host "`n[Step 3] Starting Hardhat node..." -ForegroundColor Yellow
Push-Location $HardhatLocalPath
$nodeProcess = Start-Process -FilePath "npx" -ArgumentList "hardhat", "node" -PassThru -NoNewWindow
Write-Host "Hardhat node process started (PID: $($nodeProcess.Id))" -ForegroundColor Cyan
Pop-Location

# Step 4: Wait for RPC to be ready
if (-not (Wait-ForRpc $RpcUrl)) {
    Write-Host "RPC failed to start. Killing node process..." -ForegroundColor Red
    Stop-Process -Id $nodeProcess.Id -Force
    exit 1
}

# Step 5: Deploy contract to localhost
Write-Host "`n[Step 4] Deploying contract to localhost network..." -ForegroundColor Yellow
Push-Location $HardhatLocalPath
$deployOutput = & .\node_modules\.bin\hardhat run scripts/deploy.js --network localhost 2>&1
Write-Host $deployOutput
$contractAddress = $deployOutput | Select-String "deployed to: (0x[a-fA-F0-9]{40})" | ForEach-Object { $_.Matches[0].Groups[1].Value }
if (-not $contractAddress) {
    Write-Host "Failed to extract contract address from deploy output!" -ForegroundColor Red
    Write-Host "Deploy output was:" -ForegroundColor Yellow
    Write-Host $deployOutput
    Stop-Process -Id $nodeProcess.Id -Force
    exit 1
}
Write-Host "Contract deployed to: $contractAddress" -ForegroundColor Green
Pop-Location

# Step 6: Start indexer
Write-Host "`n[Step 5] Starting indexer..." -ForegroundColor Yellow
$abiPath = Join-Path $ProjectRoot "artifacts\MilestoneFunding.abi.json"
Push-Location (Join-Path $ProjectRoot "indexer")
Write-Host "Running indexer with contract address: $contractAddress" -ForegroundColor Cyan
$indexerProcess = Start-Process -FilePath "python" -ArgumentList "indexer.py", "--rpc-url", $RpcUrl, "--contract-address", $contractAddress, "--abi-path", $abiPath, "--metrics-port", $MetricsPort -PassThru -NoNewWindow
Write-Host "Indexer started (PID: $($indexerProcess.Id))" -ForegroundColor Green
Pop-Location

# Step 7: Run backfill to import historical logs
Write-Host "`n[Step 6] Running backfill to import historical logs..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Push-Location (Join-Path $ProjectRoot "indexer")
Write-Host "Running backfill..." -ForegroundColor Cyan
& python backfill.py --rpc-url $RpcUrl --contract-address $contractAddress --abi-path $abiPath --from-block 0 --to-block latest --metrics-port $MetricsPort
Pop-Location

# Summary
Write-Host "`n=== Pipeline Summary ===" -ForegroundColor Green
Write-Host "Database seeded" -ForegroundColor Green
Write-Host "Hardhat node running (PID: $($nodeProcess.Id))" -ForegroundColor Green
Write-Host "Contract deployed to: $contractAddress" -ForegroundColor Green
Write-Host "Indexer running (PID: $($indexerProcess.Id))" -ForegroundColor Green
Write-Host "Backfill completed" -ForegroundColor Green
Write-Host "`nPrometheus metrics available at: http://127.0.0.1:$MetricsPort/metrics" -ForegroundColor Cyan
Write-Host "`nTo view database tables, run: python backend/db_inspect.py" -ForegroundColor Yellow
Write-Host "`nPress Ctrl+C to stop all processes." -ForegroundColor Yellow

# Keep script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
        if ($nodeProcess.HasExited) {
            Write-Host "Hardhat node has exited!" -ForegroundColor Red
        }
        if ($indexerProcess.HasExited) {
            Write-Host "Indexer has exited!" -ForegroundColor Red
        }
    }
} finally {
    Write-Host "`nCleaning up processes..." -ForegroundColor Yellow
    if ($indexerProcess -and -not $indexerProcess.HasExited) {
        Stop-Process -Id $indexerProcess.Id -Force
    }
    if ($nodeProcess -and -not $nodeProcess.HasExited) {
        Stop-Process -Id $nodeProcess.Id -Force
    }
    Write-Host "All processes stopped." -ForegroundColor Green
}
