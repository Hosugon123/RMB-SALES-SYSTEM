#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改進版：從 Render PostgreSQL 同步資料到本地 SQLite
功能：
1. 自動檢測環境變數或使用預設連接
2. 完整的錯誤處理和驗證
3. 備份本地資料庫
4. 清晰的進度顯示
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# 確保能夠導入 app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_database_url():
    """獲取線上資料庫連接字串"""
    # 優先從環境變數獲取
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("⚠️  未找到 DATABASE_URL 環境變數")
        print("\n請選擇資料來源：")
        print("1. 手動輸入 Render PostgreSQL 連接字串")
        print("2. 使用預設連接字串（需要密碼）")
        
        choice = input("\n請選擇 (1/2): ").strip()
        
        if choice == "1":
            db_url = input("請輸入 DATABASE_URL: ").strip()
        elif choice == "2":
            # 使用預設連接（需要更新密碼）
            db_url = input("請輸入 Render 資料庫密碼: ").strip()
            if db_url:
                db_url = f"postgresql+psycopg://rmb_user:{db_url}@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"
        else:
            print("❌ 無效的選擇")
            return None
    
    # 修復 URL 格式
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif db_url.startswith('postgresql://') and '+psycopg' not in db_url:
        db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    return db_url

def backup_local_database(local_db_path):
    """備份本地資料庫"""
    if not os.path.exists(local_db_path):
        print("ℹ️  本地資料庫不存在，無需備份")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(local_db_path).parent
    backup_name = f"sales_system_v4_backup_{timestamp}.db"
    backup_path = backup_dir / backup_name
    
    try:
        shutil.copy2(local_db_path, backup_path)
        print(f"✅ 本地資料庫已備份: {backup_path}")
        return str(backup_path)
    except Exception as e:
        print(f"⚠️  備份失敗: {e}")
        return None

def sync_database():
    """執行資料同步"""
    print("=" * 80)
    print("📥 從 Render PostgreSQL 同步到本地 SQLite")
    print("=" * 80)
    
    # 獲取資料庫連接
    online_db_url = get_database_url()
    if not online_db_url:
        return False
    
    print(f"\n✅ 已獲取線上資料庫連接")
    print(f"   連接字串: {online_db_url[:60]}...")
    
    try:
        # 準備本地資料庫路徑
        basedir = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(basedir, "instance")
        os.makedirs(instance_path, exist_ok=True)
        local_db_path = os.path.join(instance_path, "sales_system_v4.db")
        local_db_uri = f"sqlite:///{local_db_path}"
        
        # 備份本地資料庫
        print("\n" + "=" * 80)
        print("📦 備份本地資料庫...")
        print("=" * 80)
        backup_path = backup_local_database(local_db_path)
        
        # 步驟 1: 連接線上資料庫並讀取資料
        print("\n" + "=" * 80)
        print("[1/3] 從線上資料庫讀取資料...")
        print("=" * 80)
        
        # 設置環境變數以使用線上資料庫
        os.environ['DATABASE_URL'] = online_db_url
        
        # 重新導入 app 以使用線上配置
        if 'app' in sys.modules:
            import importlib
            importlib.reload(sys.modules['app'])
        
        from app import app, db
        
        # 確保使用線上資料庫
        app.config["SQLALCHEMY_DATABASE_URI"] = online_db_url
        
        # 在 app context 中讀取資料
        with app.app_context():
            from app import (
                User, Holder, CashAccount, Channel, Customer,
                PurchaseRecord, SalesRecord, LedgerEntry, CashLog,
                FIFOInventory, FIFOSalesAllocation, ProfitTransaction,
                PendingPayment, DeleteAuditLog
            )
            
            # 讀取所有資料表
            print("📖 正在讀取資料表...")
            
            try:
                users = db.session.execute(db.select(User)).scalars().all()
                holders = db.session.execute(db.select(Holder)).scalars().all()
                cash_accounts = db.session.execute(db.select(CashAccount)).scalars().all()
                channels = db.session.execute(db.select(Channel)).scalars().all()
                customers = db.session.execute(db.select(Customer)).scalars().all()
                purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
                sales = db.session.execute(db.select(SalesRecord)).scalars().all()
                ledger_entries = db.session.execute(db.select(LedgerEntry)).scalars().all()
                cash_logs = db.session.execute(db.select(CashLog)).scalars().all()
                fifo_inventory = db.session.execute(db.select(FIFOInventory)).scalars().all()
                fifo_sales = db.session.execute(db.select(FIFOSalesAllocation)).scalars().all()
                
                # 可選表（可能不存在）
                profit_transactions = []
                pending_payments = []
                delete_audit_logs = []
                
                try:
                    profit_transactions = db.session.execute(db.select(ProfitTransaction)).scalars().all()
                except:
                    print("⚠️  ProfitTransaction 表不存在，跳過")
                
                try:
                    pending_payments = db.session.execute(db.select(PendingPayment)).scalars().all()
                except:
                    print("⚠️  PendingPayment 表不存在，跳過")
                
                try:
                    delete_audit_logs = db.session.execute(db.select(DeleteAuditLog)).scalars().all()
                except:
                    print("⚠️  DeleteAuditLog 表不存在，跳過")
                
                print(f"\n✅ 讀取完成：")
                print(f"   Users: {len(users)}")
                print(f"   Holders: {len(holders)}")
                print(f"   CashAccounts: {len(cash_accounts)}")
                print(f"   Channels: {len(channels)}")
                print(f"   Customers: {len(customers)}")
                print(f"   PurchaseRecords: {len(purchases)}")
                print(f"   SalesRecords: {len(sales)}")
                print(f"   LedgerEntries: {len(ledger_entries)}")
                print(f"   CashLogs: {len(cash_logs)}")
                print(f"   FIFOInventory: {len(fifo_inventory)}")
                print(f"   FIFOSalesAllocation: {len(fifo_sales)}")
                if profit_transactions:
                    print(f"   ProfitTransactions: {len(profit_transactions)}")
                if pending_payments:
                    print(f"   PendingPayments: {len(pending_payments)}")
                if delete_audit_logs:
                    print(f"   DeleteAuditLogs: {len(delete_audit_logs)}")
                
            except Exception as e:
                print(f"❌ 讀取線上資料失敗: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # 步驟 2: 清空本地資料庫
        print("\n" + "=" * 80)
        print("[2/3] 清空本地資料庫...")
        print("=" * 80)
        
        # 移除環境變數，強制使用本地 SQLite
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        # 重新導入 app 以使用本地配置
        if 'app' in sys.modules:
            import importlib
            importlib.reload(sys.modules['app'])
        
        from app import app as local_app, db as local_db
        
        local_app.config["SQLALCHEMY_DATABASE_URI"] = local_db_uri
        
        with local_app.app_context():
            # 創建所有表
            local_db.create_all()
            print("✅ 本地資料庫表已準備完成")
            
            # 清空所有表（按外鍵順序）
            print("🗑️  正在清空資料表...")
            try:
                tables = [
                    'profit_transactions', 'fifo_sales_allocation', 'fifo_inventory',
                    'cash_logs', 'ledger_entries', 'sales_records', 'purchase_records',
                    'customers', 'channels', 'cash_accounts', 'holders', 'users'
                ]
                
                for table in tables:
                    try:
                        local_db.session.execute(local_db.text(f'DELETE FROM {table}'))
                        print(f"   ✅ 已清空 {table}")
                    except Exception as e:
                        print(f"   ⚠️  清空 {table} 時出現錯誤（可能不存在）: {e}")
                
                local_db.session.commit()
                print("✅ 本地資料庫已清空")
                
            except Exception as e:
                print(f"⚠️  清空資料庫時出現錯誤: {e}")
                local_db.session.rollback()
        
        # 步驟 3: 寫入資料到本地
        print("\n" + "=" * 80)
        print("[3/3] 寫入資料到本地資料庫...")
        print("=" * 80)
        
        # 重新設置為線上資料庫以讀取資料
        os.environ['DATABASE_URL'] = online_db_url
        
        # 重新導入
        if 'app' in sys.modules:
            import importlib
            importlib.reload(sys.modules['app'])
        
        from app import app, db
        
        app.config["SQLALCHEMY_DATABASE_URI"] = online_db_url
        
        with app.app_context():
            from app import (
                User as UserOnline, Holder as HolderOnline, CashAccount as CashAccountOnline,
                Channel as ChannelOnline, Customer as CustomerOnline,
                PurchaseRecord as PurchaseRecordOnline, SalesRecord as SalesRecordOnline,
                LedgerEntry as LedgerEntryOnline, CashLog as CashLogOnline,
                FIFOInventory as FIFOInventoryOnline, FIFOSalesAllocation as FIFOSalesAllocationOnline
            )
            
            # 重新讀取資料（使用線上連接）
            users = db.session.execute(db.select(UserOnline)).scalars().all()
            holders = db.session.execute(db.select(HolderOnline)).scalars().all()
            cash_accounts = db.session.execute(db.select(CashAccountOnline)).scalars().all()
            channels = db.session.execute(db.select(ChannelOnline)).scalars().all()
            customers = db.session.execute(db.select(CustomerOnline)).scalars().all()
            purchases = db.session.execute(db.select(PurchaseRecordOnline)).scalars().all()
            sales = db.session.execute(db.select(SalesRecordOnline)).scalars().all()
            ledger_entries = db.session.execute(db.select(LedgerEntryOnline)).scalars().all()
            cash_logs = db.session.execute(db.select(CashLogOnline)).scalars().all()
            fifo_inventory = db.session.execute(db.select(FIFOInventoryOnline)).scalars().all()
            fifo_sales = db.session.execute(db.select(FIFOSalesAllocationOnline)).scalars().all()
        
        # 切換回本地資料庫
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        if 'app' in sys.modules:
            import importlib
            importlib.reload(sys.modules['app'])
        
        from app import app as local_app, db as local_db
        
        local_app.config["SQLALCHEMY_DATABASE_URI"] = local_db_uri
        
        with local_app.app_context():
            from app import (
                User as UserLocal, Holder as HolderLocal, CashAccount as CashAccountLocal,
                Channel as ChannelLocal, Customer as CustomerLocal,
                PurchaseRecord as PurchaseRecordLocal, SalesRecord as SalesRecordLocal,
                LedgerEntry as LedgerEntryLocal, CashLog as CashLogLocal,
                FIFOInventory as FIFOInventoryLocal, FIFOSalesAllocation as FIFOSalesAllocationLocal,
                ProfitTransaction as ProfitTransactionLocal, PendingPayment as PendingPaymentLocal,
                DeleteAuditLog as DeleteAuditLogLocal
            )
            
            total_records = 0
            
            # 按順序插入（遵循外鍵依賴）
            def insert_records(model_class, records, record_name):
                nonlocal total_records
                count = 0
                for record in records:
                    try:
                        # 轉換為字典
                        if hasattr(record, '__dict__'):
                            data = {k: v for k, v in record.__dict__.items() if not k.startswith('_')}
                        else:
                            data = dict(record)
                        
                        # 創建新記錄
                        new_record = model_class(**data)
                        local_db.session.add(new_record)
                        count += 1
                        
                        # 每100筆提交一次
                        if count % 100 == 0:
                            local_db.session.commit()
                    except Exception as e:
                        print(f"   ⚠️  插入記錄時出錯: {e}")
                        continue
                
                local_db.session.commit()
                total_records += count
                print(f"   ✅ {count} 筆 {record_name}")
                return count
            
            print("📝 正在寫入資料...")
            insert_records(UserLocal, users, "Users")
            insert_records(HolderLocal, holders, "Holders")
            insert_records(CashAccountLocal, cash_accounts, "CashAccounts")
            insert_records(ChannelLocal, channels, "Channels")
            insert_records(CustomerLocal, customers, "Customers")
            insert_records(PurchaseRecordLocal, purchases, "PurchaseRecords")
            insert_records(SalesRecordLocal, sales, "SalesRecords")
            insert_records(LedgerEntryLocal, ledger_entries, "LedgerEntries")
            insert_records(CashLogLocal, cash_logs, "CashLogs")
            insert_records(FIFOInventoryLocal, fifo_inventory, "FIFOInventory")
            insert_records(FIFOSalesAllocationLocal, fifo_sales, "FIFOSalesAllocation")
            
            # 可選表（需要在寫入前從線上讀取）
            # 注意：這些表可能不存在，需要謹慎處理
            print("\n📝 正在同步可選資料表...")
            
            # 重新設置為線上資料庫以讀取可選表
            os.environ['DATABASE_URL'] = online_db_url
            if 'app' in sys.modules:
                import importlib
                importlib.reload(sys.modules['app'])
            
            from app import app as online_app, db as online_db
            online_app.config["SQLALCHEMY_DATABASE_URI"] = online_db_url
            
            # ProfitTransactions
            try:
                with online_app.app_context():
                    from app import ProfitTransaction as ProfitTransactionOnline
                    profit_transactions = online_db.session.execute(online_db.select(ProfitTransactionOnline)).scalars().all()
                
                # 切換回本地
                if 'DATABASE_URL' in os.environ:
                    del os.environ['DATABASE_URL']
                if 'app' in sys.modules:
                    import importlib
                    importlib.reload(sys.modules['app'])
                
                from app import app as local_app2, db as local_db2
                local_app2.config["SQLALCHEMY_DATABASE_URI"] = local_db_uri
                with local_app2.app_context():
                    from app import ProfitTransaction as ProfitTransactionLocal2
                    insert_records(ProfitTransactionLocal2, profit_transactions, "ProfitTransactions")
            except Exception as e:
                print(f"   ⚠️  跳過 ProfitTransactions: {e}")
            
            # PendingPayments
            try:
                os.environ['DATABASE_URL'] = online_db_url
                if 'app' in sys.modules:
                    import importlib
                    importlib.reload(sys.modules['app'])
                from app import app as online_app2, db as online_db2
                online_app2.config["SQLALCHEMY_DATABASE_URI"] = online_db_url
                
                with online_app2.app_context():
                    from app import PendingPayment as PendingPaymentOnline
                    pending_payments = online_db2.session.execute(online_db2.select(PendingPaymentOnline)).scalars().all()
                
                if 'DATABASE_URL' in os.environ:
                    del os.environ['DATABASE_URL']
                if 'app' in sys.modules:
                    import importlib
                    importlib.reload(sys.modules['app'])
                
                from app import app as local_app3, db as local_db3
                local_app3.config["SQLALCHEMY_DATABASE_URI"] = local_db_uri
                with local_app3.app_context():
                    from app import PendingPayment as PendingPaymentLocal2
                    insert_records(PendingPaymentLocal2, pending_payments, "PendingPayments")
            except Exception as e:
                print(f"   ⚠️  跳過 PendingPayments: {e}")
            
            # DeleteAuditLogs
            try:
                os.environ['DATABASE_URL'] = online_db_url
                if 'app' in sys.modules:
                    import importlib
                    importlib.reload(sys.modules['app'])
                from app import app as online_app3, db as online_db3
                online_app3.config["SQLALCHEMY_DATABASE_URI"] = online_db_url
                
                with online_app3.app_context():
                    from app import DeleteAuditLog as DeleteAuditLogOnline
                    delete_audit_logs = online_db3.session.execute(online_db3.select(DeleteAuditLogOnline)).scalars().all()
                
                if 'DATABASE_URL' in os.environ:
                    del os.environ['DATABASE_URL']
                if 'app' in sys.modules:
                    import importlib
                    importlib.reload(sys.modules['app'])
                
                from app import app as local_app4, db as local_db4
                local_app4.config["SQLALCHEMY_DATABASE_URI"] = local_db_uri
                with local_app4.app_context():
                    from app import DeleteAuditLog as DeleteAuditLogLocal2
                    insert_records(DeleteAuditLogLocal2, delete_audit_logs, "DeleteAuditLogs")
            except Exception as e:
                print(f"   ⚠️  跳過 DeleteAuditLogs: {e}")
            
            print("\n" + "=" * 80)
            print("✅ 資料同步完成！")
            print("=" * 80)
            print(f"\n📊 同步統計：")
            print(f"   總記錄數: {total_records}")
            print(f"   本地資料庫: {local_db_path}")
            if backup_path:
                print(f"   備份位置: {backup_path}")
            print(f"   同步時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ 同步失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("📥 資料庫同步工具")
    print("=" * 80)
    print("\n此工具會將 Render PostgreSQL 的所有資料同步到本地 SQLite")
    print("\n⚠️  警告：此操作會完全替換本地資料庫的內容！")
    print("   本地資料庫會自動備份到 instance/ 目錄")
    
    response = input("\n是否繼續？(yes/no): ").strip().lower()
    if response not in ["yes", "y"]:
        print("❌ 已取消")
        sys.exit(0)
    
    success = sync_database()
    
    if success:
        print("\n✅ 同步成功！本地資料庫現在與線上資料庫一致。")
    else:
        print("\n❌ 同步失敗！請檢查錯誤訊息。")
        sys.exit(1)

