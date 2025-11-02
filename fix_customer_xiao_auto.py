#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自動修復客戶「蕭」的重複扣款問題（無需互動）
使用方法：python fix_customer_xiao_auto.py
"""

from app import app, db
from app import Customer, LedgerEntry, SalesRecord
from sqlalchemy import func

def fix_customer_xiao_auto():
    """自動修復客戶「蕭」的應收帳款（不需要互動）"""
    with app.app_context():
        print("=" * 80)
        print("自動修復客戶「蕭」的應收帳款")
        print("=" * 80)
        
        # 1. 找到客戶「蕭」
        customers = db.session.execute(
            db.select(Customer).filter(Customer.name.like("%蕭%"))
        ).scalars().all()
        
        if not customers:
            print("\n❌ 找不到客戶「蕭」的記錄！")
            print("   可能原因：客戶記錄被刪除或名稱不匹配")
            print("\n建議：")
            print("1. 檢查數據庫中是否還有該客戶的其他名稱變體")
            print("2. 或使用以下 SQL 查詢查找：")
            print("   SELECT * FROM customers WHERE name LIKE '%蕭%';")
            return False
        
        customer = customers[0]
        if len(customers) > 1:
            print(f"\n⚠️  找到 {len(customers)} 個匹配的客戶，使用第一個：{customer.name}")
        
        print(f"\n找到客戶：{customer.name} (ID: {customer.id})")
        print(f"當前狀態：{'啟用' if customer.is_active else '停用'}")
        print(f"當前應收帳款：NT$ {customer.total_receivables_twd:,.2f}")
        
        # 2. 計算實際應收帳款
        # 公式：應收帳款 = 總銷售金額 - 總銷帳金額
        
        # 總銷售金額
        total_sales = db.session.execute(
            db.select(func.sum(SalesRecord.twd_amount))
            .filter(SalesRecord.customer_id == customer.id)
        ).scalar() or 0.0
        
        # 總銷帳金額（從 LedgerEntry，這是實際的銷帳記錄，只有一筆 180,000）
        total_settlements = db.session.execute(
            db.select(func.sum(LedgerEntry.amount))
            .filter(LedgerEntry.entry_type == "SETTLEMENT")
            .filter(LedgerEntry.description.like(f"%{customer.name}%"))
        ).scalar() or 0.0
        
        # 正確的應收帳款
        correct_receivables = total_sales - total_settlements
        
        print(f"\n計算結果：")
        print(f"   總銷售金額：NT$ {total_sales:,.2f}")
        print(f"   總銷帳金額：NT$ {total_settlements:,.2f}")
        print(f"   正確應收帳款：NT$ {correct_receivables:,.2f}")
        print(f"   當前應收帳款：NT$ {customer.total_receivables_twd:,.2f}")
        
        difference = correct_receivables - customer.total_receivables_twd
        print(f"   差異：NT$ {difference:+,.2f}")
        
        # 3. 如果差異很小，可能不需要修復
        if abs(difference) < 0.01:
            print("\n✅ 應收帳款已經是正確值，無需修復")
            
            # 但確保客戶是啟用狀態
            if not customer.is_active:
                customer.is_active = True
                db.session.commit()
                print("✅ 已啟用客戶記錄")
            
            return True
        
        # 4. 修復應收帳款
        old_receivables = customer.total_receivables_twd
        customer.total_receivables_twd = correct_receivables
        
        # 如果客戶被停用，啟用它
        if not customer.is_active:
            customer.is_active = True
            print("\n✅ 已啟用客戶記錄")
        
        print(f"\n修復應收帳款：")
        print(f"   {old_receivables:,.2f} → {correct_receivables:,.2f} (變動：{difference:+,.2f})")
        
        # 5. 提交更改
        try:
            db.session.commit()
            print(f"\n✅ 修復成功！客戶「{customer.name}」的應收帳款已更新")
            print(f"   新的應收帳款：NT$ {customer.total_receivables_twd:,.2f}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 修復失敗：{e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    fix_customer_xiao_auto()

