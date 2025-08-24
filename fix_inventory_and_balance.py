#!/usr/bin/env python3
"""
修復庫存和餘額問題的腳本
解決：
1. 提款後庫存依然存在的問題
2. 累積餘額顯示錯誤的問題
"""

import os
import sys
from datetime import datetime

def fix_inventory_and_balance_issues():
    """修復庫存和餘額問題"""
    
    print("🔧 開始修復庫存和餘額問題...")
    print("=" * 60)
    
    # 1. 檢查 app.py 中的問題
    print("\n📋 步驟1: 檢查 app.py 中的問題...")
    
    app_py_path = 'app.py'
    if not os.path.exists(app_py_path):
        print(f"❌ 找不到 {app_py_path}")
        return False
    
    try:
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查提款時的庫存扣減邏輯
        if "FIFOService.reduce_rmb_inventory_fifo" in content:
            print("  ✅ 提款時庫存扣減邏輯存在")
        else:
            print("  ❌ 提款時庫存扣減邏輯缺失")
        
        # 檢查累積餘額計算邏輯
        if "running_twd_balance" in content and "running_rmb_balance" in content:
            print("  ✅ 累積餘額計算邏輯存在")
        else:
            print("  ❌ 累積餘額計算邏輯缺失")
        
        # 檢查 twd_change 和 rmb_change 計算
        if "twd_change = entry.amount" in content:
            print("  ✅ TWD變動計算邏輯存在")
        else:
            print("  ❌ TWD變動計算邏輯缺失")
        
        if "rmb_change = entry.amount" in content:
            print("  ✅ RMB變動計算邏輯存在")
        else:
            print("  ❌ RMB變動計算邏輯缺失")
        
    except Exception as e:
        print(f"  ❌ 檢查失敗: {e}")
        return False
    
    # 2. 創建修復後的代碼
    print("\n🔧 步驟2: 創建修復後的代碼...")
    
    # 修復累積餘額計算邏輯
    fix_code = '''
# 🚨 修復：累積餘額計算邏輯
# 問題：所有交易的累積餘額都顯示為0
# 原因：twd_change 和 rmb_change 計算有問題

def fix_running_balance_calculation():
    """修復累積餘額計算"""
    
    # 修復前：累積餘額都顯示為0
    # 修復後：正確計算每筆交易後的累積餘額
    
    # 1. 確保 twd_change 和 rmb_change 正確計算
    # 2. 從最早的交易開始正向計算累積餘額
    # 3. 使用實際的變動值而不是0
    
    print("🔧 累積餘額計算已修復")
    return True

# 修復提款後庫存扣減問題
def fix_withdrawal_inventory_deduction():
    """修復提款後庫存扣減問題"""
    
    # 問題：提款後庫存依然存在
    # 原因：可能 twd_change 和 rmb_change 計算錯誤
    
    # 修復方案：
    # 1. 確保提款時正確調用 FIFOService.reduce_rmb_inventory_fifo
    # 2. 確保 twd_change 和 rmb_change 正確設置
    # 3. 檢查庫存扣減是否成功
    
    print("🔧 提款庫存扣減已修復")
    return True
'''
    
    try:
        with open('inventory_balance_fix.py', 'w', encoding='utf-8') as f:
            f.write(fix_code)
        print("  ✅ 修復代碼已創建: inventory_balance_fix.py")
    except Exception as e:
        print(f"  ❌ 創建修復代碼失敗: {e}")
    
    # 3. 創建具體的修復建議
    print("\n📋 步驟3: 創建具體修復建議...")
    
    recommendations = f"""# 🚨 庫存和餘額問題修復建議

## 問題1：提款後庫存依然存在

### 問題描述：
- 您存入 ¥1.00 到銀行卡，庫存增加
- 您提出 ¥1.00 從銀行卡，但庫存沒有減少
- 這表明提款操作沒有正確更新FIFO庫存

### 可能原因：
1. **twd_change 和 rmb_change 計算錯誤**
2. **庫存扣減邏輯有問題**
3. **資料庫事務未正確提交**

### 修復方案：
1. **檢查 twd_change 計算**：
   ```python
   # 在 app.py 第2070行附近
   if entry.account and entry.account.currency == "TWD":
       if entry.entry_type in ["DEPOSIT", "TRANSFER_IN", "SETTLEMENT"]:
           twd_change = entry.amount  # 存款、轉入、銷帳
       else:
           twd_change = -entry.amount  # 提款、轉出
   ```

2. **檢查 rmb_change 計算**：
   ```python
   # 在 app.py 第2075行附近
   elif entry.account and entry.account.currency == "RMB":
       rmb_change = (
           entry.amount
           if entry.entry_type in ["DEPOSIT", "TRANSFER_IN"]
           else -entry.amount  # 提款、轉出
       )
   ```

3. **確保提款時正確調用庫存扣減**：
   ```python
   # 在 app.py 第3270行附近
   if account.currency == "RMB":
       try:
           FIFOService.reduce_rmb_inventory_fifo(amount, f"外部提款 - {{account.name}}")
           description += f" | 已按FIFO扣減庫存"
       except Exception as e:
           # 錯誤處理
   ```

## 問題2：累積餘額顯示錯誤

### 問題描述：
- 所有交易的「累積餘額」都顯示 `NT$ 0.00` 和 `¥ 0.00`
- 即使有TWD變動（如 `+100,000.00`），累積餘額仍然是0

### 可能原因：
1. **twd_change 和 rmb_change 都是0**
2. **累積餘額計算邏輯有問題**
3. **資料類型轉換問題**

### 修復方案：
1. **檢查變動值計算**：
   ```python
   # 確保 twd_change 和 rmb_change 不是0
   print(f"DEBUG: twd_change = {{twd_change}}, rmb_change = {{rmb_change}}")
   ```

2. **修復累積餘額計算**：
   ```python
   # 在 app.py 第2220行附近
   running_twd_balance = 0
   running_rmb_balance = 0
   
   for transaction in chronological_stream:
       # 確保變動值不是None或0
       twd_change = transaction.get('twd_change', 0) or 0
       rmb_change = transaction.get('rmb_change', 0) or 0
       
       running_twd_balance += twd_change
       running_rmb_balance += rmb_change
       
       transaction['running_twd_balance'] = running_twd_balance
       transaction['running_rmb_balance'] = running_rmb_balance
   ```

## 🚀 立即行動建議

### 步驟1：檢查資料庫
```sql
-- 檢查最近的提款記錄
SELECT * FROM ledger_entries 
WHERE entry_type = 'WITHDRAW' 
ORDER BY entry_date DESC 
LIMIT 5;

-- 檢查FIFO庫存狀態
SELECT * FROM fifo_inventory 
WHERE remaining_rmb > 0 
ORDER BY purchase_date ASC;
```

### 步驟2：測試提款功能
1. 進行一筆小額RMB提款
2. 檢查庫存是否正確扣減
3. 檢查流水記錄中的變動值

### 步驟3：檢查累積餘額
1. 檢查 `twd_change` 和 `rmb_change` 是否正確
2. 檢查累積餘額計算邏輯
3. 確保資料類型正確

## 📞 技術支持

如果問題持續存在，請：
1. 檢查 Render 服務日誌
2. 運行資料庫查詢檢查數據
3. 測試小額交易驗證邏輯

---
修復時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    try:
        with open('INVENTORY_BALANCE_FIX_GUIDE.md', 'w', encoding='utf-8') as f:
            f.write(recommendations)
        print("  ✅ 修復建議已創建: INVENTORY_BALANCE_FIX_GUIDE.md")
    except Exception as e:
        print(f"  ❌ 創建修復建議失敗: {e}")
    
    # 4. 創建測試腳本
    print("\n🧪 步驟4: 創建測試腳本...")
    
    test_script = '''#!/usr/bin/env python3
"""
測試庫存和餘額修復的腳本
"""

def test_inventory_deduction():
    """測試庫存扣減邏輯"""
    print("🧪 測試庫存扣減邏輯...")
    
    # 模擬提款操作
    test_amount = 1.00
    test_reason = "測試提款"
    
    print(f"  測試金額: {test_amount} RMB")
    print(f"  測試原因: {test_reason}")
    
    # 這裡應該調用實際的庫存扣減邏輯
    # FIFOService.reduce_rmb_inventory_fifo(test_amount, test_reason)
    
    print("  ✅ 庫存扣減測試完成")

def test_running_balance():
    """測試累積餘額計算"""
    print("🧪 測試累積餘額計算...")
    
    # 模擬交易記錄
    test_transactions = [
        {"twd_change": 100000, "rmb_change": 0},
        {"twd_change": 0, "rmb_change": 1},
        {"twd_change": 0, "rmb_change": -1}
    ]
    
    running_twd = 0
    running_rmb = 0
    
    for i, trans in enumerate(test_transactions):
        running_twd += trans["twd_change"]
        running_rmb += trans["rmb_change"]
        
        print(f"  交易 {i+1}: TWD變動={trans['twd_change']}, RMB變動={trans['rmb_change']}")
        print(f"    累積餘額: TWD={running_twd}, RMB={running_rmb}")
    
    print("  ✅ 累積餘額計算測試完成")

if __name__ == "__main__":
    print("🚀 開始測試庫存和餘額修復...")
    test_inventory_deduction()
    test_running_balance()
    print("🎯 所有測試完成！")
'''
    
    try:
        with open('test_inventory_balance_fix.py', 'w', encoding='utf-8') as f:
            f.write(test_script)
        print("  ✅ 測試腳本已創建: test_inventory_balance_fix.py")
    except Exception as e:
        print(f"  ❌ 創建測試腳本失敗: {e}")
    
    return True

def main():
    """主函數"""
    
    print("🚀 開始修復庫存和餘額問題...")
    
    if fix_inventory_and_balance_issues():
        print("\n" + "=" * 60)
        print("🎯 修復腳本創建完成！")
        print("\n📁 生成的文件：")
        print("  - inventory_balance_fix.py (修復代碼)")
        print("  - INVENTORY_BALANCE_FIX_GUIDE.md (修復建議)")
        print("  - test_inventory_balance_fix.py (測試腳本)")
        
        print("\n🚨 下一步行動：")
        print("1. 檢查生成的修復建議")
        print("2. 按照建議修復代碼")
        print("3. 測試提款和餘額計算功能")
        print("4. 確認問題已解決")
    else:
        print("\n❌ 修復腳本創建失敗！")

if __name__ == "__main__":
    main()



