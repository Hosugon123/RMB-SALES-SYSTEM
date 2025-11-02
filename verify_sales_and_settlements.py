#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證歷史總售出、歷史總銷帳和 WITHDRAW 記錄的一致性

此腳本會計算：
1. 歷史總售出：所有 SalesRecord 的總金額（RMB 和 TWD）
2. 歷史總銷帳：所有 SETTLEMENT LedgerEntry 的總金額
3. 售出扣款 WITHDRAW 記錄：歷史的售出扣款 WITHDRAW 記錄總額
4. 驗證數據一致性和帳戶餘額正確性

使用方法：
- 本地測試: python verify_sales_and_settlements.py
- Render Shell: python verify_sales_and_settlements.py
- 或直接在 Render Shell 中創建此腳本並執行
"""

import sys
import os

# 確保可以找到 app 模組
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from app import app, db, SalesRecord, LedgerEntry, Customer, CashAccount
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("請確保在專案根目錄執行此腳本")
    sys.exit(1)

def verify_sales_and_settlements():
    """驗證歷史總售出、歷史總銷帳和 WITHDRAW 記錄"""
    print("=" * 100)
    print("驗證歷史總售出、歷史總銷帳和 WITHDRAW 記錄的一致性")
    print("=" * 100)
    
    with app.app_context():
        try:
            # ========== 1. 計算歷史總售出 ==========
            print("\n【1】計算歷史總售出")
            print("-" * 100)
            
            # 查詢所有銷售記錄
            all_sales = db.session.execute(
                db.select(SalesRecord).order_by(SalesRecord.created_at.asc())
            ).scalars().all()
            
            total_sales_rmb = sum(sale.rmb_amount for sale in all_sales)
            total_sales_twd = sum(sale.twd_amount for sale in all_sales)
            total_sales_count = len(all_sales)
            
            # 按客戶統計
            sales_by_customer = {}
            for sale in all_sales:
                customer_name = sale.customer.name if sale.customer else "未知客戶"
                if customer_name not in sales_by_customer:
                    sales_by_customer[customer_name] = {
                        'count': 0,
                        'rmb_total': 0,
                        'twd_total': 0
                    }
                sales_by_customer[customer_name]['count'] += 1
                sales_by_customer[customer_name]['rmb_total'] += sale.rmb_amount
                sales_by_customer[customer_name]['twd_total'] += sale.twd_amount
            
            print(f"總售出記錄數: {total_sales_count} 筆")
            print(f"總售出金額 (RMB): {total_sales_rmb:,.2f} RMB")
            print(f"總售出金額 (TWD): {total_sales_twd:,.2f} TWD")
            
            print(f"\n按客戶統計（前10名）:")
            sorted_customers = sorted(sales_by_customer.items(), key=lambda x: x[1]['twd_total'], reverse=True)[:10]
            for customer_name, stats in sorted_customers:
                print(f"  {customer_name}: {stats['count']} 筆, {stats['twd_total']:,.2f} TWD, {stats['rmb_total']:,.2f} RMB")
            
            # ========== 2. 計算歷史總銷帳 ==========
            print("\n【2】計算歷史總銷帳")
            print("-" * 100)
            
            all_settlements = db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "SETTLEMENT")
                .order_by(LedgerEntry.entry_date.asc())
            ).scalars().all()
            
            total_settlements = sum(settlement.amount for settlement in all_settlements)
            total_settlements_count = len(all_settlements)
            
            # 按客戶統計銷帳（從描述中提取客戶名稱）
            settlements_by_customer = {}
            for settlement in all_settlements:
                # 嘗試從描述中提取客戶名稱
                description = settlement.description or ""
                customer_name = "未知客戶"
                for cname in sales_by_customer.keys():
                    if cname in description:
                        customer_name = cname
                        break
                
                if customer_name not in settlements_by_customer:
                    settlements_by_customer[customer_name] = {
                        'count': 0,
                        'total': 0
                    }
                settlements_by_customer[customer_name]['count'] += 1
                settlements_by_customer[customer_name]['total'] += settlement.amount
            
            print(f"總銷帳記錄數: {total_settlements_count} 筆")
            print(f"總銷帳金額: {total_settlements:,.2f} TWD")
            
            print(f"\n按客戶統計（前10名）:")
            sorted_settlements = sorted(settlements_by_customer.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
            for customer_name, stats in sorted_settlements:
                print(f"  {customer_name}: {stats['count']} 筆, {stats['total']:,.2f} TWD")
            
            # ========== 3. 計算應收帳款 ==========
            print("\n【3】計算應收帳款")
            print("-" * 100)
            
            # 應收帳款 = 售出 - 銷帳
            total_receivables_calculated = total_sales_twd - total_settlements
            
            # 從資料庫中查詢所有客戶的應收帳款總和
            all_customers = db.session.execute(
                db.select(Customer)
            ).scalars().all()
            
            total_receivables_from_db = sum(customer.total_receivables_twd for customer in all_customers)
            
            print(f"計算的應收帳款 (售出 - 銷帳): {total_receivables_calculated:,.2f} TWD")
            print(f"資料庫中的應收帳款總和: {total_receivables_from_db:,.2f} TWD")
            
            discrepancy = abs(total_receivables_calculated - total_receivables_from_db)
            if discrepancy > 0.01:  # 允許小數點誤差
                print(f"⚠️  差異: {discrepancy:,.2f} TWD (可能的原因：歷史數據不一致)")
            else:
                print("✅ 應收帳款計算一致")
            
            # ========== 4. 統計售出扣款 WITHDRAW 記錄 ==========
            print("\n【4】統計售出扣款 WITHDRAW 記錄")
            print("-" * 100)
            
            withdraw_records = db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "WITHDRAW")
                .filter(LedgerEntry.description.like("%售出扣款%"))
            ).scalars().all()
            
            total_withdraw_rmb = sum(abs(record.amount) for record in withdraw_records)
            total_withdraw_count = len(withdraw_records)
            
            # 按帳戶統計
            withdraw_by_account = {}
            for record in withdraw_records:
                account_name = record.account.name if record.account else "未知帳戶"
                if account_name not in withdraw_by_account:
                    withdraw_by_account[account_name] = {
                        'count': 0,
                        'total': 0
                    }
                withdraw_by_account[account_name]['count'] += 1
                withdraw_by_account[account_name]['total'] += abs(record.amount)
            
            print(f"售出扣款 WITHDRAW 記錄數: {total_withdraw_count} 筆")
            print(f"售出扣款 WITHDRAW 總金額: {total_withdraw_rmb:,.2f} RMB")
            
            print(f"\n按帳戶統計:")
            for account_name, stats in sorted(withdraw_by_account.items(), key=lambda x: x[1]['total'], reverse=True):
                print(f"  {account_name}: {stats['count']} 筆, {stats['total']:,.2f} RMB")
            
            # ========== 5. 數據一致性驗證 ==========
            print("\n【5】數據一致性驗證")
            print("-" * 100)
            
            # 驗證：售出扣款 WITHDRAW 應該等於或接近總售出（RMB）
            ratio = (total_withdraw_rmb / total_sales_rmb * 100) if total_sales_rmb > 0 else 0
            
            print(f"售出扣款 WITHDRAW / 總售出 (RMB) = {total_withdraw_rmb:,.2f} / {total_sales_rmb:,.2f} = {ratio:.2f}%")
            
            if abs(total_withdraw_rmb - total_sales_rmb) < 0.01:
                print("✅ 售出扣款 WITHDRAW 與總售出金額一致")
            elif ratio > 95:
                print("⚠️  售出扣款 WITHDRAW 接近總售出金額（可能有少量差異）")
            else:
                print("⚠️  售出扣款 WITHDRAW 與總售出金額不一致，可能原因：")
                print("   1. 某些銷售記錄沒有創建 WITHDRAW 記錄")
                print("   2. 某些 WITHDRAW 記錄被錯誤創建")
                print("   3. 新邏輯已不再創建 WITHDRAW 記錄（這是正常的）")
            
            # ========== 6. 帳戶餘額驗證 ==========
            print("\n【6】帳戶餘額驗證")
            print("-" * 100)
            
            all_accounts = db.session.execute(
                db.select(CashAccount).filter(CashAccount.currency == "RMB")
            ).scalars().all()
            
            print("RMB 帳戶餘額檢查:")
            for account in all_accounts:
                # 計算該帳戶的理論餘額：
                # 理論餘額 = 當前餘額 + 該帳戶的售出扣款 WITHDRAW 總額
                account_withdraw = withdraw_by_account.get(account.name, {}).get('total', 0)
                theoretical_balance = account.balance + account_withdraw
                
                print(f"  {account.name}:")
                print(f"    當前餘額: {account.balance:,.2f} RMB")
                print(f"    售出扣款 WITHDRAW: {account_withdraw:,.2f} RMB")
                print(f"    理論餘額（回補後）: {theoretical_balance:,.2f} RMB")
            
            # ========== 7. 總結 ==========
            print("\n" + "=" * 100)
            print("總結")
            print("=" * 100)
            
            print(f"1. 歷史總售出: {total_sales_twd:,.2f} TWD ({total_sales_rmb:,.2f} RMB)")
            print(f"2. 歷史總銷帳: {total_settlements:,.2f} TWD")
            print(f"3. 應收帳款（售出 - 銷帳）: {total_receivables_calculated:,.2f} TWD")
            print(f"4. 售出扣款 WITHDRAW 記錄: {total_withdraw_rmb:,.2f} RMB ({total_withdraw_count} 筆)")
            
            print(f"\n建議:")
            if total_withdraw_count > 0:
                print(f"  - 發現 {total_withdraw_count} 筆售出扣款 WITHDRAW 記錄（總額 {total_withdraw_rmb:,.2f} RMB）")
                print(f"  - 這些記錄是舊邏輯創建的，現在是重複的（售出記錄已包含扣款信息）")
                print(f"  - 可以執行 'flask cleanup-sales-withdraw --dry-run' 查看清理方案")
                if abs(total_withdraw_rmb - total_sales_rmb) > 0.01:
                    print(f"  - ⚠️  WITHDRAW 總額與總售出不一致，清理前請仔細確認")
            else:
                print(f"  - ✅ 沒有發現售出扣款 WITHDRAW 記錄，數據乾淨")
            
            if discrepancy > 0.01:
                print(f"  - ⚠️  應收帳款計算與資料庫不一致（差異 {discrepancy:,.2f} TWD）")
                print(f"  - 建議執行 'flask rebuild-customer-ar' 重建應收帳款")
            
        except Exception as e:
            print(f"\n❌ 驗證失敗: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == "__main__":
    print("歷史總售出、歷史總銷帳和 WITHDRAW 記錄驗證工具")
    print("此工具會計算並驗證所有相關數據的一致性\n")
    
    exit_code = verify_sales_and_settlements()
    sys.exit(exit_code)

