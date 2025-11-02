# 驗證腳本使用指南

## 📋 功能說明

`verify_sales_and_settlements.py` 會計算並驗證：
1. **歷史總售出**：所有 SalesRecord 的總金額（RMB 和 TWD）
2. **歷史總銷帳**：所有 SETTLEMENT LedgerEntry 的總金額
3. **售出扣款 WITHDRAW 記錄**：歷史的售出扣款 WITHDRAW 記錄總額
4. **數據一致性驗證**：檢查所有數據是否一致

## 🖥️ 本地測試（推薦先測試）

### 方法 1：直接執行（使用本地資料庫）

```bash
# 確保在專案根目錄
cd F:\Code_design\Cursor_code\RMB-SALES-SYSTEM

# 執行腳本
python verify_sales_and_settlements.py
```

### 方法 2：使用線上資料庫測試

```bash
# Windows
set DATABASE_URL=postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4
python verify_sales_and_settlements.py

# Linux/Mac
export DATABASE_URL="postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"
python verify_sales_and_settlements.py
```

## 🌐 在 Render Shell 中執行（不需要重新部署）

### 步驟 1：連接到 Render Shell

1. 在 Render Dashboard 中進入您的 Web Service
2. 點擊 "Shell" 按鈕

### 步驟 2：創建腳本文件

在 Render Shell 中執行以下命令創建腳本：

```bash
cd ~/project/src
cat > verify_sales_and_settlements.py << 'ENDOFFILE'
```

然後**複製整個 `verify_sales_and_settlements.py` 文件的內容**貼上，最後輸入：

```
ENDOFFILE
```

### 步驟 3：執行腳本

```bash
python verify_sales_and_settlements.py
```

## 🚀 快速方式：直接複製貼上腳本內容

如果腳本已經在本地，可以：

1. 在 Render Shell 中執行：
```bash
cd ~/project/src
cat > verify_sales_and_settlements.py
```

2. **複製整個 `verify_sales_and_settlements.py` 文件內容**（在本地打開文件，全選複製）

3. **在 Render Shell 中貼上**（右鍵或 Ctrl+V）

4. **按 Enter，然後按 Ctrl+D** 結束輸入

5. 執行：
```bash
python verify_sales_and_settlements.py
```

## 📊 輸出說明

腳本會顯示：

1. **【1】計算歷史總售出**
   - 總售出記錄數
   - 總售出金額 (RMB 和 TWD)
   - 按客戶統計（前10名）

2. **【2】計算歷史總銷帳**
   - 總銷帳記錄數
   - 總銷帳金額 (TWD)
   - 按客戶統計（前10名）

3. **【3】計算應收帳款**
   - 計算的應收帳款 (售出 - 銷帳)
   - 資料庫中的應收帳款總和
   - 差異檢查

4. **【4】統計售出扣款 WITHDRAW 記錄**
   - 售出扣款 WITHDRAW 記錄數
   - 售出扣款 WITHDRAW 總金額
   - 按帳戶統計

5. **【5】數據一致性驗證**
   - 售出扣款 WITHDRAW 與總售出金額的比較

6. **【6】帳戶餘額驗證**
   - 每個 RMB 帳戶的當前餘額
   - 售出扣款 WITHDRAW 金額
   - 理論餘額（回補後）

7. **總結與建議**
   - 所有數據的總結
   - 建議的後續操作

## 💡 常見問題

### Q: 為什麼 Flask 命令不可用？

A: 因為 Flask CLI 命令需要重新部署才能使用。這個獨立腳本可以直接執行，不需要部署。

### Q: 可以在本地測試然後在 Render 執行嗎？

A: 可以！腳本完全獨立，可以在任何環境執行。

### Q: 需要修改資料庫嗎？

A: 不需要。這個腳本只是**讀取和驗證**數據，不會修改任何數據。

### Q: 執行失敗怎麼辦？

A: 檢查：
1. 是否在正確的目錄（專案根目錄）
2. 資料庫連接是否正常
3. 環境變數是否正確設置（如果使用線上資料庫）

## 📝 下一步

執行完驗證後，如果發現問題：

1. **如果有售出扣款 WITHDRAW 記錄**：
   ```bash
   flask cleanup-sales-withdraw --dry-run  # 查看清理方案
   ```

2. **如果應收帳款不一致**：
   ```bash
   flask rebuild-customer-ar  # 重建應收帳款
   ```

3. **如果需要更詳細的分析**：
   可以根據腳本輸出進一步調查問題

