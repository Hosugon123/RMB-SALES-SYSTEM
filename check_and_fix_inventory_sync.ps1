# 庫存與帳戶餘額同步檢查與修復腳本
# 使用方法: .\check_and_fix_inventory_sync.ps1 -BaseUrl "https://您的網站網址" -SessionCookie "您的session cookie"

param(
    [string]$BaseUrl = "https://rmb-sales-system-test1.onrender.com",
    [string]$SessionCookie = ""
)

# 設置 TLS 1.2（Render 需要）
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# 創建會話對象來保持 cookies
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# 如果有提供 session cookie，添加到請求中
if ($SessionCookie) {
    $session.Cookies.SetCookies([Uri]$BaseUrl, $SessionCookie)
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "庫存與帳戶餘額同步檢查與修復工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 步驟 1: 檢查數據狀態
Write-Host "【步驟 1】檢查數據狀態..." -ForegroundColor Yellow
Write-Host ""

try {
    $statusUrl = "$BaseUrl/api/admin/data-status"
    Write-Host "正在訪問: $statusUrl" -ForegroundColor Gray
    
    $statusResponse = Invoke-RestMethod -Uri $statusUrl -Method Get -WebSession $session -ErrorAction Stop
    
    Write-Host "✅ 數據狀態獲取成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "庫存狀態:" -ForegroundColor Cyan
    Write-Host "  總批次數: $($statusResponse.data.inventory.total_batches)"
    Write-Host "  原始總額: $($statusResponse.data.inventory.total_original) RMB"
    Write-Host "  剩餘總額: $($statusResponse.data.inventory.total_remaining) RMB"
    Write-Host "  已分配總額: $($statusResponse.data.inventory.total_allocated) RMB"
    Write-Host "  一致性檢查: $(if ($statusResponse.data.inventory.consistency_check) { '✅ 通過' } else { '❌ 失敗' })"
    Write-Host ""
    Write-Host "現金帳戶狀態:" -ForegroundColor Cyan
    Write-Host "  TWD帳戶數: $($statusResponse.data.cash_accounts.twd_accounts)"
    Write-Host "  RMB帳戶數: $($statusResponse.data.cash_accounts.rmb_accounts)"
    Write-Host "  TWD總額: $($statusResponse.data.cash_accounts.total_twd) TWD"
    Write-Host "  RMB總額: $($statusResponse.data.cash_accounts.total_rmb) RMB"
    Write-Host ""
}
catch {
    Write-Host "❌ 檢查數據狀態失敗: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "響應內容: $responseBody" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "提示: 如果看到 401 或 403 錯誤，您需要先登入網站獲取 session cookie" -ForegroundColor Yellow
    Write-Host "      然後使用 -SessionCookie 參數提供 cookie" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "【步驟 2】執行詳細診斷..." -ForegroundColor Yellow
Write-Host ""

try {
    $diagnosisUrl = "$BaseUrl/api/admin/inventory-diagnosis"
    Write-Host "正在訪問: $diagnosisUrl" -ForegroundColor Gray
    
    $diagnosisResponse = Invoke-RestMethod -Uri $diagnosisUrl -Method Get -WebSession $session -ErrorAction Stop
    
    Write-Host "✅ 診斷完成！" -ForegroundColor Green
    Write-Host ""
    Write-Host "全局摘要:" -ForegroundColor Cyan
    Write-Host "  總買入RMB: $($diagnosisResponse.global_summary.total_purchase_rmb) RMB"
    Write-Host "  總售出RMB: $($diagnosisResponse.global_summary.total_sales_rmb) RMB"
    Write-Host "  正確的全局FIFO: $($diagnosisResponse.global_summary.correct_global_fifo) RMB"
    Write-Host "  實際的全局FIFO: $($diagnosisResponse.global_summary.actual_global_fifo) RMB"
    Write-Host "  帳戶餘額總和: $($diagnosisResponse.global_summary.total_rmb_account_balance) RMB"
    Write-Host ""
    Write-Host "差異分析:" -ForegroundColor Cyan
    Write-Host "  全局差異: $($diagnosisResponse.global_summary.global_difference) RMB"
    Write-Host "  FIFO差異: $($diagnosisResponse.global_summary.fifo_difference) RMB"
    Write-Host "  餘額差異: $($diagnosisResponse.global_summary.balance_difference) RMB"
    Write-Host ""
    
    if ($diagnosisResponse.global_summary.has_issue) {
        Write-Host "⚠️  發現全局數據不一致！" -ForegroundColor Red
    } else {
        Write-Host "✅ 全局數據一致" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "帳戶檢查結果:" -ForegroundColor Cyan
    Write-Host "  總帳戶數: $($diagnosisResponse.summary.total_accounts)"
    Write-Host "  有問題的帳戶數: $($diagnosisResponse.summary.accounts_with_issues)"
    Write-Host ""
    
    if ($diagnosisResponse.account_issues.Count -gt 0) {
        Write-Host "發現問題的帳戶:" -ForegroundColor Yellow
        foreach ($issue in $diagnosisResponse.account_issues) {
            Write-Host "  - $($issue.holder_name)-$($issue.account_name) (ID: $($issue.account_id))" -ForegroundColor Yellow
            Write-Host "    帳戶餘額: $($issue.account_balance) RMB" -ForegroundColor Gray
            Write-Host "    FIFO庫存: $($issue.fifo_inventory) RMB" -ForegroundColor Gray
            Write-Host "    正確FIFO: $($issue.correct_fifo) RMB" -ForegroundColor Gray
            Write-Host "    差異: $($issue.difference) RMB" -ForegroundColor $(if ($issue.difference -gt 0) { "Red" } else { "Yellow" })
            Write-Host ""
        }
    } else {
        Write-Host "✅ 所有帳戶數據一致" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ 診斷失敗: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "響應內容: $responseBody" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "【步驟 3】是否需要執行修復？" -ForegroundColor Yellow
Write-Host ""

if ($diagnosisResponse.global_summary.has_issue -or $diagnosisResponse.summary.accounts_with_issues -gt 0) {
    $fixChoice = Read-Host "發現數據不一致，是否執行自動修復？(y/n)"
    
    if ($fixChoice -eq "y" -or $fixChoice -eq "Y") {
        Write-Host ""
        Write-Host "正在執行修復..." -ForegroundColor Yellow
        
        try {
            $fixUrl = "$BaseUrl/api/admin/data-recovery"
            Write-Host "正在訪問: $fixUrl" -ForegroundColor Gray
            
            $fixResponse = Invoke-RestMethod -Uri $fixUrl -Method Post -WebSession $session -ErrorAction Stop
            
            Write-Host "✅ 修復完成！" -ForegroundColor Green
            Write-Host ""
            Write-Host "修復摘要:" -ForegroundColor Cyan
            Write-Host "  修復的庫存批次: $($fixResponse.summary.inventory_batches_fixed)"
            Write-Host "  修復的現金帳戶: $($fixResponse.summary.cash_accounts_fixed)"
            Write-Host "  修復的客戶: $($fixResponse.summary.customers_fixed)"
            Write-Host ""
            Write-Host "最終狀態:" -ForegroundColor Cyan
            Write-Host "  庫存原始總額: $($fixResponse.final_status.inventory.total_original) RMB"
            Write-Host "  庫存剩餘總額: $($fixResponse.final_status.inventory.total_remaining) RMB"
            Write-Host "  TWD帳戶總額: $($fixResponse.final_status.cash_accounts.total_twd) TWD"
            Write-Host "  RMB帳戶總額: $($fixResponse.final_status.cash_accounts.total_rmb) RMB"
            Write-Host ""
            Write-Host "建議: 請再次執行步驟 2 驗證修復結果" -ForegroundColor Yellow
        }
        catch {
            Write-Host "❌ 修復失敗: $($_.Exception.Message)" -ForegroundColor Red
            if ($_.Exception.Response) {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $responseBody = $reader.ReadToEnd()
                Write-Host "響應內容: $responseBody" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "已取消修復操作" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ 數據一致，無需修復" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "檢查完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

