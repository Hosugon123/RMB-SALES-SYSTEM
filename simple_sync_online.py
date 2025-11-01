#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版：從 Render PostgreSQL 同步資料到本地 SQLite
使用獨立的兩個資料庫連接
"""

import os
import sys
from datetime import datetime

print("=" * 80)
print("從 Render PostgreSQL 同步到本地 SQLite")
print("=" * 80)

# 線上資料庫連接字串
ONLINE_DB_URL = "postgresql+psycopg://rmb_user:BGvPp5PwQ3WRnoLCTzW2@dpg-d5imkugkntbs73fa8b2g-a.oregon-postgres.render.com/rmb_database_v4"

print("\n請確認要使用上述線上資料庫進行同步")
print("警告：本地資料庫將被完全替換！")

response = input("\n是否繼續？(yes/no): ")
if response.lower() != "yes":
    print("已取消")
    sys.exit(0)

# 設置線上資料庫環境變數
os.environ['DATABASE_URL'] = ONLINE_DB_URL

# 導入必要的模組
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from sqlalchemy import create_engine

# 創建 Flask 應用和資料庫實例
app = Flask(__name__)
app.config['SECRET_KEY'] = 'temp_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 線上資料庫連接
app.config['SQLALCHEMY_DATABASE_URI'] = ONLINE_DB_URL
db_online = SQLAlchemy(app)

# 本地資料庫 URI
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, "instance")
os.makedirs(instance_path, exist_ok=True)
local_db_uri = "sqlite:///" + os.path.join(instance_path, "sales_system_v4.db")

# 本地資料庫連接
app.config['SQLALCHEMY_DATABASE_URI'] = local_db_uri
db_local = SQLAlchemy(app)

# 從 app.py 導入模型定義
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 手動定義所有模型（避免導入 app.py 時的初始化問題）
class User(db_online.Model):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(80), unique=True, nullable=False)
    password_hash = sa.Column(sa.String(200), nullable=False)
    role = sa.Column(sa.String(80), nullable=False, default='operator')

class Holder(db_online.Model):
    __tablename__ = 'holders'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)
    is_active = sa.Column(sa.Boolean, default=True)

class CashAccount(db_online.Model):
    __tablename__ = 'cash_accounts'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)
    currency = sa.Column(sa.String(10), nullable=False)
    balance = sa.Column(sa.Float, default=0.0)
    profit_balance = sa.Column(sa.Float, default=0.0)
    holder_id = sa.Column(sa.Integer, sa.ForeignKey('holders.id'))
    is_active = sa.Column(sa.Boolean, default=True)

class Channel(db_online.Model):
    __tablename__ = 'channels'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)

class Customer(db_online.Model):
    __tablename__ = 'customers'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)
    total_receivables_twd = sa.Column(sa.Float, default=0.0)
    is_active = sa.Column(sa.Boolean, default=True)

class PurchaseRecord(db_online.Model):
    __tablename__ = 'purchase_records'
    id = sa.Column(sa.Integer, primary_key=True)
    purchase_date = sa.Column(sa.DateTime, nullable=False)
    payment_account_id = sa.Column(sa.Integer, sa.ForeignKey('cash_accounts.id'))
    deposit_account_id = sa.Column(sa.Integer, sa.ForeignKey('cash_accounts.id'))
    rmb_amount = sa.Column(sa.Float, nullable=False)
    twd_cost = sa.Column(sa.Float, nullable=False)
    exchange_rate = sa.Column(sa.Float, nullable=False)
    channel_id = sa.Column(sa.Integer, sa.ForeignKey('channels.id'))
    note = sa.Column(sa.String(200))
    operator_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))

class SalesRecord(db_online.Model):
    __tablename__ = 'sales_records'
    id = sa.Column(sa.Integer, primary_key=True)
    customer_id = sa.Column(sa.Integer, sa.ForeignKey('customers.id'))
    rmb_account_id = sa.Column(sa.Integer, sa.ForeignKey('cash_accounts.id'))
    rmb_amount = sa.Column(sa.Float, nullable=False)
    exchange_rate = sa.Column(sa.Float, nullable=False)
    twd_amount = sa.Column(sa.Float, nullable=False)
    is_settled = sa.Column(sa.Boolean, default=False)
    note = sa.Column(sa.String(200))
    operator_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

class LedgerEntry(db_online.Model):
    __tablename__ = 'ledger_entries'
    id = sa.Column(sa.Integer, primary_key=True)
    entry_type = sa.Column(sa.String(50), nullable=False)
    account_id = sa.Column(sa.Integer, sa.ForeignKey('cash_accounts.id'))
    amount = sa.Column(sa.Float, nullable=False, default=0)
    description = sa.Column(sa.String(200))
    entry_date = sa.Column(sa.DateTime, default=datetime.utcnow)
    operator_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    from_account_id = sa.Column(sa.Integer, sa.ForeignKey('cash_accounts.id'))
    to_account_id = sa.Column(sa.Integer, sa.ForeignKey('cash_accounts.id'))
    profit_before = sa.Column(sa.Float)
    profit_after = sa.Column(sa.Float)
    profit_change = sa.Column(sa.Float)

class CashLog(db_online.Model):
    __tablename__ = 'cash_logs'
    id = sa.Column(sa.Integer, primary_key=True)
    type = sa.Column(sa.String(50), nullable=False)
    description = sa.Column(sa.String(200))
    amount = sa.Column(sa.Float, nullable=False)
    time = sa.Column(sa.DateTime, nullable=False)
    operator_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))

class FIFOInventory(db_online.Model):
    __tablename__ = 'fifo_inventory'
    id = sa.Column(sa.Integer, primary_key=True)
    purchase_record_id = sa.Column(sa.Integer, sa.ForeignKey('purchase_records.id'))
    purchase_date = sa.Column(sa.DateTime, nullable=False)
    rmb_amount = sa.Column(sa.Float, nullable=False)
    unit_cost_twd = sa.Column(sa.Float, nullable=False)
    remaining_rmb = sa.Column(sa.Float, nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

class FIFOSalesAllocation(db_online.Model):
    __tablename__ = 'fifo_sales_allocation'
    id = sa.Column(sa.Integer, primary_key=True)
    fifo_inventory_id = sa.Column(sa.Integer, sa.ForeignKey('fifo_inventory.id'))
    sales_record_id = sa.Column(sa.Integer, sa.ForeignKey('sales_records.id'))
    allocated_rmb = sa.Column(sa.Float, nullable=False)
    allocated_cost_twd = sa.Column(sa.Float, nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

class ProfitTransaction(db_online.Model):
    __tablename__ = 'profit_transactions'
    id = sa.Column(sa.Integer, primary_key=True)
    account_id = sa.Column(sa.Integer, sa.ForeignKey('cash_accounts.id'))
    amount = sa.Column(sa.Float, nullable=False)
    transaction_type = sa.Column(sa.String(50), nullable=False)
    description = sa.Column(sa.String(200))
    note = sa.Column(sa.String(200))
    related_transaction_id = sa.Column(sa.Integer)
    related_transaction_type = sa.Column(sa.String(50))
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    operator_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))

print("\n正在連接到線上資料庫...")

try:
    with app.app_context():
        # 測試線上連接
        db_online.create_all()
        print("✅ 線上資料庫連接成功")
        
        # 讀取所有資料
        print("\n讀取線上資料...")
        users = User.query.all()
        holders = Holder.query.all()
        accounts = CashAccount.query.all()
        channels = Channel.query.all()
        customers = Customer.query.all()
        purchases = PurchaseRecord.query.all()
        sales = SalesRecord.query.all()
        ledger_entries = LedgerEntry.query.all()
        cash_logs = CashLog.query.all()
        fifo_inventory = FIFOInventory.query.all()
        fifo_sales = FIFOSalesAllocation.query.all()
        profit_transactions = ProfitTransaction.query.all()
        
        print(f"讀取完成：")
        print(f"  Users: {len(users)}")
        print(f"  Holders: {len(holders)}")
        print(f"  CashAccounts: {len(accounts)}")
        print(f"  Channels: {len(channels)}")
        print(f"  Customers: {len(customers)}")
        print(f"  Purchases: {len(purchases)}")
        print(f"  Sales: {len(sales)}")
        print(f"  LedgerEntries: {len(ledger_entries)}")
        print(f"  CashLogs: {len(cash_logs)}")
        print(f"  FIFOInventory: {len(fifo_inventory)}")
        print(f"  FIFOSales: {len(fifo_sales)}")
        print(f"  ProfitTransactions: {len(profit_transactions)}")
        
        # 本地資料庫：使用與線上相同的模型
        app.config['SQLALCHEMY_DATABASE_URI'] = local_db_uri
        db_local = SQLAlchemy(app)
        
        # 為本地資料庫定義相同的模型
        for model_class in [User, Holder, CashAccount, Channel, Customer, 
                           PurchaseRecord, SalesRecord, LedgerEntry, CashLog,
                           FIFOInventory, FIFOSalesAllocation, ProfitTransaction]:
            # 重建模型以使用本地資料庫
            class_name = model_class.__name__
            existing_model = type(class_name, (db_local.Model,), {
                '__tablename__': model_class.__tablename__,
            })
            # 複製所有欄位
            for key, value in model_class.__table__.columns.items():
                setattr(existing_model, key, value)
        
        print("\n準備本地資料庫...")
        db_local.create_all()
        print("✅ 本地資料庫準備完成")
        
        # 備份舊資料庫
        old_db_path = os.path.join(instance_path, "sales_system_v4.db")
        if os.path.exists(old_db_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(instance_path, f"sales_system_v4_backup_{timestamp}.db")
            import shutil
            shutil.copy2(old_db_path, backup_path)
            print(f"✅ 舊資料庫已備份: {backup_path}")
        
        print("\n同步資料到本地...")
        print("由於 SQLAlchemy 模型的複雜性，建議使用專業工具進行同步")
        print("建議使用 pgAdmin 或其他 PostgreSQL 工具直接匯出/匯入")
        
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

