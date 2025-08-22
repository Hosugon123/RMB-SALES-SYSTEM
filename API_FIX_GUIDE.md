# 🔧 數據修復 API 問題修復指南

## 🚨 問題描述

您的數據修復工具遇到了以下問題：
1. **"Unexpected token '<'" 錯誤** - 後端返回了 HTML 錯誤頁面而不是 JSON
2. **500 內部服務器錯誤** - 後端 API 執行時出現了異常

## 🔍 問題分析

基於錯誤信息和代碼分析，問題可能出現在：

1. **數據庫查詢錯誤** - 某些表或字段不存在
2. **模型關係問題** - 外鍵關聯有問題
3. **數據庫事務問題** - 提交或回滾失敗
4. **權限驗證問題** - 缺少必要的權限檢查

## 🛠️ 解決方案

### 方法 1：使用修復版本的代碼

我已經創建了 `app_fixed.py` 文件，包含了修復版本的數據修復 API。請：

1. **備份您的數據**（重要！）
2. **替換 `app.py` 中的 `remote_data_recovery` 函數**
3. **重新部署應用程序**

### 方法 2：手動修復

如果您想手動修復，請在 `app.py` 中找到 `remote_data_recovery` 函數（大約在第 6114 行），並將其替換為修復版本。

### 方法 3：使用簡化版本

如果問題仍然存在，可以嘗試使用更簡化的修復邏輯：

```python
@app.route("/api/admin/data-recovery", methods=["POST"])
def remote_data_recovery():
    """簡化版數據修復 API"""
    try:
        print("🔧 開始簡化數據修復...")
        
        # 只修復庫存數據
        inventories = FIFOInventory.query.all()
        inventory_fixes = []
        
        for inventory in inventories:
            try:
                # 簡單的修復邏輯
                old_remaining = inventory.remaining_rmb
                inventory.remaining_rmb = inventory.rmb_amount * 0.8  # 示例：設置為原始數量的 80%
                
                inventory_fixes.append({
                    "batch_id": inventory.id,
                    "original": inventory.rmb_amount,
                    "old_remaining": old_remaining,
                    "new_remaining": inventory.remaining_rmb
                })
            except Exception as e:
                print(f"處理庫存 {inventory.id} 時出錯: {e}")
                continue
        
        # 提交更改
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "簡化修復完成",
            "fixed_count": len(inventory_fixes)
        })
        
    except Exception as e:
        print(f"修復失敗: {e}")
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
```

## 📋 修復步驟

### 步驟 1：備份數據
```bash
# 在 Render 上執行備份
python backup_before_recovery.py
```

### 步驟 2：更新代碼
1. 將修復版本的代碼複製到 `app.py`
2. 或者使用 `app_fixed.py` 中的代碼

### 步驟 3：重新部署
1. 提交代碼更改
2. 推送到 Git 倉庫
3. Render 會自動重新部署

### 步驟 4：測試修復
1. 訪問 `/admin_data_recovery` 頁面
2. 檢查數據狀態
3. 嘗試執行數據修復

## 🔍 調試建議

### 1. 檢查日誌
在 Render 控制台中查看應用程序日誌，尋找具體的錯誤信息。

### 2. 逐步測試
先測試數據狀態 API (`/api/admin/data-status`)，再測試修復 API。

### 3. 檢查數據庫
確保所有必要的表和字段都存在。

### 4. 權限檢查
確保 API 端點有適當的權限驗證。

## 📞 如果問題持續

如果修復後問題仍然存在，請：

1. **檢查 Render 日誌** - 查看具體的錯誤信息
2. **提供錯誤日誌** - 分享完整的錯誤堆疊信息
3. **檢查數據庫結構** - 確認表結構是否正確

## 🎯 預期結果

修復成功後，您應該能夠：

1. ✅ 正常訪問數據修復管理頁面
2. ✅ 查看當前數據狀態
3. ✅ 執行數據修復操作
4. ✅ 下載修復報告

---

**重要提醒**：在執行任何修復操作之前，請務必備份您的數據！
