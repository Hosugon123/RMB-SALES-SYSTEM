#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從部署端資料庫下拉到本地資料庫
功能：
1. 從部署端 PostgreSQL 讀取所有資料
2. 備份本地 SQLite 資料庫
3. 清空本地資料庫
4. 將資料寫入本地 SQLite
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
    # 優先從環境變數獲取
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
            # 使用預設連接
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

def pull_database(debug=False):
    """執行資料下拉
    
    Args:
        debug: 是否啟用調試模式（顯示詳細錯誤）
    """
    print("=" * 80)
    print("📥 從部署端資料庫下拉到本地")
    if debug:
        print("🔍 調試模式已啟用")
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
        os.makedirs(instance_path, exist_ok=True)
        local_db_path = os.path.join(instance_path, "sales_system_v4.db")
        # 使用與 app.py 相同的方式構建 URI（SQLAlchemy 會自動處理 Windows 路徑）
        local_db_uri = "sqlite:///" + local_db_path
        
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
        
        # 重新導入 app 以使用部署端配置
        if 'app' in sys.modules:
            import importlib
            importlib.reload(sys.modules['app'])
        
        from app import app, db
        
        # 確保使用部署端資料庫
        app.config["SQLALCHEMY_DATABASE_URI"] = deployment_db_url
        
        # 在 app context 中讀取資料
        with app.app_context():
            from app import (
                User, Holder, CashAccount, Channel, Customer,
                PurchaseRecord, SalesRecord, LedgerEntry, CashLog,
                FIFOInventory, FIFOSalesAllocation, ProfitTransaction,
                PendingPayment, DeleteAuditLog, Transaction, CardPurchase
            )
            
            # 讀取所有資料表
            print("📖 正在讀取資料表...")
            
            # 定義讀取函數，帶錯誤處理
            def read_table(model_class, table_name, required=True):
                """讀取資料表，帶錯誤處理"""
                try:
                    result = db.session.execute(db.select(model_class)).scalars().all()
                    print(f"   ✅ {table_name}: {len(result)} 筆")
                    return result
                except Exception as e:
                    if required:
                        print(f"   ❌ {table_name} 讀取失敗（必需表）: {e}")
                        raise  # 必需表失敗時拋出異常
                    else:
                        print(f"   ⚠️  {table_name} 讀取失敗（可選表）: {e}")
                        return []
            
            try:
                # 基礎表（無外鍵依賴）- 必需
                users = read_table(User, "Users", required=True)
                holders = read_table(Holder, "Holders", required=True)
                channels = read_table(Channel, "Channels", required=True)
                
                # 依賴基礎表的表 - 必需
                cash_accounts = read_table(CashAccount, "CashAccounts", required=True)
                customers = read_table(Customer, "Customers", required=True)
                
                # 依賴上述表的表 - 必需
                purchases = read_table(PurchaseRecord, "PurchaseRecords", required=True)
                sales = read_table(SalesRecord, "SalesRecords", required=True)
                
                # 其他表 - 必需
                ledger_entries = read_table(LedgerEntry, "LedgerEntries", required=True)
                cash_logs = read_table(CashLog, "CashLogs", required=True)
                
                # 可能不存在的表 - 可選
                transactions = read_table(Transaction, "Transactions", required=False)
                card_purchases = read_table(CardPurchase, "CardPurchases", required=False)
                
                # FIFO 相關 - 必需
                fifo_inventory = read_table(FIFOInventory, "FIFOInventory", required=True)
                fifo_sales = read_table(FIFOSalesAllocation, "FIFOSalesAllocation", required=True)
                
                # 可選表（可能不存在）
                profit_transactions = read_table(ProfitTransaction, "ProfitTransactions", required=False)
                pending_payments = read_table(PendingPayment, "PendingPayments", required=False)
                delete_audit_logs = read_table(DeleteAuditLog, "DeleteAuditLogs", required=False)
                
                print(f"\n✅ 讀取完成，統計：")
                
                # 將資料轉換為字典格式（便於序列化）
                def to_dict(obj):
                    """將 SQLAlchemy 對象轉換為字典"""
                    result = {}
                    for column in obj.__table__.columns:
                        try:
                            value = getattr(obj, column.name)
                            # 處理 datetime 對象（保持原樣，SQLAlchemy 會處理）
                            # 處理其他特殊類型
                            if value is not None:
                                result[column.name] = value
                            elif column.nullable:
                                # 可為空的欄位，保留 None
                                result[column.name] = None
                            # 不可為空的欄位且有預設值時，不包含在字典中，讓模型使用預設值
                        except AttributeError:
                            # 欄位不存在，跳過
                            continue
                    return result
                
                users_data = [to_dict(u) for u in users]
                holders_data = [to_dict(h) for h in holders]
                channels_data = [to_dict(c) for c in channels]
                cash_accounts_data = [to_dict(c) for c in cash_accounts]
                customers_data = [to_dict(c) for c in customers]
                purchases_data = [to_dict(p) for p in purchases]
                sales_data = [to_dict(s) for s in sales]
                ledger_entries_data = [to_dict(e) for e in ledger_entries]
                cash_logs_data = [to_dict(c) for c in cash_logs]
                transactions_data = [to_dict(t) for t in transactions]
                card_purchases_data = [to_dict(c) for c in card_purchases]
                fifo_inventory_data = [to_dict(f) for f in fifo_inventory]
                fifo_sales_data = [to_dict(f) for f in fifo_sales]
                profit_transactions_data = [to_dict(p) for p in profit_transactions] if profit_transactions else []
                pending_payments_data = [to_dict(p) for p in pending_payments] if pending_payments else []
                delete_audit_logs_data = [to_dict(d) for d in delete_audit_logs] if delete_audit_logs else []
                
            except Exception as e:
                print(f"❌ 讀取部署端資料失敗: {e}")
                import traceback
                print("\n詳細錯誤訊息：")
                traceback.print_exc()
                print("\n💡 提示：")
                print("   1. 檢查網路連線是否正常")
                print("   2. 確認資料庫連接字串是否正確")
                print("   3. 確認資料庫密碼是否正確")
                return False
        
        # 步驟 2: 清空本地資料庫
        print("\n" + "=" * 80)
        print("[2/3] 清空本地資料庫...")
        print("=" * 80)
        
        # 移除環境變數，強制使用本地 SQLite
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        # 恢復原始環境變數（如果存在）
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        
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
            
            # 清空所有表（按外鍵順序，從依賴表到基礎表）
            print("🗑️  正在清空資料表...")
            try:
                # 按外鍵依賴順序清空（從最依賴到最基礎）
                # 注意：Transaction 依賴 SalesRecord，所以要先清空
                tables = [
                    'profit_transactions', 'fifo_sales_allocations', 'fifo_inventory',
                    'delete_audit_logs', 'pending_payments', 
                    'transactions',  # 依賴 sales_records
                    'card_purchases', 'cash_logs', 'ledger_entries', 
                    'sales_records', 'purchase_records',
                    'customers', 'cash_accounts', 'channels', 'holders', 'user'
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
            
            total_records = 0
            
            # 按順序插入（遵循外鍵依賴）
            def insert_records(model_class, data_list, record_name, batch_size=100):
                nonlocal total_records
                count = 0
                errors = []
                
                if not data_list:
                    print(f"   ℹ️  {record_name}: 無資料")
                    return 0
                
                for i in range(0, len(data_list), batch_size):
                    batch = data_list[i:i+batch_size]
                    batch_errors = []
                    
                    for data in batch:
                        try:
                            # 清理資料：移除 SQLAlchemy 內部屬性，只保留模型存在的欄位
                            clean_data = {}
                            # 獲取模型的所有欄位名稱
                            model_columns = {col.name for col in model_class.__table__.columns}
                            
                            for k, v in data.items():
                                # 跳過 SQLAlchemy 內部屬性
                                if k.startswith('_'):
                                    continue
                                # 只保留模型中存在的欄位
                                if k in model_columns:
                                    clean_data[k] = v
                            
                            # 創建記錄
                            new_record = model_class(**clean_data)
                            local_db.session.add(new_record)
                            count += 1
                            
                        except Exception as e:
                            record_id = data.get('id', 'unknown')
                            error_msg = f"ID {record_id}: {str(e)}"
                            batch_errors.append(error_msg)
                            if debug or len(batch_errors) <= 5:  # 調試模式顯示所有錯誤，否則只顯示前5個
                                print(f"   ⚠️  插入 {record_name} 記錄時出錯 ({error_msg})")
                                if debug:
                                    import traceback
                                    traceback.print_exc()
                            continue
                    
                    # 每批次提交一次
                    try:
                        local_db.session.commit()
                    except Exception as e:
                        print(f"   ⚠️  提交 {record_name} 批次時出錯: {e}")
                        # 嘗試逐個提交以找出問題記錄
                        local_db.session.rollback()
                        # 重新嘗試，這次逐個提交
                        for data in batch:
                            try:
                                clean_data = {k: v for k, v in data.items() if not k.startswith('_')}
                                new_record = model_class(**clean_data)
                                local_db.session.add(new_record)
                                local_db.session.commit()
                                count += 1
                            except Exception as e2:
                                local_db.session.rollback()
                                record_id = data.get('id', 'unknown')
                                errors.append(f"ID {record_id}: {str(e2)}")
                                if len(errors) <= 10:
                                    print(f"   ⚠️  單筆插入失敗 (ID {record_id}): {e2}")
                
                total_records += count
                if errors:
                    print(f"   ⚠️  {record_name}: {count} 筆成功，{len(errors)} 筆失敗")
                    if len(errors) > 10:
                        print(f"   ⚠️  （僅顯示前10個錯誤，共 {len(errors)} 個錯誤）")
                else:
                    print(f"   ✅ {count} 筆 {record_name}")
                
                return count
            
            print("📝 正在寫入資料...")
            # 按外鍵依賴順序插入
            insert_records(UserLocal, users_data, "Users")
            insert_records(HolderLocal, holders_data, "Holders")
            insert_records(ChannelLocal, channels_data, "Channels")
            insert_records(CashAccountLocal, cash_accounts_data, "CashAccounts")
            insert_records(CustomerLocal, customers_data, "Customers")
            insert_records(PurchaseRecordLocal, purchases_data, "PurchaseRecords")
            insert_records(SalesRecordLocal, sales_data, "SalesRecords")
            insert_records(LedgerEntryLocal, ledger_entries_data, "LedgerEntries")
            insert_records(CashLogLocal, cash_logs_data, "CashLogs")
            insert_records(TransactionLocal, transactions_data, "Transactions")
            insert_records(CardPurchaseLocal, card_purchases_data, "CardPurchases")
            insert_records(FIFOInventoryLocal, fifo_inventory_data, "FIFOInventory")
            insert_records(FIFOSalesAllocationLocal, fifo_sales_data, "FIFOSalesAllocation")
            
            if profit_transactions_data:
                insert_records(ProfitTransactionLocal, profit_transactions_data, "ProfitTransactions")
            if pending_payments_data:
                insert_records(PendingPaymentLocal, pending_payments_data, "PendingPayments")
            if delete_audit_logs_data:
                insert_records(DeleteAuditLogLocal, delete_audit_logs_data, "DeleteAuditLogs")
            
            print("\n" + "=" * 80)
            print("✅ 資料下拉完成！")
            print("=" * 80)
            print(f"\n📊 同步統計：")
            print(f"   總記錄數: {total_records}")
            print(f"   本地資料庫: {local_db_path}")
            if backup_path:
                print(f"   備份位置: {backup_path}")
            print(f"   同步時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ 下拉失敗: {e}")
        import traceback
        print("\n詳細錯誤訊息：")
        traceback.print_exc()
        print("\n💡 疑難排解建議：")
        print("   1. 檢查上面的錯誤訊息，找出具體失敗的表或記錄")
        print("   2. 確認本地資料庫結構是否與部署端一致")
        print("   3. 檢查是否有外鍵約束問題")
        print("   4. 查看備份檔案是否已創建")
        return False
    finally:
        # 恢復原始環境變數
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("📥 資料庫下拉工具")
    print("=" * 80)
    print("\n此工具會將部署端 PostgreSQL 的所有資料下拉到本地 SQLite")
    print("\n⚠️  警告：此操作會完全替換本地資料庫的內容！")
    print("   本地資料庫會自動備份到 instance/ 目錄")
    
    response = input("\n是否繼續？(yes/no): ").strip().lower()
    if response not in ["yes", "y"]:
        print("❌ 已取消")
        sys.exit(0)
    
    # 詢問是否啟用調試模式
    debug_response = input("\n是否啟用調試模式（顯示詳細錯誤）？(yes/no，預設 no): ").strip().lower()
    debug_mode = debug_response in ["yes", "y"]
    
    try:
        success = pull_database(debug=debug_mode)
        
        if success:
            print("\n✅ 下拉成功！本地資料庫現在與部署端資料庫一致。")
            print("\n💡 提示：現在可以移除 DATABASE_URL 環境變數來使用本地資料庫進行測試。")
        else:
            print("\n❌ 下拉失敗！請檢查上面的錯誤訊息。")
            print("\n📋 常見問題解決方案：")
            print("   1. 如果看到連接錯誤：檢查網路和資料庫連接字串")
            print("   2. 如果看到外鍵錯誤：可能是資料順序問題，嘗試重新執行")
            print("   3. 如果看到欄位錯誤：可能是模型結構不一致，檢查 app.py 中的模型定義")
            print("   4. 如果看到提交錯誤：查看具體是哪個表的哪筆記錄出問題")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

