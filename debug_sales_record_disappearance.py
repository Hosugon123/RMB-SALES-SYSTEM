#!/usr/bin/env python3
"""
診斷SalesRecord消失問題的腳本
"""

import sqlite3
import sys
from datetime import datetime

def connect_db():
    """連接資料庫"""
    try:
        # 使用正確的資料庫文件
        conn = sqlite3.connect('instance/sales_system_v4.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")
        return None

def check_sales_records(conn):
    """檢查SalesRecord表的所有記錄"""
    cursor = conn.cursor()
    
    print("🔍 檢查SalesRecord表的所有記錄:")
    cursor.execute("""
        SELECT id, customer_id, rmb_account_id, rmb_amount, twd_amount, 
               is_settled, created_at, operator_id
        FROM sales_records 
        ORDER BY id DESC
        LIMIT 20
    """)
    
    records = cursor.fetchall()
    print(f"📊 總共找到 {len(records)} 筆SalesRecord記錄:")
    
    for record in records:
        print(f"  - ID: {record['id']}, 客戶ID: {record['customer_id']}, "
              f"RMB: {record['rmb_amount']}, 時間: {record['created_at']}")
    
    return records

def check_recent_activity(conn):
    """檢查最近的活動"""
    cursor = conn.cursor()
    
    print("\n🔍 檢查最近的資料庫活動:")
    
    # 檢查是否有刪除審計記錄
    cursor.execute("""
        SELECT table_name, record_id, operation_type, deleted_at, operator_name
        FROM delete_audit_logs 
        WHERE table_name = 'sales_records'
        ORDER BY deleted_at DESC
        LIMIT 10
    """)
    
    deletions = cursor.fetchall()
    if deletions:
        print(f"📋 找到 {len(deletions)} 筆SalesRecord刪除記錄:")
        for del_record in deletions:
            print(f"  - 刪除ID: {del_record['record_id']}, "
                  f"操作: {del_record['operation_type']}, "
                  f"時間: {del_record['deleted_at']}, "
                  f"操作者: {del_record['operator_name']}")
    else:
        print("✅ 沒有找到SalesRecord刪除記錄")
    
    # 檢查FIFO分配記錄
    cursor.execute("""
        SELECT fsa.id, fsa.sales_record_id, fsa.allocated_rmb, fsa.allocation_date
        FROM fifo_sales_allocations fsa
        ORDER BY fsa.allocation_date DESC
        LIMIT 10
    """)
    
    allocations = cursor.fetchall()
    if allocations:
        print(f"\n📋 找到 {len(allocations)} 筆FIFO分配記錄:")
        for alloc in allocations:
            print(f"  - 分配ID: {alloc['id']}, 銷售記錄ID: {alloc['sales_record_id']}, "
                  f"分配RMB: {alloc['allocated_rmb']}, 時間: {alloc['allocation_date']}")
    else:
        print("\n✅ 沒有找到FIFO分配記錄")

def check_foreign_key_constraints(conn):
    """檢查外鍵約束"""
    cursor = conn.cursor()
    
    print("\n🔍 檢查外鍵約束:")
    
    # 檢查SalesRecord的外鍵
    cursor.execute("PRAGMA foreign_key_list(sales_records)")
    fk_list = cursor.fetchall()
    
    if fk_list:
        print("📋 SalesRecord表的外鍵約束:")
        for fk in fk_list:
            print(f"  - 欄位: {fk[3]}, 參考表: {fk[2]}, 參考欄位: {fk[4]}")
    else:
        print("✅ SalesRecord表沒有外鍵約束")

def check_database_integrity(conn):
    """檢查資料庫完整性"""
    cursor = conn.cursor()
    
    print("\n🔍 檢查資料庫完整性:")
    
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()
    
    if result[0] == 'ok':
        print("✅ 資料庫完整性檢查通過")
    else:
        print(f"❌ 資料庫完整性檢查失敗: {result[0]}")

def check_recent_sales_with_details(conn):
    """檢查最近的銷售記錄詳情"""
    cursor = conn.cursor()
    
    print("\n🔍 檢查最近的銷售記錄詳情:")
    
    cursor.execute("""
        SELECT sr.id, sr.customer_id, sr.rmb_account_id, sr.rmb_amount, 
               sr.twd_amount, sr.is_settled, sr.created_at, sr.operator_id,
               c.name as customer_name, ca.name as account_name
        FROM sales_records sr
        LEFT JOIN customers c ON sr.customer_id = c.id
        LEFT JOIN cash_accounts ca ON sr.rmb_account_id = ca.id
        ORDER BY sr.id DESC
        LIMIT 10
    """)
    
    records = cursor.fetchall()
    print(f"📊 最近10筆銷售記錄詳情:")
    
    for record in records:
        print(f"  - ID: {record['id']}")
        print(f"    客戶: {record['customer_name']} (ID: {record['customer_id']})")
        print(f"    帳戶: {record['account_name']} (ID: {record['rmb_account_id']})")
        print(f"    RMB: {record['rmb_amount']}, TWD: {record['twd_amount']}")
        print(f"    已結清: {record['is_settled']}, 時間: {record['created_at']}")
        print(f"    操作者: {record['operator_id']}")
        print()

def main():
    """主函數"""
    print("🚀 開始診斷SalesRecord消失問題...")
    print(f"⏰ 診斷時間: {datetime.now()}")
    
    conn = connect_db()
    if not conn:
        sys.exit(1)
    
    try:
        # 檢查SalesRecord記錄
        records = check_sales_records(conn)
        
        # 檢查最近活動
        check_recent_activity(conn)
        
        # 檢查外鍵約束
        check_foreign_key_constraints(conn)
        
        # 檢查資料庫完整性
        check_database_integrity(conn)
        
        # 檢查最近銷售記錄詳情
        check_recent_sales_with_details(conn)
        
        print("\n🎯 診斷完成！")
        
        # 分析結果
        if len(records) == 0:
            print("❌ 沒有找到任何SalesRecord記錄！")
        elif len(records) < 10:
            print(f"⚠️ 只找到 {len(records)} 筆記錄，可能確實有記錄被刪除")
        else:
            print("✅ SalesRecord記錄看起來正常")
            
    except Exception as e:
        print(f"❌ 診斷過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
