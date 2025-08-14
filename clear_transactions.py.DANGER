#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理交易紀錄腳本
清空所有交易相關數據，但保留持有人和帳戶資訊
"""

import sqlite3
import os
from datetime import datetime

def clear_transactions():
    """清空所有交易紀錄，保留持有人和帳戶資訊"""
    
    # 數據庫路徑
    db_path = "instance/sales_system_v4.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 數據庫文件不存在: {db_path}")
        return False
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 連接到數據庫成功")
        
        # 開始事務
        cursor.execute("BEGIN TRANSACTION")
        
        # 清空交易相關表（按依賴關係順序）
        tables_to_clear = [
            "fifo_sales_allocations",  # FIFO銷售分配
            "sales_records",           # 銷售記錄
            "purchase_records",        # 買入記錄
            "cash_logs",               # 現金日誌
            "ledger_entries",          # 記帳分錄
            "fifo_inventory",          # FIFO庫存
            "card_purchases",          # 刷卡記錄
        ]
        
        for table in tables_to_clear:
            try:
                # 檢查表是否存在
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    # 清空表數據
                    cursor.execute(f"DELETE FROM {table}")
                    affected_rows = cursor.rowcount
                    print(f"✅ 清空表 {table}: 刪除 {affected_rows} 條記錄")
                else:
                    print(f"⚠️  表 {table} 不存在，跳過")
            except Exception as e:
                print(f"❌ 清空表 {table} 失敗: {e}")
                continue
        
        # 重置自增ID
        print("\n🔄 重置自增ID...")
        for table in tables_to_clear:
            try:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                    print(f"✅ 重置表 {table} 的自增ID")
            except Exception as e:
                print(f"⚠️  重置表 {table} 自增ID失敗: {e}")
                continue
        
        # 清空客戶應收帳款
        print("\n💰 清空客戶應收帳款...")
        try:
            cursor.execute("UPDATE customers SET total_receivables_twd = 0.0")
            affected_rows = cursor.rowcount
            print(f"✅ 清空客戶應收帳款: 更新 {affected_rows} 條記錄")
        except Exception as e:
            print(f"❌ 清空客戶應收帳款失敗: {e}")
        
        # 提交事務
        conn.commit()
        print("\n✅ 所有交易紀錄清理完成！")
        
        # 顯示清理後的狀態
        print("\n📊 清理後的數據狀態:")
        
        # 檢查持有人和帳戶
        cursor.execute("SELECT COUNT(*) FROM holders")
        holders_count = cursor.fetchone()[0]
        print(f"   - 持有人數量: {holders_count}")
        
        cursor.execute("SELECT COUNT(*) FROM cash_accounts")
        accounts_count = cursor.fetchone()[0]
        print(f"   - 現金帳戶數量: {accounts_count}")
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        customers_count = cursor.fetchone()[0]
        print(f"   - 客戶數量: {customers_count}")
        
        # 檢查交易表是否為空
        for table in tables_to_clear:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   - {table}: {count} 條記錄")
            except:
                print(f"   - {table}: 表不存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 清理過程中發生錯誤: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()
            print("🔌 數據庫連接已關閉")

if __name__ == "__main__":
    print("🚀 開始清理交易紀錄...")
    print("=" * 50)
    
    # 確認操作
    confirm = input("⚠️  此操作將清空所有交易紀錄，確定繼續嗎？(y/N): ")
    
    if confirm.lower() in ['y', 'yes']:
        success = clear_transactions()
        if success:
            print("\n🎉 清理完成！系統已重置為初始狀態。")
        else:
            print("\n💥 清理失敗，請檢查錯誤信息。")
    else:
        print("❌ 操作已取消")
