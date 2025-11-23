#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證資料庫同步狀態
檢查本地資料庫是否有資料
"""

import os
import sys

# 確保能夠導入 app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_local_database():
    """驗證本地資料庫內容"""
    print("=" * 80)
    print("驗證本地資料庫同步狀態")
    print("=" * 80)
    
    # 檢查資料庫檔案
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, "instance")
    local_db_path = os.path.join(instance_path, "sales_system_v4.db")
    
    print(f"\n資料庫檔案路徑: {local_db_path}")
    
    if not os.path.exists(local_db_path):
        print("❌ 資料庫檔案不存在！")
        print("   請先執行 pull_deployment_db_simple.py 下拉資料")
        return False
    
    file_size = os.path.getsize(local_db_path)
    print(f"資料庫檔案大小: {file_size:,} 位元組")
    
    if file_size < 1000:
        print("⚠️  資料庫檔案很小，可能沒有資料")
    
    # 檢查環境變數
    print(f"\n環境變數檢查:")
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        print(f"  DATABASE_URL: {db_url[:60]}...")
        print("  ⚠️  警告：檢測到 DATABASE_URL 環境變數")
        print("     應用程式可能連接到部署端資料庫，而不是本地資料庫")
        print("     請移除 DATABASE_URL 環境變數以使用本地資料庫")
    else:
        print("  DATABASE_URL: 未設置（將使用本地 SQLite）✓")
    
    # 連接本地資料庫並檢查資料
    print(f"\n連接本地資料庫...")
    
    # 確保不使用部署端資料庫
    if 'DATABASE_URL' in os.environ:
        original_db_url = os.environ.get('DATABASE_URL')
        del os.environ['DATABASE_URL']
    else:
        original_db_url = None
    
    try:
        # 重新導入 app 以使用本地配置
        if 'app' in sys.modules:
            import importlib
            importlib.reload(sys.modules['app'])
        
        from app import app, db
        
        with app.app_context():
            from app import (
                User, Holder, CashAccount, Channel, Customer,
                PurchaseRecord, SalesRecord, LedgerEntry, CashLog,
                FIFOInventory, FIFOSalesAllocation, Transaction
            )
            
            print("\n資料統計:")
            print("-" * 80)
            
            # 檢查各表的記錄數
            tables = {
                "Users": User,
                "Holders": Holder,
                "Channels": Channel,
                "CashAccounts": CashAccount,
                "Customers": Customer,
                "PurchaseRecords": PurchaseRecord,
                "SalesRecords": SalesRecord,
                "LedgerEntries": LedgerEntry,
                "CashLogs": CashLog,
                "Transactions": Transaction,
                "FIFOInventory": FIFOInventory,
                "FIFOSalesAllocation": FIFOSalesAllocation,
            }
            
            total_records = 0
            for table_name, model_class in tables.items():
                try:
                    count = db.session.execute(db.select(model_class)).scalars().count()
                    total_records += count
                    status = "✓" if count > 0 else "✗"
                    print(f"  {status} {table_name:25s}: {count:6d} 筆")
                except Exception as e:
                    print(f"  ✗ {table_name:25s}: 錯誤 - {e}")
            
            print("-" * 80)
            print(f"  總記錄數: {total_records:,} 筆")
            
            # 檢查現金帳戶餘額
            print("\n現金帳戶餘額:")
            print("-" * 80)
            try:
                accounts = db.session.execute(db.select(CashAccount)).scalars().all()
                if accounts:
                    total_balance = 0
                    total_profit = 0
                    for account in accounts:
                        if account.currency == 'TWD':
                            total_balance += account.balance
                            total_profit += account.profit_balance
                        print(f"  {account.name:20s} ({account.currency:3s}): 餘額 {account.balance:15,.2f}, 利潤 {account.profit_balance:15,.2f}")
                    
                    if total_balance > 0 or total_profit > 0:
                        print(f"\n  台幣總餘額: NT$ {total_balance:,.2f}")
                        print(f"  台幣總利潤: NT$ {total_profit:,.2f}")
                    else:
                        print("\n  ⚠️  所有帳戶餘額為 0")
                else:
                    print("  ⚠️  沒有現金帳戶")
            except Exception as e:
                print(f"  ✗ 讀取帳戶失敗: {e}")
            
            # 檢查客戶應收帳款
            print("\n客戶應收帳款:")
            print("-" * 80)
            try:
                customers = db.session.execute(db.select(Customer)).scalars().all()
                if customers:
                    total_receivables = 0
                    for customer in customers:
                        if customer.total_receivables_twd > 0:
                            print(f"  {customer.name:20s}: NT$ {customer.total_receivables_twd:15,.2f}")
                            total_receivables += customer.total_receivables_twd
                    
                    if total_receivables > 0:
                        print(f"\n  總應收帳款: NT$ {total_receivables:,.2f}")
                    else:
                        print("  ⚠️  所有客戶應收帳款為 0")
                else:
                    print("  ⚠️  沒有客戶")
            except Exception as e:
                print(f"  ✗ 讀取客戶失敗: {e}")
            
            # 總結
            print("\n" + "=" * 80)
            if total_records == 0:
                print("❌ 資料庫為空！")
                print("   請執行 pull_deployment_db_simple.py 下拉資料")
                return False
            elif db_url:
                print("⚠️  資料庫有資料，但應用程式可能連接到部署端資料庫")
                print("   請移除 DATABASE_URL 環境變數後重啟應用程式")
                return False
            else:
                print("✓ 資料庫有資料，且應用程式應該使用本地資料庫")
                return True
                
    except Exception as e:
        print(f"\n❌ 驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 恢復環境變數
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url

if __name__ == "__main__":
    verify_local_database()

