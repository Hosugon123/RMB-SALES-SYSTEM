# 簡化版庫存同步檢查腳本（使用已部署的 API）
# 使用方法: .\check_inventory_sync_simple.ps1

param(
    [string]$BaseUrl = "https://rmb-sales-system-test1.onrender.com"
)

# 設置 TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "庫存與帳戶餘額同步檢查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步驟 1: 檢查數據狀態
Write-Host "【步驟 1】檢查數據狀態..." -ForegroundColor Yellow
Write-Host ""

try {
    $statusUrl = "$BaseUrl/api/admin/data-status"
    Write-Host "正在訪問: $statusUrl" -ForegroundColor Gray
    
    $statusResponse = Invoke-RestMethod -Uri $statusUrl -Method Get -ErrorAction Stop
    
    Write-Host "✅ 數據狀態獲取成功！" -ForegroundColor Green
    Write-Host ""
    
    # 顯示庫存狀態
    $inv = $statusResponse.data.inventory
    Write-Host "庫存狀態:" -ForegroundColor Cyan
    Write-Host "  總批次數: $($inv.total_batches)"
    Write-Host "  原始總額: $([math]::Round($inv.total_original, 2)) RMB"
    Write-Host "  已分配總額: $([math]::Round($inv.total_allocated, 2)) RMB"
    Write-Host "  剩餘總額: $([math]::Round($inv.total_remaining, 2)) RMB"
    
    # 計算差異
    $expectedRemaining = $inv.total_original - $inv.total_allocated
    $actualDifference = $inv.total_remaining - $expectedRemaining
    
    Write-Host ""
    Write-Host "庫存一致性分析:" -ForegroundColor Yellow
    Write-Host "  預期剩餘 (原始-已分配): $([math]::Round($expectedRemaining, 2)) RMB"
    Write-Host "  實際剩餘: $([math]::Round($inv.total_remaining, 2)) RMB"
    Write-Host "  差異: $([math]::Round($actualDifference, 2)) RMB"
    
    if ($inv.consistency_check) {
        Write-Host "  狀態: ✅ 一致性檢查通過" -ForegroundColor Green
    } else {
        Write-Host "  狀態: ⚠️  一致性檢查失敗" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "現金帳戶狀態:" -ForegroundColor Cyan
    $cash = $statusResponse.data.cash_accounts
    Write-Host "  TWD帳戶數: $($cash.twd_accounts)"
    Write-Host "  RMB帳戶數: $($cash.rmb_accounts)"
    Write-Host "  TWD總額: $([math]::Round($cash.total_twd, 2)) TWD"
    Write-Host "  RMB總額: $([math]::Round($cash.total_rmb, 2)) RMB"
    
    Write-Host ""
    Write-Host "客戶狀態:" -ForegroundColor Cyan
    $cust = $statusResponse.data.customers
    Write-Host "  總客戶數: $($cust.total_customers)"
    Write-Host "  應收帳款總額: $([math]::Round($cust.total_receivables, 2)) TWD"
    
    # 分析問題
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "問題分析" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $hasIssues = $false
    
    # 檢查庫存一致性
    if (-not $inv.consistency_check) {
        $hasIssues = $true
        Write-Host "⚠️  發現庫存數據不一致！" -ForegroundColor Red
        Write-Host "   差異: $([math]::Round($actualDifference, 2)) RMB" -ForegroundColor Yellow
        Write-Host "   建議: 執行數據修復 API" -ForegroundColor Yellow
    }
    
    # 檢查帳戶餘額與庫存的關係
    # 理論上：RMB帳戶餘額總和應該等於FIFO庫存剩餘總額
    $balanceVsInventory = $cash.total_rmb - $inv.total_remaining
    if ([math]::Abs($balanceVsInventory) -gt 0.01) {
        $hasIssues = $true
        Write-Host "⚠️  帳戶餘額與庫存不匹配！" -ForegroundColor Red
        Write-Host "   RMB帳戶餘額: $([math]::Round($cash.total_rmb, 2)) RMB" -ForegroundColor Yellow
        Write-Host "   FIFO庫存剩餘: $([math]::Round($inv.total_remaining, 2)) RMB" -ForegroundColor Yellow
        Write-Host "   差異: $([math]::Round($balanceVsInventory, 2)) RMB" -ForegroundColor Yellow
        Write-Host "   建議: 執行數據修復 API" -ForegroundColor Yellow
    }
    
    if (-not $hasIssues) {
        Write-Host "✅ 未發現明顯問題" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "修復建議" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    if ($hasIssues) {
        Write-Host ""
        Write-Host "發現數據不一致，建議執行修復：" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "執行以下命令進行修復：" -ForegroundColor Cyan
        Write-Host "  Invoke-RestMethod -Uri `"$BaseUrl/api/admin/data-recovery`" -Method Post" -ForegroundColor White
        Write-Host ""
        Write-Host "或者使用瀏覽器訪問（需要登入）：" -ForegroundColor Cyan
        Write-Host "  $BaseUrl/api/admin/data-recovery" -ForegroundColor White
        Write-Host "  (使用 POST 方法)" -ForegroundColor Gray
    } else {
        Write-Host "數據看起來正常，無需修復" -ForegroundColor Green
    }
    
}
catch {
    Write-Host "❌ 檢查失敗: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "HTTP 狀態碼: $statusCode" -ForegroundColor Red
        
        if ($statusCode -eq 401 -or $statusCode -eq 403) {
            Write-Host ""
            Write-Host "提示: 此 API 需要登入認證" -ForegroundColor Yellow
            Write-Host "      請先在瀏覽器中登入網站，然後獲取 session cookie" -ForegroundColor Yellow
        } elseif ($statusCode -eq 404) {
            Write-Host ""
            Write-Host "提示: API 端點不存在，可能尚未部署" -ForegroundColor Yellow
        }
    }
    exit 1
}

Write-Host ""
Write-Host "檢查完成！" -ForegroundColor Green

