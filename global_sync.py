#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局數據同步函數 - 每次數據更新後重新整理整個資料庫
"""

from sqlalchemy import text

def sync_entire_database(db_session):
    """
    同步整個資料庫 - 重新整理所有數據
    每次數據更新後調用此函數
    """
    try:
        print("🔄 開始全局數據同步...")
        
        # 1. 重新計算所有帳戶餘額（從流水記錄）
        db_session.execute(text("""
            UPDATE cash_accounts 
            SET balance = (
                SELECT COALESCE(SUM(
                    CASE 
                        WHEN currency = 'TWD' THEN twd_change
                        WHEN currency = 'RMB' THEN rmb_change
                        ELSE 0
                    END
                ), 0)
                FROM ledger_entries 
                WHERE account_id = cash_accounts.id
            )
            WHERE is_active = 1
        """))
        
        # 2. 重新計算應收帳款（從銷售記錄）
        db_session.execute(text("""
            UPDATE customers 
            SET total_receivables_twd = (
                SELECT COALESCE(SUM(twd_amount), 0)
                FROM sales_records 
                WHERE customer_id = customers.id 
                AND status = 'pending'
            )
            WHERE is_active = 1
        """))
        
        # 3. 檢查並修復庫存一致性
        # 清理孤立的庫存記錄
        db_session.execute(text("""
            DELETE FROM fifo_inventory 
            WHERE purchase_record_id NOT IN (SELECT id FROM purchase_records)
        """))
        
        # 清理破損的庫存分配記錄
        db_session.execute(text("""
            DELETE FROM fifo_sales_allocations 
            WHERE fifo_inventory_id NOT IN (SELECT id FROM fifo_inventory)
            OR sales_record_id NOT IN (SELECT id FROM sales_records)
        """))
        
        # 4. 重置負餘額帳戶為0
        db_session.execute(text("""
            UPDATE cash_accounts 
            SET balance = 0 
            WHERE balance < 0 AND is_active = 1
        """))
        
        # 提交所有更改
        db_session.commit()
        
        print("✅ 全局數據同步完成")
        return True
        
    except Exception as e:
        print(f"❌ 全局數據同步失敗: {e}")
        db_session.rollback()
        return False

def quick_sync(db_session):
    """
    快速同步 - 只同步關鍵數據
    用於頻繁的數據更新
    """
    try:
        print("🔄 快速數據同步...")
        
        # 只同步帳戶餘額和應收帳款
        db_session.execute(text("""
            UPDATE cash_accounts 
            SET balance = (
                SELECT COALESCE(SUM(
                    CASE 
                        WHEN currency = 'TWD' THEN twd_change
                        WHEN currency = 'RMB' THEN rmb_change
                        ELSE 0
                    END
                ), 0)
                FROM ledger_entries 
                WHERE account_id = cash_accounts.id
            )
            WHERE is_active = 1
        """))
        
        db_session.execute(text("""
            UPDATE customers 
            SET total_receivables_twd = (
                SELECT COALESCE(SUM(twd_amount), 0)
                FROM sales_records 
                WHERE customer_id = customers.id 
                AND status = 'pending'
            )
            WHERE is_active = 1
        """))
        
        db_session.commit()
        print("✅ 快速數據同步完成")
        return True
        
    except Exception as e:
        print(f"❌ 快速數據同步失敗: {e}")
        db_session.rollback()
        return False
