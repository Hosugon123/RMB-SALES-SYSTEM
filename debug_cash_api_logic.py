#!/usr/bin/env python3
"""
直接測試現金管理API邏輯的腳本
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# 添加當前目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_app():
    """創建Flask應用程式實例"""
    app = Flask(__name__)
    
    # 資料庫配置
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/sales_system_v4.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app

def test_cash_api_logic():
    """測試現金管理API邏輯"""
    print("測試現金管理API邏輯")
    print("=" * 50)
    
    app = create_app()
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # 1. 查詢銷售記錄
            print("1. 查詢銷售記錄...")
            sales_query = text("""
                SELECT s.id, s.customer_id, s.rmb_account_id, s.twd_amount, s.rmb_amount, 
                       s.exchange_rate, s.is_settled, s.created_at,
                       c.name as customer_name, ca.name as rmb_account_name
                FROM sales_records s
                LEFT JOIN customers c ON s.customer_id = c.id
                LEFT JOIN cash_accounts ca ON s.rmb_account_id = ca.id
                ORDER BY s.created_at DESC
                LIMIT 10
            """)
            
            result = db.session.execute(sales_query).fetchall()
            print(f"   查詢到 {len(result)} 筆銷售記錄")
            
            if result:
                print("   前5筆銷售記錄:")
                for i, row in enumerate(result[:5]):
                    print(f"     {i+1}. ID: {row[0]}, 客戶: {row[8]}, RMB帳戶: {row[9]}, "
                          f"TWD: {row[3]}, RMB: {row[4]}, 已結算: {row[6]}")
            
            # 2. 模擬現金管理API的查詢邏輯
            print("\n2. 模擬現金管理API查詢...")
            
            # 查詢銷售記錄（模擬API中的查詢）
            from app import SalesRecord, Customer, CashAccount, User
            from sqlalchemy.orm import selectinload
            
            sales = db.session.execute(
                db.select(SalesRecord)
                .options(
                    selectinload(SalesRecord.customer),
                    selectinload(SalesRecord.rmb_account),
                    selectinload(SalesRecord.operator)
                )
                .order_by(SalesRecord.created_at.desc())
                .limit(20)
            ).scalars().all()
            
            print(f"   通過ORM查詢到 {len(sales)} 筆銷售記錄")
            
            if sales:
                print("   前5筆銷售記錄詳情:")
                for i, s in enumerate(sales[:5]):
                    print(f"     {i+1}. ID: {s.id}")
                    print(f"        客戶: {s.customer.name if s.customer else 'N/A'}")
                    print(f"        RMB帳戶: {s.rmb_account.name if s.rmb_account else 'N/A'}")
                    print(f"        操作者: {s.operator.username if s.operator else 'N/A'}")
                    print(f"        TWD: {s.twd_amount}, RMB: {s.rmb_amount}")
                    print(f"        已結算: {s.is_settled}")
                    print(f"        創建時間: {s.created_at}")
                    print()
            
            # 3. 檢查關聯數據是否正確載入
            print("3. 檢查關聯數據...")
            for i, s in enumerate(sales[:3]):
                print(f"   銷售記錄 {s.id}:")
                print(f"     客戶關聯: {hasattr(s, 'customer') and s.customer is not None}")
                print(f"     RMB帳戶關聯: {hasattr(s, 'rmb_account') and s.rmb_account is not None}")
                print(f"     操作者關聯: {hasattr(s, 'operator') and s.operator is not None}")
                
                if s.customer:
                    print(f"     客戶名稱: {s.customer.name}")
                if s.rmb_account:
                    print(f"     RMB帳戶名稱: {s.rmb_account.name}")
                if s.operator:
                    print(f"     操作者名稱: {s.operator.username}")
                print()
            
            # 4. 模擬銷售記錄處理邏輯
            print("4. 模擬銷售記錄處理...")
            unified_stream = []
            
            for i, s in enumerate(sales[:3]):  # 只處理前3筆
                print(f"   處理銷售記錄 {i+1}: ID {s.id}")
                
                try:
                    # 基本屬性
                    sale_id = s.id
                    customer_name = s.customer.name if s.customer else "未知客戶"
                    rmb_account_name = s.rmb_account.name if s.rmb_account else "N/A"
                    operator_name = s.operator.username if s.operator else "未知"
                    created_at = s.created_at
                    rmb_amount = s.rmb_amount or 0
                    twd_amount = s.twd_amount or 0
                    
                    print(f"     基本屬性: 客戶={customer_name}, RMB帳戶={rmb_account_name}, 操作者={operator_name}")
                    
                    # 構建銷售記錄字典
                    sales_record = {
                        "type": "售出",
                        "date": created_at.isoformat() if created_at else "未知時間",
                        "description": f"售予 {customer_name}",
                        "twd_change": 0,
                        "rmb_change": round(-rmb_amount, 2),
                        "operator": operator_name,
                        "payment_account": rmb_account_name,
                        "deposit_account": "應收帳款",
                        "profit": 0,  # 簡化，不計算利潤
                        "note": None
                    }
                    
                    unified_stream.append(sales_record)
                    print(f"     [OK] 已添加到unified_stream")
                    
                except Exception as e:
                    print(f"     [ERROR] 處理失敗: {e}")
            
            print(f"\n5. 處理結果:")
            print(f"   unified_stream 長度: {len(unified_stream)}")
            
            if unified_stream:
                print("   成功處理的記錄:")
                for i, record in enumerate(unified_stream):
                    print(f"     {i+1}. {record['type']} - {record['description']} ({record['date']})")
            else:
                print("   [ERROR] 沒有成功處理任何記錄")
            
            # 6. 檢查可能導致問題的原因
            print("\n6. 問題診斷:")
            
            # 檢查是否有客戶關聯問題
            no_customer_count = sum(1 for s in sales if not s.customer)
            print(f"   沒有客戶關聯的記錄: {no_customer_count}")
            
            # 檢查是否有RMB帳戶關聯問題
            no_rmb_account_count = sum(1 for s in sales if not s.rmb_account)
            print(f"   沒有RMB帳戶關聯的記錄: {no_rmb_account_count}")
            
            # 檢查是否有操作者關聯問題
            no_operator_count = sum(1 for s in sales if not s.operator)
            print(f"   沒有操作者關聯的記錄: {no_operator_count}")
            
            if no_customer_count > 0:
                print("   [WARNING] 發現沒有客戶關聯的記錄，這可能導致記錄被跳過")
            
            if no_rmb_account_count > 0:
                print("   [WARNING] 發現沒有RMB帳戶關聯的記錄，這可能導致記錄被跳過")
            
            if no_operator_count > 0:
                print("   [WARNING] 發現沒有操作者關聯的記錄，這可能導致記錄被跳過")
            
    except Exception as e:
        print(f"[ERROR] 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cash_api_logic()
