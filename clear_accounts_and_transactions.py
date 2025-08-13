#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空帳戶金額和交易紀錄腳本
保留帳戶結構和持有人信息，只清空金額和交易數據
"""

import sqlite3
import os
import sys

def clear_accounts_and_transactions():
    """清空帳戶金額和交易紀錄"""
    
    # 嘗試多個可能的數據庫路徑
    db_paths = [
        'sales_system_v4.db',
        'instance/sales_system_v4.db',
        '../instance/sales_system_v4.db',
        '../../instance/sales_system_v4.db'
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ 找不到數據庫文件")
        print("嘗試的路徑:")
        for path in db_paths:
            print(f"  - {path}")
        print(f"當前工作目錄: {os.getcwd()}")
        return False
    
    print(f"✅ 找到數據庫: {db_path}")
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查數據庫表結構...")
        
        # 檢查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"發現的表: {tables}")
        
        # 清空帳戶金額
        print("\n💰 清空帳戶金額...")
        cursor.execute("UPDATE cash_accounts SET balance = 0")
        accounts_updated = cursor.rowcount
        print(f"✅ 已清空 {accounts_updated} 個帳戶的金額")
        
        # 清空交易相關記錄
        print("\n📝 清空交易紀錄...")
        
        # 清空FIFO銷售分配
        cursor.execute("DELETE FROM fifo_sales_allocations")
        fifo_sales_deleted = cursor.rowcount
        print(f"✅ 已清空 {fifo_sales_deleted} 條FIFO銷售分配記錄")
        
        # 清空FIFO庫存
        cursor.execute("DELETE FROM fifo_inventory")
        fifo_inventory_deleted = cursor.rowcount
        print(f"✅ 已清空 {fifo_inventory_deleted} 條FIFO庫存記錄")
        
        # 清空銷售記錄
        cursor.execute("DELETE FROM sales_records")
        sales_deleted = cursor.rowcount
        print(f"✅ 已清空 {sales_deleted} 條銷售記錄")
        
        # 清空買入記錄
        cursor.execute("DELETE FROM purchase_records")
        purchases_deleted = cursor.rowcount
        print(f"✅ 已清空 {purchases_deleted} 條買入記錄")
        
        # 清空刷卡記錄
        cursor.execute("DELETE FROM card_purchases")
        card_purchases_deleted = cursor.rowcount
        print(f"✅ 已清空 {card_purchases_deleted} 條刷卡記錄")
        
        # 清空記帳記錄
        cursor.execute("DELETE FROM ledger_entries")
        ledger_deleted = cursor.rowcount
        print(f"✅ 已清空 {ledger_deleted} 條記帳記錄")
        
        # 清空現金日誌
        cursor.execute("DELETE FROM cash_logs")
        cash_logs_deleted = cursor.rowcount
        print(f"✅ 已清空 {cash_logs_deleted} 條現金日誌")
        
        # 重置自增ID
        print("\n🔄 重置自增ID...")
        tables_to_reset = [
            'fifo_sales_allocations',
            'fifo_inventory', 
            'sales_records',
            'purchase_records',
            'card_purchases',
            'ledger_entries',
            'cash_logs'
        ]
        
        for table in tables_to_reset:
            try:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                print(f"✅ 已重置 {table} 的自增ID")
            except sqlite3.OperationalError:
                print(f"⚠️  {table} 沒有自增ID或表不存在")
        
        # 提交更改
        conn.commit()
        
        print("\n🎉 清空完成！")
        print(f"總共清空了:")
        print(f"  - 帳戶金額: {accounts_updated} 個")
        print(f"  - FIFO銷售分配: {fifo_sales_deleted} 條")
        print(f"  - FIFO庫存: {fifo_inventory_deleted} 條")
        print(f"  - 銷售記錄: {sales_deleted} 條")
        print(f"  - 買入記錄: {purchases_deleted} 條")
        print(f"  - 刷卡記錄: {card_purchases_deleted} 條")
        print(f"  - 記帳記錄: {ledger_deleted} 條")
        print(f"  - 現金日誌: {cash_logs_deleted} 條")
        
        # 驗證清空結果
        print("\n🔍 驗證清空結果...")
        cursor.execute("SELECT COUNT(*) FROM cash_accounts WHERE balance != 0")
        non_zero_accounts = cursor.fetchone()[0]
        print(f"非零餘額帳戶數量: {non_zero_accounts}")
        
        cursor.execute("SELECT COUNT(*) FROM sales_records")
        remaining_sales = cursor.fetchone()[0]
        print(f"剩餘銷售記錄: {remaining_sales}")
        
        cursor.execute("SELECT COUNT(*) FROM purchase_records")
        remaining_purchases = cursor.fetchone()[0]
        print(f"剩餘買入記錄: {remaining_purchases}")
        
        cursor.execute("SELECT COUNT(*) FROM ledger_entries")
        remaining_ledger = cursor.fetchone()[0]
        print(f"剩餘記帳記錄: {remaining_ledger}")
        
        cursor.execute("SELECT COUNT(*) FROM cash_logs")
        remaining_cash_logs = cursor.fetchone()[0]
        print(f"剩餘現金日誌: {remaining_cash_logs}")
        
        if non_zero_accounts == 0 and remaining_sales == 0 and remaining_purchases == 0 and remaining_ledger == 0 and remaining_cash_logs == 0:
            print("✅ 所有數據已成功清空！")
        else:
            print("⚠️  部分數據可能未完全清空")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 數據庫操作錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 發生未知錯誤: {e}")
        return False

if __name__ == "__main__":
    print("🧹 開始清空帳戶金額和交易紀錄...")
    print("=" * 50)
    
    success = clear_accounts_and_transactions()
    
    print("=" * 50)
    if success:
        print("🎯 清空操作完成！")
    else:
        print("💥 清空操作失敗！")
    
    input("\n按 Enter 鍵退出...")


