# Render Shell 執行分析腳本指南

## 📋 執行步驟

### 第 1 步：連接到 Render Shell

1. 登入 [Render Dashboard](https://dashboard.render.com)
2. 選擇您的 Web Service（rmb-sales-system）
3. 點擊 "Shell" 按鈕

### 第 2 步：拉取最新代碼

在 Render Shell 中執行：

```bash
cd ~/project/src
git pull
```

這會從 GitHub 拉取最新代碼，包括 `analyze_withdraw_accounts.py` 腳本。

### 第 3 步：執行分析腳本

```bash
python analyze_withdraw_accounts.py
```

---

## 🔍 腳本會分析什麼？

此腳本會詳細分析：

1. **WITHDRAW 記錄的歷史**
   - 最早和最晚的記錄時間
   - 記錄的總數和總額

2. **三個支付寶帳戶的詳細比較**
   - 0107 支付寶
   - 7773 支付寶  
   - 6186 支付寶

3. **每個帳戶的數據**
   - 當前餘額
   - WITHDRAW 總額
   - 銷售總額
   - 理論餘額（回補後）
   - 數據差異分析

4. **0107 支付寶問題診斷**
   - 找出金額不對的根本原因
   - 檢查是否有從其他帳戶扣款的情況
   - 驗證 WITHDRAW 記錄的帳戶ID分佈

---

## 📊 預期輸出

腳本會顯示類似以下的輸出：

```
================================================================================
分析售出扣款 WITHDRAW 記錄的歷史和計算邏輯
================================================================================

【1】查找所有售出扣款 WITHDRAW 記錄
找到 XXXX 筆售出扣款 WITHDRAW 記錄

【2】按帳戶分析售出扣款 WITHDRAW 記錄
找到目標帳戶：
  0107: 0107支付寶 (ID: 27)
  7773: 7773支付寶 (ID: 23)
  6186: 6186支付寶 (ID: 31)

【3】詳細分析三個支付寶帳戶
...

【4】交叉比對三個帳戶的算式
...

【5】0107 支付寶異常分析
...

【6】WITHDRAW 記錄的計算邏輯說明
...

【7】0107 支付寶問題診斷
...
```

---

## ⚠️ 如果遇到問題

### 問題 1：Git pull 失敗
```bash
# 檢查 Git 狀態
git status

# 如果有衝突，先暫存更改
git stash
git pull
git stash pop
```

### 問題 2：腳本執行失敗（導入錯誤）
```bash
# 確保在正確的目錄
cd ~/project/src
pwd

# 檢查文件是否存在
ls -la analyze_withdraw_accounts.py

# 檢查 Python 環境
python --version
which python
```

### 問題 3：數據庫連接錯誤
腳本使用 Render 環境變數 `DATABASE_URL`，如果連接失敗：
```bash
# 檢查環境變數
echo $DATABASE_URL

# 如果沒有設置，需要設置正確的資料庫 URL
```

---

## 📝 執行完成後

執行完成後，腳本會輸出詳細的分析報告，包括：

- ✅ 三個帳戶的數據對比表
- ✅ 0107 支付寶問題的根本原因
- ✅ WITHDRAW 記錄的計算邏輯說明
- ✅ 建議的後續操作

請將輸出結果保存或截圖，以便後續分析和處理。

---

## 🚀 快速執行命令（一鍵複製）

```bash
cd ~/project/src && git pull && python analyze_withdraw_accounts.py
```

直接在 Render Shell 中貼上執行即可！

