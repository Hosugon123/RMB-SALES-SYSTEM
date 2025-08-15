#!/usr/bin/env python3
"""
修復客戶數據問題
移除誤植到 Holder 表中的客戶數據
"""

import sys
import os
from datetime import datetime

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_customer_data():
    """修復客戶數據"""
    try:
        from app import app, db, Customer, Holder, SalesRecord
        
        with app.app_context():
            print("🔧 開始修復客戶數據...")
            print("=" * 50)
            
            # 1. 檢查當前狀態
            customers = Customer.query.all()
            holders = Holder.query.all()
            
            print(f"📊 當前狀態:")
            print(f"   Customer 表: {len(customers)} 條記錄")
            print(f"   Holder 表: {len(holders)} 條記錄")
            
            # 2. 查找可能誤植的客戶數據
            # 查找沒有現金帳戶的持有人（可能是客戶）
            misplaced_customers = []
            for holder in holders:
                # 如果持有人沒有現金帳戶，可能是誤植的客戶
                if not holder.cash_accounts:
                    # 檢查是否已經在 Customer 表中存在
                    existing_customer = Customer.query.filter_by(name=holder.name).first()
                    if not existing_customer:
                        misplaced_customers.append(holder)
            
            print(f"\n🔍 發現 {len(misplaced_customers)} 個可能誤植的客戶:")
            for holder in misplaced_customers:
                print(f"   - {holder.name} (Holder ID: {holder.id})")
            
            # 3. 移動誤植的客戶到正確的表
            if misplaced_customers:
                print(f"\n🔄 開始移動誤植的客戶...")
                
                for holder in misplaced_customers:
                    # 創建正確的客戶記錄
                    new_customer = Customer(
                        name=holder.name,
                        is_active=holder.is_active,
                        total_receivables_twd=0.0
                    )
                    db.session.add(new_customer)
                    db.session.flush()  # 獲取新的ID
                    
                    print(f"   ✅ 創建客戶: {new_customer.name} (Customer ID: {new_customer.id})")
                    
                    # 更新相關的銷售記錄（如果有）
                    # 注意：這裡需要小心，因為 SalesRecord 使用 customer_id 而不是 holder_id
                    # 如果之前有錯誤的關聯，需要手動修復
                    
                    # 刪除誤植的持有人記錄
                    db.session.delete(holder)
                    print(f"   🗑️  刪除誤植的持有人: {holder.name} (Holder ID: {holder.id})")
                
                db.session.commit()
                print(f"   💾 已提交更改")
            else:
                print(f"\n✅ 沒有發現誤植的客戶數據")
            
            # 4. 顯示修復後的狀態
            customers_after = Customer.query.all()
            holders_after = Holder.query.all()
            
            print(f"\n📊 修復後狀態:")
            print(f"   Customer 表: {len(customers_after)} 條記錄")
            print(f"   Holder 表: {len(holders_after)} 條記錄")
            
            print(f"\n📋 Customer 表詳細:")
            for customer in customers_after:
                print(f"   - {customer.name} (ID: {customer.id})")
            
            print(f"\n📋 Holder 表詳細:")
            for holder in holders_after:
                account_count = len(holder.cash_accounts) if holder.cash_accounts else 0
                print(f"   - {holder.name} (ID: {holder.id}, 帳戶數: {account_count})")
            
            print("=" * 50)
            print("🎉 客戶數據修復完成！")
            
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_customer_data()
