# 線上資料庫 WITHDRAW 清理指南

## ⚠️ 重要警告

在執行任何清理操作之前，**務必確認**以下問題：

1. **這些 WITHDRAW 記錄是否真的有實際扣款？**
2. **線上帳戶餘額是否已經正確？**
3. **回補餘額是否會導致帳戶餘額錯誤增加？**

## 背景

線上資料庫找到 330 筆售出扣款 WITHDRAW 記錄，總金額 3,677,897.62 RMB。

### 數據統計

```
帳戶: 0107支付寶 (ID: 27)
  記錄數量: 322 筆
  總扣款金額: 3,429,239.62 RMB

帳戶: 7773支付寶 (ID: 23)
  記錄數量: 5 筆
  總扣款金額: 228,658.00 RMB

帳戶: 6186支付寶 (ID: 31)
  記錄數量: 3 筆
  總扣款金額: 20,000.00 RMB

總記錄數: 330 筆
總扣款金額: 3,677,897.62 RMB
```

## 關鍵問題

### 問題1：LedgerEntry 是否會自動修改帳戶餘額？

**答案：不會**

經過代碼檢查，發現：
- **LedgerEntry 只是流水記錄**，不會自動修改帳戶餘額
- **帳戶餘額的修改發生在具體操作中**（如 FIFO 分配、提款等）

### 問題2：這些 WITHDRAW 記錄是否真的有實際扣款？

**需要確認**

根據當前代碼邏輯（`app.py` 第 989-998 行）：
- 售出流程只在 FIFO 分配時扣款一次
- **不會**創建 WITHDRAW LedgerEntry

這意味著**舊代碼可能有雙重扣款邏輯**，但：
- 如果舊代碼在創建 WITHDRAW 時沒有實際扣款，那麼回補會導致餘額錯誤增加
- 如果舊代碼有實際扣款，那麼回補是正確的

### 問題3：清理邏輯是否正確？

**可能的兩種情況：**

#### 情況A：WITHDRAW 只是顯示記錄（不需要回補）

如果過去的 WITHDRAW LedgerEntry **只是為了流水記錄**，且**沒有實際扣款**，那麼：

**正確做法：**
1. ✅ 直接刪除 WITHDRAW LedgerEntry 記錄
2. ❌ **不要** 回補帳戶餘額

#### 情況B：有雙重扣款（需要回補）

如果過去的代碼確實有雙重扣款邏輯：
1. FIFO 扣款一次
2. WITHDRAW 再扣一次

那麼：
**正確做法：**
1. ✅ 回補帳戶餘額
2. ✅ 刪除 WITHDRAW LedgerEntry 記錄

## 驗證方法

### 步驟1：檢查當前帳戶餘額

在線上資料庫執行查詢：

```sql
-- 檢查這些帳戶的當前餘額
SELECT id, name, balance, currency 
FROM cash_accounts 
WHERE id IN (27, 23, 31);
```

### 步驟2：根據交易記錄計算正確餘額

檢查是否有其他操作影響餘額：

```sql
-- 查看這些帳戶的所有交易記錄
SELECT 
    le.entry_type,
    le.description,
    le.amount,
    le.entry_date
FROM ledger_entries le
WHERE le.account_id IN (27, 23, 31)
ORDER BY le.entry_date DESC
LIMIT 100;
```

### 步驟3：對比分析

比較：
1. 帳戶當前餘額
2. 根據所有交易記錄計算的餘額
3. 如果清理後的預期餘額（當前餘額 + 回補金額）

如果帳戶當前餘額**已經正確**（與根據交易記錄計算的餘額一致），那麼**不應該回補**。

## 建議操作

### 方案A：安全方案（推薦）

**只刪除記錄，不回補餘額**

1. 確認這些 WITHDRAW 記錄只是重複的流水記錄
2. 修改清理腳本，去掉回補邏輯
3. 只執行刪除操作

### 方案B：完整方案（謹慎使用）

**回補餘額 + 刪除記錄**

1. 確認這些 WITHDRAW 記錄確實造成了餘額錯誤
2. 先備份資料庫
3. 執行完整的清理腳本（包含回補）

## 修改後的清理腳本（只刪除）

如果需要**只刪除**記錄，修改 `app.py` 的清理命令：

```python
@app.cli.command("cleanup-sales-withdraw")
@click.option('--dry-run', is_flag=True, help='僅分析，不實際執行清理')
@click.option('--no-reimbursement', is_flag=True, help='不回補餘額，只刪除記錄')
def cleanup_sales_withdraw_command(dry_run, no_reimbursement):
    """清理歷史售出扣款的 WITHDRAW LedgerEntry 記錄"""
    
    # ... 統計代碼 ...
    
    if not no_reimbursement:
        # 回補帳戶餘額
        for account_id, stats in account_stats.items():
            account = stats['account']
            if account:
                old_balance = account.balance
                account.balance += stats['total_amount']
                new_balance = account.balance
                print(f"\n✅ 帳戶 {account.name}: 回補 {stats['total_amount']:.2f} RMB")
                print(f"   餘額變化: {old_balance:.2f} -> {new_balance:.2f}")
    else:
        print("\n⚠️  跳過餘額回補（只刪除記錄）")
    
    # 刪除所有 WITHDRAW 記錄
    for record in withdraw_records:
        db.session.delete(record)
    
    db.session.commit()
    print(f"\n✅ 清理完成！")
```

執行時使用 `--no-reimbursement` 參數：

```bash
flask cleanup-sales-withdraw --no-reimbursement
```

## 最終建議

**在執行清理之前：**

1. ✅ 檢查線上帳戶實際餘額
2. ✅ 根據交易記錄計算預期餘額
3. ✅ 確認是否真的有餘額錯誤
4. ✅ 備份資料庫
5. ✅ 先使用 `--dry-run` 模式查看效果

**如果不確定：**
- 建議先**只刪除記錄**（使用 `--no-reimbursement` 參數）
- 觀察餘額是否正確
- 如果有問題，再考慮回補

## 相關文件

- `CRITICAL_ISSUE_ANALYSIS.md`：關鍵問題分析
- `WITHDRAW_CLEANUP_SUMMARY.md`：本地清理總結
- `app.py`：清理命令代碼（第 2318-2401 行）

