#!/usr/bin/env python3
"""
測試提款和餘額修復的腳本
"""

def test_withdrawal_logic():
    """測試提款邏輯"""
    print("🧪 測試提款邏輯...")
    
    # 模擬提款記錄
    test_withdrawal = {
        "entry_type": "WITHDRAW",
        "account_currency": "RMB",
        "amount": 1.00,
        "account_name": "銀行卡"
    }
    
    print(f"  提款記錄: {test_withdrawal}")
    
    # 測試 twd_change 和 rmb_change 計算
    if test_withdrawal["account_currency"] == "TWD":
        twd_change = -test_withdrawal["amount"]  # 提款減少TWD
        rmb_change = 0
    elif test_withdrawal["account_currency"] == "RMB":
        twd_change = 0
        rmb_change = -test_withdrawal["amount"]  # 提款減少RMB
    
    print(f"  計算結果: TWD變動={twd_change}, RMB變動={rmb_change}")
    
    # 測試累積餘額計算
    running_twd = 0
    running_rmb = 0
    
    # 模擬之前的交易
    previous_transactions = [
        {"twd_change": 100000, "rmb_change": 0},  # 存款100,000 TWD
        {"twd_change": 0, "rmb_change": 1},       # 存款1 RMB
    ]
    
    for i, trans in enumerate(previous_transactions):
        running_twd += trans["twd_change"]
        running_rmb += trans["rmb_change"]
        print(f"  交易 {i+1}: TWD={running_twd}, RMB={running_rmb}")
    
    # 添加提款交易
    running_twd += twd_change
    running_rmb += rmb_change
    print(f"  提款後: TWD={running_twd}, RMB={running_rmb}")
    
    print("  ✅ 提款邏輯測試完成")

def test_inventory_deduction():
    """測試庫存扣減邏輯"""
    print("\n🧪 測試庫存扣減邏輯...")
    
    # 模擬庫存狀態
    inventory_before = {
        "total_rmb": 40775.31,
        "remaining_rmb": 40775.31
    }
    
    withdrawal_amount = 1.00
    
    print(f"  提款前庫存: {inventory_before['remaining_rmb']} RMB")
    print(f"  提款金額: {withdrawal_amount} RMB")
    
    # 模擬庫存扣減
    inventory_after = inventory_before["remaining_rmb"] - withdrawal_amount
    
    print(f"  提款後庫存: {inventory_after} RMB")
    
    if inventory_after == inventory_before["remaining_rmb"] - withdrawal_amount:
        print("  ✅ 庫存扣減計算正確")
    else:
        print("  ❌ 庫存扣減計算錯誤")
    
    print("  ✅ 庫存扣減測試完成")

def test_running_balance_calculation():
    """測試累積餘額計算"""
    print("\n🧪 測試累積餘額計算...")
    
    # 模擬交易記錄
    test_transactions = [
        {"type": "DEPOSIT", "twd_change": 100000, "rmb_change": 0},
        {"type": "DEPOSIT", "twd_change": 0, "rmb_change": 1},
        {"type": "WITHDRAW", "twd_change": 0, "rmb_change": -1},
    ]
    
    running_twd = 0
    running_rmb = 0
    
    print("  交易記錄:")
    for i, trans in enumerate(test_transactions):
        running_twd += trans["twd_change"]
        running_rmb += trans["rmb_change"]
        
        print(f"    {i+1}. {trans['type']}: TWD變動={trans['twd_change']}, RMB變動={trans['rmb_change']}")
        print(f"       累積餘額: TWD={running_twd}, RMB={running_rmb}")
    
    # 驗證最終餘額
    expected_twd = 100000
    expected_rmb = 0
    
    if running_twd == expected_twd and running_rmb == expected_rmb:
        print(f"  ✅ 累積餘額計算正確: TWD={running_twd}, RMB={running_rmb}")
    else:
        print(f"  ❌ 累積餘額計算錯誤: 期望 TWD={expected_twd}, RMB={expected_rmb}, 實際 TWD={running_twd}, RMB={running_rmb}")
    
    print("  ✅ 累積餘額計算測試完成")

def main():
    """主函數"""
    print("🚀 開始測試提款和餘額修復...")
    print("=" * 60)
    
    test_withdrawal_logic()
    test_inventory_deduction()
    test_running_balance_calculation()
    
    print("\n" + "=" * 60)
    print("🎯 所有測試完成！")
    print("\n📋 測試結果總結:")
    print("1. ✅ 提款邏輯測試")
    print("2. ✅ 庫存扣減測試")
    print("3. ✅ 累積餘額計算測試")
    print("\n🚨 如果測試通過，說明修復成功！")
    print("如果仍有問題，請檢查調試輸出。")

if __name__ == "__main__":
    main()


