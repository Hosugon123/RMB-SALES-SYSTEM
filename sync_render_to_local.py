#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從 Render PostgreSQL 資料庫同步資料到本地 SQLite
使用 Flask-Migrate 和 SQLAlchemy 進行同步
"""

import os
import sys
from datetime import datetime

# 在導入 app 之前設置環境變數
# 這是從 Render 環境獲取資料庫連接字串
DATABASE_URL = "postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"
os.environ['DATABASE_URL'] = DATABASE_URL

print("開始同步 Render 資料庫到本地...")
print(f"線上資料庫: {DATABASE_URL[:50]}...")

# 現在導入 app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def sync_database():
    """同步線上資料庫到本地"""
    print("=" * 80)
    print("從 Render PostgreSQL 同步到本地 SQLite")
    print("=" * 80)
    
    try:
        # 導入需要的模組
        from app import app, db
        
        # 步驟 1: 從線上讀取資料
        print("\n[步驟 1/4] 從線上資料庫讀取資料...")
        
        with app.app_context():
            # 確保使用線上資料庫（已通過環境變數設置）
            print(f"連接字串: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
            
            # 導入所有模型
            from app import (
                User, Holder, CashAccount, Channel, Customer,
                PurchaseRecord, SalesRecord, LedgerEntry, CashLog,
                FIFOInventory, FIFOSalesAllocation, ProfitTransaction
            )
            
            # 讀取所有資料
            users_data = []
            for u in User.query.all():
                users_data.append({
                    'id': u.id,
                    'username': u.username,
                    'password_hash': u.password_hash,
                    'role': u.role
                })
            
            holders_data = []
            for h in Holder.query.all():
                holders_data.append({
                    'id': h.id,
                    'name': h.name,
                    'is_active': h.is_active
                })
            
            accounts_data = []
            for a in CashAccount.query.all():
                accounts_data.append({
                    'id': a.id,
                    'name': a.name,
                    'currency': a.currency,
                    'balance': a.balance,
                    'profit_balance': a.profit_balance,
                    'holder_id': a.holder_id,
                    'is_active': a.is_active
                })
            
            channels_data = []
            for c in Channel.query.all():
                channels_data.append({
                    'id': c.id,
                    'name': c.name
                })
            
            customers_data = []
            for c in Customer.query.all():
                customers_data.append({
                    'id': c.id,
                    'name': c.name,
                    'total_receivables_twd': c.total_receivables_twd,
                    'is_active': c.is_active
                })
            
            purchases_data = []
            for p in PurchaseRecord.query.all():
                purchases_data.append({
                    'id': p.id,
                    'purchase_date': p.purchase_date,
                    'payment_account_id': p.payment_account_id,
                    'deposit_account_id': p.deposit_account_id,
                    'rmb_amount': p.rmb_amount,
                    'twd_cost': p.twd_cost,
                    'exchange_rate': p.exchange_rate,
                    'channel_id': p.channel_id,
                    'note': getattr(p, 'note', None) if hasattr(p, 'note') else None,
                    'operator_id': p.operator_id
                })
            
            sales_data = []
            for s in SalesRecord.query.all():
                sales_data.append({
                    'id': s.id,
                    'customer_id': s.customer_id,
                    'rmb_account_id': s.rmb_account_id,
                    'rmb_amount': s.rmb_amount,
                    'exchange_rate': s.exchange_rate,
                    'twd_amount': s.twd_amount,
                    'is_settled': s.is_settled,
                    'note': getattr(s, 'note', None) if hasattr(s, 'note') else None,
                    'operator_id': s.operator_id,
                    'created_at': s.created_at
                })
            
            ledger_entries_data = []
            for e in LedgerEntry.query.all():
                ledger_entries_data.append({
                    'id': e.id,
                    'entry_type': e.entry_type,
                    'account_id': e.account_id,
                    'from_account_id': e.from_account_id,
                    'to_account_id': e.to_account_id,
                    'amount': e.amount,
                    'description': e.description,
                    'entry_date': e.entry_date,
                    'operator_id': e.operator_id,
                    'profit_before': e.profit_before,
                    'profit_after': e.profit_after,
                    'profit_change': e.profit_change
                })
            
            cash_logs_data = []
            for c in CashLog.query.all():
                cash_logs_data.append({
                    'id': c.id,
                    'type': c.type,
                    'description': c.description,
                    'amount': c.amount,
                    'time': c.time,
                    'operator_id': c.operator_id
                })
            
            fifo_inventory_data = []
            for f in FIFOInventory.query.all():
                fifo_inventory_data.append({
                    'id': f.id,
                    'purchase_record_id': f.purchase_record_id,
                    'purchase_date': f.purchase_date,
                    'rmb_amount': f.rmb_amount,
                    'unit_cost_twd': f.unit_cost_twd,
                    'remaining_rmb': f.remaining_rmb,
                    'created_at': f.created_at
                })
            
            fifo_sales_data = []
            for f in FIFOSalesAllocation.query.all():
                fifo_sales_data.append({
                    'id': f.id,
                    'fifo_inventory_id': f.fifo_inventory_id,
                    'sales_record_id': f.sales_record_id,
                    'allocated_rmb': f.allocated_rmb,
                    'allocated_cost_twd': f.allocated_cost_twd,
                    'created_at': f.created_at
                })
            
            profit_transactions_data = []
            for p in ProfitTransaction.query.all():
                profit_transactions_data.append({
                    'id': p.id,
                    'account_id': p.account_id,
                    'amount': p.amount,
                    'transaction_type': p.transaction_type,
                    'description': p.description,
                    'note': p.note,
                    'related_transaction_id': p.related_transaction_id,
                    'related_transaction_type': p.related_transaction_type,
                    'created_at': p.created_at,
                    'operator_id': p.operator_id
                })
            
            print(f"✅ 讀取完成：")
            print(f"   Users: {len(users_data)}")
            print(f"   Holders: {len(holders_data)}")
            print(f"   CashAccounts: {len(accounts_data)}")
            print(f"   Channels: {len(channels_data)}")
            print(f"   Customers: {len(customers_data)}")
            print(f"   Purchases: {len(purchases_data)}")
            print(f"   Sales: {len(sales_data)}")
            print(f"   LedgerEntries: {len(ledger_entries_data)}")
            print(f"   CashLogs: {len(cash_logs_data)}")
            print(f"   FIFOInventory: {len(fifo_inventory_data)}")
            print(f"   FIFOSales: {len(fifo_sales_data)}")
            print(f"   ProfitTransactions: {len(profit_transactions_data)}")
        
        # 步驟 2: 切換到本地資料庫
        print("\n[步驟 2/4] 準備本地資料庫...")
        
        # 移除環境變數，強制使用本地 SQLite
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        # 重新載入 app 以使用本地配置
        import importlib
        import app
        importlib.reload(app)
        
        from app import app as local_app, db as local_db
        
        with local_app.app_context():
            # 備份舊資料庫
            instance_path = os.path.join(os.path.dirname(__file__), "instance")
            old_db_path = os.path.join(instance_path, "sales_system_v4.db")
            if os.path.exists(old_db_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(instance_path, f"sales_system_v4_backup_{timestamp}.db")
                import shutil
                shutil.copy2(old_db_path, backup_path)
                print(f"✅ 舊資料庫已備份: {backup_path}")
            
            # 清空本地資料庫
            print("清空本地資料庫...")
            try:
                local_db.session.execute(local_db.text('DELETE FROM profit_transactions'))
                local_db.session.execute(local_db.text('DELETE FROM fifo_sales_allocation'))
                local_db.session.execute(local_db.text('DELETE FROM fifo_inventory'))
                local_db.session.execute(local_db.text('DELETE FROM cash_logs'))
                local_db.session.execute(local_db.text('DELETE FROM ledger_entries'))
                local_db.session.execute(local_db.text('DELETE FROM sales_records'))
                local_db.session.execute(local_db.text('DELETE FROM purchase_records'))
                local_db.session.execute(local_db.text('DELETE FROM customers'))
                local_db.session.execute(local_db.text('DELETE FROM channels'))
                local_db.session.execute(local_db.text('DELETE FROM cash_accounts'))
                local_db.session.execute(local_db.text('DELETE FROM holders'))
                local_db.session.execute(local_db.text('DELETE FROM users'))
                local_db.session.commit()
                print("✅ 本地資料庫已清空")
            except Exception as e:
                print(f"⚠️ 清空資料庫時出現錯誤（可能表格為空）: {e}")
                local_db.session.rollback()
            
            # 重新導入模型（確保是本地版本）
            from app import (
                User as LocalUser, Holder as LocalHolder, CashAccount as LocalCashAccount,
                Channel as LocalChannel, Customer as LocalCustomer,
                PurchaseRecord as LocalPurchaseRecord, SalesRecord as LocalSalesRecord,
                LedgerEntry as LocalLedgerEntry, CashLog as LocalCashLog,
                FIFOInventory as LocalFIFOInventory, FIFOSalesAllocation as LocalFIFOSalesAllocation,
                ProfitTransaction as LocalProfitTransaction
            )
            
            # 步驟 3: 寫入資料到本地
            print("\n[步驟 3/4] 寫入資料到本地資料庫...")
            
            # 使用 bulk_insert_mappings 提高效率
            def insert_records(model, data_list, batch_size=100):
                for i in range(0, len(data_list), batch_size):
                    batch = data_list[i:i+batch_size]
                    local_db.session.bulk_insert_mappings(model, batch)
                    local_db.session.commit()
                return len(data_list)
            
            total = 0
            total += insert_records(LocalUser, users_data)
            print(f"   ✅ {len(users_data)} 筆 Users")
            
            total += insert_records(LocalHolder, holders_data)
            print(f"   ✅ {len(holders_data)} 筆 Holders")
            
            total += insert_records(LocalCashAccount, accounts_data)
            print(f"   ✅ {len(accounts_data)} 筆 CashAccounts")
            
            total += insert_records(LocalChannel, channels_data)
            print(f"   ✅ {len(channels_data)} 筆 Channels")
            
            total += insert_records(LocalCustomer, customers_data)
            print(f"   ✅ {len(customers_data)} 筆 Customers")
            
            total += insert_records(LocalPurchaseRecord, purchases_data)
            print(f"   ✅ {len(purchases_data)} 筆 PurchaseRecords")
            
            total += insert_records(LocalSalesRecord, sales_data)
            print(f"   ✅ {len(sales_data)} 筆 SalesRecords")
            
            total += insert_records(LocalLedgerEntry, ledger_entries_data)
            print(f"   ✅ {len(ledger_entries_data)} 筆 LedgerEntries")
            
            total += insert_records(LocalCashLog, cash_logs_data)
            print(f"   ✅ {len(cash_logs_data)} 筆 CashLogs")
            
            total += insert_records(LocalFIFOInventory, fifo_inventory_data)
            print(f"   ✅ {len(fifo_inventory_data)} 筆 FIFOInventory")
            
            total += insert_records(LocalFIFOSalesAllocation, fifo_sales_data)
            print(f"   ✅ {len(fifo_sales_data)} 筆 FIFOSalesAllocation")
            
            total += insert_records(LocalProfitTransaction, profit_transactions_data)
            print(f"   ✅ {len(profit_transactions_data)} 筆 ProfitTransactions")
            
            print("\n[步驟 4/4] 驗證同步結果...")
            
            # 統計本地資料
            local_users_count = LocalUser.query.count()
            local_accounts_count = LocalCashAccount.query.count()
            local_sales_count = LocalSalesRecord.query.count()
            local_purchases_count = LocalPurchaseRecord.query.count()
            
            print(f"✅ 本地資料統計：")
            print(f"   Users: {local_users_count}")
            print(f"   CashAccounts: {local_accounts_count}")
            print(f"   SalesRecords: {local_sales_count}")
            print(f"   PurchaseRecords: {local_purchases_count}")
            
            # 驗證數量一致
            if (local_users_count == len(users_data) and 
                local_accounts_count == len(accounts_data) and
                local_sales_count == len(sales_data) and
                local_purchases_count == len(purchases_data)):
                print("✅ 驗證通過：資料數量一致")
            else:
                print("⚠️ 警告：部分資料數量不一致")
            
            print("\n" + "=" * 80)
            print("✅ 同步完成！")
            print("=" * 80)
            print(f"\n本地資料庫位置: {old_db_path}")
            print(f"同步時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"總共同步: {total} 筆記錄")
            
            return True
            
    except Exception as e:
        print(f"\n❌ 同步失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Render PostgreSQL 同步到本地 SQLite 工具")
    print("此工具會將線上資料庫的所有資料同步到本地 SQLite")
    print("\n警告：此操作會完全替換本地資料庫的內容！")
    
    response = input("\n是否繼續？(yes/no): ")
    if response.lower() != "yes":
        print("已取消")
        sys.exit(0)
    
    success = sync_database()
    
    if success:
        print("\n✅ 同步成功！本地資料庫現在與線上資料庫一致。")
    else:
        print("\n❌ 同步失敗！請檢查錯誤訊息。")


