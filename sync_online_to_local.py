#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從 Render 線上資料庫同步資料到本地 SQLite
同步策略：完全替換本地資料
"""

import os
import sys
from datetime import datetime

# 確保能夠導入 app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def sync_database():
    """同步線上資料庫到本地"""
    print("=" * 80)
    print("開始從 Render 資料庫同步資料到本地...")
    print("=" * 80)
    
    try:
        # 步驟 1: 獲取線上資料
        print("\n[1/4] 連接到線上資料庫並讀取資料...")
        from app import app, db
        
        # 強制使用線上資料庫
        online_db_url = os.environ.get('DATABASE_URL')
        if not online_db_url:
            print("❌ 錯誤：未找到 DATABASE_URL 環境變數")
            print("請先設置 Render 資料庫連接字串")
            return False
        
        # 修復 URL 格式
        if online_db_url.startswith('postgres://'):
            online_db_url = online_db_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif online_db_url.startswith('postgresql://'):
            online_db_url = online_db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        
        # 使用線上資料庫
        app.config["SQLALCHEMY_DATABASE_URI"] = online_db_url
        
        # 重新初始化 db（使用線上配置）
        from flask_sqlalchemy import SQLAlchemy
        db_online = SQLAlchemy(app)
        
        # 重新導入所有模型（使用新的 db 實例）
        from app import (
            User, Holder, CashAccount, Channel, Customer, 
            PurchaseRecord, SalesRecord, LedgerEntry, CashLog,
            FIFOInventory, FIFOSalesAllocation, ProfitTransaction
        )
        
        with app.app_context():
            # 讀取所有線上資料
            users = db_online.session.execute(db_online.select(User)).scalars().all()
            holders = db_online.session.execute(db_online.select(Holder)).scalars().all()
            cash_accounts = db_online.session.execute(db_online.select(CashAccount)).scalars().all()
            channels = db_online.session.execute(db_online.select(Channel)).scalars().all()
            customers = db_online.session.execute(db_online.select(Customer)).scalars().all()
            purchases = db_online.session.execute(db_online.select(PurchaseRecord)).scalars().all()
            sales = db_online.session.execute(db_online.select(SalesRecord)).scalars().all()
            ledger_entries = db_online.session.execute(db_online.select(LedgerEntry)).scalars().all()
            cash_logs = db_online.session.execute(db_online.select(CashLog)).scalars().all()
            fifo_inventory = db_online.session.execute(db_online.select(FIFOInventory)).scalars().all()
            fifo_sales = db_online.session.execute(db_online.select(FIFOSalesAllocation)).scalars().all()
            profit_transactions = db_online.session.execute(db_online.select(ProfitTransaction)).scalars().all()
            
            print(f"✅ 讀取完成：")
            print(f"   Users: {len(users)}")
            print(f"   Holders: {len(holders)}")
            print(f"   CashAccounts: {len(cash_accounts)}")
            print(f"   Channels: {len(channels)}")
            print(f"   Customers: {len(customers)}")
            print(f"   Purchases: {len(purchases)}")
            print(f"   Sales: {len(sales)}")
            print(f"   LedgerEntries: {len(ledger_entries)}")
            print(f"   CashLogs: {len(cash_logs)}")
            print(f"   FIFOInventory: {len(fifo_inventory)}")
            print(f"   FIFOSales: {len(fifo_sales)}")
            print(f"   ProfitTransactions: {len(profit_transactions)}")
        
        # 步驟 2: 連接本地資料庫
        print("\n[2/4] 連接到本地資料庫...")
        
        # 配置本地 SQLite
        basedir = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(basedir, "instance")
        os.makedirs(instance_path, exist_ok=True)
        local_db_uri = "sqlite:///" + os.path.join(instance_path, "sales_system_v4.db")
        
        app.config["SQLALCHEMY_DATABASE_URI"] = local_db_uri
        
        # 重新初始化 db（使用本地配置）
        db_local = SQLAlchemy(app)
        
        # 確保本地資料庫有所有表格
        with app.app_context():
            db_local.create_all()
            print("✅ 本地資料庫連接成功，表格已準備完成")
        
        # 步驟 3: 清空本地資料庫
        print("\n[3/4] 清空本地資料庫...")
        with app.app_context():
            # 按順序刪除，避免外鍵約束錯誤
            try:
                db_local.session.execute(db_local.text('DELETE FROM profit_transactions'))
                db_local.session.execute(db_local.text('DELETE FROM fifo_sales_allocation'))
                db_local.session.execute(db_local.text('DELETE FROM fifo_inventory'))
                db_local.session.execute(db_local.text('DELETE FROM cash_logs'))
                db_local.session.execute(db_local.text('DELETE FROM ledger_entries'))
                db_local.session.execute(db_local.text('DELETE FROM sales_records'))
                db_local.session.execute(db_local.text('DELETE FROM purchase_records'))
                db_local.session.execute(db_local.text('DELETE FROM customers'))
                db_local.session.execute(db_local.text('DELETE FROM channels'))
                db_local.session.execute(db_local.text('DELETE FROM cash_accounts'))
                db_local.session.execute(db_local.text('DELETE FROM holders'))
                db_local.session.execute(db_local.text('DELETE FROM users'))
                db_local.session.commit()
                print("✅ 本地資料庫已清空")
            except Exception as e:
                print(f"⚠️ 清空資料庫時出現錯誤（可能表格為空）: {e}")
                db_local.session.rollback()
        
        # 步驟 4: 寫入線上資料到本地
        print("\n[4/4] 寫入資料到本地資料庫...")
        
        with app.app_context():
            # 重新設置為線上資料庫
            app.config["SQLALCHEMY_DATABASE_URI"] = online_db_url
            db_online = SQLAlchemy(app)
            
            # 重新導入模型（使用線上 db）
            from app import (
                User as UserOnline, Holder as HolderOnline, CashAccount as CashAccountOnline,
                Channel as ChannelOnline, Customer as CustomerOnline, 
                PurchaseRecord as PurchaseRecordOnline, SalesRecord as SalesRecordOnline,
                LedgerEntry as LedgerEntryOnline, CashLog as CashLogOnline,
                FIFOInventory as FIFOInventoryOnline, FIFOSalesAllocation as FIFOSalesAllocationOnline,
                ProfitTransaction as ProfitTransactionOnline
            )
            
            # 讀取所有線上資料
            users = db_online.session.execute(db_online.select(UserOnline)).scalars().all()
            holders = db_online.session.execute(db_online.select(HolderOnline)).scalars().all()
            cash_accounts = db_online.session.execute(db_online.select(CashAccountOnline)).scalars().all()
            channels = db_online.session.execute(db_online.select(ChannelOnline)).scalars().all()
            customers = db_online.session.execute(db_online.select(CustomerOnline)).scalars().all()
            purchases = db_online.session.execute(db_online.select(PurchaseRecordOnline)).scalars().all()
            sales = db_online.session.execute(db_online.select(SalesRecordOnline)).scalars().all()
            ledger_entries = db_online.session.execute(db_online.select(LedgerEntryOnline)).scalars().all()
            cash_logs = db_online.session.execute(db_online.select(CashLogOnline)).scalars().all()
            fifo_inventory = db_online.session.execute(db_online.select(FIFOInventoryOnline)).scalars().all()
            fifo_sales = db_online.session.execute(db_online.select(FIFOSalesAllocationOnline)).scalars().all()
            profit_transactions = db_online.session.execute(db_online.select(ProfitTransactionOnline)).scalars().all()
            
            # 轉換為本地資料庫
            app.config["SQLALCHEMY_DATABASE_URI"] = local_db_uri
            db_local = SQLAlchemy(app)
            
            # 重新導入模型（使用本地 db）
            from app import (
                User as UserLocal, Holder as HolderLocal, CashAccount as CashAccountLocal,
                Channel as ChannelLocal, Customer as CustomerLocal,
                PurchaseRecord as PurchaseRecordLocal, SalesRecord as SalesRecordLocal,
                LedgerEntry as LedgerEntryLocal, CashLog as CashLogLocal,
                FIFOInventory as FIFOInventoryLocal, FIFOSalesAllocation as FIFOSalesAllocationLocal,
                ProfitTransaction as ProfitTransactionLocal
            )
            
            # 創建字典映射 ID（避免外鍵問題）
            user_id_map = {}
            holder_id_map = {}
            channel_id_map = {}
            customer_id_map = {}
            account_id_map = {}
            
            # 1. 插入 Users
            print("  寫入 Users...")
            for u in users:
                new_user = UserLocal(
                    id=u.id,
                    username=u.username,
                    password_hash=u.password_hash,
                    role=u.role
                )
                db_local.session.add(new_user)
                user_id_map[u.id] = new_user
            db_local.session.commit()
            print(f"    ✅ {len(users)} 筆 Users")
            
            # 2. 插入 Holders
            print("  寫入 Holders...")
            for h in holders:
                new_holder = HolderLocal(
                    id=h.id,
                    name=h.name,
                    is_active=h.is_active
                )
                db_local.session.add(new_holder)
                holder_id_map[h.id] = new_holder
            db_local.session.commit()
            print(f"    ✅ {len(holders)} 筆 Holders")
            
            # 3. 插入 CashAccounts
            print("  寫入 CashAccounts...")
            for c in cash_accounts:
                new_account = CashAccountLocal(
                    id=c.id,
                    name=c.name,
                    currency=c.currency,
                    balance=c.balance,
                    profit_balance=c.profit_balance,
                    holder_id=c.holder_id,
                    is_active=c.is_active
                )
                db_local.session.add(new_account)
                account_id_map[c.id] = new_account
            db_local.session.commit()
            print(f"    ✅ {len(cash_accounts)} 筆 CashAccounts")
            
            # 4. 插入 Channels
            print("  寫入 Channels...")
            for c in channels:
                new_channel = ChannelLocal(
                    id=c.id,
                    name=c.name
                )
                db_local.session.add(new_channel)
                channel_id_map[c.id] = new_channel
            db_local.session.commit()
            print(f"    ✅ {len(channels)} 筆 Channels")
            
            # 5. 插入 Customers
            print("  寫入 Customers...")
            for c in customers:
                new_customer = CustomerLocal(
                    id=c.id,
                    name=c.name,
                    total_receivables_twd=c.total_receivables_twd,
                    is_active=c.is_active
                )
                db_local.session.add(new_customer)
                customer_id_map[c.id] = new_customer
            db_local.session.commit()
            print(f"    ✅ {len(customers)} 筆 Customers")
            
            # 6. 插入 PurchaseRecords
            print("  寫入 PurchaseRecords...")
            for p in purchases:
                new_purchase = PurchaseRecordLocal(
                    id=p.id,
                    purchase_date=p.purchase_date,
                    payment_account_id=p.payment_account_id,
                    deposit_account_id=p.deposit_account_id,
                    rmb_amount=p.rmb_amount,
                    twd_cost=p.twd_cost,
                    exchange_rate=p.exchange_rate,
                    channel_id=p.channel_id,
                    note=getattr(p, 'note', None) if hasattr(p, 'note') else None,
                    operator_id=p.operator_id
                )
                db_local.session.add(new_purchase)
            db_local.session.commit()
            print(f"    ✅ {len(purchases)} 筆 PurchaseRecords")
            
            # 7. 插入 SalesRecords
            print("  寫入 SalesRecords...")
            for s in sales:
                new_sale = SalesRecordLocal(
                    id=s.id,
                    customer_id=s.customer_id,
                    rmb_account_id=s.rmb_account_id,
                    rmb_amount=s.rmb_amount,
                    exchange_rate=s.exchange_rate,
                    twd_amount=s.twd_amount,
                    is_settled=s.is_settled,
                    note=getattr(s, 'note', None) if hasattr(s, 'note') else None,
                    operator_id=s.operator_id,
                    created_at=s.created_at
                )
                db_local.session.add(new_sale)
            db_local.session.commit()
            print(f"    ✅ {len(sales)} 筆 SalesRecords")
            
            # 8. 插入 LedgerEntries
            print("  寫入 LedgerEntries...")
            for e in ledger_entries:
                new_entry = LedgerEntryLocal(
                    id=e.id,
                    entry_type=e.entry_type,
                    account_id=e.account_id,
                    from_account_id=e.from_account_id,
                    to_account_id=e.to_account_id,
                    amount=e.amount,
                    description=e.description,
                    entry_date=e.entry_date,
                    operator_id=e.operator_id,
                    profit_before=e.profit_before,
                    profit_after=e.profit_after,
                    profit_change=e.profit_change
                )
                db_local.session.add(new_entry)
            db_local.session.commit()
            print(f"    ✅ {len(ledger_entries)} 筆 LedgerEntries")
            
            # 9. 插入 CashLogs
            print("  寫入 CashLogs...")
            for c in cash_logs:
                new_log = CashLogLocal(
                    id=c.id,
                    type=c.type,
                    description=c.description,
                    amount=c.amount,
                    time=c.time,
                    operator_id=c.operator_id
                )
                db_local.session.add(new_log)
            db_local.session.commit()
            print(f"    ✅ {len(cash_logs)} 筆 CashLogs")
            
            # 10. 插入 FIFOInventory
            print("  寫入 FIFOInventory...")
            for f in fifo_inventory:
                new_fifo = FIFOInventoryLocal(
                    id=f.id,
                    purchase_record_id=f.purchase_record_id,
                    purchase_date=f.purchase_date,
                    rmb_amount=f.rmb_amount,
                    unit_cost_twd=f.unit_cost_twd,
                    remaining_rmb=f.remaining_rmb,
                    created_at=f.created_at
                )
                db_local.session.add(new_fifo)
            db_local.session.commit()
            print(f"    ✅ {len(fifo_inventory)} 筆 FIFOInventory")
            
            # 11. 插入 FIFOSalesAllocation
            print("  寫入 FIFOSalesAllocation...")
            for f in fifo_sales:
                new_allocation = FIFOSalesAllocationLocal(
                    id=f.id,
                    fifo_inventory_id=f.fifo_inventory_id,
                    sales_record_id=f.sales_record_id,
                    allocated_rmb=f.allocated_rmb,
                    allocated_cost_twd=f.allocated_cost_twd,
                    created_at=f.created_at
                )
                db_local.session.add(new_allocation)
            db_local.session.commit()
            print(f"    ✅ {len(fifo_sales)} 筆 FIFOSalesAllocation")
            
            # 12. 插入 ProfitTransactions
            print("  寫入 ProfitTransactions...")
            for p in profit_transactions:
                new_profit = ProfitTransactionLocal(
                    id=p.id,
                    account_id=p.account_id,
                    amount=p.amount,
                    transaction_type=p.transaction_type,
                    description=p.description,
                    note=p.note,
                    related_transaction_id=p.related_transaction_id,
                    related_transaction_type=p.related_transaction_type,
                    created_at=p.created_at,
                    operator_id=p.operator_id
                )
                db_local.session.add(new_profit)
            db_local.session.commit()
            print(f"    ✅ {len(profit_transactions)} 筆 ProfitTransactions")
            
            print("\n" + "=" * 80)
            print("✅ 資料同步完成！")
            print("=" * 80)
            print(f"\n本地資料庫位置: {local_db_uri}")
            print(f"同步時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ 同步失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Render 資料庫同步到本地工具")
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



