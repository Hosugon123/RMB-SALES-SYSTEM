# 線上資料庫售出扣款 WITHDRAW 清理指南

## 🎯 適用於線上資料庫（Render PostgreSQL）

本指南說明如何在線上資料庫上安全地執行清理操作。

## 使用方式

### 方法1：使用 Flask CLI 命令（推薦）

#### 1.1 查看分析結果（Dry Run）
```bash
flask cleanup-sales-withdraw --dry-run
```
- ✅ 只分析數據，不實際修改
- ✅ 顯示統計資訊和回補計劃
- ✅ 完全安全，可多次執行

**示例輸出：**
```
🔍 開始分析歷史售出扣款 WITHDRAW 記錄... (DRY RUN（僅分析）)

找到 10 筆售出扣款 WITHDRAW 記錄

統計資訊：
--------------------------------------------------------------------------------
帳戶: 測試用 (ID: 6)
  記錄數量: 3 筆
  總扣款金額: 7000.00 RMB
--------------------------------------------------------------------------------
總記錄數: 10 筆
總扣款金額: 17310.00 RMB

✅ DRY RUN 模式：僅顯示分析結果，不實際執行清理
```

#### 1.2 執行實際清理（需要確認）
```bash
flask cleanup-sales-withdraw
```
- ⚠️  會修改資料庫
- ✅ 執行前會要求確認（輸入 `yes` 繼續）

#### 1.3 執行實際清理（跳過確認）
```bash
flask cleanup-sales-withdraw --force
```
- ⚠️  會修改資料庫，不詢問確認
- ⚠️  適合自動化腳本使用
- ✅ 請確保已備份資料庫

### 方法2：通過 Render Shell 執行

#### 2.1 連接到 Render Shell
```bash
# 在 Render Dashboard 中進入您的 Web Service
# 點擊 "Shell" 按鈕
```

#### 2.2 在 Shell 中執行命令
```bash
# 先分析（Dry Run）
flask cleanup-sales-withdraw --dry-run

# 執行清理（需要確認）
flask cleanup-sales-withdraw

# 或直接執行（跳過確認）
flask cleanup-sales-withdraw --force
```

### 方法3：通過 Render 的 Environment Variables

如果 `flask` 命令不可用，可以直接設置環境變數並執行 Python：

```bash
# 在 Render Shell 中
export FLASK_APP=app.py

# 執行命令
python -m flask cleanup-sales-withdraw --dry-run
python -m flask cleanup-sales-withdraw
python -m flask cleanup-sales-withdraw --force
```

## ⚠️  重要注意事項

### 執行前準備

1. **備份資料庫**（強烈建議）
   ```bash
   # Render 提供自動備份功能，建議先手動創建一個備份點
   ```

2. **檢查數據**
   - 先執行 `--dry-run` 查看影響範圍
   - 確認統計資訊合理
   - 檢查帳戶餘額變化是否符合預期

3. **選擇合適時間**
   - 建議在低峰時段執行
   - 確保沒有其他用戶正在操作系統

### 執行後驗證

1. **驗證帳戶餘額**
   ```sql
   -- 在 Render PostgreSQL Console 中檢查
   SELECT id, name, balance, currency 
   FROM cash_accounts 
   WHERE currency = 'RMB' 
   ORDER BY id;
   ```

2. **確認記錄已刪除**
   ```bash
   flask cleanup-sales-withdraw --dry-run
   # 應該顯示 "找到 0 筆售出扣款 WITHDRAW 記錄"
   ```

3. **檢查流水頁面**
   - 登入系統
   - 訪問現金管理頁面
   - 確認不再顯示重複的「售出扣款」記錄

## 📊 預期結果

### 清理前
- 每筆售出顯示兩條記錄：WITHDRAW "售出扣款" + "售出"
- 餘額變化可能顯示錯誤

### 清理後
- ✅ 每筆售出只顯示一條記錄："售出"
- ✅ 餘額變化正確顯示
- ✅ 帳戶餘額已回補
- ✅ 流水顯示清晰

## 🔍 故障排除

### 問題1：SSL 連接錯誤
```
connection to server at "35.227.164.209", port 5432 failed: SSL connection has been closed unexpectedly
```

**解決方案：**
- 這是臨時網絡問題
- 等待幾分鐘後重試
- 或通過 Render Shell 執行（連接更穩定）

### 問題2：命令不存在
```
flask: command not found
```

**解決方案：**
```bash
# 使用完整路徑
python -m flask cleanup-sales-withdraw --dry-run

# 或確保 flask 已安裝
pip install flask flask-cli
```

### 問題3：權限錯誤
```
Permission denied
```

**解決方案：**
- 確認您有資料庫寫入權限
- 檢查環境變數中的 DATABASE_URL
- 聯繫 Render 支援

## 📝 清理範例

### 範例1：本地資料庫清理（已完成）

```bash
# 本地已成功清理
找到 10 筆售出扣款 WITHDRAW 記錄
帳戶 測試用: 回補 7000.00 RMB
  餘額變化: 42000.00 -> 49000.00
✅ 清理完成！
  刪除記錄: 10 筆
  回補餘額: 17310.00 RMB
```

### 範例2：線上資料庫清理（待執行）

```bash
# 在 Render Shell 中執行
$ flask cleanup-sales-withdraw --dry-run

# 根據輸出結果決定是否執行清理
$ flask cleanup-sales-withdraw
# 輸入 yes 確認
```

## 🎉 完成檢查清單

- [ ] 執行 `--dry-run` 檢查數據
- [ ] 創建資料庫備份
- [ ] 確認統計資訊合理
- [ ] 執行清理命令
- [ ] 驗證帳戶餘額
- [ ] 確認記錄已刪除
- [ ] 檢查流水頁面顯示
- [ ] 通知團隊修復已完成

## 📞 需要幫助？

如果遇到問題，請：
1. 查看 `WITHDRAW_CLEANUP_SUMMARY.md` 了解詳細修復內容
2. 查看 `FIX_EXPLANATION.md` 了解修復邏輯
3. 檢查 Render 的日誌輸出
4. 聯繫開發團隊

