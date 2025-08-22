# Render 部署和數據修復指南

## 🚀 在 Render 上部署數據修復工具

### 方法 1：網頁界面修復（推薦）

#### 步驟 1：上傳修復文件
1. 將以下文件上傳到您的 Render 項目：
   - `remote_data_fix_api.py`
   - `templates/admin_data_recovery.html`

2. 或者直接在 Render 的 Web Editor 中創建這些文件

#### 步驟 2：修改主應用
在您的 `app.py` 中添加以下代碼：

```python
# 在文件頂部添加導入
from flask import jsonify
from sqlalchemy import func, and_
import traceback
from datetime import datetime

# 在現有路由後添加修復 API
@app.route("/api/admin/data-recovery", methods=["POST"])
def remote_data_recovery():
    """遠程數據修復 API 端點"""
    try:
        # 這裡可以添加權限檢查
        # if not current_user.is_authenticated or not current_user.is_admin:
        #     return jsonify({"status": "error", "message": "權限不足"}), 403
        
        print("🔧 開始遠程數據修復...")
        
        # 1. 修復庫存數據
        print("📦 修復庫存數據...")
        inventories = FIFOInventory.query.filter_by(is_active=True).all()
        
        inventory_fixes = []
        for inventory in inventories:
            # 計算實際的已出帳數量
            actual_issued = SalesRecord.query.filter(
                and_(
                    SalesRecord.inventory_batch_id == inventory.id,
                    SalesRecord.is_active == True
                )
            ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
            
            # 更新庫存記錄
            old_issued = inventory.issued_rmb
            old_remaining = inventory.remaining_rmb
            
            inventory.issued_rmb = actual_issued
            inventory.remaining_rmb = inventory.original_rmb - actual_issued
            
            # 如果剩餘數量為0，標記為已出清
            if inventory.remaining_rmb <= 0:
                inventory.is_active = False
            
            inventory_fixes.append({
                "batch_id": inventory.id,
                "original": inventory.original_rmb,
                "old_issued": old_issued,
                "new_issued": actual_issued,
                "old_remaining": old_remaining,
                "new_remaining": inventory.remaining_rmb,
                "is_active": inventory.is_active
            })
        
        # 2. 修復現金帳戶餘額
        print("💰 修復現金帳戶餘額...")
        cash_accounts = CashAccount.query.filter_by(is_active=True).all()
        
        account_fixes = []
        for account in cash_accounts:
            old_balance = account.balance
            
            if account.currency == "TWD":
                # TWD 帳戶餘額計算
                payment_amount = PurchaseRecord.query.filter(
                    and_(
                        PurchaseRecord.payment_account_id == account.id,
                        PurchaseRecord.is_active == True
                    )
                ).with_entities(func.sum(PurchaseRecord.twd_cost)).scalar() or 0
                
                ledger_debits = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.account_id == account.id,
                        LedgerEntry.entry_type.in_(['WITHDRAW', 'TRANSFER_OUT', 'CARD_PURCHASE']),
                        LedgerEntry.is_active == True
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                ledger_credits = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.account_id == account.id,
                        LedgerEntry.entry_type.in_(['DEPOSIT', 'TRANSFER_IN', 'SETTLEMENT']),
                        LedgerEntry.is_active == True
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                cash_debits = CashLog.query.filter(
                    and_(
                        CashLog.account_id == account.id,
                        CashLog.type.in_(['WITHDRAWAL', 'CARD_PURCHASE']),
                        CashLog.is_active == True
                    )
                ).with_entities(func.sum(CashLog.amount)).scalar() or 0
                
                cash_credits = CashLog.query.filter(
                    and_(
                        CashLog.account_id == account.id,
                        CashLog.type.in_(['DEPOSIT', 'SETTLEMENT']),
                        CashLog.is_active == True
                    )
                ).with_entities(func.sum(CashLog.amount)).scalar() or 0
                
                new_balance = (account.initial_balance or 0) - payment_amount - ledger_debits - cash_debits + ledger_credits + cash_credits
                
            elif account.currency == "RMB":
                # RMB 帳戶餘額計算
                deposit_amount = PurchaseRecord.query.filter(
                    and_(
                        PurchaseRecord.deposit_account_id == account.id,
                        PurchaseRecord.is_active == True
                    )
                ).with_entities(func.sum(PurchaseRecord.rmb_amount)).scalar() or 0
                
                sales_amount = SalesRecord.query.filter(
                    and_(
                        SalesRecord.rmb_account_id == account.id,
                        SalesRecord.is_active == True
                    )
                ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                
                ledger_debits = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.account_id == account.id,
                        LedgerEntry.entry_type.in_(['WITHDRAW', 'TRANSFER_OUT']),
                        LedgerEntry.is_active == True
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                ledger_credits = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.account_id == account.id,
                        LedgerEntry.entry_type.in_(['DEPOSIT', 'TRANSFER_IN']),
                        LedgerEntry.is_active == True
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                new_balance = (account.initial_balance or 0) + deposit_amount - sales_amount - ledger_debits + ledger_credits
            
            account.balance = new_balance
            
            account_fixes.append({
                "account_id": account.id,
                "account_name": account.account_name,
                "currency": account.currency,
                "old_balance": old_balance,
                "new_balance": new_balance
            })
        
        # 3. 修復客戶應收帳款
        print("📋 修復客戶應收帳款...")
        customers = Customer.query.filter_by(is_active=True).all()
        
        customer_fixes = []
        for customer in customers:
            old_receivables = customer.total_receivables_twd
            
            # 總銷售金額
            total_sales = SalesRecord.query.filter(
                and_(
                    SalesRecord.customer_id == customer.id,
                    SalesRecord.is_active == True
                )
            ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
            
            # 已收款金額
            received_amount = LedgerEntry.query.filter(
                and_(
                    LedgerEntry.customer_id == customer.id,
                    LedgerEntry.entry_type == 'SETTLEMENT',
                    LedgerEntry.is_active == True
                )
            ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
            
            # 應收帳款餘額
            receivables_balance = total_sales - received_amount
            customer.total_receivables_twd = receivables_balance
            
            customer_fixes.append({
                "customer_id": customer.id,
                "customer_name": customer.name,
                "old_receivables": old_receivables,
                "new_receivables": receivables_balance,
                "total_sales": total_sales,
                "received_amount": received_amount
            })
        
        # 提交所有更改
        db.session.commit()
        
        # 4. 驗證修復結果
        total_original = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.original_rmb)).scalar() or 0
        total_issued = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.issued_rmb)).scalar() or 0
        total_remaining = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
        
        total_twd = CashAccount.query.filter_by(currency="TWD", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
        total_rmb = CashAccount.query.filter_by(currency="RMB", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
        
        total_receivables = Customer.query.filter_by(is_active=True).with_entities(func.sum(Customer.total_receivables_twd)).scalar() or 0
        
        print("✅ 遠程數據修復完成！")
        
        return jsonify({
            "status": "success",
            "message": "數據修復完成",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "inventory_batches_fixed": len(inventory_fixes),
                "cash_accounts_fixed": len(account_fixes),
                "customers_fixed": len(customer_fixes)
            },
            "final_status": {
                "inventory": {
                    "total_original": total_original,
                    "total_issued": total_issued,
                    "total_remaining": total_remaining
                },
                "cash_accounts": {
                    "total_twd": total_twd,
                    "total_rmb": total_rmb
                },
                "receivables": total_receivables
            },
            "details": {
                "inventory_fixes": inventory_fixes,
                "account_fixes": account_fixes,
                "customer_fixes": customer_fixes
            }
        })
        
    except Exception as e:
        print(f"❌ 遠程數據修復失敗: {e}")
        traceback.print_exc()
        db.session.rollback()
        
        return jsonify({
            "status": "error",
            "message": f"數據修復失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

# 添加狀態檢查 API
@app.route("/api/admin/data-status", methods=["GET"])
def get_data_status():
    """獲取當前數據狀態"""
    try:
        # 庫存狀態
        active_inventories = FIFOInventory.query.filter_by(is_active=True).count()
        total_original = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.original_rmb)).scalar() or 0
        total_remaining = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
        total_issued = FIFOInventory.query.filter_by(is_active=True).with_entities(func.sum(FIFOInventory.issued_rmb)).scalar() or 0
        
        # 現金帳戶狀態
        twd_accounts = CashAccount.query.filter_by(currency="TWD", is_active=True).count()
        rmb_accounts = CashAccount.query.filter_by(currency="RMB", is_active=True).count()
        total_twd = CashAccount.query.filter_by(currency="TWD", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
        total_rmb = CashAccount.query.filter_by(currency="RMB", is_active=True).with_entities(func.sum(CashAccount.balance)).scalar() or 0
        
        # 客戶狀態
        active_customers = Customer.query.filter_by(is_active=True).count()
        total_receivables = Customer.query.filter_by(is_active=True).with_entities(func.sum(Customer.total_receivables_twd)).scalar() or 0
        
        return jsonify({
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "inventory": {
                    "active_batches": active_inventories,
                    "total_original": total_original,
                    "total_remaining": total_remaining,
                    "total_issued": total_issued,
                    "consistency_check": abs(total_original - total_issued - total_remaining) < 0.01
                },
                "cash_accounts": {
                    "twd_accounts": twd_accounts,
                    "rmb_accounts": rmb_accounts,
                    "total_twd": total_twd,
                    "total_rmb": total_rmb
                },
                "customers": {
                    "active_customers": active_customers,
                    "total_receivables": total_receivables
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"獲取數據狀態失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

# 添加修復頁面路由
@app.route("/admin_data_recovery")
def admin_data_recovery():
    return render_template("admin_data_recovery.html")
```

#### 步驟 3：重新部署
1. 保存所有文件
2. Render 會自動檢測變更並重新部署
3. 或者手動觸發重新部署

#### 步驟 4：訪問修復界面
```
https://your-app-name.onrender.com/admin_data_recovery
```

### 方法 2：通過 Render Shell 執行

#### 步驟 1：打開 Render Shell
1. 在 Render Dashboard 中進入您的服務
2. 點擊 "Shell" 標籤
3. 等待終端加載完成

#### 步驟 2：執行修復腳本
```bash
# 進入項目目錄
cd /opt/render/project/src

# 檢查文件是否存在
ls -la *.py

# 執行修復腳本
python render_data_fix.py
```

### 方法 3：通過 HTTP 請求觸發

#### 步驟 1：添加觸發端點
在 `app.py` 中添加：

```python
@app.route("/trigger-recovery", methods=["POST"])
def trigger_recovery():
    """觸發數據修復的端點"""
    try:
        # 執行修復邏輯
        from render_data_fix import render_data_fix
        result = render_data_fix()
        
        if result:
            return jsonify({
                "status": "success",
                "message": "數據修復完成",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "數據修復失敗"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
```

#### 步驟 2：觸發修復
```bash
# 使用 curl 觸發
curl -X POST https://your-app-name.onrender.com/trigger-recovery

# 或者使用 Postman 等工具
```

## 🔧 權限和安全設置

### 添加管理員權限檢查
```python
from flask_login import login_required, current_user

@app.route("/api/admin/data-recovery", methods=["POST"])
@login_required
def remote_data_recovery():
    # 檢查管理員權限
    if not current_user.is_admin:
        return jsonify({"status": "error", "message": "權限不足"}), 403
    
    # ... 修復邏輯 ...
```

### 添加 API 密鑰驗證
```python
@app.route("/api/admin/data-recovery", methods=["POST"])
def remote_data_recovery():
    # 檢查 API 密鑰
    api_key = request.headers.get('X-API-Key')
    if api_key != os.environ.get('ADMIN_API_KEY'):
        return jsonify({"status": "error", "message": "無效的 API 密鑰"}), 401
    
    # ... 修復邏輯 ...
```

## 📱 使用建議

### 1. 選擇合適的方法
- **網頁界面**：適合日常維護和監控
- **Shell 執行**：適合緊急修復和調試
- **HTTP 觸發**：適合自動化腳本和 CI/CD

### 2. 執行時機
- 選擇系統使用量較少的時間
- 提前通知其他用戶
- 確保沒有重要操作正在進行

### 3. 監控和日誌
- 檢查 Render 的日誌輸出
- 監控數據庫連接狀態
- 記錄所有修復操作

## 🚨 故障排除

### 常見問題

1. **模組導入錯誤**：
   ```
   解決方案：確保所有依賴都已安裝，檢查 requirements.txt
   ```

2. **數據庫連接錯誤**：
   ```
   解決方案：檢查環境變數和數據庫配置
   ```

3. **權限錯誤**：
   ```
   解決方案：檢查用戶權限和 API 密鑰設置
   ```

4. **超時錯誤**：
   ```
   解決方案：增加超時設置，或分段執行修復
   ```

### 調試技巧

1. **檢查 Render 日誌**：
   - 在 Dashboard 中查看實時日誌
   - 檢查錯誤和警告信息

2. **測試 API 端點**：
   - 使用 Postman 或 curl 測試
   - 檢查響應狀態和錯誤信息

3. **驗證數據庫連接**：
   - 測試基本查詢
   - 檢查表結構和數據

## 📊 監控和維護

### 定期檢查
- **每日**：檢查系統狀態
- **每週**：執行數據一致性檢查
- **每月**：執行完整數據修復

### 預防措施
1. **定期備份**：設置自動備份
2. **監控系統**：設置數據一致性監控
3. **用戶培訓**：培訓正確使用系統

## 總結

在 Render 上執行數據修復有多種方式：

- ✅ **網頁界面**：最用戶友好，適合日常使用
- ✅ **Shell 執行**：最直接，適合緊急情況
- ✅ **HTTP 觸發**：最靈活，適合自動化

選擇適合您需求的方法，確保數據安全和系統穩定。如果遇到問題，請檢查 Render 日誌和錯誤信息。
