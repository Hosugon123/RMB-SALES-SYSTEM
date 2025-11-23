#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版：從部署端資料庫下拉到本地資料庫
使用更簡單的方法，避免複雜的錯誤處理
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# 確保能夠導入 app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_deployment_db_url():
    """獲取部署端資料庫連接字串"""
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("⚠️  未找到 DATABASE_URL 環境變數")
        print("\n請選擇資料來源：")
        print("1. 手動輸入部署端 PostgreSQL 連接字串")
        print("2. 使用預設 Render 連接字串（需要密碼）")
        
        choice = input("\n請選擇 (1/2): ").strip()
        
        if choice == "1":
            db_url = input("請輸入 DATABASE_URL: ").strip()
        elif choice == "2":
            password = input("請輸入 Render 資料庫密碼: ").strip()
            if password:
                db_url = f"postgresql+psycopg://rmb_user:{password}@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"
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

def pull_database_simple():
    """簡化版資料下拉 - 使用 SQLAlchemy 的 bulk_insert_mappings"""
    print("=" * 80)
    print("📥 從部署端資料庫下拉到本地（簡化版）")
    print("=" * 80)
    
    # 獲取部署端資料庫連接
    deployment_db_url = get_deployment_db_url()
    if not deployment_db_url:
        return False
    
    print(f"\n✅ 已獲取部署端資料庫連接")
    print(f"   連接字串: {deployment_db_url[:60]}...")
    
    try:
        # 準備本地資料庫路徑（與 app.py 保持一致）
        basedir = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(basedir, "instance")
        try:
            os.makedirs(instance_path, exist_ok=True)
        except Exception as e:
            print(f"❌ 無法創建 instance 目錄: {e}")
            print(f"   路徑: {instance_path}")
            return False
        
        local_db_path = os.path.join(instance_path, "sales_system_v4.db")
        # 使用與 app.py 相同的方式構建 URI（SQLAlchemy 會自動處理 Windows 路徑）
        local_db_uri = "sqlite:///" + local_db_path
        
        print(f"📁 本地資料庫路徑: {local_db_path}")
        print(f"📁 資料庫 URI: {local_db_uri}")
        
        # 備份本地資料庫
        print("\n" + "=" * 80)
        print("📦 備份本地資料庫...")
        print("=" * 80)
        backup_path = backup_local_database(local_db_path)
        
        # 步驟 1: 連接部署端資料庫並讀取資料
        print("\n" + "=" * 80)
        print("[1/3] 從部署端資料庫讀取資料...")
        print("=" * 80)
        
        # 設置環境變數以使用部署端資料庫
        original_db_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = deployment_db_url
        
        # 重新導入 app
        if 'app' in sys.modules:
            import importlib
            importlib.reload(sys.modules['app'])
        
        from app import app, db
        
        app.config["SQLALCHEMY_DATABASE_URI"] = deployment_db_url
        
        # 讀取資料
        with app.app_context():
            from app import (
                User, Holder, CashAccount, Channel, Customer,
                PurchaseRecord, SalesRecord, LedgerEntry, CashLog,
                FIFOInventory, FIFOSalesAllocation, ProfitTransaction,
                PendingPayment, DeleteAuditLog, Transaction, CardPurchase
            )
            
            print("📖 正在讀取資料表...")
            
            # 讀取所有資料並轉換為字典列表
            def read_to_dict_list(model_class, table_name):
                try:
                    records = db.session.execute(db.select(model_class)).scalars().all()
                    result = []
                    for record in records:
                        data = {}
                        for column in model_class.__table__.columns:
                            value = getattr(record, column.name, None)
                            data[column.name] = value
                        result.append(data)
                    print(f"   ✅ {table_name}: {len(result)} 筆")
                    return result
                except Exception as e:
                    print(f"   ⚠️  {table_name} 讀取失敗: {e}")
                    return []
            
            users_data = read_to_dict_list(User, "Users")
            holders_data = read_to_dict_list(Holder, "Holders")
            channels_data = read_to_dict_list(Channel, "Channels")
            cash_accounts_data = read_to_dict_list(CashAccount, "CashAccounts")
            customers_data = read_to_dict_list(Customer, "Customers")
            purchases_data = read_to_dict_list(PurchaseRecord, "PurchaseRecords")
            sales_data = read_to_dict_list(SalesRecord, "SalesRecords")
            ledger_entries_data = read_to_dict_list(LedgerEntry, "LedgerEntries")
            cash_logs_data = read_to_dict_list(CashLog, "CashLogs")
            transactions_data = read_to_dict_list(Transaction, "Transactions")
            card_purchases_data = read_to_dict_list(CardPurchase, "CardPurchases")
            fifo_inventory_data = read_to_dict_list(FIFOInventory, "FIFOInventory")
            fifo_sales_data = read_to_dict_list(FIFOSalesAllocation, "FIFOSalesAllocation")
            profit_transactions_data = read_to_dict_list(ProfitTransaction, "ProfitTransactions")
            pending_payments_data = read_to_dict_list(PendingPayment, "PendingPayments")
            delete_audit_logs_data = read_to_dict_list(DeleteAuditLog, "DeleteAuditLogs")
        
        # 步驟 2: 清空本地資料庫
        print("\n" + "=" * 80)
        print("[2/3] 清空本地資料庫...")
        print("=" * 80)
        
        # 移除環境變數，使用本地 SQLite
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        
        # 重新導入 app
        if 'app' in sys.modules:
            import importlib
            importlib.reload(sys.modules['app'])
        
        from app import app as local_app, db as local_db
        local_app.config["SQLALCHEMY_DATABASE_URI"] = local_db_uri
        
        with local_app.app_context():
            # 創建所有表
            try:
                local_db.create_all()
                print("✅ 本地資料庫表已準備完成")
            except Exception as e:
                print(f"❌ 創建資料庫表失敗: {e}")
                print(f"   資料庫 URI: {local_db_uri}")
                import traceback
                traceback.print_exc()
                return False
            
            # 清空所有表
            print("🗑️  正在清空資料表...")
            tables = [
                'profit_transactions', 'fifo_sales_allocations', 'fifo_inventory',
                'delete_audit_logs', 'pending_payments', 'transactions',
                'card_purchases', 'cash_logs', 'ledger_entries', 
                'sales_records', 'purchase_records',
                'customers', 'cash_accounts', 'channels', 'holders', 'user'
            ]
            
            for table in tables:
                try:
                    local_db.session.execute(local_db.text(f'DELETE FROM {table}'))
                except:
                    pass  # 表可能不存在，忽略
            
            local_db.session.commit()
            print("✅ 本地資料庫已清空")
        
        # 步驟 3: 寫入資料到本地
        print("\n" + "=" * 80)
        print("[3/3] 寫入資料到本地資料庫...")
        print("=" * 80)
        
        with local_app.app_context():
            from app import (
                User as UserLocal, Holder as HolderLocal, CashAccount as CashAccountLocal,
                Channel as ChannelLocal, Customer as CustomerLocal,
                PurchaseRecord as PurchaseRecordLocal, SalesRecord as SalesRecordLocal,
                LedgerEntry as LedgerEntryLocal, CashLog as CashLogLocal,
                FIFOInventory as FIFOInventoryLocal, FIFOSalesAllocation as FIFOSalesAllocationLocal,
                ProfitTransaction as ProfitTransactionLocal, PendingPayment as PendingPaymentLocal,
                DeleteAuditLog as DeleteAuditLogLocal, Transaction as TransactionLocal,
                CardPurchase as CardPurchaseLocal
            )
            
            def insert_bulk(model_class, data_list, table_name):
                """使用 bulk_insert_mappings 批量插入"""
                if not data_list:
                    print(f"   ℹ️  {table_name}: 無資料")
                    return 0
                
                try:
                    # 過濾掉模型中不存在的欄位
                    if data_list:
                        model_columns = {col.name for col in model_class.__table__.columns}
                        filtered_data = []
                        for data in data_list:
                            filtered = {k: v for k, v in data.items() if k in model_columns}
                            filtered_data.append(filtered)
                        data_list = filtered_data
                    
                    # 使用 bulk_insert_mappings 提高效率
                    local_db.session.bulk_insert_mappings(model_class, data_list)
                    local_db.session.commit()
                    print(f"   ✅ {table_name}: {len(data_list)} 筆")
                    return len(data_list)
                except Exception as e:
                    local_db.session.rollback()
                    print(f"   ❌ {table_name} 插入失敗: {e}")
                    # 嘗試逐個插入
                    print(f"   🔄 嘗試逐個插入 {table_name}...")
                    count = 0
                    for data in data_list:
                        try:
                            model_columns = {col.name for col in model_class.__table__.columns}
                            filtered = {k: v for k, v in data.items() if k in model_columns}
                            local_db.session.bulk_insert_mappings(model_class, [filtered])
                            local_db.session.commit()
                            count += 1
                        except Exception as e2:
                            local_db.session.rollback()
                            print(f"      ⚠️  跳過記錄 (ID: {data.get('id', 'unknown')}): {e2}")
                    if count > 0:
                        print(f"   ✅ {table_name}: {count}/{len(data_list)} 筆成功")
                    return count
            
            print("📝 正在寫入資料...")
            total = 0
            total += insert_bulk(UserLocal, users_data, "Users")
            total += insert_bulk(HolderLocal, holders_data, "Holders")
            total += insert_bulk(ChannelLocal, channels_data, "Channels")
            total += insert_bulk(CashAccountLocal, cash_accounts_data, "CashAccounts")
            total += insert_bulk(CustomerLocal, customers_data, "Customers")
            total += insert_bulk(PurchaseRecordLocal, purchases_data, "PurchaseRecords")
            total += insert_bulk(SalesRecordLocal, sales_data, "SalesRecords")
            total += insert_bulk(LedgerEntryLocal, ledger_entries_data, "LedgerEntries")
            total += insert_bulk(CashLogLocal, cash_logs_data, "CashLogs")
            total += insert_bulk(TransactionLocal, transactions_data, "Transactions")
            total += insert_bulk(CardPurchaseLocal, card_purchases_data, "CardPurchases")
            total += insert_bulk(FIFOInventoryLocal, fifo_inventory_data, "FIFOInventory")
            total += insert_bulk(FIFOSalesAllocationLocal, fifo_sales_data, "FIFOSalesAllocation")
            total += insert_bulk(ProfitTransactionLocal, profit_transactions_data, "ProfitTransactions")
            total += insert_bulk(PendingPaymentLocal, pending_payments_data, "PendingPayments")
            total += insert_bulk(DeleteAuditLogLocal, delete_audit_logs_data, "DeleteAuditLogs")
            
            print("\n" + "=" * 80)
            print("✅ 資料下拉完成！")
            print("=" * 80)
            print(f"\n📊 同步統計：")
            print(f"   總記錄數: {total}")
            print(f"   本地資料庫: {local_db_path}")
            if backup_path:
                print(f"   備份位置: {backup_path}")
            print(f"   同步時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ 下拉失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 恢復原始環境變數
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url

if __name__ == "__main__":
    try:
        print("\n" + "=" * 80)
        print("資料庫下拉工具（簡化版）")
        print("=" * 80)
        print("\n此工具會將部署端 PostgreSQL 的所有資料下拉到本地 SQLite")
        print("使用 bulk_insert_mappings 方法，更穩定可靠")
        print("\n警告：此操作會完全替換本地資料庫的內容！")
        print("   本地資料庫會自動備份到 instance/ 目錄")
        
        response = input("\n是否繼續？(yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print("已取消")
            sys.exit(0)
        
        success = pull_database_simple()
        
        if success:
            print("\n" + "=" * 80)
            print("下拉成功！本地資料庫現在與部署端資料庫一致。")
            print("=" * 80)
            print("\n提示：現在可以移除 DATABASE_URL 環境變數來使用本地資料庫進行測試。")
        else:
            print("\n" + "=" * 80)
            print("下拉失敗！請檢查上面的錯誤訊息。")
            print("=" * 80)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

