"""
修復買入記錄錯誤刪除的回滾問題

此腳本用於修復線上系統中已經執行過錯誤刪除操作的買入記錄。
錯誤的刪除操作沒有正確回滾帳戶餘額，導致：
- RMB帳戶餘額正常（因為沒有扣除）
- 台幣帳戶餘額錯誤（應該回補但沒有回補）

修復方案：
1. 比對備份資料庫，找出被刪除的買入記錄
2. 計算這些記錄應該回滾的台幣金額
3. 手動修正台幣帳戶餘額
"""

import sqlite3
import os
from datetime import datetime
import json


def connect_db(db_path):
    """連接資料庫"""
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫: {db_path}")
        return None
    return sqlite3.connect(db_path)


def get_purchase_records(conn):
    """獲取所有買入記錄"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, payment_account_id, deposit_account_id, 
               rmb_amount, exchange_rate, twd_cost, created_at
        FROM purchase_records
        ORDER BY id
    """)
    records = cursor.fetchall()
    return {r[0]: {
        'id': r[0],
        'payment_account_id': r[1],
        'deposit_account_id': r[2],
        'rmb_amount': r[3],
        'exchange_rate': r[4],
        'twd_cost': r[5],
        'created_at': r[6]
    } for r in records}


def get_cash_accounts(conn):
    """獲取所有帳戶"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, currency, balance, holder_id
        FROM cash_accounts
        ORDER BY id
    """)
    records = cursor.fetchall()
    return {r[0]: {
        'id': r[0],
        'name': r[1],
        'currency': r[2],
        'balance': r[3],
        'holder_id': r[4]
    } for r in records}


def analyze_deletion_impact(backup_purchases, current_purchases, backup_accounts, current_accounts):
    """分析刪除操作的影響"""
    deleted_purchases = []
    
    # 找出被刪除的買入記錄
    for purchase_id, purchase_data in backup_purchases.items():
        if purchase_id not in current_purchases:
            # 檢查是否為正常買入記錄（非純利潤庫存）
            if (purchase_data['payment_account_id'] is not None and 
                purchase_data['twd_cost'] > 0):
                deleted_purchases.append(purchase_data)
    
    if not deleted_purchases:
        print("✅ 沒有發現被錯誤刪除的正常買入記錄")
        return None
    
    print(f"\n🔍 發現 {len(deleted_purchases)} 筆被刪除的正常買入記錄：")
    print("=" * 80)
    
    # 計算需要修正的金額
    account_adjustments = {}  # account_id -> adjustment_amount
    
    for purchase in deleted_purchases:
        payment_account_id = purchase['payment_account_id']
        payment_account = backup_accounts.get(payment_account_id)
        
        if payment_account and payment_account['currency'] == 'TWD':
            print(f"\n記錄 ID: {purchase['id']}")
            print(f"  付款帳戶: {payment_account['name']} (ID: {payment_account_id})")
            print(f"  RMB金額: ¥{purchase['rmb_amount']:,.2f}")
            print(f"  台幣成本: ${purchase['twd_cost']:,.2f}")
            print(f"  匯率: {purchase['exchange_rate']:.4f}")
            print(f"  創建時間: {purchase['created_at']}")
            print(f"  ⚠️ 應該回補但沒有回補的台幣: ${purchase['twd_cost']:,.2f}")
            
            # 累計需要調整的金額
            if payment_account_id not in account_adjustments:
                account_adjustments[payment_account_id] = {
                    'account_name': payment_account['name'],
                    'currency': payment_account['currency'],
                    'total_adjustment': 0,
                    'records': []
                }
            
            account_adjustments[payment_account_id]['total_adjustment'] += purchase['twd_cost']
            account_adjustments[payment_account_id]['records'].append({
                'purchase_id': purchase['id'],
                'rmb_amount': purchase['rmb_amount'],
                'twd_cost': purchase['twd_cost'],
                'created_at': purchase['created_at']
            })
    
    print("\n" + "=" * 80)
    print("\n📊 需要修正的帳戶匯總：")
    print("=" * 80)
    
    for account_id, adjustment_data in account_adjustments.items():
        current_account = current_accounts.get(account_id)
        if current_account:
            print(f"\n帳戶: {adjustment_data['account_name']} (ID: {account_id})")
            print(f"  幣別: {adjustment_data['currency']}")
            print(f"  當前餘額: ${current_account['balance']:,.2f}")
            print(f"  需要增加: ${adjustment_data['total_adjustment']:,.2f}")
            print(f"  修正後餘額: ${current_account['balance'] + adjustment_data['total_adjustment']:,.2f}")
            print(f"  涉及記錄數: {len(adjustment_data['records'])} 筆")
    
    return account_adjustments


def generate_fix_sql(account_adjustments, current_accounts):
    """生成修復SQL語句"""
    if not account_adjustments:
        return []
    
    sql_statements = []
    sql_statements.append("-- 修復買入記錄錯誤刪除的回滾問題")
    sql_statements.append(f"-- 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_statements.append("-- 請在執行前備份資料庫！")
    sql_statements.append("")
    sql_statements.append("BEGIN TRANSACTION;")
    sql_statements.append("")
    
    for account_id, adjustment_data in account_adjustments.items():
        current_account = current_accounts.get(account_id)
        if current_account:
            new_balance = current_account['balance'] + adjustment_data['total_adjustment']
            sql_statements.append(
                f"-- 修正帳戶: {adjustment_data['account_name']} "
                f"(當前: ${current_account['balance']:,.2f} -> 修正後: ${new_balance:,.2f})"
            )
            sql_statements.append(
                f"UPDATE cash_accounts SET balance = {new_balance:.2f} WHERE id = {account_id};"
            )
            sql_statements.append("")
    
    sql_statements.append("COMMIT;")
    sql_statements.append("")
    sql_statements.append("-- 執行完成後，請驗證帳戶餘額是否正確")
    
    return sql_statements


def main():
    """主程序"""
    print("=" * 80)
    print("買入記錄錯誤刪除回滾修復工具")
    print("=" * 80)
    print()
    
    # 請用戶指定備份檔案和當前資料庫
    print("請提供以下資訊：")
    print()
    
    backup_db_path = input("1. 備份資料庫路徑 (例: ./backups/sales_system_backup_20250109.db): ").strip()
    if not backup_db_path:
        print("❌ 必須提供備份資料庫路徑")
        return
    
    current_db_path = input("2. 當前資料庫路徑 (預設: ./instance/sales_system.db): ").strip()
    if not current_db_path:
        current_db_path = "./instance/sales_system.db"
    
    print()
    print("=" * 80)
    print("開始分析...")
    print("=" * 80)
    
    # 連接資料庫
    backup_conn = connect_db(backup_db_path)
    if not backup_conn:
        return
    
    current_conn = connect_db(current_db_path)
    if not current_conn:
        backup_conn.close()
        return
    
    try:
        # 獲取資料
        print("\n📥 讀取備份資料庫...")
        backup_purchases = get_purchase_records(backup_conn)
        backup_accounts = get_cash_accounts(backup_conn)
        print(f"   找到 {len(backup_purchases)} 筆買入記錄")
        
        print("\n📥 讀取當前資料庫...")
        current_purchases = get_purchase_records(current_conn)
        current_accounts = get_cash_accounts(current_conn)
        print(f"   找到 {len(current_purchases)} 筆買入記錄")
        
        # 分析刪除影響
        account_adjustments = analyze_deletion_impact(
            backup_purchases, current_purchases,
            backup_accounts, current_accounts
        )
        
        if not account_adjustments:
            print("\n✅ 沒有需要修復的資料")
            return
        
        # 生成修復SQL
        print("\n" + "=" * 80)
        print("生成修復SQL...")
        print("=" * 80)
        
        sql_statements = generate_fix_sql(account_adjustments, current_accounts)
        
        # 儲存SQL到檔案
        output_file = f"fix_purchase_deletion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_statements))
        
        print(f"\n✅ 修復SQL已儲存到: {output_file}")
        print("\n修復SQL內容：")
        print("-" * 80)
        print('\n'.join(sql_statements))
        print("-" * 80)
        
        # 儲存詳細報告
        report_file = f"fix_purchase_deletion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'backup_db': backup_db_path,
            'current_db': current_db_path,
            'account_adjustments': account_adjustments,
            'sql_file': output_file
        }
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 詳細報告已儲存到: {report_file}")
        
        print("\n" + "=" * 80)
        print("下一步操作：")
        print("=" * 80)
        print("1. 請仔細檢查生成的SQL檔案")
        print("2. 在執行前請先備份當前資料庫")
        print("3. 使用以下命令執行修復（在線上環境）：")
        print(f"   sqlite3 your_database.db < {output_file}")
        print("4. 或在Python中執行：")
        print("   from flask import Flask")
        print("   from app import db")
        print("   # 讀取SQL檔案並執行")
        print("\n⚠️ 重要提醒：")
        print("   - 此操作會直接修改帳戶餘額")
        print("   - 請在測試環境先驗證")
        print("   - 執行後請檢查帳戶餘額是否正確")
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        backup_conn.close()
        current_conn.close()


if __name__ == "__main__":
    main()


