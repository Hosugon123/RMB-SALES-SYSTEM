#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修復客戶「蕭」的重複扣款問題
問題：2025/10/30 的銷帳 NT$ 180,000 被重複扣減（實際扣了 360,000）
導致客戶應收帳款異常或記錄消失
"""

# 需要在 app 上下文中運行
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import func, text
from datetime import datetime

def find_customer_xiao(db, Customer):
    """找到客戶「蕭」的記錄"""
    customers = db.session.execute(
        db.select(Customer).filter(Customer.name.like("%蕭%"))
    ).scalars().all()
    
    return customers

def analyze_customer_xiao(db, Customer, LedgerEntry, SalesRecord):
    """分析客戶「蕭」的數據狀況"""
    print("=" * 80)
    print("分析客戶「蕭」的數據狀況")
    print("=" * 80)
    
    customers = find_customer_xiao(db, Customer)
    
    if not customers:
        print("❌ 找不到客戶「蕭」的記錄！")
        print("\n可能原因：")
        print("1. 客戶記錄被刪除")
        print("2. 客戶名稱不完全匹配")
        print("\n建議：請檢查數據庫中是否有該客戶的其他名稱變體")
        return None
    
    customer = customers[0]
    if len(customers) > 1:
        print(f"⚠️  找到 {len(customers)} 個匹配的客戶，使用第一個：")
        for c in customers:
            print(f"   - ID: {c.id}, 名稱: {c.name}, 應收帳款: {c.total_receivables_twd:,.2f}")
    
    print(f"\n客戶資訊：")
    print(f"   ID: {customer.id}")
    print(f"   名稱: {customer.name}")
    print(f"   狀態: {'啟用' if customer.is_active else '停用'}")
    print(f"   當前應收帳款: NT$ {customer.total_receivables_twd:,.2f}")
    
    # 計算實際應收帳款
    print(f"\n計算實際應收帳款...")
    
    # 1. 計算所有銷售記錄總額
    total_sales = db.session.execute(
        db.select(func.sum(SalesRecord.twd_amount))
        .filter(SalesRecord.customer_id == customer.id)
    ).scalar() or 0.0
    
    print(f"   總銷售金額: NT$ {total_sales:,.2f}")
    
    # 2. 計算所有銷帳記錄總額（從 LedgerEntry）
    total_settlements = db.session.execute(
        db.select(func.sum(LedgerEntry.amount))
        .filter(LedgerEntry.entry_type == "SETTLEMENT")
        .filter(LedgerEntry.description.like(f"%{customer.name}%"))
    ).scalar() or 0.0
    
    print(f"   總銷帳金額（從 LedgerEntry）: NT$ {total_settlements:,.2f}")
    
    # 3. 查找 2025/10/30 的銷帳記錄
    settlement_20251030 = db.session.execute(
        db.select(LedgerEntry)
        .filter(LedgerEntry.entry_type == "SETTLEMENT")
        .filter(LedgerEntry.description.like(f"%{customer.name}%"))
        .filter(LedgerEntry.description.like("%銷帳收款%"))
        .order_by(LedgerEntry.entry_date.desc())
    ).scalars().all()
    
    print(f"\n   找到 {len(settlement_20251030)} 筆銷帳記錄：")
    for entry in settlement_20251030:
        print(f"      - ID: {entry.id}, 日期: {entry.entry_date}, 金額: NT$ {entry.amount:,.2f}")
        print(f"        描述: {entry.description}")
    
    # 4. 正確的應收帳款 = 總銷售 - 總銷帳
    correct_receivables = total_sales - total_settlements
    
    print(f"\n   正確應收帳款: NT$ {correct_receivables:,.2f}")
    print(f"   當前應收帳款: NT$ {customer.total_receivables_twd:,.2f}")
    
    difference = correct_receivables - customer.total_receivables_twd
    
    if abs(difference) > 0.01:  # 允許小數點誤差
        print(f"\n   ⚠️  差異: NT$ {difference:,.2f}")
        if difference > 0:
            print(f"   → 需要增加 NT$ {difference:,.2f}（可能因為重複扣款）")
        else:
            print(f"   → 需要減少 NT$ {abs(difference):,.2f}")
    
    return {
        'customer': customer,
        'total_sales': total_sales,
        'total_settlements': total_settlements,
        'correct_receivables': correct_receivables,
        'current_receivables': customer.total_receivables_twd,
        'difference': difference,
        'settlements': settlement_20251030
    }

def fix_customer_xiao(db, Customer, LedgerEntry, SalesRecord):
    """修復客戶「蕭」的應收帳款"""
    print("\n" + "=" * 80)
    print("開始修復客戶「蕭」的應收帳款")
    print("=" * 80)
    
    analysis = analyze_customer_xiao(db, Customer, LedgerEntry, SalesRecord)
    
    if not analysis:
        return False
    
    customer = analysis['customer']
    correct_receivables = analysis['correct_receivables']
    current_receivables = analysis['current_receivables']
    difference = analysis['difference']
    
    # 如果差異很小，可能不需要修復
    if abs(difference) < 0.01:
        print("\n✅ 應收帳款已經是正確值，無需修復")
        return True
    
    # 如果客戶被停用，先啟用
    if not customer.is_active:
        print(f"\n⚠️  客戶「{customer.name}」目前為停用狀態，將啟用...")
        customer.is_active = True
    
    # 修復應收帳款
    old_receivables = customer.total_receivables_twd
    customer.total_receivables_twd = correct_receivables
    
    print(f"\n修復應收帳款：")
    print(f"   原值: NT$ {old_receivables:,.2f}")
    print(f"   新值: NT$ {correct_receivables:,.2f}")
    print(f"   變動: NT$ {difference:+,.2f}")
    
    # 記錄修復操作到 LedgerEntry
    try:
        adjustment_description = f"數據修復：修正重複扣款問題，恢復客戶「{customer.name}」應收帳款 ({old_receivables:,.2f} -> {correct_receivables:,.2f})"
        
        # 檢查是否有 AR_ADJUSTMENT 類型，如果沒有則使用 SETTLEMENT 或創建新的
        adjustment_entry = LedgerEntry(
            entry_type="AR_ADJUSTMENT",
            amount=difference,
            description=adjustment_description,
            entry_date=datetime.utcnow(),
            operator_id=1  # 系統修復，使用 ID 1 作為操作員
        )
        
        # 如果有 account_id 欄位，可以設為 None
        if hasattr(LedgerEntry, 'account_id'):
            adjustment_entry.account_id = None
        
        db.session.add(adjustment_entry)
        print(f"\n✅ 已創建修復記錄到 LedgerEntry")
        
    except Exception as e:
        print(f"\n⚠️  創建修復記錄失敗: {e}")
        print("   但客戶應收帳款已修復")
    
    # 提交更改
    try:
        db.session.commit()
        print(f"\n✅ 修復完成！客戶「{customer.name}」的應收帳款已更新為 NT$ {correct_receivables:,.2f}")
        
        # 驗證修復結果
        db.session.refresh(customer)
        print(f"\n驗證結果：")
        print(f"   客戶 ID: {customer.id}")
        print(f"   客戶名稱: {customer.name}")
        print(f"   狀態: {'啟用' if customer.is_active else '停用'}")
        print(f"   應收帳款: NT$ {customer.total_receivables_twd:,.2f}")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ 修復失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    # 導入 app 和模型（需要在 app 上下文中）
    from app import app, db
    from app import Customer, LedgerEntry, SalesRecord, CashLog
    
    with app.app_context():
        print("\n" + "=" * 80)
        print("客戶「蕭」應收帳款修復工具")
        print("=" * 80)
        print("\n此工具將：")
        print("1. 查找客戶「蕭」的記錄")
        print("2. 分析應收帳款數據")
        print("3. 修復因重複扣款造成的應收帳款錯誤")
        print("4. 確保客戶記錄可見（啟用狀態）")
        print("\n" + "=" * 80)
        
        # 先分析
        analysis = analyze_customer_xiao(db, Customer, LedgerEntry, SalesRecord)
        
        if not analysis:
            print("\n❌ 無法找到客戶記錄，請手動檢查數據庫")
            return
        
        # 詢問是否要修復
        print("\n" + "=" * 80)
        response = input("是否要修復客戶「蕭」的應收帳款？(y/n): ").strip().lower()
        
        if response == 'y' or response == 'yes':
            fix_customer_xiao(db, Customer, LedgerEntry, SalesRecord)
        else:
            print("\n已取消修復操作")

if __name__ == '__main__':
    main()

