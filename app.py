import os
import traceback
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date, timezone
from sqlalchemy import func, and_

# ===================================================================
# 2. App、資料庫、遷移與登入管理器的初始化
# ===================================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "a_very_very_secret_key_that_is_long_and_secure"
)
# 資料庫配置 - 支持 PostgreSQL (Render) 和 SQLite (本地)
if os.environ.get('DATABASE_URL'):
    # Render 雲端環境 - 使用 PostgreSQL
    database_url = os.environ.get('DATABASE_URL')
    # 修復 Render PostgreSQL URL 格式問題，強制使用 psycopg3
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    print(f"使用資料庫連接字串: {database_url[:50]}...")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # 本地開發環境 - 使用 SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, "instance")
    os.makedirs(instance_path, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        instance_path, "sales_system_v4.db"
    )

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "請先登入以存取此頁面。"
login_manager.login_message_category = "info"

# 在應用程式啟動時初始化資料庫
def init_database():
    """初始化資料庫和創建預設管理員帳戶"""
    try:
        with app.app_context():
            # 檢查資料庫是否已經初始化
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"檢查資料庫表格: {existing_tables}")
            
            if 'user' not in existing_tables:
                # 只有當表格不存在時才創建
                print("創建資料庫表格...")
                db.create_all()
                print("資料庫表格已創建")
            else:
                print("資料庫表格已存在")
                
                # 檢查現有數據
                try:
                    user_count = User.query.count()
                    print(f"現有用戶數量: {user_count}")
                    
                    if user_count > 0:
                        print("資料庫中已有數據，跳過初始化")
                        return
                except Exception as e:
                    print(f"檢查用戶數據時出錯: {e}")
            
            # 檢查是否已有管理員帳戶
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                # 創建預設管理員帳戶
                admin_user = User(
                    username='admin',
                    role='admin',
                    is_active=True
                )
                admin_user.set_password('admin123')  # 預設密碼，請在首次登入後修改
                
                db.session.add(admin_user)
                db.session.commit()
                print("預設管理員帳戶創建成功")
                print("   用戶名: admin")
                print("   密碼: admin123")
                print("   請在首次登入後立即修改密碼！")
            else:
                print("管理員帳戶已存在")
                
    except Exception as e:
        print(f"資料庫初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

# 使用 Flask 3.x 兼容的方式初始化資料庫
@app.before_request
def before_request():
    """在每個請求前檢查資料庫是否已初始化"""
    if not hasattr(app, '_database_initialized'):
        print("首次請求，初始化資料庫...")
        init_database()
        app._database_initialized = True
        print("資料庫初始化完成")
    else:
        print("資料庫已初始化，跳過")

# ===================================================================
# 3. 資料庫模型 (Models) 定義 - 【V4.0 職責分離重構版】
# ===================================================================


class User(db.Model, UserMixin):
    __tablename__ = "user"  # <---【修正】統一為單數
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(
        db.String(50), default="operator", nullable=False
    )  # <---【修正】引入 Role
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    @property
    def is_admin(self):
        return self.role == "admin"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Holder(db.Model):
    __tablename__ = "holders"  # <---【職責】只代表「內部資金持有人」
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    cash_accounts = db.relationship(
        "CashAccount",
        back_populates="holder",
        lazy="select",
        cascade="all, delete-orphan",
    )


class Customer(db.Model):
    __tablename__ = "customers"  # <---【新增】專門代表「外部顧客」
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    total_receivables_twd = db.Column(db.Float, nullable=False, default=0.0)
    sales = db.relationship(
        "SalesRecord",
        back_populates="customer",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )


class CashAccount(db.Model):
    __tablename__ = "cash_accounts"
    id = db.Column(db.Integer, primary_key=True)
    holder_id = db.Column(db.Integer, db.ForeignKey("holders.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    profit_balance = db.Column(db.Float, nullable=False, default=0.0)  # 新增：獨立利潤餘額
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    holder = db.relationship("Holder", back_populates="cash_accounts", lazy="select")


class Channel(db.Model):
    __tablename__ = "channels"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    purchase_records = db.relationship(
        "PurchaseRecord", back_populates="channel", lazy="dynamic"
    )


class PurchaseRecord(db.Model):
    __tablename__ = "purchase_records"
    id = db.Column(db.Integer, primary_key=True)
    payment_account_id = db.Column(
        db.Integer, db.ForeignKey("cash_accounts.id"), nullable=True
    )
    deposit_account_id = db.Column(
        db.Integer, db.ForeignKey("cash_accounts.id"), nullable=True
    )
    channel_id = db.Column(db.Integer, db.ForeignKey("channels.id"), nullable=True)
    rmb_amount = db.Column(db.Float, nullable=False)
    exchange_rate = db.Column(db.Float, nullable=False)
    twd_cost = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), nullable=False, default='paid')  # 'paid' 或 'unpaid'
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )  # <---【修正】統一外鍵目標
    channel = db.relationship("Channel", back_populates="purchase_records")
    payment_account = db.relationship(
        "CashAccount", foreign_keys=[payment_account_id], backref="paid_purchases"
    )
    deposit_account = db.relationship(
        "CashAccount", foreign_keys=[deposit_account_id], backref="deposited_purchases"
    )
    operator = db.relationship("User", backref="purchase_records")
    
    # FIFO 關聯
    fifo_inventory = db.relationship("FIFOInventory", back_populates="purchase_record", cascade="all, delete-orphan")
    
    # 待付款項關聯
    pending_payment = db.relationship("PendingPayment", back_populates="purchase_record", cascade="all, delete-orphan")


class PendingPayment(db.Model):
    """待付款項模型 - 記錄未付款的買入記錄"""
    __tablename__ = "pending_payments"
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_record_id = db.Column(db.Integer, db.ForeignKey("purchase_records.id"), nullable=False)
    amount_twd = db.Column(db.Float, nullable=False)  # 待付金額（台幣）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)  # 付款時間
    is_settled = db.Column(db.Boolean, nullable=False, default=False)  # 是否已結清
    
    # 關聯關係
    purchase_record = db.relationship("PurchaseRecord", back_populates="pending_payment")


class FIFOInventory(db.Model):
    """FIFO庫存模型 - 記錄每批貨物的庫存狀態"""
    __tablename__ = "fifo_inventory"
    id = db.Column(db.Integer, primary_key=True)
    purchase_record_id = db.Column(db.Integer, db.ForeignKey("purchase_records.id"), nullable=False)
    
    # 庫存信息
    rmb_amount = db.Column(db.Float, nullable=False)  # 原始買入RMB數量
    remaining_rmb = db.Column(db.Float, nullable=False)  # 剩餘RMB數量
    unit_cost_twd = db.Column(db.Float, nullable=False)  # 單位成本（台幣）
    exchange_rate = db.Column(db.Float, nullable=False)  # 買入匯率
    
    # 時間信息
    purchase_date = db.Column(db.DateTime, nullable=False)  # 買入日期
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    purchase_record = db.relationship("PurchaseRecord", back_populates="fifo_inventory")
    sales_allocations = db.relationship("FIFOSalesAllocation", back_populates="fifo_inventory", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FIFOInventory(id={self.id}, remaining_rmb={self.remaining_rmb}, unit_cost={self.unit_cost_twd})>"


class FIFOSalesAllocation(db.Model):
    """FIFO銷售分配模型 - 記錄每次銷售從哪批庫存中扣除"""
    __tablename__ = "fifo_sales_allocations"
    id = db.Column(db.Integer, primary_key=True)
    
    # 關聯ID
    fifo_inventory_id = db.Column(db.Integer, db.ForeignKey("fifo_inventory.id"), nullable=False)
    sales_record_id = db.Column(db.Integer, db.ForeignKey("sales_records.id"), nullable=False)
    
    # 分配信息
    allocated_rmb = db.Column(db.Float, nullable=False)  # 分配的RMB數量
    allocated_cost_twd = db.Column(db.Float, nullable=False)  # 分配的台幣成本
    allocation_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯
    fifo_inventory = db.relationship("FIFOInventory", back_populates="sales_allocations")
    sales_record = db.relationship("SalesRecord", backref="fifo_allocations")
    
    def __repr__(self):
        return f"<FIFOSalesAllocation(id={self.id}, rmb={self.allocated_rmb}, cost={self.allocated_cost_twd})>"


class SalesRecord(db.Model):
    __tablename__ = "sales_records"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("customers.id"), nullable=False
    )  # <---【修正】指向 customers 表
    rmb_account_id = db.Column(
        db.Integer, db.ForeignKey("cash_accounts.id"), nullable=True
    )
    rmb_amount = db.Column(db.Float, nullable=False)
    exchange_rate = db.Column(db.Float, nullable=False)
    twd_amount = db.Column(db.Float, nullable=False)
    is_settled = db.Column(
        db.Boolean, nullable=False, default=False
    )  # <---【修正】使用 is_settled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )  # <---【修正】統一外鍵目標
    customer = db.relationship("Customer", back_populates="sales")
    rmb_account = db.relationship("CashAccount", foreign_keys=[rmb_account_id], backref="sales_from_account")
    operator = db.relationship("User", backref="sales_records")
    transactions = db.relationship(
        "Transaction", back_populates="sales_record", cascade="all, delete-orphan"
    )


class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    sales_record_id = db.Column(
        db.Integer, db.ForeignKey("sales_records.id"), nullable=False
    )
    twd_account_id = db.Column(
        db.Integer, db.ForeignKey("cash_accounts.id"), nullable=False
    )
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.String(200))
    sales_record = db.relationship("SalesRecord", back_populates="transactions")
    twd_account = db.relationship("CashAccount")


class LedgerEntry(db.Model):
    __tablename__ = "ledger_entries"
    id = db.Column(db.Integer, primary_key=True)
    entry_type = db.Column(db.String(50), nullable=False, index=True)
    account_id = db.Column(
        db.Integer, db.ForeignKey("cash_accounts.id"), nullable=True
    )  # <---【修正】允許為空
    amount = db.Column(db.Float, nullable=False, default=0)
    description = db.Column(db.String(200))
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )  # <---【修正】統一外鍵目標
    
    # 新增：詳細利潤信息欄位
    profit_before = db.Column(db.Float, nullable=True)  # 變動前利潤
    profit_after = db.Column(db.Float, nullable=True)   # 變動後利潤
    profit_change = db.Column(db.Float, nullable=True)  # 變動之利潤數字
    
    account = db.relationship("CashAccount")
    operator = db.relationship("User")


class CashLog(db.Model):
    __tablename__ = "cash_logs"
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50))
    description = db.Column(db.String(200))
    amount = db.Column(db.Float)
    # 新增操作人員
    operator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    operator = db.relationship("User")
    # 暫時移除帳戶關聯，避免數據庫結構不匹配
    # account_id = db.Column(db.Integer, db.ForeignKey("cash_accounts.id"), nullable=True)
    # account = db.relationship("CashAccount", backref="cash_logs")


# ===================================================================
# 新增：刷卡記帳模型
# ===================================================================
class CardPurchase(db.Model):
    __tablename__ = "card_purchases"
    id = db.Column(db.Integer, primary_key=True)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    supplier = db.Column(db.String(200), nullable=False)  # 刷卡對象/供應商
    rmb_amount = db.Column(db.Float, nullable=False)  # 原始刷卡金額
    twd_equivalent = db.Column(db.Float, nullable=False)  # 信用卡帳單金額
    calculated_rate = db.Column(db.Float, nullable=False)  # 計算出的成本匯率
    rmb_with_fee = db.Column(db.Float, nullable=False)  # 含3%手續費的RMB金額
    operator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯關係
    operator = db.relationship("User", backref="card_purchases")
    
    def __repr__(self):
        return f'<CardPurchase {self.id}: {self.supplier} - ¥{self.rmb_amount}>'


# ===================================================================
# 刪除記錄審計模型
# ===================================================================
class DeleteAuditLog(db.Model):
    """刪除記錄審計模型 - 記錄所有刪除操作"""
    __tablename__ = "delete_audit_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 刪除的記錄資訊
    table_name = db.Column(db.String(50), nullable=False)  # 被刪除的表名
    record_id = db.Column(db.Integer, nullable=False)  # 被刪除的記錄ID
    
    # 刪除前的資料（JSON格式存儲）
    deleted_data = db.Column(db.Text, nullable=False)  # 被刪除記錄的完整資料
    
    # 帳戶餘額變化（JSON格式存儲）
    balance_changes = db.Column(db.Text, nullable=True)  # 刪除前後的帳戶餘額變化
    
    # 操作資訊
    operation_type = db.Column(db.String(50), nullable=False)  # 操作類型：DELETE, REVERSE_PURCHASE, REVERSE_SALE等
    description = db.Column(db.String(500), nullable=True)  # 操作描述
    
    # 操作者資訊
    operator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    operator_name = db.Column(db.String(100), nullable=True)  # 操作者名稱（備用）
    
    # 時間資訊
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # IP和用戶代理（用於安全審計）
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    
    # 關聯關係
    operator = db.relationship("User", backref="delete_audit_logs")
    
    def __repr__(self):
        return f'<DeleteAuditLog {self.id}: {self.table_name}.{self.record_id} by {self.operator_name}>'
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'deleted_data': self.deleted_data,
            'operation_type': self.operation_type,
            'description': self.description,
            'operator_name': self.operator_name,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }


class ProfitTransaction(db.Model):
    """利潤交易記錄模型 - 記錄所有利潤變動"""
    __tablename__ = "profit_transactions"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 關聯帳戶
    account_id = db.Column(db.Integer, db.ForeignKey("cash_accounts.id"), nullable=False)
    
    # 交易資訊
    transaction_type = db.Column(db.String(50), nullable=False)  # PROFIT_EARNED, PROFIT_WITHDRAW, PROFIT_ADJUSTMENT
    amount = db.Column(db.Float, nullable=False)  # 利潤變動金額（正數為增加，負數為減少）
    balance_before = db.Column(db.Float, nullable=False)  # 變動前利潤餘額
    balance_after = db.Column(db.Float, nullable=False)   # 變動後利潤餘額
    
    # 關聯交易記錄
    related_transaction_id = db.Column(db.Integer, nullable=True)  # 關聯的交易記錄ID
    related_transaction_type = db.Column(db.String(50), nullable=True)  # 關聯的交易類型
    
    # 描述和備註
    description = db.Column(db.String(500), nullable=True)
    note = db.Column(db.String(200), nullable=True)
    
    # 操作者資訊
    operator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    # 時間資訊
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 關聯
    account = db.relationship("CashAccount", backref="profit_transactions")
    operator = db.relationship("User", backref="profit_transactions")
    
    def __repr__(self):
        return f'<ProfitTransaction {self.id}: {self.transaction_type} {self.amount} on account {self.account_id}>'


# ===================================================================
# 利潤管理服務類
# ===================================================================
class ProfitService:
    """利潤管理服務類 - 處理所有利潤相關操作"""
    
    @staticmethod
    def add_profit(account_id, amount, transaction_type, description=None, note=None, 
                   related_transaction_id=None, related_transaction_type=None, operator_id=None):
        """增加利潤到指定帳戶"""
        try:
            account = db.session.get(CashAccount, account_id)
            if not account:
                return {"success": False, "message": "帳戶不存在"}
            
            if operator_id is None:
                operator_id = current_user.id if current_user and current_user.is_authenticated else 1
            
            # 記錄變動前餘額
            balance_before = account.profit_balance
            
            # 更新利潤餘額
            account.profit_balance += amount
            balance_after = account.profit_balance
            
            # 同步更新總金額（利潤變動時總金額也要變動）
            account.balance += amount
            
            # 創建利潤交易記錄
            profit_transaction = ProfitTransaction(
                account_id=account_id,
                transaction_type=transaction_type,
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                related_transaction_id=related_transaction_id,
                related_transaction_type=related_transaction_type,
                description=description,
                note=note,
                operator_id=operator_id
            )
            
            db.session.add(profit_transaction)
            db.session.commit()
            
            return {
                "success": True, 
                "message": f"利潤變動成功：{amount:+.2f}",
                "balance_before": balance_before,
                "balance_after": balance_after,
                "transaction_id": profit_transaction.id
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"利潤變動失敗: {str(e)}"}
    
    @staticmethod
    def withdraw_profit(account_id, amount, description=None, note=None, operator_id=None):
        """從指定帳戶提取利潤"""
        try:
            account = db.session.get(CashAccount, account_id)
            if not account:
                return {"success": False, "message": "帳戶不存在"}
            
            if account.profit_balance < amount:
                return {"success": False, "message": f"利潤餘額不足，當前餘額: {account.profit_balance:.2f}"}
            
            if operator_id is None:
                operator_id = current_user.id if current_user and current_user.is_authenticated else 1
            
            # 記錄變動前餘額
            balance_before = account.profit_balance
            
            # 更新利潤餘額（減少）
            account.profit_balance -= amount
            balance_after = account.profit_balance
            
            # 同步更新總金額（利潤變動時總金額也要變動）
            account.balance -= amount
            
            # 創建利潤交易記錄
            profit_transaction = ProfitTransaction(
                account_id=account_id,
                transaction_type="PROFIT_WITHDRAW",
                amount=-amount,  # 負數表示提取
                balance_before=balance_before,
                balance_after=balance_after,
                description=description or f"利潤提取: {amount:.2f}",
                note=note,
                operator_id=operator_id
            )
            
            db.session.add(profit_transaction)
            db.session.commit()
            
            return {
                "success": True, 
                "message": f"利潤提取成功：{amount:.2f}",
                "balance_before": balance_before,
                "balance_after": balance_after,
                "transaction_id": profit_transaction.id
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"利潤提取失敗: {str(e)}"}
    
    @staticmethod
    def adjust_profit(account_id, new_balance, description=None, note=None, operator_id=None):
        """調整利潤餘額到指定數值"""
        try:
            account = db.session.get(CashAccount, account_id)
            if not account:
                return {"success": False, "message": "帳戶不存在"}
            
            if operator_id is None:
                operator_id = current_user.id if current_user and current_user.is_authenticated else 1
            
            # 記錄變動前餘額
            balance_before = account.profit_balance
            
            # 計算調整金額
            adjustment_amount = new_balance - balance_before
            
            # 更新利潤餘額
            account.profit_balance = new_balance
            balance_after = new_balance
            
            # 同步更新總金額（利潤變動時總金額也要變動）
            account.balance += adjustment_amount
            
            # 創建利潤交易記錄
            profit_transaction = ProfitTransaction(
                account_id=account_id,
                transaction_type="PROFIT_ADJUSTMENT",
                amount=adjustment_amount,
                balance_before=balance_before,
                balance_after=balance_after,
                description=description or f"利潤調整: {balance_before:.2f} → {balance_after:.2f}",
                note=note,
                operator_id=operator_id
            )
            
            db.session.add(profit_transaction)
            db.session.commit()
            
            return {
                "success": True, 
                "message": f"利潤調整成功：{balance_before:.2f} → {balance_after:.2f}",
                "balance_before": balance_before,
                "balance_after": balance_after,
                "adjustment_amount": adjustment_amount,
                "transaction_id": profit_transaction.id
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"利潤調整失敗: {str(e)}"}
    
    @staticmethod
    def get_profit_history(account_id=None, limit=50):
        """獲取利潤變動歷史"""
        try:
            query = db.select(ProfitTransaction).options(
                db.selectinload(ProfitTransaction.account),
                db.selectinload(ProfitTransaction.operator)
            ).order_by(ProfitTransaction.created_at.desc())
            
            if account_id:
                query = query.filter(ProfitTransaction.account_id == account_id)
            
            if limit:
                query = query.limit(limit)
            
            transactions = db.session.execute(query).scalars().all()
            
            return {
                "success": True,
                "transactions": [
                    {
                        "id": t.id,
                        "account_name": t.account.name if t.account else "未知帳戶",
                        "transaction_type": t.transaction_type,
                        "amount": t.amount,
                        "balance_before": t.balance_before,
                        "balance_after": t.balance_after,
                        "description": t.description,
                        "note": t.note,
                        "operator_name": t.operator.username if t.operator else "未知",
                        "created_at": t.created_at.isoformat()
                    }
                    for t in transactions
                ]
            }
            
        except Exception as e:
            return {"success": False, "message": f"獲取利潤歷史失敗: {str(e)}"}


# ===================================================================
# 刪除記錄審計服務類
# ===================================================================

class DeleteAuditService:
    """刪除記錄審計服務類"""
    
    @staticmethod
    def collect_balance_changes(affected_accounts):
        """收集帳戶餘額變化資訊"""
        try:
            import json
            
            balance_changes = []
            for account in affected_accounts:
                balance_changes.append({
                    'account_id': account.id,
                    'account_name': account.name,
                    'currency': account.currency,
                    'balance_before': getattr(account, '_balance_before', None),
                    'balance_after': account.balance,
                    'change': account.balance - getattr(account, '_balance_before', account.balance)
                })
            
            return json.dumps(balance_changes, ensure_ascii=False) if balance_changes else None
            
        except Exception as e:
            print(f"收集餘額變化失敗: {e}")
            return None
    
    @staticmethod
    def log_deletion(table_name, record_id, deleted_data, operation_type, description=None, operator_id=None, request=None, balance_changes=None):
        """記錄刪除操作"""
        try:
            # 獲取操作者資訊
            operator_name = None
            if operator_id:
                operator = db.session.get(User, operator_id)
                if operator:
                    operator_name = operator.username
            
            # 獲取IP和用戶代理
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent', '')[:500]  # 限制長度
            
            # 創建審計記錄
            audit_log = DeleteAuditLog(
                table_name=table_name,
                record_id=record_id,
                deleted_data=deleted_data,
                operation_type=operation_type,
                description=description,
                operator_id=operator_id,
                operator_name=operator_name,
                ip_address=ip_address,
                user_agent=user_agent,
                balance_changes=balance_changes
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            print(f"刪除記錄已記錄到審計日誌: {table_name}.{record_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"記錄刪除審計日誌失敗: {e}")
            return False
    
    @staticmethod
    def get_deletion_logs(table_name=None, operator_id=None, limit=50):
        """獲取刪除記錄"""
        try:
            query = db.session.execute(db.select(DeleteAuditLog))
            
            if table_name:
                query = query.filter(DeleteAuditLog.table_name == table_name)
            
            if operator_id:
                query = query.filter(DeleteAuditLog.operator_id == operator_id)
            
            query = query.order_by(DeleteAuditLog.deleted_at.desc()).limit(limit)
            
            logs = query.scalars().all()
            return [log.to_dict() for log in logs]
            
        except Exception as e:
            if "does not exist" in str(e) and "delete_audit_logs" in str(e):
                print("警告: delete_audit_logs 表格不存在，返回空結果")
                db.session.rollback()
                return []
            else:
                print(f"獲取刪除記錄失敗: {e}")
                db.session.rollback()
                return []
    
    @staticmethod
    def get_deletion_log_by_id(log_id):
        """根據ID獲取刪除記錄"""
        try:
            log = db.session.get(DeleteAuditLog, log_id)
            return log.to_dict() if log else None
        except Exception as e:
            if "does not exist" in str(e) and "delete_audit_logs" in str(e):
                print("警告: delete_audit_logs 表格不存在，返回空結果")
                db.session.rollback()
                return None
            else:
                print(f"獲取刪除記錄失敗: {e}")
                db.session.rollback()
                return None


# ===================================================================
# FIFO 服務類
# ===================================================================

class FIFOService:
    """FIFO庫存管理服務類"""
    
    @staticmethod
    def create_inventory_from_purchase(purchase_record):
        """從買入記錄創建FIFO庫存"""
        try:
            # 創建FIFO庫存記錄
            fifo_inventory = FIFOInventory(
                purchase_record_id=purchase_record.id,
                rmb_amount=purchase_record.rmb_amount,
                remaining_rmb=purchase_record.rmb_amount,
                unit_cost_twd=purchase_record.twd_cost / purchase_record.rmb_amount,
                exchange_rate=purchase_record.exchange_rate,
                purchase_date=purchase_record.purchase_date
            )
            
            db.session.add(fifo_inventory)
            db.session.commit()
            print(f"已創建FIFO庫存記錄: {fifo_inventory}")
            return fifo_inventory
            
        except Exception as e:
            db.session.rollback()
            print(f"創建FIFO庫存失敗: {e}")
            raise
    
    @staticmethod
    def allocate_inventory_for_sale(sales_record):
        """為銷售記錄分配FIFO庫存"""
        try:
            rmb_amount = sales_record.rmb_amount
            remaining_to_allocate = rmb_amount
            total_cost = 0
            allocations = []
            
            # 按買入時間順序獲取有庫存的記錄（FIFO原則）
            available_inventory = (
                db.session.execute(
                    db.select(FIFOInventory)
                    .filter(FIFOInventory.remaining_rmb > 0)
                    .order_by(FIFOInventory.purchase_date.asc())  # 最早的優先
                )
                .scalars()
                .all()
            )
            
            if not available_inventory:
                raise ValueError("沒有可用的庫存")
            
            for inventory in available_inventory:
                if remaining_to_allocate <= 0:
                    break
                
                # 計算從這批庫存中分配多少
                allocate_from_this_batch = min(remaining_to_allocate, inventory.remaining_rmb)
                
                # 創建分配記錄
                allocation = FIFOSalesAllocation(
                    fifo_inventory_id=inventory.id,
                    sales_record_id=sales_record.id,
                    allocated_rmb=allocate_from_this_batch,
                    allocated_cost_twd=allocate_from_this_batch * inventory.unit_cost_twd
                )
                
                # 更新庫存剩餘數量
                inventory.remaining_rmb -= allocate_from_this_batch
                
                # 關鍵修正：從銷售記錄指定的出貨帳戶扣款RMB
                if sales_record.rmb_account:
                    sales_account = sales_record.rmb_account
                    sales_account.balance -= allocate_from_this_batch
                    print(f"從出貨帳戶 {sales_account.name} 扣款: -{allocate_from_this_batch} RMB")
                
                # 累計成本
                total_cost += allocation.allocated_cost_twd
                remaining_to_allocate -= allocate_from_this_batch
                
                allocations.append(allocation)
                db.session.add(allocation)
                
                print(f" 從庫存批次 {inventory.id} 分配 {allocate_from_this_batch} RMB，成本 {allocation.allocated_cost_twd} TWD")
            
            if remaining_to_allocate > 0:
                raise ValueError(f"庫存不足，還需要 {remaining_to_allocate} RMB")
            
            db.session.flush()  # 改為flush，讓上層控制commit
            print(f"FIFO分配完成，總成本: {total_cost} TWD")
            
            # 計算利潤
            profit_twd = sales_record.twd_amount - total_cost
            print(f"利潤計算: 售價 {sales_record.twd_amount} TWD - 成本 {total_cost} TWD = 利潤 {profit_twd} TWD")
            
            return {
                'allocations': allocations,
                'total_cost': total_cost,
                'total_rmb': rmb_amount,
                'profit_twd': profit_twd  # 新增利潤計算
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"FIFO分配失敗: {e}")
            raise
    
    @staticmethod
    def get_current_inventory():
        """獲取當前庫存狀態（包括已用完的庫存，按買入時間倒序排列，最多20條）"""
        try:
            inventory = (
                db.session.execute(
                    db.select(FIFOInventory)
                    .options(
                        db.selectinload(FIFOInventory.purchase_record).selectinload(PurchaseRecord.channel),
                        db.selectinload(FIFOInventory.purchase_record).selectinload(PurchaseRecord.payment_account),
                        db.selectinload(FIFOInventory.purchase_record).selectinload(PurchaseRecord.deposit_account)
                    )
                    .order_by(FIFOInventory.purchase_date.desc())  # 新的在最上面
                    .limit(20)  # 限制20條記錄
                )
                .scalars()
                .all()
            )
            
            inventory_summary = []
            for inv in inventory:
                # 計算已出帳數量（原始數量 - 剩餘數量）
                sold_rmb = inv.rmb_amount - inv.remaining_rmb
                
                # 判斷是否為存款/手續費記錄（無渠道且無付款帳戶的虛擬買入記錄）
                is_deposit_record = (
                    inv.purchase_record.channel is None and
                    inv.purchase_record.payment_account is None
                )
                # 純利潤庫存（手續費）檢測：成本為0 或 描述帶有關鍵字
                try:
                    desc = getattr(inv.purchase_record, 'description', '') or ''
                except Exception:
                    desc = ''
                is_pure_profit = (inv.purchase_record.twd_cost == 0) or ('純利潤' in desc or '手續費' in desc)
                channel_label = '手續費' if (is_deposit_record and is_pure_profit) else (
                    '存款' if is_deposit_record else (inv.purchase_record.channel.name if inv.purchase_record.channel else 'N/A')
                )
                
                inventory_summary.append({
                    'id': inv.id,
                    'purchase_date': inv.purchase_date.strftime('%Y-%m-%d'),
                    'channel': channel_label,
                    'payment_account': inv.purchase_record.payment_account.name if inv.purchase_record.payment_account else 'N/A',
                    'deposit_account': inv.purchase_record.deposit_account.name if inv.purchase_record.deposit_account else 'N/A',
                    'original_rmb': inv.rmb_amount,
                    'remaining_rmb': inv.remaining_rmb,
                    'sold_rmb': sold_rmb,  # 新增：已出帳數量
                    'unit_cost_twd': inv.unit_cost_twd,
                    'exchange_rate': inv.exchange_rate,
                    'total_value_twd': inv.remaining_rmb * inv.unit_cost_twd
                })
            
            return inventory_summary
            
        except Exception as e:
            print(f"獲取庫存狀態失敗: {e}")
            return []
    
    # ===================================================================
    # 新增：錯誤處理和回滾機制
    # ===================================================================
    
    @staticmethod
    def simple_reverse_sale_allocation(sales_record_id):
        """簡化的回滾銷售記錄方法，用於診斷問題"""
        try:
            print(f"開始簡化回滾銷售記錄 {sales_record_id}")
            
            # 查找該銷售記錄
            sales_record = db.session.get(SalesRecord, sales_record_id)
            if not sales_record:
                print(f"找不到銷售記錄 {sales_record_id}")
                return False
            
            print(f"找到銷售記錄: 客戶ID={sales_record.customer_id}, RMB={sales_record.rmb_amount}")
            
            # 查找該銷售記錄的所有FIFO分配
            allocations = db.session.execute(
                db.select(FIFOSalesAllocation)
                .filter(FIFOSalesAllocation.sales_record_id == sales_record_id)
            ).scalars().all()
            
            print(f"找到 {len(allocations)} 個FIFO分配記錄")
            
            # 簡化的回滾邏輯
            for allocation in allocations:
                # 恢復庫存數量
                if allocation.fifo_inventory:
                    allocation.fifo_inventory.remaining_rmb += allocation.allocated_rmb
                    print(f"恢復庫存批次 {allocation.fifo_inventory.id} 的數量: +{allocation.allocated_rmb} RMB")
                
                # 刪除分配記錄
                db.session.delete(allocation)
                print(f"刪除FIFO分配記錄 {allocation.id}")
            
            # 更新客戶應收帳款
            if sales_record.customer:
                customer = sales_record.customer
                customer.total_receivables_twd -= sales_record.twd_amount
                if customer.total_receivables_twd < 0:
                    customer.total_receivables_twd = 0
                print(f"更新客戶 {customer.name} 的應收帳款: -{sales_record.twd_amount} TWD")
            
            # 恢復RMB帳戶餘額
            if sales_record.rmb_account:
                sales_record.rmb_account.balance += sales_record.rmb_amount
                print(f"恢復RMB帳戶 {sales_record.rmb_account.name} 的餘額: +{sales_record.rmb_amount} RMB")
            
            # 刪除銷售記錄本身
            db.session.delete(sales_record)
            print(f"刪除銷售記錄 {sales_record_id}")
            
            db.session.commit()
            print(f"簡化回滾銷售記錄 {sales_record_id} 成功")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"簡化回滾銷售記錄失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def reverse_sale_allocation(sales_record_id):
        """完全回滾銷售記錄（包括FIFO分配和銷售記錄本身）"""
        try:
            print(f"開始回滾銷售記錄 {sales_record_id}")
            
            # 查找該銷售記錄
            sales_record = (
                db.session.execute(
                    db.select(SalesRecord)
                    .filter(SalesRecord.id == sales_record_id)
                )
                .scalars()
                .first()
            )
            
            if not sales_record:
                print(f"找不到銷售記錄 {sales_record_id}")
                return False
            
            print(f"找到銷售記錄: 客戶ID={sales_record.customer_id}, RMB={sales_record.rmb_amount}, TWD={sales_record.twd_amount}")
            
            # 查找該銷售記錄的所有FIFO分配
            allocations = (
                db.session.execute(
                    db.select(FIFOSalesAllocation)
                    .filter(FIFOSalesAllocation.sales_record_id == sales_record_id)
                )
                .scalars()
                .all()
            )
            
            print(f"找到 {len(allocations)} 個FIFO分配記錄")
            
            # --- 關鍵修正：更新客戶的應收帳款 ---
            # 在刪除銷售記錄之前，先更新客戶的應收帳款
            if sales_record.customer:
                customer = sales_record.customer
                # 減少客戶的應收帳款
                customer.total_receivables_twd -= sales_record.twd_amount
                print(f"更新客戶 {customer.name} 的應收帳款: -{sales_record.twd_amount} TWD")
                
                # 確保應收帳款不會變成負數
                if customer.total_receivables_twd < 0:
                    customer.total_receivables_twd = 0
                    print(f"客戶 {customer.name} 的應收帳款已調整為 0")
            
            # --- 關鍵修正：恢復RMB帳戶的餘額 ---
            # 先記錄所有受影響帳戶的原始餘額
            affected_accounts = []
            
            # 恢復每個FIFO分配對應的RMB帳戶餘額
            for allocation in allocations:
                if allocation.fifo_inventory and allocation.fifo_inventory.purchase_record.deposit_account:
                    # 檢查收款帳戶是否為RMB帳戶
                    deposit_account = allocation.fifo_inventory.purchase_record.deposit_account
                    if deposit_account.currency == 'RMB':
                        # 記錄原始餘額
                        if deposit_account not in affected_accounts:
                            deposit_account._balance_before = deposit_account.balance
                            affected_accounts.append(deposit_account)
                        
                        # 如果是RMB帳戶，直接恢復RMB餘額
                        deposit_account.balance += allocation.allocated_rmb
                        print(f"恢復RMB帳戶 {deposit_account.name} 的餘額: +{allocation.allocated_rmb} RMB")
                    else:
                        # 如果不是RMB帳戶，需要找到對應的RMB帳戶
                        # 根據買入記錄的邏輯，RMB餘額應該在deposit_account中
                        # 但這裡需要檢查是否有其他RMB帳戶需要恢復
                        print(f"警告：庫存來源帳戶 {deposit_account.name} 不是RMB帳戶")
                        
                        # 嘗試找到對應的RMB帳戶
                        # 這裡需要根據業務邏輯來確定如何恢復RMB餘額
                        # 可能需要檢查是否有其他RMB帳戶需要恢復
                        
                        # 實現智能RMB餘額恢復邏輯
                        # 當庫存來源帳戶不是RMB帳戶時，需要找到對應的RMB帳戶
                        # 這裡我們需要根據業務邏輯來確定如何恢復RMB餘額
                        
                        # 方案1：檢查是否有其他RMB帳戶需要恢復
                        # 方案2：如果沒有明確的RMB帳戶，則記錄這個問題
                        
                        # 暫時記錄這個問題，讓管理員手動處理
                        print(f"需要手動檢查RMB餘額恢復邏輯")
                        print(f"   分配RMB: {allocation.allocated_rmb}")
                        print(f"   庫存來源帳戶: {deposit_account.name} (非RMB帳戶)")
                        
                        # TODO: 實現更智能的RMB餘額恢復邏輯
                        # 可能需要檢查是否有其他RMB帳戶需要恢復
                        # 或者創建一個虛擬的RMB餘額記錄
            
            # 回滾每個分配
            for allocation in allocations:
                # 恢復庫存數量
                inventory = allocation.fifo_inventory
                if inventory:
                    inventory.remaining_rmb += allocation.allocated_rmb
                    print(f"恢復庫存批次 {inventory.id} 的數量: +{allocation.allocated_rmb} RMB")
                
                # 刪除分配記錄
                db.session.delete(allocation)
                print(f"刪除FIFO分配記錄 {allocation.id}")
            
            # 記錄刪除審計日誌（在刪除前記錄完整資料）
            try:
                import json
                from flask import request
                
                # 準備被刪除記錄的資料
                deleted_data = {
                    'id': sales_record.id,
                    'customer_id': sales_record.customer_id,
                    'rmb_amount': sales_record.rmb_amount,
                    'twd_amount': sales_record.twd_amount,
                    'exchange_rate': sales_record.exchange_rate,
                    'is_settled': sales_record.is_settled,
                    'created_at': sales_record.created_at.isoformat() if sales_record.created_at else None,
                    'operator_id': sales_record.operator_id,
                    'customer_name': sales_record.customer.name if sales_record.customer else None
                }
                
                # 獲取操作者ID
                operator_id = None
                try:
                    from flask_login import current_user
                    operator_id = current_user.id if current_user and hasattr(current_user, 'id') else 1
                except:
                    operator_id = 1
                
                # 收集餘額變化資訊
                balance_changes = DeleteAuditService.collect_balance_changes(affected_accounts)
                
                # 記錄審計日誌
                DeleteAuditService.log_deletion(
                    table_name='sales_records',
                    record_id=sales_record_id,
                    deleted_data=json.dumps(deleted_data, ensure_ascii=False),
                    operation_type='REVERSE_SALE',
                    description=f'回滾銷售記錄：客戶 {deleted_data.get("customer_name", "N/A")}, RMB {sales_record.rmb_amount}, TWD {sales_record.twd_amount}',
                    operator_id=operator_id,
                    request=request,
                    balance_changes=balance_changes
                )
            except Exception as audit_error:
                print(f"記錄審計日誌失敗: {audit_error}")
                # 不讓審計日誌失敗影響主要操作
            
            # 刪除銷售記錄本身
            db.session.delete(sales_record)
            print(f"刪除銷售記錄 {sales_record_id}")
            
            db.session.commit()
            print(f"成功完全回滾銷售記錄 {sales_record_id}")
            
            # 調用全局數據同步，確保帳戶餘額和庫存一致
            try:
                from global_sync import sync_entire_database
                sync_entire_database(db.session)
                print(f"全局數據同步完成，帳戶餘額和庫存已重新整理")
            except Exception as sync_error:
                print(f"全局數據同步失敗: {sync_error}")
                # 不讓全局同步失敗影響主要操作
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"回滾銷售記錄失敗: {e}")
            return False
    
    @staticmethod
    def reverse_purchase_inventory(purchase_record_id):
        """完全回滾買入記錄（包括FIFO庫存和買入記錄本身）"""
        try:
            print(f"開始回滾買入記錄 {purchase_record_id}")
            
            # 查找該買入記錄
            purchase_record = (
                db.session.execute(
                    db.select(PurchaseRecord)
                    .filter(PurchaseRecord.id == purchase_record_id)
                )
                .scalars()
                .first()
            )
            
            if not purchase_record:
                print(f"找不到買入記錄 {purchase_record_id}")
                return False
            
            print(f"找到買入記錄: channel={purchase_record.channel_id}, payment_account={purchase_record.payment_account_id}, twd_cost={purchase_record.twd_cost}")
            
            # 查找該買入記錄的FIFO庫存
            inventory = (
                db.session.execute(
                    db.select(FIFOInventory)
                    .filter(FIFOInventory.purchase_record_id == purchase_record_id)
                )
                .scalars()
                .first()
            )
            
            print(f"查找FIFO庫存: inventory_id={inventory.id if inventory else None}")
            
            # 檢查是否有銷售分配
            if inventory:
                allocations = (
                    db.session.execute(
                        db.select(FIFOSalesAllocation)
                        .filter(FIFOSalesAllocation.fifo_inventory_id == inventory.id)
                    )
                    .scalars()
                    .all()
                )
                
                print(f"檢查銷售分配: 找到 {len(allocations)} 個分配記錄")
                
                if allocations:
                    print(f"庫存批次 {inventory.id} 已有銷售分配，無法直接回滾")
                    for alloc in allocations:
                        print(f"  分配記錄: {alloc.id}, 銷售記錄: {alloc.sales_record_id}, 分配RMB: {alloc.allocated_rmb}")
                    return False
                
                # 刪除庫存記錄
                db.session.delete(inventory)
                print(f"刪除FIFO庫存記錄 {inventory.id}")
            else:
                print(f"找不到對應的FIFO庫存記錄，purchase_record_id: {purchase_record_id}")
                # 即使沒有庫存記錄，我們仍然可以繼續處理買入記錄的回滾
            
            # 回滾帳戶餘額：根據買入記錄類型進行不同的處理
            # 先記錄所有受影響帳戶的原始餘額
            affected_accounts = []
            
            if (purchase_record.channel is None and 
                purchase_record.payment_account is None and 
                purchase_record.twd_cost == 0):
                # 純利潤庫存（手續費）：從入庫帳戶中扣除
                if purchase_record.deposit_account:
                    deposit_account = purchase_record.deposit_account
                    # 記錄原始餘額
                    deposit_account._balance_before = deposit_account.balance
                    affected_accounts.append(deposit_account)
                    
                    deposit_account.balance -= purchase_record.rmb_amount
                    print(f"從帳戶 {deposit_account.name} 扣除手續費: -{purchase_record.rmb_amount} RMB")
                    
                    # 創建提款流水記錄（使用系統用戶ID，避免current_user問題）
                    try:
                        # 嘗試獲取當前用戶ID，如果失敗則使用默認值
                        operator_id = current_user.id if current_user and hasattr(current_user, 'id') else 1
                    except:
                        operator_id = 1  # 默認系統用戶ID
                    
                    entry = LedgerEntry(
                        entry_type="WITHDRAW",
                        account_id=deposit_account.id,
                        amount=purchase_record.rmb_amount,
                        description="獨立儲值頁面：刪除儲值紀錄回退純利潤庫存",
                        operator_id=operator_id,
                    )
                    db.session.add(entry)
                    print(f"創建提款流水記錄: -{purchase_record.rmb_amount} RMB")
            else:
                # 正常買入記錄：回滾帳戶餘額
                # RMB帳戶刪除款項（減少RMB餘額）
                if purchase_record.deposit_account:
                    deposit_account = purchase_record.deposit_account
                    # 記錄原始餘額
                    deposit_account._balance_before = deposit_account.balance
                    affected_accounts.append(deposit_account)
                    
                    deposit_account.balance -= purchase_record.rmb_amount
                    print(f"回滾RMB帳戶 {deposit_account.name}: -{purchase_record.rmb_amount} RMB")
                
                # 台幣帳戶回補款項（增加台幣餘額）
                if purchase_record.payment_account:
                    payment_account = purchase_record.payment_account
                    # 記錄原始餘額
                    payment_account._balance_before = payment_account.balance
                    affected_accounts.append(payment_account)
                    
                    payment_account.balance += purchase_record.twd_cost
                    print(f"回補台幣帳戶 {payment_account.name}: +{purchase_record.twd_cost} TWD")
            
            # 記錄刪除審計日誌（在刪除前記錄完整資料）
            try:
                import json
                from flask import request
                
                # 準備被刪除記錄的資料
                deleted_data = {
                    'id': purchase_record.id,
                    'payment_account_id': purchase_record.payment_account_id,
                    'deposit_account_id': purchase_record.deposit_account_id,
                    'channel_id': purchase_record.channel_id,
                    'rmb_amount': purchase_record.rmb_amount,
                    'exchange_rate': purchase_record.exchange_rate,
                    'twd_cost': purchase_record.twd_cost,
                    'purchase_date': purchase_record.purchase_date.isoformat() if purchase_record.purchase_date else None,
                    'operator_id': purchase_record.operator_id
                }
                
                # 獲取操作者ID
                operator_id = None
                try:
                    operator_id = current_user.id if current_user and hasattr(current_user, 'id') else 1
                except:
                    operator_id = 1
                
                # 收集餘額變化資訊
                balance_changes = DeleteAuditService.collect_balance_changes(affected_accounts)
                
                # 記錄審計日誌
                DeleteAuditService.log_deletion(
                    table_name='purchase_records',
                    record_id=purchase_record_id,
                    deleted_data=json.dumps(deleted_data, ensure_ascii=False),
                    operation_type='REVERSE_PURCHASE',
                    description=f'回滾買入記錄：RMB {purchase_record.rmb_amount}, 台幣成本 {purchase_record.twd_cost}',
                    operator_id=operator_id,
                    request=request,
                    balance_changes=balance_changes
                )
            except Exception as audit_error:
                print(f"記錄審計日誌失敗: {audit_error}")
            
            # 刪除買入記錄本身
            db.session.delete(purchase_record)
            print(f"刪除買入記錄 {purchase_record_id}")
            
            db.session.commit()
            print(f"成功完全回滾買入記錄 {purchase_record_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"回滾買入記錄失敗: {e}")
            import traceback
            print(f"詳細錯誤信息: {traceback.format_exc()}")
            return False
    
    @staticmethod
    def audit_inventory_consistency():
        """審計庫存一致性"""
        try:
            issues = []
            
            # 檢查庫存數量是否為負數
            negative_inventory = (
                db.session.execute(
                    db.select(FIFOInventory)
                    .filter(FIFOInventory.remaining_rmb < 0)
                )
                .scalars()
                .all()
            )
            
            if negative_inventory:
                for inv in negative_inventory:
                    issues.append(f"庫存批次 {inv.id} 剩餘數量為負數: {inv.remaining_rmb}")
            
            # 檢查分配總和是否超過原始數量
            all_inventory = db.session.execute(db.select(FIFOInventory)).scalars().all()
            
            for inv in all_inventory:
                total_allocated = sum(
                    allocation.allocated_rmb 
                    for allocation in inv.sales_allocations
                )
                
                if total_allocated > inv.rmb_amount:
                    issues.append(f"庫存批次 {inv.id} 分配總和超過原始數量: {total_allocated} > {inv.rmb_amount}")
            
            return issues
            
        except Exception as e:
            print(f"庫存一致性審計失敗: {e}")
            return [f"審計過程發生錯誤: {e}"]
    
    @staticmethod
    def fix_inventory_consistency():
        """修復庫存一致性问题"""
        try:
            fixed_issues = []
            
            # 修復負數庫存
            negative_inventory = (
                db.session.execute(
                    db.select(FIFOInventory)
                    .filter(FIFOInventory.remaining_rmb < 0)
                )
                .scalars()
                .all()
            )
            
            for inv in negative_inventory:
                # 重新計算剩餘數量
                total_allocated = sum(
                    allocation.allocated_rmb 
                    for allocation in inv.sales_allocations
                )
                inv.remaining_rmb = max(0, inv.rmb_amount - total_allocated)
                fixed_issues.append(f"修復庫存批次 {inv.id} 的負數數量")
            
            db.session.commit()
            print(f"修復了 {len(fixed_issues)} 個庫存一致性问题")
            return fixed_issues
            
        except Exception as e:
            db.session.rollback()
            print(f"修復庫存一致性失敗: {e}")
            return []
    
    @staticmethod
    def reduce_rmb_inventory_fifo(amount, reason="外部提款"):
        """按FIFO原則扣減RMB庫存"""
        try:
            remaining_to_reduce = amount
            reduced_items = []
            
            # 按買入時間順序獲取有庫存的記錄（FIFO原則）
            available_inventory = (
                db.session.execute(
                    db.select(FIFOInventory)
                    .filter(FIFOInventory.remaining_rmb > 0)
                    .order_by(FIFOInventory.purchase_date.asc())  # 最早的優先
                )
                .scalars()
                .all()
            )
            
            if not available_inventory:
                raise ValueError("沒有可用的庫存")
            
            # 計算總可用庫存
            total_available = sum(inv.remaining_rmb for inv in available_inventory)
            if total_available < amount:
                raise ValueError(f"庫存不足：需要 {amount:,.2f}，可用 {total_available:,.2f}")
            
            # 按FIFO順序扣減庫存
            for inventory in available_inventory:
                if remaining_to_reduce <= 0:
                    break
                
                # 計算從這批庫存中扣減多少
                reduce_from_this_batch = min(remaining_to_reduce, inventory.remaining_rmb)
                
                # 更新庫存剩餘數量
                inventory.remaining_rmb -= reduce_from_this_batch
                remaining_to_reduce -= reduce_from_this_batch
                
                reduced_items.append({
                    'inventory_id': inventory.id,
                    'reduced_amount': reduce_from_this_batch,
                    'remaining_after': inventory.remaining_rmb
                })
                
                print(f" 從庫存批次 {inventory.id} 扣減 {reduce_from_this_batch} RMB，剩餘 {inventory.remaining_rmb} RMB")
            
            db.session.flush()  # 確保更新被保存
            print(f"成功按FIFO扣減庫存 {amount} RMB，原因：{reason}")
            return reduced_items
            
        except Exception as e:
            print(f"扣減庫存失敗: {e}")
            raise
    
    @staticmethod
    def calculate_profit_for_sale(sales_record):
        """計算某筆銷售的利潤（使用FIFO方法）"""
        try:
            # 獲取該銷售記錄的所有FIFO分配
            allocations = (
                db.session.execute(
                    db.select(FIFOSalesAllocation)
                    .filter(FIFOSalesAllocation.sales_record_id == sales_record.id)
                )
                .scalars()
                .all()
            )
            
            if not allocations:
                # 如果沒有FIFO分配，使用預覽計算
                return FIFOService.calculate_profit_preview_for_sale(sales_record)
            
            # 使用FIFO分配計算利潤
            total_profit_twd = 0
            total_cost_twd = 0
            sales_exchange_rate = sales_record.twd_amount / sales_record.rmb_amount  # 售出匯率
            
            # 遍歷每個FIFO分配，計算每批的利潤
            pure_profit_twd = 0  # 純利潤庫存的絕對利潤
            regular_profit_twd = 0  # 一般庫存的利潤
            
            for allocation in allocations:
                # 獲取對應的庫存記錄
                inventory = allocation.fifo_inventory
                if not inventory:
                    continue
                
                # 該批次的買入匯率
                purchase_exchange_rate = inventory.exchange_rate
                
                # 該批次的售出金額（RMB）
                allocated_rmb = allocation.allocated_rmb
                
                # 該批次的成本（TWD）
                allocated_cost_twd = allocation.allocated_cost_twd
                
                # 檢查是否為純利潤庫存（成本為0）
                is_pure_profit = allocated_cost_twd == 0
                
                if is_pure_profit:
                    # 純利潤庫存：售出金額全部為利潤
                    pure_profit_twd += sales_record.twd_amount * (allocated_rmb / sales_record.rmb_amount)
                    print(f"純利潤庫存：批次 {inventory.id}，分配RMB {allocated_rmb}，純利潤 {pure_profit_twd} TWD")
                else:
                    # 一般庫存：按匯率差計算利潤
                    batch_profit_twd = (sales_exchange_rate - purchase_exchange_rate) * allocated_rmb
                    regular_profit_twd += batch_profit_twd
                    total_cost_twd += allocated_cost_twd
                    print(f"一般庫存：批次 {inventory.id}，買入匯率 {purchase_exchange_rate}，售出匯率 {sales_exchange_rate}，分配RMB {allocated_rmb}，批次利潤 {batch_profit_twd} TWD")
            
            # 總利潤 = 一般庫存利潤 + 純利潤庫存利潤
            total_profit_twd = regular_profit_twd + pure_profit_twd
            
            # 計算利潤率
            profit_margin = (total_profit_twd / sales_record.twd_amount * 100) if sales_record.twd_amount > 0 else 0
            
            return {
                'sales_amount': sales_record.twd_amount,
                'total_cost_twd': total_cost_twd,
                'profit_twd': total_profit_twd,
                'profit_margin': profit_margin,
                'pure_profit_twd': pure_profit_twd,  # 純利潤庫存產生的絕對利潤
                'regular_profit_twd': regular_profit_twd,  # 一般庫存產生的利潤
                'regular_profit_margin': (regular_profit_twd / (sales_record.twd_amount - pure_profit_twd) * 100) if (sales_record.twd_amount - pure_profit_twd) > 0 else 0,  # 一般庫存的利潤率
                'allocations': [
                    {
                        'inventory_id': allocation.fifo_inventory_id,
                        'allocated_rmb': allocation.allocated_rmb,
                        'allocated_cost': allocation.allocated_cost_twd,
                        'purchase_date': allocation.fifo_inventory.purchase_date.strftime('%Y-%m-%d'),
                        'purchase_exchange_rate': allocation.fifo_inventory.exchange_rate,
                        'is_pure_profit': allocation.allocated_cost_twd == 0,
                        'batch_profit': (sales_record.twd_amount * (allocation.allocated_rmb / sales_record.rmb_amount)) if allocation.allocated_cost_twd == 0 else (sales_exchange_rate - allocation.fifo_inventory.exchange_rate) * allocation.allocated_rmb
                    }
                    for allocation in allocations
                ]
            }
            
        except Exception as e:
            print(f"計算利潤失敗: {e}")
            return None
    
    @staticmethod
    def calculate_profit_preview_for_sale(sales_record):
        """為銷售記錄計算利潤預覽（基於FIFO庫存）"""
        try:
            rmb_amount = sales_record.rmb_amount
            sales_exchange_rate = sales_record.twd_amount / sales_record.rmb_amount  # 售出匯率
            
            remaining_to_calculate = rmb_amount
            total_cost_twd = 0
            cost_breakdown = []
            
            # 按買入時間順序獲取有庫存的記錄（FIFO原則）
            available_inventory = (
                db.session.execute(
                    db.select(FIFOInventory)
                    .filter(FIFOInventory.remaining_rmb > 0)
                    .order_by(FIFOInventory.purchase_date.asc())  # 最早的優先
                )
                .scalars()
                .all()
            )
            
            if not available_inventory:
                return None
            
            for inventory in available_inventory:
                if remaining_to_calculate <= 0:
                    break
                
                # 計算從這批庫存中分配多少
                allocate_from_this_batch = min(remaining_to_calculate, inventory.remaining_rmb)
                
                # 計算這批的成本
                batch_cost_twd = allocate_from_this_batch * inventory.unit_cost_twd
                
                # 累計成本
                total_cost_twd += batch_cost_twd
                remaining_to_calculate -= allocate_from_this_batch
                
                # 記錄成本分解
                cost_breakdown.append({
                    'purchase_date': inventory.purchase_date.strftime('%Y-%m-%d'),
                    'channel': inventory.purchase_record.channel.name if inventory.purchase_record.channel else 'N/A',
                    'rmb_amount': allocate_from_this_batch,
                    'unit_cost_twd': inventory.unit_cost_twd,
                    'batch_cost_twd': batch_cost_twd,
                    'purchase_exchange_rate': inventory.exchange_rate
                })
                
                print(f"預覽：從庫存批次 {inventory.id} 分配 {allocate_from_this_batch} RMB，成本 {batch_cost_twd} TWD")
            
            if remaining_to_calculate > 0:
                return None  # 庫存不足
            
            # 使用FIFO方法計算利潤：每批分別計算後加總
            total_profit_twd = 0
            
            # 遍歷每個成本分解項目，計算每批的利潤
            for item in cost_breakdown:
                # 該批次的買入匯率
                purchase_exchange_rate = item['purchase_exchange_rate']
                
                # 該批次的RMB金額
                batch_rmb = item['rmb_amount']
                
                # 計算該批次的利潤：(售出匯率 - 買入匯率) × 該批次的RMB金額
                batch_profit_twd = (sales_exchange_rate - purchase_exchange_rate) * batch_rmb
                
                # 累計利潤
                total_profit_twd += batch_profit_twd
                
                print(f"FIFO預覽利潤計算：批次 {item['purchase_date']}，買入匯率 {purchase_exchange_rate}，售出匯率 {sales_exchange_rate}，RMB {batch_rmb}，批次利潤 {batch_profit_twd} TWD")
            
            # 計算利潤率
            revenue_twd = rmb_amount * sales_exchange_rate
            profit_margin = (total_profit_twd / revenue_twd * 100) if revenue_twd > 0 else 0
            
            return {
                'total_cost_twd': total_cost_twd,
                'profit_twd': total_profit_twd,
                'profit_margin': profit_margin,
                'sales_exchange_rate': sales_exchange_rate,
                'cost_breakdown': cost_breakdown
            }
            
        except Exception as e:
            print(f"計算銷售利潤預覽失敗: {e}")
            return None
    
    @staticmethod
    def calculate_profit_preview(rmb_amount, exchange_rate):
        """計算售出利潤預覽（不實際分配庫存）"""
        try:
            remaining_to_calculate = rmb_amount
            total_cost_twd = 0
            cost_breakdown = []
            
            # 按買入時間順序獲取有庫存的記錄（FIFO原則）
            available_inventory = (
                db.session.execute(
                    db.select(FIFOInventory)
                    .filter(FIFOInventory.remaining_rmb > 0)
                    .order_by(FIFOInventory.purchase_date.asc())  # 最早的優先
                )
                .scalars()
                .all()
            )
            
            if not available_inventory:
                return None
            
            for inventory in available_inventory:
                if remaining_to_calculate <= 0:
                    break
                
                # 計算從這批庫存中分配多少
                allocate_from_this_batch = min(remaining_to_calculate, inventory.remaining_rmb)
                
                # 計算這批的成本
                batch_cost_twd = allocate_from_this_batch * inventory.unit_cost_twd
                
                # 累計成本
                total_cost_twd += batch_cost_twd
                remaining_to_calculate -= allocate_from_this_batch
                
                # 記錄成本分解
                cost_breakdown.append({
                    'purchase_date': inventory.purchase_date.strftime('%Y-%m-%d'),
                    'channel': inventory.purchase_record.channel.name if inventory.purchase_record.channel else 'N/A',
                    'rmb_amount': allocate_from_this_batch,
                    'unit_cost_twd': inventory.unit_cost_twd,
                    'batch_cost_twd': batch_cost_twd
                })
                
                print(f"預覽：從庫存批次 {inventory.id} 分配 {allocate_from_this_batch} RMB，成本 {batch_cost_twd} TWD")
            
            if remaining_to_calculate > 0:
                return None  # 庫存不足
            
            # 計算收入和利潤
            revenue_twd = rmb_amount * exchange_rate
            profit_twd = revenue_twd - total_cost_twd
            profit_margin = (profit_twd / revenue_twd * 100) if revenue_twd > 0 else 0
            
            return {
                'total_cost_twd': total_cost_twd,
                'profit_twd': profit_twd,
                'profit_margin': profit_margin,
                'cost_breakdown': cost_breakdown
            }
            
        except Exception as e:
            print(f"計算利潤預覽失敗: {e}")
            return None


# ===================================================================
# 4. Flask-Login 與權限裝飾器
# ===================================================================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("您沒有權限存取此頁面。", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# ===================================================================
# 5. 自訂 Flask CLI 命令
# ===================================================================
@app.cli.command("create-admin")
def create_admin_command():
    """創建一個預設的管理員帳號。"""
    if User.query.filter_by(username="admin").first():
        print("管理員 'admin' 已存在。")
        return
    admin_user = User(username="admin", role="admin")
    admin_user.set_password("password")
    db.session.add(admin_user)
    db.session.commit()
    print("管理員 'admin' 已創建，密碼為 'password'。")


# <---【移除】舊的 init-db 命令，完全由 Flask-Migrate 取代


# ===================================================================
# 6. 使用者認證與首頁路由
# ===================================================================
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(
            url_for("admin_dashboard" if current_user.is_admin else "dashboard")
        )
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        print(f"登入嘗試: username={username}")  # 調試日誌
        
        user = User.query.filter_by(username=username).first()
        print(f"用戶查詢結果: {user}")  # 調試日誌
        
        if user and user.check_password(password):
            print(f"登入成功: {username}")  # 調試日誌
            login_user(user, remember=True)
            flash(f"歡迎回來，{username}！", "success")
            return redirect(url_for("dashboard"))
        else:
            print(f"登入失敗: {username}")  # 調試日誌
            flash("無效的使用者名稱或密碼。", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("您已成功登出。", "success")
    return redirect(url_for("login"))


# ===================================================================
# 7. 主要功能頁面路由 (重構並簡化)
# ===================================================================
@app.route("/dashboard")
@login_required
def dashboard():
    """普通用戶的儀表板頁面"""
    try:
        # --- 修正：直接使用實際帳戶餘額計算總資產，與現金管理頁面保持一致 ---
        all_accounts_obj = (
            db.session.execute(db.select(CashAccount).order_by(CashAccount.holder_id))
            .scalars()
            .all()
        )

        total_twd_cash = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "TWD"
        )
        total_rmb_stock = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "RMB"
        )
        


        # 計算總應收帳款
        customers_with_receivables = (
            db.session.execute(
                db.select(Customer)
                .filter_by(is_active=True)
                .filter(Customer.total_receivables_twd > 0)
                .order_by(Customer.total_receivables_twd.desc())
            )
            .scalars()
            .all()
        )
        
        total_receivables = sum(c.total_receivables_twd for c in customers_with_receivables)

        # 獲取最近的交易記錄
        recent_purchases = (
            db.session.execute(
                db.select(PurchaseRecord)
                .order_by(PurchaseRecord.purchase_date.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )

        recent_sales = (
            db.session.execute(
                db.select(SalesRecord)
                .order_by(SalesRecord.created_at.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )

        # 計算總利潤（從所有銷售記錄計算，並扣除利潤提款）
        total_profit_twd = 0.0
        all_sales = (
            db.session.execute(
                db.select(SalesRecord)
            )
            .scalars()
            .all()
        )
        
        for sale in all_sales:
            profit_info = FIFOService.calculate_profit_for_sale(sale)
            if profit_info:
                total_profit_twd += profit_info.get('profit_twd', 0.0)
        
        # 扣除利潤提款記錄
        try:
            profit_withdrawals = (
                db.session.execute(
                    db.select(LedgerEntry)
                    .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
                )
                .scalars()
                .all()
            )
        except Exception as e:
            if "profit_before does not exist" in str(e):
                print("警告: 儀表板查詢 PROFIT_WITHDRAW 記錄時缺少欄位，跳過查詢")
                db.session.rollback()
                profit_withdrawals = []
            else:
                db.session.rollback()
                raise e
        
        total_profit_withdrawals = sum(entry.amount for entry in profit_withdrawals)
        total_profit_twd -= total_profit_withdrawals
        
        print(f"DEBUG: 普通用戶儀表板利潤計算 - 銷售利潤: {total_profit_twd + total_profit_withdrawals:.2f}, 利潤提款: {total_profit_withdrawals:.2f}, 最終利潤: {total_profit_twd:.2f}")

        return render_template(
            "dashboard.html",
            total_twd=total_twd_cash,
            total_rmb=total_rmb_stock,
            total_receivables=total_receivables,
            total_profit_twd=total_profit_twd,
            recent_purchases=recent_purchases,
            recent_sales=recent_sales,
            is_admin=False
        )

    except Exception as e:
        flash(f"載入儀表板時發生錯誤: {e}", "danger")
        return render_template(
            "dashboard.html",
            total_twd=0.0,
            total_rmb=0.0,
            total_receivables=0.0,
            recent_purchases=[],
            recent_sales=[],
            is_admin=False
        )


@app.route("/admin/delete_audit_logs")
@admin_required
def admin_delete_audit_logs():
    """刪除記錄審計頁面"""
    try:
        # 獲取查詢參數
        table_name = request.args.get('table_name', '')
        operator_id = request.args.get('operator_id', '')
        page = int(request.args.get('page', 1))
        per_page = 20
        
        # 構建查詢
        query = db.select(DeleteAuditLog)
        
        if table_name:
            query = query.filter(DeleteAuditLog.table_name == table_name)
        
        if operator_id:
            try:
                operator_id_int = int(operator_id)
                query = query.filter(DeleteAuditLog.operator_id == operator_id_int)
            except ValueError:
                pass
        
        # 排序和分頁
        query = query.order_by(DeleteAuditLog.deleted_at.desc())
        
        # 獲取總數
        try:
            total_logs = db.session.execute(db.select(db.func.count(DeleteAuditLog.id))).scalar()
        except Exception as e:
            if "does not exist" in str(e) and "delete_audit_logs" in str(e):
                print("警告: delete_audit_logs 表格不存在，返回空結果")
                db.session.rollback()
                total_logs = 0
                audit_logs = []
            else:
                db.session.rollback()
                raise e
        else:
            # 重新執行查詢以獲取分頁結果
            try:
                audit_logs = db.session.execute(
                    query.offset((page - 1) * per_page).limit(per_page)
                ).scalars().all()
            except Exception as e:
                if "does not exist" in str(e) and "delete_audit_logs" in str(e):
                    print("警告: delete_audit_logs 表格不存在，返回空結果")
                    db.session.rollback()
                    audit_logs = []
                else:
                    db.session.rollback()
                    raise e
        
        # 轉換為字典格式
        logs_data = []
        for log in audit_logs:
            try:
                import json
                deleted_data = json.loads(log.deleted_data) if log.deleted_data else {}
            except:
                deleted_data = {}
            
            try:
                balance_changes = json.loads(log.balance_changes) if log.balance_changes else None
            except:
                balance_changes = None
            
            log_dict = {
                'id': log.id,
                'table_name': log.table_name,
                'record_id': log.record_id,
                'deleted_data': deleted_data,
                'operation_type': log.operation_type,
                'description': log.description,
                'operator_name': log.operator_name,
                'deleted_at': log.deleted_at,
                'ip_address': log.ip_address,
                'balance_changes': balance_changes
            }
            logs_data.append(log_dict)
        
        # 分頁資訊
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_logs,
            'pages': (total_logs + per_page - 1) // per_page,
            'has_prev': page > 1,
            'has_next': page * per_page < total_logs,
            'prev_num': page - 1,
            'next_num': page + 1,
        }
        
        # 獲取所有操作者列表（用於篩選）
        operators = db.session.execute(
            db.select(User.id, User.username)
            .order_by(User.username)
        ).all()
        
        return render_template(
            "admin/delete_audit_logs.html",
            audit_logs=logs_data,
            pagination=pagination,
            table_name=table_name,
            operator_id=operator_id,
            operators=operators,
            total_logs=total_logs
        )
        
    except Exception as e:
        print(f"載入刪除記錄審計頁面失敗: {e}")
        import traceback
        traceback.print_exc()
        flash("載入刪除記錄審計頁面時發生錯誤", "danger")
        return render_template(
            "admin/delete_audit_logs.html",
            audit_logs=[],
            pagination=None,
            table_name="",
            operator_id="",
            operators=[],
            total_logs=0
        )


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    """管理員儀表板頁面"""
    try:
        # --- 修正：直接使用實際帳戶餘額作為總資產，與現金管理頁面保持一致 ---
        all_accounts_obj = (
            db.session.execute(db.select(CashAccount))
            .scalars()
            .all()
        )

        total_twd_cash = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "TWD"
        )
        total_rmb_stock = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "RMB"
        )
        
        # 計算總應收帳款
        customers_with_receivables = (
            db.session.execute(
                db.select(Customer)
                .filter_by(is_active=True)
                .filter(Customer.total_receivables_twd > 0)
                .order_by(Customer.total_receivables_twd.desc())
            )
            .scalars()
            .all()
        )
        
        total_receivables = sum(c.total_receivables_twd for c in customers_with_receivables)

        latest_purchase = (
            db.session.execute(
                db.select(PurchaseRecord).order_by(PurchaseRecord.purchase_date.desc())
            )
            .scalars()
            .first()
        )
        current_buy_rate = latest_purchase.exchange_rate if latest_purchase else 4.5

        # 只計算台幣資產，不包含人民幣估值
        twd_assets = total_twd_cash

        # 計算總利潤（從所有銷售記錄計算，並扣除利潤提款）
        total_profit_twd = 0.0
        all_sales = (
            db.session.execute(
                db.select(SalesRecord)
            )
            .scalars()
            .all()
        )
        
        for sale in all_sales:
            profit_info = FIFOService.calculate_profit_for_sale(sale)
            if profit_info:
                total_profit_twd += profit_info.get('profit_twd', 0.0)
        
        # 扣除利潤提款記錄
        try:
            profit_withdrawals = (
                db.session.execute(
                    db.select(LedgerEntry)
                    .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
                )
                .scalars()
                .all()
            )
        except Exception as e:
            if "profit_before does not exist" in str(e):
                print("警告: 儀表板查詢 PROFIT_WITHDRAW 記錄時缺少欄位，跳過查詢")
                db.session.rollback()
                profit_withdrawals = []
            else:
                db.session.rollback()
                raise e
        
        total_profit_withdrawals = sum(entry.amount for entry in profit_withdrawals)
        total_profit_twd -= total_profit_withdrawals
        
        print(f"DEBUG: 管理員儀表板利潤計算 - 銷售利潤: {total_profit_twd + total_profit_withdrawals:.2f}, 利潤提款: {total_profit_withdrawals:.2f}, 最終利潤: {total_profit_twd:.2f}")
        
        # 设置变量别名以保持模板兼容性
        total_unsettled_amount_twd = total_receivables
        
        # 獲取庫存管理相關數據
        # 1. 近30日庫存變化趨勢
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # 查詢近30日的庫存變化
        inventory_changes = (
            db.session.execute(
                db.select(FIFOInventory)
                .filter(FIFOInventory.purchase_date >= thirty_days_ago)
                .order_by(FIFOInventory.purchase_date)
            )
            .scalars()
            .all()
        )
        
        # 按日期分組統計庫存變化
        inventory_by_date = {}
        for inv in inventory_changes:
            date_str = inv.purchase_date.strftime('%Y-%m-%d')
            if date_str not in inventory_by_date:
                inventory_by_date[date_str] = 0
            inventory_by_date[date_str] += inv.remaining_rmb
        
        # 生成圖表數據
        chart_labels = []
        chart_values = []
        current_date = thirty_days_ago
        while current_date <= datetime.now():
            date_str = current_date.strftime('%Y-%m-%d')
            chart_labels.append(date_str)
            chart_values.append(inventory_by_date.get(date_str, 0))
            current_date += timedelta(days=1)
        
        chart_data = {
            "labels": chart_labels,
            "values": chart_values,
        }
        
        # 2. 庫存狀態概覽
        # 查詢庫存總覽
        total_inventory_rmb = sum(inv.remaining_rmb for inv in inventory_changes)
        active_inventory_count = len([inv for inv in inventory_changes if inv.remaining_rmb > 0])
        exhausted_inventory_count = len([inv for inv in inventory_changes if inv.remaining_rmb <= 0])
        
        # 查詢庫存分配情況
        total_allocated_rmb = (
            db.session.execute(
                db.select(func.sum(FIFOSalesAllocation.allocated_rmb))
            )
            .scalar() or 0
        )
        
        # 庫存效率指標
        inventory_efficiency = (total_allocated_rmb / (total_inventory_rmb + total_allocated_rmb)) * 100 if (total_inventory_rmb + total_allocated_rmb) > 0 else 0
        
        return render_template(
            "admin.html",
            total_twd_cash=total_twd_cash,
            total_rmb_stock=total_rmb_stock,
            current_buy_rate=current_buy_rate,
            twd_assets=twd_assets,
            total_profit_twd=total_profit_twd,
            total_unsettled_amount_twd=total_unsettled_amount_twd,
            chart_data=chart_data,
            # 新增的庫存管理數據
            total_inventory_rmb=total_inventory_rmb,
            active_inventory_count=active_inventory_count,
            exhausted_inventory_count=exhausted_inventory_count,
            total_allocated_rmb=total_allocated_rmb,
            inventory_efficiency=inventory_efficiency,
        )
    except Exception as e:
        flash(f"載入儀表板數據時發生錯誤: {e}", "danger")
        # 在錯誤情況下，也要提供一個包含 chart_data 的預設上下文
        return render_template(
            "admin.html",
            total_twd_cash=0,
            total_rmb_stock=0,
            current_buy_rate=4.5,
            twd_assets=0,
            total_profit_twd=0,
            total_unsettled_amount_twd=0,
            chart_data={"labels": [], "values": []},
            # 新增的庫存管理數據預設值
            total_inventory_rmb=0,
            active_inventory_count=0,
            exhausted_inventory_count=0,
            total_allocated_rmb=0,
            inventory_efficiency=0,
        )


@app.route("/sales-entry")
@login_required
def sales_entry():
    """售出錄入頁面"""
    try:
        # --- 查詢頁面所需的動態資料 ---

        # 1. 查詢所有可用的客戶
        customers = (
            db.session.execute(
                db.select(Customer).filter_by(is_active=True).order_by(Customer.name)
            )
            .scalars()
            .all()
        )

        # 2. 查詢我方所有 RMB 帳戶，用於出貨
        #    我們需要同時獲取持有人資訊，以便在下拉選單中分組
        holders_with_rmb_accounts = (
            db.session.execute(
                db.select(Holder)
                .filter_by(is_active=True)
                .options(db.selectinload(Holder.cash_accounts))
            )
            .scalars()
            .all()
        )

        # --- 關鍵修正：直接使用實際帳戶餘額 ---
        # 獲取所有活躍的持有人和帳戶
        holders_with_accounts = (
            db.session.execute(
                db.select(Holder)
                .filter_by(is_active=True)
                .options(db.selectinload(Holder.cash_accounts))
            )
            .scalars()
            .all()
        )

        owner_rmb_accounts_grouped = []
        for holder in holders_with_accounts:
            rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
            if rmb_accounts:
                owner_rmb_accounts_grouped.append({
                    "holder_name": holder.name,
                    "accounts": [
                        {
                            "id": acc.id,
                            "name": acc.name,
                            "balance": float(acc.balance)  # 直接使用資料庫中的餘額
                        }
                        for acc in rmb_accounts
                    ]
                })

        # 3. 查詢所有未結清 (is_settled = False) 的銷售紀錄，實現分頁
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # 獲取總數
        total_sales = (
            db.session.execute(
                db.select(func.count(SalesRecord.id))
                .filter_by(is_settled=False)
            )
            .scalar()
        )
        
        # 計算分頁
        total_pages = (total_sales + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # 查詢當前頁的銷售記錄
        recent_unsettled_sales = (
            db.session.execute(
                db.select(SalesRecord)
                .filter_by(is_settled=False)
                .order_by(SalesRecord.created_at.desc())
                .offset(offset)
                .limit(per_page)
            )
            .scalars()
            .all()
        )
        
        # 4. 為每個銷售記錄計算利潤信息
        for sale in recent_unsettled_sales:
            profit_info = FIFOService.calculate_profit_for_sale(sale)
            if profit_info:
                sale.profit_info = profit_info
            else:
                sale.profit_info = None

        # 準備分頁資訊
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_sales,
            'pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1,
            'next_num': page + 1,
        }

        # --- 將所有查詢到的資料傳遞給前端模板 ---
        return render_template(
            "sales_entry.html",
            customers=customers,
            owner_rmb_accounts_grouped=owner_rmb_accounts_grouped,
            recent_unsettled_sales=recent_unsettled_sales,
            pagination=pagination,
        )

    except Exception as e:
        flash(f"載入售出錄入頁面時發生嚴重錯誤: {e}", "danger")
        return render_template(
            "sales_entry.html",
            customers=[],
            owner_rmb_accounts_grouped=[],
            recent_unsettled_sales=[],
        )


@app.route("/api/sales-entry", methods=["POST"])
@login_required
def api_sales_entry():
    """
    處理來自「售出錄入頁面」的訂單創建請求。
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "無效的請求格式。"}), 400

    try:
        # 1. 獲取並驗證資料
        customer_id = data.get("customer_id")
        customer_name_manual = data.get("customer_name_manual")
        rmb_account_id = int(data.get("rmb_account_id"))
        rmb_amount = float(data.get("rmb_amount"))
        exchange_rate = float(data.get("exchange_rate"))

        # 驗證客戶信息：必須有客戶ID或客戶名稱
        if not customer_id and not customer_name_manual:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "請選擇常用客戶或輸入客戶名稱。",
                    }
                ),
                400,
            )

        if not all([rmb_account_id, rmb_amount > 0, exchange_rate > 0]):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "出貨帳戶、金額和匯率都必須正確填寫。",
                    }
                ),
                400,
            )

        # 2. 處理客戶信息
        customer = None
        if customer_id:
            # 使用現有客戶ID
            customer = db.session.get(Customer, int(customer_id))
            if not customer:
                return jsonify({"status": "error", "message": "找不到指定的客戶。"}), 404
        else:
            # 使用手動輸入的客戶名稱
            customer_name = customer_name_manual.strip()
            if not customer_name:
                return jsonify({"status": "error", "message": "客戶名稱不能為空。"}), 400
            
            # 查找或創建客戶
            customer = Customer.query.filter_by(name=customer_name).first()
            if not customer:
                customer = Customer(name=customer_name)
                db.session.add(customer)
                db.session.flush()  # 獲取ID
        
        rmb_account = db.session.get(CashAccount, rmb_account_id)

        if not customer:
            return jsonify({"status": "error", "message": "找不到指定的客戶。"}), 404
        if not rmb_account or rmb_account.currency != "RMB":
            return jsonify({"status": "error", "message": "無效的 RMB 出貨帳戶。"}), 400
        if rmb_account.balance < rmb_amount:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"RMB 庫存不足！帳戶 {rmb_account.name} 僅剩 {rmb_account.balance:,.2f}。",
                    }
                ),
                400,
            )

        # 3. 核心業務邏輯
        twd_amount = round(rmb_amount * exchange_rate, 2)

        # 更新客戶餘額（應收帳款增加）
        customer.total_receivables_twd += twd_amount
        
        # 注意：RMB帳戶餘額不在此處扣款，而是在FIFO庫存分配時從實際庫存來源帳戶扣款

        # 創建銷售紀錄
        new_sale = SalesRecord(
            customer_id=customer.id,
            rmb_account_id=rmb_account.id,
            rmb_amount=rmb_amount,
            exchange_rate=exchange_rate,
            twd_amount=twd_amount,
            is_settled=False,
            operator_id=current_user.id,  # <--- V4.0 核心功能！記錄操作者
        )
        db.session.add(new_sale)
        db.session.flush()  # 先獲取ID，但不提交
        
        # 4. 更新FIFO庫存（關鍵修正！）
        try:
            # 使用FIFO服務分配庫存
            fifo_result = FIFOService.allocate_inventory_for_sale(new_sale)
            print(f"FIFO庫存分配成功: {fifo_result}")
            
            # 5. 自動記錄利潤到RMB帳戶和LedgerEntry
            print(f"DEBUG: fifo_result = {fifo_result}")
            if fifo_result and 'profit_twd' in fifo_result:
                profit_amount = fifo_result['profit_twd']
                print(f"DEBUG: 售出利潤金額: {profit_amount} TWD")
                
                try:
                    # 找到對應的RMB帳戶
                    rmb_account = new_sale.rmb_account
                    print(f"DEBUG: RMB帳戶 = {rmb_account}")
                    if rmb_account:
                        # 記錄到ProfitService（保持原有邏輯）
                        profit_result = ProfitService.add_profit(
                            account_id=rmb_account.id,
                            amount=profit_amount,
                            transaction_type="PROFIT_EARNED",
                            description=f"銷售利潤：客戶「{customer.name}」",
                            note=f"RMB {new_sale.rmb_amount}，匯率 {new_sale.twd_amount/new_sale.rmb_amount:.4f}",
                            related_transaction_id=new_sale.id,
                            related_transaction_type="SALES",
                            operator_id=current_user.id
                        )
                        
                        # 同時記錄到LedgerEntry中，用於利潤管理歷史
                        try:
                            # 計算當前總利潤（不包含當前銷售記錄）
                            existing_sales = db.session.execute(
                                db.select(SalesRecord)
                                .filter(SalesRecord.id != new_sale.id)
                            ).scalars().all()
                            
                            current_total_profit = 0.0
                            for sale in existing_sales:
                                sale_profit_info = FIFOService.calculate_profit_for_sale(sale)
                                if sale_profit_info:
                                    current_total_profit += sale_profit_info.get('profit_twd', 0.0)
                            
                            # 扣除之前的利潤提款
                            try:
                                profit_withdrawals = db.session.execute(
                                    db.select(LedgerEntry)
                                    .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
                                ).scalars().all()
                                total_withdrawals = sum(entry.amount for entry in profit_withdrawals)
                                current_total_profit -= total_withdrawals
                            except:
                                pass  # 如果查詢失敗，忽略
                            
                            # 創建利潤記錄
                            profit_entry = LedgerEntry(
                                entry_type="PROFIT_EARNED",
                                amount=profit_amount,
                                description=f"售出利潤：{customer.name}",
                                operator_id=current_user.id,
                                profit_before=current_total_profit,
                                profit_after=current_total_profit + profit_amount,
                                profit_change=profit_amount
                            )
                            db.session.add(profit_entry)
                            db.session.flush()  # 確保記錄被添加到會話中
                            print(f"✅ 記錄售出利潤到LedgerEntry成功: {profit_amount:.2f} TWD")
                            print(f"DEBUG: 利潤記錄 - 前: {current_total_profit:.2f}, 後: {current_total_profit + profit_amount:.2f}, 變動: {profit_amount:.2f}")
                            print(f"DEBUG: LedgerEntry ID: {profit_entry.id}")
                        except Exception as ledger_error:
                            print(f"⚠️ 記錄售出利潤到LedgerEntry失敗: {ledger_error}")
                            import traceback
                            traceback.print_exc()
                        
                        if profit_result["success"]:
                            print(f"✅ 自動記錄銷售利潤成功: {profit_amount:.2f} TWD")
                        else:
                            print(f"⚠️ 自動記錄銷售利潤失敗: {profit_result['message']}")
                    else:
                        print("⚠️ 找不到RMB帳戶，跳過利潤記錄")
                except Exception as profit_error:
                    print(f"⚠️ 記錄銷售利潤時發生錯誤: {profit_error}")
                    # 不影響銷售記錄的創建
        except Exception as e:
            print(f"FIFO庫存分配失敗: {e}")
            # 如果FIFO分配失敗，回滾整個交易
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"庫存分配失敗: {e}"
            }), 500
        
        # 提交所有更改
        db.session.commit()

        # 觸發全局數據同步（重新整理整個資料庫）
        try:
            from global_sync import sync_entire_database
            sync_entire_database(db.session)
            print(" 銷售記錄創建後全局數據同步完成")
        except Exception as sync_error:
            print(f"全局數據同步失敗（不影響銷售記錄）: {sync_error}")

        return jsonify(
            {
                "status": "success",
                "message": f"訂單創建成功！客戶「{customer.name}」新增應收款 NT$ {twd_amount:,.2f}。",
            }
        )

    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "輸入的資料格式不正確。"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"!! Error in api_sales_entry: {e}")
        import traceback

        traceback.print_exc()
        return (
            jsonify({"status": "error", "message": "伺服器內部錯誤，操作失敗。"}),
            500,
        )


@app.route("/cash_management")
@login_required
def cash_management_operator():
    """非管理員用戶的現金管理頁面"""
    try:
        page = request.args.get("page", 1, type=int)

        # 暫時移除過濾，直接查詢所有持有人
        holders_obj = (
            db.session.execute(db.select(Holder).filter_by(is_active=True))
            .scalars()
            .all()
        )
        
        # 轉換為可序列化的字典格式
        holders_data = [
            {
                "id": holder.id,
                "name": holder.name,
                "is_active": holder.is_active
            }
            for holder in holders_obj
        ]
        
        all_accounts_obj = (
            db.session.execute(db.select(CashAccount).order_by(CashAccount.holder_id))
            .scalars()
            .all()
        )

        total_twd = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "TWD"
        )
        total_rmb = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "RMB"
        )

        # 查詢應收帳款數據 - 添加錯誤處理
        try:
            customers_with_receivables = (
                db.session.execute(
                    db.select(Customer)
                    .filter_by(is_active=True)
                    .filter(Customer.total_receivables_twd > 0)
                    .order_by(Customer.total_receivables_twd.desc())
                )
                .scalars()
                .all()
            )
            
            total_receivables = sum(c.total_receivables_twd for c in customers_with_receivables)
        except Exception as customer_error:
            print(f"Customer表查詢失敗，可能表不存在: {customer_error}")
            customers_with_receivables = []
            total_receivables = 0.0

        accounts_by_holder = {}
        # 先為所有持有人創建條目，即使沒有帳戶
        for holder in holders_obj:
            accounts_by_holder[holder.id] = {
                "holder_name": holder.name,
                "accounts": [],
                "total_twd": 0,
                "total_rmb": 0,
            }
        
        # 然後添加帳戶信息
        for acc in all_accounts_obj:
            if acc.holder_id in accounts_by_holder:
                accounts_by_holder[acc.holder_id]["accounts"].append(
                    {
                        "id": acc.id,
                        "name": acc.name,
                        "currency": acc.currency,
                        "balance": acc.balance,
                        "profit_balance": acc.profit_balance,  # 新增：利潤餘額
                        "is_active": acc.is_active,
                    }
                )
                if acc.currency == "TWD":
                    accounts_by_holder[acc.holder_id]["total_twd"] += acc.balance
                elif acc.currency == "RMB":
                    accounts_by_holder[acc.holder_id]["total_rmb"] += acc.balance

        purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
        sales = db.session.execute(
            db.select(SalesRecord)
            .options(
                db.selectinload(SalesRecord.customer),
                db.selectinload(SalesRecord.rmb_account)
            )
        ).scalars().all()
        # 安全地查詢 LedgerEntry，處理可能缺少的欄位
        try:
            misc_entries = db.session.execute(
                db.select(LedgerEntry)
                .options(db.selectinload(LedgerEntry.account))
            ).scalars().all()
        except Exception as e:
            if "profit_before does not exist" in str(e):
                print("警告: ledger_entries 表格缺少利潤欄位，跳過查詢")
                db.session.rollback()  # 回滾失敗的事務
                misc_entries = []
                db.session.begin()  # 開始新事務
            else:
                db.session.rollback()  # 回滾失敗的事務
                raise e
        # 確保在乾淨的事務中查詢 cash_logs
        try:
            cash_logs = db.session.execute(db.select(CashLog)).scalars().all()
        except Exception as e:
            print(f"警告: cash_logs 查詢失敗: {e}")
            db.session.rollback()
            cash_logs = []

        unified_stream = []
        for p in purchases:
            if p.payment_account and p.deposit_account:
                # 獲取渠道名稱
                channel_name = "未知渠道"
                if p.channel:
                    channel_name = p.channel.name
                elif hasattr(p, 'channel_name_manual') and p.channel_name_manual:
                    channel_name = p.channel_name_manual
                
                unified_stream.append(
                    {
                        "type": "買入",
                        "date": p.purchase_date.isoformat(),
                        "description": f"向 {channel_name} 買入",
                        "twd_change": -p.twd_cost,
                        "rmb_change": p.rmb_amount,
                        "operator": p.operator.username if p.operator else "未知",
                        "payment_account": p.payment_account.name if p.payment_account else "N/A",
                        "deposit_account": p.deposit_account.name if p.deposit_account else "N/A",
                        "note": p.note if hasattr(p, 'note') and p.note else None,
                    }
                )
        for s in sales:
            if s.customer:
                # 計算銷售利潤
                profit_info = FIFOService.calculate_profit_for_sale(s)
                profit_twd = profit_info.get('profit_twd', 0.0) if profit_info else 0.0
                
                unified_stream.append(
                    {
                        "type": "售出",
                        "date": s.created_at.isoformat(),
                        "description": f"向 {s.customer.name} 售出",
                        "twd_change": 0,  # 銷售時不顯示TWD變動
                        "rmb_change": -s.rmb_amount,
                        "operator": s.operator.username if s.operator else "未知",
                        "payment_account": "N/A",
                        "deposit_account": "N/A",
                        "note": f"利潤: {profit_twd:.2f} TWD" if profit_twd > 0 else None,
                    }
                )
        for entry in misc_entries:
            unified_stream.append(
                {
                    "type": "記帳",
                    "date": entry.entry_date.isoformat(),
                    "description": entry.description,
                    "twd_change": entry.amount if entry.entry_type == "TWD" else 0,
                    "rmb_change": entry.amount if entry.entry_type == "RMB" else 0,
                    "operator": entry.operator.username if entry.operator else "未知",
                    "payment_account": entry.account.name if entry.account else "N/A",
                    "deposit_account": "N/A",
                    "note": entry.description,
                }
            )
        for log in cash_logs:
            twd_change = 0
            rmb_change = 0
            
            # 根據類型設置金額變動
            if log.type == "SETTLEMENT":
                # 銷帳記錄：記錄TWD收入
                twd_change = log.amount
                rmb_change = 0
            elif log.type == "TWD":
                # TWD現金日誌
                twd_change = log.amount
                rmb_change = 0
            elif log.type == "RMB":
                # RMB現金日誌
                twd_change = 0
                rmb_change = log.amount
            else:
                # 其他類型
                twd_change = 0
                rmb_change = 0
            
            unified_stream.append(
                {
                    "type": log.type,  # 使用實際的類型名稱
                    "date": log.time.isoformat(),
                    "description": log.description,
                    "twd_change": twd_change,
                    "rmb_change": rmb_change,
                    "operator": log.operator.username if log.operator else "未知",
                    "payment_account": "N/A",
                    "deposit_account": "N/A",
                    "note": log.description,
                }
            )

        # 按日期排序，最新的在前面
        unified_stream.sort(key=lambda x: x["date"], reverse=True)

        # --- 修正：使用實際帳戶餘額作為總資產，而不是流水計算的累積餘額 ---
        # 計算當前實際的帳戶總餘額
        actual_total_twd = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "TWD"
        )
        actual_total_rmb = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "RMB"
        )
        
        # 使用實際餘額作為總資產
        total_twd = actual_total_twd
        total_rmb = actual_total_rmb
        
        # 計算每筆交易後的累積餘額（用於流水顯示，從實際餘額開始倒推）
        running_twd_balance = actual_total_twd
        running_rmb_balance = actual_total_rmb
        
        # 從最新的交易開始，向前倒推每筆交易前的餘額
        for movement in unified_stream:
            # 記錄此筆交易後的餘額（當前累積餘額）
            movement['running_twd_balance'] = running_twd_balance
            movement['running_rmb_balance'] = running_rmb_balance
            
            # 計算此筆交易前的餘額（為下一筆交易準備）
            running_twd_balance -= (movement.get('twd_change', 0) or 0)
            running_rmb_balance -= (movement.get('rmb_change', 0) or 0)

        # --- 修正：使用實際的資料庫餘額，不重新計算 ---
        accounts_by_holder = {}
        for holder in holders_obj:
            accounts_by_holder[holder.id] = {
                "holder_name": holder.name,
                "accounts": [],
                "total_twd": 0,
                "total_rmb": 0,
            }
        
        # 使用實際的帳戶餘額
        for acc in all_accounts_obj:
            if acc.holder_id in accounts_by_holder:
                accounts_by_holder[acc.holder_id]["accounts"].append({
                    "id": acc.id,
                    "name": acc.name,
                    "currency": acc.currency,
                    "balance": acc.balance,  # 使用實際資料庫餘額
                    "is_active": acc.is_active,
                })
                
                # 累計持有人總餘額
                if acc.currency == "TWD":
                    accounts_by_holder[acc.holder_id]["total_twd"] += acc.balance
                elif acc.currency == "RMB":
                    accounts_by_holder[acc.holder_id]["total_rmb"] += acc.balance
        
        # 分頁處理
        items_per_page = 20
        total_items = len(unified_stream)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_stream = unified_stream[start_idx:end_idx]

        # 查詢待付款項數據
        try:
            pending_payments = (
                db.session.execute(
                    db.select(PendingPayment)
                    .filter_by(is_settled=False)
                    .order_by(PendingPayment.created_at.desc())
                )
                .scalars()
                .all()
            )
        except Exception as pending_error:
            print(f"PendingPayment表查詢失敗，可能表不存在: {pending_error}")
            pending_payments = []

        # 準備 owner_accounts 數據
        all_accounts_obj = (
            db.session.execute(db.select(CashAccount).order_by(CashAccount.holder_id))
            .scalars()
            .all()
        )
        
        owner_accounts_data = [
            {
                "id": a.id,
                "name": a.name,
                "currency": a.currency,
                "holder_id": a.holder_id,
                "balance": a.balance
            }
            for a in all_accounts_obj
        ]
        

        return render_template(
            "cash_management.html",
            holders=holders_data,
            accounts_by_holder=accounts_by_holder,
            total_twd=total_twd,
            total_rmb=total_rmb,
            total_receivables_twd=total_receivables,
            customers_with_receivables=customers_with_receivables,
            pending_payments=pending_payments,
            owner_accounts=owner_accounts_data,
            movements=paginated_stream,
            current_page=page,
            total_pages=total_pages,
            total_items=total_items,
            items_per_page=items_per_page,
        )

    except Exception as e:
        flash(f"載入現金管理頁面時發生錯誤: {e}", "danger")
        return render_template(
            "cash_management.html",
            holders=[],
            accounts_by_holder={},
            total_twd=0.0,
            total_rmb=0.0,
            total_receivables_twd=0.0,
            customers_with_receivables=[],
            pending_payments=[],
            owner_accounts=[],
            movements=[],
            current_page=1,
            total_pages=1,
            total_items=0,
            items_per_page=20,
        )


@app.route("/admin/cash_management")
@login_required
def cash_management():
    try:
        page = request.args.get("page", 1, type=int)

        # 暫時移除過濾，直接查詢所有持有人
        holders_obj = (
            db.session.execute(db.select(Holder).filter_by(is_active=True))
            .scalars()
            .all()
        )
        
        all_accounts_obj = (
            db.session.execute(db.select(CashAccount).order_by(CashAccount.holder_id))
            .scalars()
            .all()
        )

        total_twd = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "TWD"
        )
        total_rmb = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "RMB"
        )

        # 查詢應收帳款數據 - 添加錯誤處理
        try:
            customers_with_receivables = (
                db.session.execute(
                    db.select(Customer)
                    .filter_by(is_active=True)
                    .filter(Customer.total_receivables_twd > 0)
                    .order_by(Customer.total_receivables_twd.desc())
                )
                .scalars()
                .all()
            )
            
            total_receivables = sum(c.total_receivables_twd for c in customers_with_receivables)
        except Exception as customer_error:
            print(f"Customer表查詢失敗，可能表不存在: {customer_error}")
            customers_with_receivables = []
            total_receivables = 0.0

        accounts_by_holder = {}
        # 先為所有持有人創建條目，即使沒有帳戶
        for holder in holders_obj:
            accounts_by_holder[holder.id] = {
                "holder_name": holder.name,
                "accounts": [],
                "total_twd": 0,
                "total_rmb": 0,
            }
        
        # 然後添加帳戶信息
        for acc in all_accounts_obj:
            if acc.holder_id in accounts_by_holder:
                accounts_by_holder[acc.holder_id]["accounts"].append(
                    {
                        "id": acc.id,
                        "name": acc.name,
                        "currency": acc.currency,
                        "balance": acc.balance,
                        "profit_balance": acc.profit_balance,  # 新增：利潤餘額
                        "is_active": acc.is_active,
                    }
                )
                if acc.currency == "TWD":
                    accounts_by_holder[acc.holder_id]["total_twd"] += acc.balance
                elif acc.currency == "RMB":
                    accounts_by_holder[acc.holder_id]["total_rmb"] += acc.balance

        purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
        sales = db.session.execute(
            db.select(SalesRecord)
            .options(
                db.selectinload(SalesRecord.customer),
                db.selectinload(SalesRecord.rmb_account)
            )
        ).scalars().all()
        # 安全地查詢 LedgerEntry，處理可能缺少的欄位
        try:
            misc_entries = db.session.execute(
                db.select(LedgerEntry)
                .options(db.selectinload(LedgerEntry.account))
            ).scalars().all()
        except Exception as e:
            if "profit_before does not exist" in str(e):
                print("警告: ledger_entries 表格缺少利潤欄位，跳過查詢")
                db.session.rollback()  # 回滾失敗的事務
                misc_entries = []
                db.session.begin()  # 開始新事務
            else:
                db.session.rollback()  # 回滾失敗的事務
                raise e
        # 確保在乾淨的事務中查詢 cash_logs
        try:
            cash_logs = db.session.execute(db.select(CashLog)).scalars().all()
        except Exception as e:
            print(f"警告: cash_logs 查詢失敗: {e}")
            db.session.rollback()
            cash_logs = []

        unified_stream = []
        for p in purchases:
            if p.payment_account and p.deposit_account:
                # 獲取渠道名稱
                channel_name = "未知渠道"
                if p.channel:
                    channel_name = p.channel.name
                elif hasattr(p, 'channel_name_manual') and p.channel_name_manual:
                    channel_name = p.channel_name_manual
                
                unified_stream.append(
                    {
                        "type": "買入",
                        "date": p.purchase_date.isoformat(),
                        "description": f"向 {channel_name} 買入",
                        "twd_change": -p.twd_cost,
                        "rmb_change": p.rmb_amount,
                        "operator": p.operator.username if p.operator else "未知",
                        "payment_account": p.payment_account.name if p.payment_account else "N/A",
                        "deposit_account": p.deposit_account.name if p.deposit_account else "N/A",
                        "note": p.note if hasattr(p, 'note') and p.note else None,
                    }
                )
        for s in sales:
            if s.customer:
                # 計算銷售利潤
                profit_info = FIFOService.calculate_profit_for_sale(s)
                profit = profit_info['profit_twd'] if profit_info else 0
                
                unified_stream.append(
                    {
                        "type": "售出",
                        "date": s.created_at.isoformat(),
                        "description": f"售予 {s.customer.name}",
                        "twd_change": 0,  # 售出不直接增加現金，而是增加應收帳款
                        "rmb_change": -s.rmb_amount,
                        "operator": s.operator.username if s.operator else "未知",
                        "profit": profit,
                        "payment_account": s.rmb_account.name if s.rmb_account else "N/A",  # 出貨的RMB帳戶
                        "deposit_account": "應收帳款",  # 售出產生應收帳款
                        "note": s.note if hasattr(s, 'note') and s.note else None,
                    }
                )
        for entry in misc_entries:
            twd_change = 0
            rmb_change = 0
            
            # 調試信息：檢查每個記帳記錄
            print(f"DEBUG: 處理記帳記錄 - 類型: {entry.entry_type}, 帳戶: {entry.account.name if entry.account else 'N/A'}, 金額: {entry.amount}")
            
            # 優化：移除對BUY_IN_DEBIT和BUY_IN_CREDIT的特殊處理
            # 因為買入交易現在只使用PurchaseRecord，不需要額外的LedgerEntry
            
            # 處理其他類型的記帳記錄
            if entry.account and entry.account.currency == "TWD":
                if entry.entry_type in ["DEPOSIT", "TRANSFER_IN", "SETTLEMENT"]:
                    # 存款、轉入、銷帳都是增加TWD餘額
                    twd_change = entry.amount
                else:
                    # 其他類型（如提款、轉出）是減少TWD餘額
                    twd_change = -entry.amount
                
                print(f"  TWD帳戶變動: {twd_change} (類型: {entry.entry_type})")
                
            elif entry.account and entry.account.currency == "RMB":
                rmb_change = (
                    entry.amount
                    if entry.entry_type in ["DEPOSIT", "TRANSFER_IN"]
                    else -entry.amount
                )
                
                print(f"  RMB帳戶變動: {rmb_change} (類型: {entry.entry_type})")
            
            # 顯示所有記帳記錄，包括提款記錄
            # 移除過濾，確保提款記錄被包含在內
            if True:  # 暫時移除過濾，檢查所有記錄
                # 根據交易類型設置出入款帳戶
                payment_account = "N/A"
                deposit_account = "N/A"
                
                if entry.entry_type in ["DEPOSIT"]:
                    # 存款：外部 -> 帳戶
                    payment_account = "外部存款"
                    deposit_account = entry.account.name if entry.account else "N/A"
                elif entry.entry_type in ["WITHDRAW"]:
                    # 提款：帳戶 -> 外部
                    payment_account = entry.account.name if entry.account else "N/A"
                    deposit_account = "外部提款"
                elif entry.entry_type in ["TRANSFER_OUT"]:
                    # 轉出：本帳戶 -> 其他帳戶
                    payment_account = entry.account.name if entry.account else "N/A"
                    # 從描述中提取目標帳戶名稱
                    if "轉出至" in entry.description:
                        deposit_account = entry.description.replace("轉出至 ", "")
                    else:
                        deposit_account = "N/A"
                elif entry.entry_type in ["TRANSFER_IN"]:
                    # 轉入：其他帳戶 -> 本帳戶
                    deposit_account = entry.account.name if entry.account else "N/A"
                    # 從描述中提取來源帳戶名稱
                    if "從" in entry.description and "轉入" in entry.description:
                        payment_account = entry.description.replace("從 ", "").replace(" 轉入", "")
                    else:
                        payment_account = "N/A"
                elif entry.entry_type in ["SETTLEMENT"]:
                    # 銷帳：客戶 -> 帳戶
                    payment_account = "客戶付款"
                    deposit_account = entry.account.name if entry.account else "N/A"
                else:
                    # 其他類型
                    payment_account = entry.account.name if entry.account else "N/A"
                    deposit_account = "N/A"
                
                # 調試信息：檢查添加到流水記錄的數據
                print(f"  添加到流水記錄: 類型={entry.entry_type}, TWD變動={twd_change}, RMB變動={rmb_change}")
                
                unified_stream.append(
                    {
                        "type": entry.entry_type,
                        "date": entry.entry_date.isoformat(),
                        "description": entry.description,
                        "twd_change": twd_change,
                        "rmb_change": rmb_change,
                        "operator": entry.operator.username if entry.operator else "未知",
                        "payment_account": payment_account,
                        "deposit_account": deposit_account,
                        "note": getattr(entry, 'note', None) or (entry.description.split(' - ', 1)[1] if ' - ' in entry.description else None),
                    }
                )

        # 處理現金日誌記錄
        for log in cash_logs:
            twd_change = 0
            rmb_change = 0
            
            # 優化：移除對BUY_IN的特殊處理
            # 因為買入交易現在只使用PurchaseRecord，不需要額外的CashLog
            
            if log.type == "CARD_PURCHASE":
                # 刷卡記帳：記錄TWD支出
                twd_change = -log.amount
                rmb_change = 0
            elif log.type == "SETTLEMENT":
                # 銷帳記錄：記錄TWD收入
                twd_change = log.amount
                rmb_change = 0
            else:
                # 其他類型的現金日誌
                twd_change = 0
                rmb_change = 0
            
            # 只顯示非買入相關的現金日誌
            if log.type != "BUY_IN":
                # 根據現金日誌類型設置出入款帳戶
                payment_account = "N/A"
                deposit_account = "N/A"
                
                if log.type == "CARD_PURCHASE":
                    # 刷卡支出
                    payment_account = "刷卡"
                    deposit_account = "N/A"
                elif log.type == "SETTLEMENT":
                    # 銷帳收入：從對應的LedgerEntry中找到帳戶信息
                    payment_account = "客戶付款"
                    deposit_account = "N/A"
                    
                    # 查找對應的LedgerEntry來獲取帳戶信息
                    matching_entry = None
                    for entry in misc_entries:
                        if (entry.entry_type == "SETTLEMENT" and 
                            entry.description == log.description and
                            abs((entry.entry_date - log.time).total_seconds()) < 10):  # 10秒內的記錄認為是同一筆
                            matching_entry = entry
                            break
                    
                    if matching_entry and matching_entry.account:
                        deposit_account = matching_entry.account.name
                    else:
                        deposit_account = "現金帳戶"
                else:
                    # 其他類型的現金日誌
                    payment_account = "N/A"
                    deposit_account = "N/A"
                
                unified_stream.append(
                    {
                        "type": log.type,
                        "date": log.time.isoformat(),
                        "description": log.description,
                        "twd_change": twd_change,
                        "rmb_change": rmb_change,
                        "operator": log.operator.username if log.operator else "未知",
                        "payment_account": payment_account,
                        "deposit_account": deposit_account,
                        "note": getattr(log, 'note', None),
                    }
                )

        # 按日期排序（新的在前）
        unified_stream.sort(key=lambda x: x["date"], reverse=True)
        
        # --- 修正：使用實際帳戶餘額作為總資產，而不是流水計算的累積餘額 ---
        # 計算當前實際的帳戶總餘額
        actual_total_twd = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "TWD"
        )
        actual_total_rmb = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "RMB"
        )
        
        # 使用實際餘額作為總資產
        total_twd = actual_total_twd
        total_rmb = actual_total_rmb
        
        # 計算每筆交易後的累積餘額（用於流水顯示，從實際餘額開始倒推）
        running_twd_balance = actual_total_twd
        running_rmb_balance = actual_total_rmb
        
        # 從最新的交易開始，向前倒推每筆交易前的餘額
        for movement in unified_stream:
            # 記錄此筆交易後的餘額（當前累積餘額）
            movement['running_twd_balance'] = running_twd_balance
            movement['running_rmb_balance'] = running_rmb_balance
            
            # 計算此筆交易前的餘額（為下一筆交易準備）
            running_twd_balance -= (movement.get('twd_change', 0) or 0)
            running_rmb_balance -= (movement.get('rmb_change', 0) or 0)
        
        # --- 修正：使用實際的資料庫餘額，不重新計算 ---
        accounts_by_holder = {}
        for holder in holders_obj:
            accounts_by_holder[holder.id] = {
                "holder_name": holder.name,
                "accounts": [],
                "total_twd": 0,
                "total_rmb": 0,
            }
        
        # 使用實際的帳戶餘額
        for acc in all_accounts_obj:
            if acc.holder_id in accounts_by_holder:
                accounts_by_holder[acc.holder_id]["accounts"].append({
                    "id": acc.id,
                    "name": acc.name,
                    "currency": acc.currency,
                    "balance": acc.balance,  # 使用實際資料庫餘額
                    "is_active": acc.is_active,
                })
                
                # 累計持有人總餘額
                if acc.currency == "TWD":
                    accounts_by_holder[acc.holder_id]["total_twd"] += acc.balance
                elif acc.currency == "RMB":
                    accounts_by_holder[acc.holder_id]["total_rmb"] += acc.balance

        per_page = 50
        total_items = len(unified_stream)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_items = unified_stream[start:end]

        from math import ceil

        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total_items,
            "pages": ceil(total_items / per_page),
            "has_prev": page > 1,
            "has_next": page * per_page < total_items,
            "prev_num": page - 1,
            "next_num": page + 1,
        }

        # 查詢待付款項數據
        try:
            pending_payments = (
                db.session.execute(
                    db.select(PendingPayment)
                    .filter_by(is_settled=False)
                    .order_by(PendingPayment.created_at.desc())
                )
                .scalars()
                .all()
            )
        except Exception as pending_error:
            print(f"PendingPayment表查詢失敗，可能表不存在: {pending_error}")
            pending_payments = []

        # --- 關鍵修正：確保您傳遞的是正確的分頁後數據 ---
        return render_template(
            "cash_management.html",
            total_twd=total_twd,
            total_rmb=total_rmb,
            total_receivables_twd=total_receivables,
            customers_with_receivables=customers_with_receivables,
            pending_payments=pending_payments,
            accounts_by_holder=accounts_by_holder,
            movements=paginated_items,  # <-- 傳遞分頁後的當前頁數據
            pagination=pagination,  # <-- 傳遞分頁控制對象
            holders=[{"id": h.id, "name": h.name} for h in holders_obj],
            owner_accounts=[
                {
                    "id": a.id,
                    "name": a.name,
                    "currency": a.currency,
                    "holder_id": a.holder_id,
                    "balance": a.balance
                }
                for a in all_accounts_obj
            ],
        )
    except Exception as e:
        print(f"!! 現金管理頁面發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        flash("載入現金管理數據時發生嚴重錯誤。", "danger")
        return render_template(
            "cash_management.html",
            total_twd=0,
            total_rmb=0,
            total_receivables_twd=0,
            customers_with_receivables=[],
            pending_payments=[],
            accounts_by_holder={},
            movements=[],
            holders=[],
            owner_accounts=[],
            pagination=None,
        )


@app.route("/buy-in")
@login_required
def buy_in():
    """買入頁面"""
    try:
        channels = (
            db.session.execute(
                db.select(Channel).filter_by(is_active=True).order_by(Channel.name)
            )
            .scalars()
            .all()
        )
        
        # 轉換為可序列化的格式
        channels_serializable = [
            {
                "id": channel.id,
                "name": channel.name,
                "is_active": channel.is_active
            }
            for channel in channels
        ]

        # 2. 查詢我方所有資金持有人及其下的帳戶，用於付款和收款
        holders_with_accounts = (
            db.session.execute(
                db.select(Holder)
                .filter_by(is_active=True)
                .options(db.selectinload(Holder.cash_accounts))
            )
            .scalars()
            .all()
        )

        # --- 修正：直接查詢實際的帳戶餘額並序列化 ---
        # 按持有人分組帳戶，直接使用資料庫中的餘額
        owner_twd_accounts_grouped = {}
        owner_rmb_accounts_grouped = {}
        
        for holder in holders_with_accounts:
            twd_accounts = [acc for acc in holder.cash_accounts if acc.currency == "TWD" and acc.is_active]
            rmb_accounts = [acc for acc in holder.cash_accounts if acc.currency == "RMB" and acc.is_active]
            
            if twd_accounts:
                # 轉換為可序列化的格式，直接使用資料庫餘額
                owner_twd_accounts_grouped[holder.name] = [
                    {
                        "id": acc.id,
                        "name": acc.name,
                        "currency": acc.currency,
                        "balance": float(acc.balance)  # 直接使用資料庫中的餘額
                    }
                    for acc in twd_accounts
                ]
            if rmb_accounts:
                # 轉換為可序列化的格式，直接使用資料庫中的餘額
                owner_rmb_accounts_grouped[holder.name] = [
                    {
                        "id": acc.id,
                        "name": acc.name,
                        "currency": acc.currency,
                        "balance": float(acc.balance)  # 直接使用資料庫中的餘額
                    }
                    for acc in rmb_accounts
                ]

        # 實現分頁功能 - 每頁顯示10筆買入紀錄
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # 查詢所有買入紀錄並實現分頁
        purchases_pagination = (
            db.session.execute(
                db.select(PurchaseRecord)
                .options(
                    db.selectinload(PurchaseRecord.channel),
                    db.selectinload(PurchaseRecord.payment_account),
                    db.selectinload(PurchaseRecord.deposit_account),
                    db.selectinload(PurchaseRecord.operator)
                )
                .order_by(PurchaseRecord.purchase_date.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            .scalars()
            .all()
        )
        
        # 計算總筆數和總頁數
        total_purchases = db.session.execute(
            db.select(db.func.count(PurchaseRecord.id))
        ).scalar()
        
        total_pages = (total_purchases + per_page - 1) // per_page
        
        # 建立分頁資訊
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_purchases,
            'pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1,
            'next_num': page + 1,
        }
        
        # 轉換為可序列化的格式
        recent_purchases_serializable = []
        for record in purchases_pagination:
            recent_purchases_serializable.append({
                "id": record.id,
                "purchase_date": record.purchase_date,
                "rmb_amount": float(record.rmb_amount),
                "exchange_rate": float(record.exchange_rate),
                "twd_cost": float(record.twd_cost),
                "channel": {
                    "id": record.channel.id,
                    "name": record.channel.name
                } if record.channel else None,
                "payment_account": {
                    "id": record.payment_account.id,
                    "name": record.payment_account.name
                } if record.payment_account else None,
                "deposit_account": {
                    "id": record.deposit_account.id,
                    "name": record.deposit_account.name
                } if record.deposit_account else None,
                "operator": {
                    "id": record.operator.id,
                    "username": record.operator.username
                } if record.operator else None
            })

        return render_template(
            "buy_in.html",
            channels=channels_serializable,
            owner_twd_accounts_grouped=owner_twd_accounts_grouped,
            owner_rmb_accounts_grouped=owner_rmb_accounts_grouped,
            recent_purchases=recent_purchases_serializable,
            pagination=pagination,
        )

    except Exception as e:
        flash(f"載入買入頁面時發生嚴重錯誤: {e}", "danger")
        # 即使出錯，也回傳一個安全的空頁面，避免程式崩潰
        return render_template(
            "buy_in.html",
            channels=[],
            owner_twd_accounts_grouped={},
            owner_rmb_accounts_grouped={},
            recent_purchases=[],
            pagination={
                'page': 1,
                'per_page': 10,
                'total': 0,
                'pages': 0,
                'has_prev': False,
                'has_next': False,
                'prev_num': 0,
                'next_num': 0,
            },
        )


@app.route("/card-purchase")
@login_required
def card_purchase():
    """刷卡記帳頁面"""
    try:
        # 獲取當前日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 獲取分頁參數
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # 查詢刷卡記錄，按日期降序排列
        purchases_query = (
            db.select(CardPurchase)
            .options(db.selectinload(CardPurchase.operator))
            .order_by(CardPurchase.purchase_date.desc())
        )
        
        # 分頁
        purchases = db.paginate(
            purchases_query,
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template(
            "card_purchase.html",
            today=today,
            purchases=purchases
        )
        
    except Exception as e:
        flash(f"載入刷卡記帳頁面時發生錯誤: {e}", "danger")
        return render_template(
            "card_purchase.html",
            today=datetime.now().strftime('%Y-%m-%d'),
            purchases=None
        )


@app.route("/api/card-purchase", methods=["POST"])
@login_required
def api_card_purchase():
    """處理刷卡記帳的 API"""
    try:
        data = request.form
        
        # 獲取表單數據
        purchase_date = datetime.strptime(data.get('purchase_date'), '%Y-%m-%d')
        supplier = data.get('supplier')
        rmb_amount = float(data.get('rmb_amount'))
        twd_equivalent = float(data.get('twd_equivalent'))
        
        # 計算含3%手續費的RMB金額
        rmb_with_fee = rmb_amount * 1.03
        
        # 計算成本匯率
        calculated_rate = twd_equivalent / rmb_with_fee
        
        # 創建新的刷卡記錄
        new_purchase = CardPurchase(
            purchase_date=purchase_date,
            supplier=supplier,
            rmb_amount=rmb_amount,
            twd_equivalent=twd_equivalent,
            calculated_rate=calculated_rate,
            rmb_with_fee=rmb_with_fee,
            operator_id=current_user.id
        )
        
        db.session.add(new_purchase)

        # 創建現金日誌記錄 - 刷卡記帳
        cash_log = CashLog(
            type="CARD_PURCHASE",
            description=f"刷卡記帳：{supplier}，RMB ¥{rmb_amount:,.2f}，TWD {twd_equivalent:,.2f}，匯率 {calculated_rate:.4f}",
            amount=twd_equivalent,
            operator_id=current_user.id
        )
        db.session.add(cash_log)

        db.session.commit()
        
        flash("刷卡記帳成功！", "success")
        return redirect(url_for('card_purchase'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"刷卡記帳失敗: {e}", "danger")
        return redirect(url_for('card_purchase'))


@app.route("/api/buy-in", methods=["POST"])
@login_required
def api_buy_in():
    """
    處理所有來自「買入頁面」的後端 API 請求，包括：
    - 執行一筆買入交易 (action: 'record_purchase')
    - 新增常用渠道 (action: 'add_channel')
    - 刪除常用渠道 (action: 'delete_channel')
    """
    data = request.get_json()
    if not data or "action" not in data:
        return jsonify({"status": "error", "message": "無效的請求格式。"}), 400

    action = data.get("action")

    try:
        # === 執行一筆買入交易 ===
        if action == "record_purchase":
            # 1. 獲取並驗證資料
            try:
                payment_account_id = data.get("payment_account_id")
                if payment_account_id:
                    payment_account_id = int(payment_account_id)
                deposit_account_id = int(data.get("deposit_account_id"))
                rmb_amount = float(data.get("rmb_amount"))
                exchange_rate = float(data.get("exchange_rate"))
                channel_id = data.get("channel_id")  # 可能為空字符串、null或數字
                channel_name_manual = data.get("channel_name_manual", "").strip()
                payment_status = data.get("payment_status", "paid")  # 默認為已付款
            except (ValueError, TypeError, AttributeError):
                return (
                    jsonify({"status": "error", "message": "輸入的資料格式不正確。"}),
                    400,
                )

            # 根據付款狀態進行不同的驗證
            if payment_status == "paid":
                # 已付款：需要付款帳戶
                if not all([payment_account_id, deposit_account_id, rmb_amount > 0, exchange_rate > 0]):
                    return (
                        jsonify({"status": "error", "message": "所有帳戶和金額欄位都必須正確填寫。"}),
                        400,
                    )
            else:
                # 未付款：不需要付款帳戶
                if not all([deposit_account_id, rmb_amount > 0, exchange_rate > 0]):
                    return (
                        jsonify({"status": "error", "message": "入庫帳戶和金額欄位都必須正確填寫。"}),
                    400,
                )
            
            # 驗證渠道：必須有渠道ID或手動輸入的渠道名稱
            if not channel_id and not channel_name_manual:
                return (
                    jsonify(
                        {"status": "error", "message": "請選擇或輸入一個購買渠道。"}
                    ),
                    400,
                )

            # 2. 查詢資料庫物件
            payment_account = None
            if payment_account_id:
                payment_account = db.session.get(CashAccount, payment_account_id)
                if not payment_account or payment_account.currency != "TWD":
                    return (
                        jsonify({"status": "error", "message": "無效的 TWD 付款帳戶。"}),
                        400,
                    )
            
            deposit_account = db.session.get(CashAccount, deposit_account_id)
            if not deposit_account or deposit_account.currency != "RMB":
                return (
                    jsonify({"status": "error", "message": "無效的 RMB 入庫帳戶。"}),
                    400,
                )

            # 3. 核心業務邏輯
            twd_cost = rmb_amount * exchange_rate
            
            # 根據付款狀態檢查餘額
            if payment_status == "paid" and payment_account and payment_account.balance < twd_cost:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"TWD 帳戶餘額不足！需要 {twd_cost:,.2f}，但僅剩 {payment_account.balance:,.2f}。",
                        }
                    ),
                    400,
                )

            # 處理渠道
            final_channel_id = None
            if channel_id and channel_id.strip():  # 檢查是否為有效的渠道ID
                try:
                    final_channel_id = int(channel_id)
                except (ValueError, TypeError):
                    final_channel_id = None
            
            if not final_channel_id and channel_name_manual:
                channel = db.session.execute(
                    db.select(Channel).filter_by(name=channel_name_manual)
                ).scalar_one_or_none()
                if not channel:
                    channel = Channel(name=channel_name_manual)
                    db.session.add(channel)
                    db.session.flush()  # 為了立即獲取 ID
                final_channel_id = channel.id

            # 更新帳戶餘額
            if payment_status == "paid" and payment_account:
                # 已付款：立即扣款
                payment_account.balance -= twd_cost
            
            # 入庫（無論付款狀態如何都要入庫）
            deposit_account.balance += rmb_amount

            # 創建採購紀錄
            new_purchase = PurchaseRecord(
                payment_account_id=payment_account.id if payment_account else None,
                deposit_account_id=deposit_account.id,
                channel_id=final_channel_id,
                rmb_amount=rmb_amount,
                exchange_rate=exchange_rate,
                twd_cost=twd_cost,
                payment_status=payment_status,
                operator_id=current_user.id,  # <--- V4.0 核心功能！
            )
            db.session.add(new_purchase)
            db.session.flush()  # 立即獲取ID，以便創建FIFO庫存

            # 創建FIFO庫存記錄
            try:
                FIFOService.create_inventory_from_purchase(new_purchase)
                print(f"已為買入記錄 {new_purchase.id} 創建FIFO庫存")
            except Exception as e:
                print(f"創建FIFO庫存失敗: {e}")
                # 即使FIFO創建失敗，也不影響主要交易
                pass
            
            # 如果付款狀態為未付款，創建待付款項
            if payment_status == "unpaid":
                try:
                    pending_payment = PendingPayment(
                        purchase_record_id=new_purchase.id,
                        amount_twd=twd_cost
                    )
                    db.session.add(pending_payment)
                    print(f"已為買入記錄 {new_purchase.id} 創建待付款項: NT$ {twd_cost:,.2f}")
                except Exception as e:
                    print(f"創建待付款項失敗: {e}")
                    # 即使待付款項創建失敗，也不影響主要交易
                pass

            # 優化：移除重複的記帳記錄，只保留主要的PurchaseRecord
            # 因為PurchaseRecord已經包含了完整的交易信息，不需要額外的LedgerEntry和CashLog
            
            db.session.commit()

            # 觸發全局數據同步（重新整理整個資料庫）
            try:
                from global_sync import sync_entire_database
                sync_entire_database(db.session)
                print(" 買入記錄創建後全局數據同步完成")
            except Exception as sync_error:
                print(f"全局數據同步失敗（不影響買入記錄）: {sync_error}")

            # 根據付款狀態返回不同的成功訊息
            if payment_status == "paid":
                message = f"交易成功！已從 {payment_account.name} 付款，並將 RMB 存入 {deposit_account.name}。"
            else:
                message = f"交易成功！已將 RMB 存入 {deposit_account.name}，待付款項 NT$ {twd_cost:,.2f} 已建立。"

            return jsonify(
                {
                    "status": "success",
                    "message": message,
                }
            )

        # === 新增/刪除渠道等其他操作... ===
        # (此處可以加入 add_channel, delete_channel 的邏輯，與您舊版 API 類似)

        else:
            return (
                jsonify({"status": "error", "message": f"未知的操作: '{action}'"}),
                400,
            )

    except Exception as e:
        db.session.rollback()
        print(f"!! Error in api_buy_in: {e}")  # 在後端印出詳細錯誤
        import traceback

        traceback.print_exc()
        return (
            jsonify({"status": "error", "message": "伺服器內部錯誤，操作失敗。"}),
            500,
        )


@app.route("/api/settle-pending-payment", methods=["POST"])
@login_required
def settle_pending_payment_api():
    """
    處理待付款項銷帳的 API
    """
    try:
        data = request.get_json()
        pending_id = data.get("pending_id")
        payment_account_id = data.get("payment_account_id")
        settlement_amount = float(data.get("settlement_amount"))
        note = data.get("note", "").strip()
        
        # 驗證必填欄位
        if not all([pending_id, payment_account_id, settlement_amount]):
            return jsonify({"status": "error", "message": "缺少必填欄位"}), 400
        
        # 查詢待付款項
        pending_payment = db.session.get(PendingPayment, pending_id)
        if not pending_payment:
            return jsonify({"status": "error", "message": "找不到待付款項"}), 404
        
        if pending_payment.is_settled:
            return jsonify({"status": "error", "message": "該待付款項已經結清"}), 400
        
        # 查詢付款帳戶
        payment_account = db.session.get(CashAccount, payment_account_id)
        if not payment_account or payment_account.currency != "TWD":
            return jsonify({"status": "error", "message": "無效的 TWD 付款帳戶"}), 400
        
        # 檢查銷帳金額
        if settlement_amount <= 0:
            return jsonify({"status": "error", "message": "銷帳金額必須大於 0"}), 400
        
        if settlement_amount > pending_payment.amount_twd:
            return jsonify({"status": "error", "message": "銷帳金額不能超過待付金額"}), 400
        
        # 檢查帳戶餘額
        if payment_account.balance < settlement_amount:
            return jsonify({"status": "error", "message": f"付款帳戶餘額不足，需要 {settlement_amount:,.2f}，但僅剩 {payment_account.balance:,.2f}"}), 400
        
        # 執行銷帳
        # 1. 扣除付款帳戶餘額
        payment_account.balance -= settlement_amount
        
        # 2. 更新待付款項狀態
        pending_payment.amount_twd -= settlement_amount
        pending_payment.paid_at = datetime.utcnow()
        
        # 如果完全結清，標記為已結清
        if pending_payment.amount_twd <= 0:
            pending_payment.is_settled = True
            pending_payment.amount_twd = 0
        
        # 3. 創建流水記錄
        description = f"待付款項銷帳 - 買入記錄 #{pending_payment.purchase_record_id}"
        if note:
            description += f" | {note}"
        
        # 創建流水記錄
        ledger_entry = LedgerEntry(
            account_id=payment_account.id,
            amount=-settlement_amount,  # 負數表示支出
            description=description,
            operator_id=current_user.id
        )
        db.session.add(ledger_entry)
        
        # 提交所有變更
        db.session.commit()
        
        # 記錄刪除審計日誌
        try:
            import json
            from flask import request
            
            # 準備被銷帳的資料
            deleted_data = {
                'pending_payment_id': pending_payment.id,
                'purchase_record_id': pending_payment.purchase_record_id,
                'original_amount_twd': pending_payment.amount_twd + settlement_amount,  # 原始金額
                'settlement_amount': settlement_amount,
                'remaining_amount': pending_payment.amount_twd,
                'payment_account_id': payment_account.id,
                'payment_account_name': payment_account.name,
                'note': note,
                'settled_at': datetime.utcnow().isoformat()
            }
            
            # 記錄帳戶餘額變化
            affected_accounts = [payment_account]
            payment_account._balance_before = payment_account.balance + settlement_amount  # 記錄原始餘額
            
            balance_changes = DeleteAuditService.collect_balance_changes(affected_accounts)
            
            # 記錄審計日誌
            DeleteAuditService.log_deletion(
                table_name='pending_payments',
                record_id=pending_payment.id,
                deleted_data=json.dumps(deleted_data, ensure_ascii=False),
                operation_type='SETTLE_PENDING_PAYMENT',
                description=f'待付款項銷帳：買入記錄 #{pending_payment.purchase_record_id}，銷帳金額 NT$ {settlement_amount:,.2f}',
                operator_id=current_user.id,
                request=request,
                balance_changes=balance_changes
            )
        except Exception as audit_error:
            print(f"記錄銷帳審計日誌失敗: {audit_error}")
        
        # 返回成功訊息
        if pending_payment.is_settled:
            message = f"待付款項已完全結清！從 {payment_account.name} 扣款 NT$ {settlement_amount:,.2f}。"
        else:
            message = f"部分銷帳成功！從 {payment_account.name} 扣款 NT$ {settlement_amount:,.2f}，剩餘待付 NT$ {pending_payment.amount_twd:,.2f}。"
        
        return jsonify({
            "status": "success",
            "message": message
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"待付款項銷帳失敗: {e}")
        return jsonify({"status": "error", "message": "銷帳操作失敗"}), 500


@app.route("/api/process_payment", methods=["POST"])
@admin_required
def process_payment_api():
    """
    處理客戶付款（銷帳）的後端 API。
    接收客戶 ID、付款金額和收款帳戶，然後自動沖銷該客戶名下最早的未付訂單。
    """
    data = request.get_json()
    try:
        customer_id = int(data.get("customer_id"))
        payment_amount = float(data.get("payment_amount"))
        twd_account_id = int(data.get("twd_account_id"))  # 收款到哪個我方 TWD 帳戶
        note = data.get("note", "").strip()  # 獲取備註
    except (ValueError, TypeError, AttributeError):
        return jsonify({"status": "error", "message": "輸入的資料格式不正確。"}), 400

    if not all([customer_id, payment_amount > 0, twd_account_id]):
        return (
            jsonify(
                {"status": "error", "message": "客戶、付款金額和收款帳戶皆為必填。"}
            ),
            400,
        )

    try:
        # --- 1. 獲取核心物件 ---
        customer = db.session.get(Customer, customer_id)
        twd_account = db.session.get(CashAccount, twd_account_id)

        # --- 2. 業務邏輯驗證 ---
        if not customer:
            return jsonify({"status": "error", "message": "無效的客戶 ID。"}), 404
        if not twd_account or twd_account.currency != "TWD":
            return jsonify({"status": "error", "message": "無效的 TWD 收款帳戶。"}), 400
        if customer.total_receivables_twd < payment_amount:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"付款金額超過應收帳款！客戶應收 {customer.total_receivables_twd:,.2f}，但付款 {payment_amount:,.2f}。",
                    }
                ),
                400,
            )

        # --- 3. 執行付款處理 ---
        # 更新收款帳戶餘額
        twd_account.balance += payment_amount

        # 更新客戶應收帳款
        customer.total_receivables_twd -= payment_amount

        # 創建LedgerEntry記錄以確保在流水中顯示
        description = f"客戶 {customer.name} 銷帳 NT$ {payment_amount:,.2f}"
        if note:
            description += f" - {note}"
        
        ledger_entry = LedgerEntry(
            entry_type="SETTLEMENT",
            description=description,
            amount=payment_amount,
            account_id=twd_account_id,
            operator_id=current_user.id,
        )
        db.session.add(ledger_entry)

        # 自動沖銷最早的未付訂單
        unpaid_sales = (
            db.session.execute(
                db.select(SalesRecord)
                .filter_by(customer_id=customer.id, is_settled=False)
                .order_by(SalesRecord.created_at.asc())  # 最早的優先
            )
            .scalars()
            .all()
        )

        remaining_payment = payment_amount
        settled_sales = []

        for sale in unpaid_sales:
            if remaining_payment <= 0:
                break

            # 計算這筆訂單能沖銷多少
            settle_amount = min(remaining_payment, sale.twd_amount)
            remaining_payment -= settle_amount

            # 更新訂單狀態
            if settle_amount >= sale.twd_amount:
                sale.is_settled = True
                settled_sales.append(sale)

            # 創建交易記錄
            transaction_note = f"客戶付款沖銷 - 訂單 #{sale.id}"
            if note:
                transaction_note += f" - {note}"
            
            transaction = Transaction(
                sales_record_id=sale.id,
                twd_account_id=twd_account.id,
                amount=settle_amount,
                note=transaction_note,
            )
            db.session.add(transaction)

        db.session.commit()

        # 準備回應訊息
        if settled_sales:
            settled_ids = [s.id for s in settled_sales]
            message = f"銷帳成功！已沖銷 {len(settled_sales)} 筆訂單 (ID: {', '.join(map(str, settled_ids))})"
        else:
            # 檢查是否有未付訂單
            if unpaid_sales:
                message = f"銷帳成功！付款金額已記錄，但訂單僅部分沖銷。"
            else:
                message = f"銷帳成功！付款 NT$ {payment_amount:,.2f} 已記錄到帳戶。"

        return jsonify({"status": "success", "message": message})

    except Exception as e:
        db.session.rollback()
        print(f"!! Error in process_payment_api: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": "伺服器內部錯誤，操作失敗。"}), 500


@app.route("/fifo-inventory")
@login_required
def fifo_inventory():
    """FIFO庫存管理頁面"""
    try:
        # 獲取當前FIFO庫存狀態
        inventory_data = FIFOService.get_current_inventory()
        
        # 獲取最近的銷售記錄（用於展示利潤計算）
        recent_sales = (
            db.session.execute(
                db.select(SalesRecord)
                .options(db.selectinload(SalesRecord.customer))
                .order_by(SalesRecord.created_at.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )
        
        # 計算每筆銷售的利潤
        sales_with_profit = []
        for sale in recent_sales:
            try:
                profit_info = FIFOService.calculate_profit_for_sale(sale)
                if profit_info:
                    sales_with_profit.append({
                        'id': sale.id,
                        'customer_name': sale.customer.name if sale.customer else 'N/A',
                        'rmb_amount': sale.rmb_amount,
                        'twd_amount': sale.twd_amount,
                        'created_at': sale.created_at.strftime('%Y-%m-%d') if sale.created_at else 'N/A',
                        'profit_twd': profit_info['profit_twd'],
                        'profit_margin': profit_info['profit_margin'],
                        'total_cost': profit_info['total_cost_twd']
                    })
            except Exception as sale_error:
                print(f"計算銷售 {sale.id} 利潤時發生錯誤: {sale_error}")
                continue
        
        return render_template(
            "fifo_inventory.html",
            inventory_data=inventory_data,
            sales_with_profit=sales_with_profit
        )
        
    except Exception as e:
        print(f"載入FIFO庫存頁面時發生錯誤: {e}")
        flash(f"載入FIFO庫存頁面時發生錯誤: {e}", "danger")
        return render_template(
            "fifo_inventory.html",
            inventory_data=[],
            sales_with_profit=[]
        )

@app.route("/api/fifo-inventory/status")
@login_required
def api_fifo_inventory_status():
    """API端點：獲取FIFO庫存實時狀態"""
    try:
        # 獲取當前FIFO庫存狀態
        inventory_data = FIFOService.get_current_inventory()
        
        # 獲取最近的銷售記錄（用於展示利潤計算）
        recent_sales = (
            db.session.execute(
                db.select(SalesRecord)
                .options(db.selectinload(SalesRecord.customer))
                .order_by(SalesRecord.created_at.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )
        
        # 計算每筆銷售的利潤
        sales_with_profit = []
        for sale in recent_sales:
            try:
                profit_info = FIFOService.calculate_profit_for_sale(sale)
                if profit_info:
                    sales_with_profit.append({
                        'id': sale.id,
                        'customer_name': sale.customer.name if sale.customer else 'N/A',
                        'rmb_amount': sale.rmb_amount,
                        'twd_amount': sale.twd_amount,
                        'created_at': sale.created_at.strftime('%Y-%m-%d') if sale.created_at else 'N/A',
                        'profit_twd': profit_info['profit_twd'],
                        'profit_margin': profit_info['profit_margin'],
                        'total_cost': profit_info['total_cost_twd']
                    })
            except Exception as sale_error:
                print(f"API計算銷售 {sale.id} 利潤時發生錯誤: {sale_error}")
                continue
        
        return jsonify({
            'status': 'success',
            'inventory_data': inventory_data,
            'sales_with_profit': sales_with_profit
        })
        
    except Exception as e:
        print(f"獲取FIFO庫存狀態失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': f'獲取庫存狀態失敗: {e}'
        }), 500


# ===================================================================
# 新增：FIFO庫存維護和錯誤處理API端點
# ===================================================================

@app.route("/api/audit-inventory", methods=["POST"])
@admin_required
def api_audit_inventory():
    """API端點：審計庫存一致性"""
    try:
        issues = FIFOService.audit_inventory_consistency()
        return jsonify({
            'status': 'success',
            'issues': issues
        })
    except Exception as e:
        print(f"審計庫存一致性失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': f'審計失敗: {e}'
        }), 500


@app.route("/api/fix-inventory", methods=["POST"])
@admin_required
def api_fix_inventory():
    """API端點：修復庫存一致性问题"""
    try:
        fixed_issues = FIFOService.fix_inventory_consistency()
        return jsonify({
            'status': 'success',
            'fixed_issues': fixed_issues
        })
    except Exception as e:
        print(f"修復庫存一致性失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': f'修復失敗: {e}'
        }), 500


@app.route("/api/inventory-status", methods=["GET"])
@admin_required
def api_inventory_status():
    """API端點：獲取詳細的庫存狀態報告"""
    try:
        # 獲取所有庫存記錄
        all_inventory = db.session.execute(db.select(FIFOInventory)).scalars().all()
        
        total_batches = len(all_inventory)
        active_batches = len([inv for inv in all_inventory if inv.remaining_rmb > 0])
        exhausted_batches = len([inv for inv in all_inventory if inv.remaining_rmb <= 0])
        
        # 計算總庫存價值
        total_value = sum(
            inv.remaining_rmb * inv.unit_cost_twd 
            for inv in all_inventory 
            if inv.remaining_rmb > 0
        )
        
        return jsonify({
            'status': 'success',
            'total_batches': total_batches,
            'active_batches': active_batches,
            'exhausted_batches': exhausted_batches,
            'total_value': total_value
        })
        
    except Exception as e:
        print(f"獲取庫存狀態報告失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': f'獲取狀態報告失敗: {e}'
        }), 500


@app.route("/api/reverse-sale-allocation/<int:sales_record_id>", methods=["POST"])
@admin_required
def api_reverse_sale_allocation(sales_record_id):
    """API端點：完全回滾銷售記錄（僅管理員）"""
    try:
        success = FIFOService.reverse_sale_allocation(sales_record_id)
        if success:
            return jsonify({
                'status': 'success',
                'message': f'成功取消銷售記錄 {sales_record_id}，已完全刪除相關數據'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'取消銷售記錄 {sales_record_id} 失敗'
            }), 400
    except Exception as e:
        print(f"取消銷售記錄失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': f'取消失敗: {e}'
        }), 500

@app.route("/api/user-reverse-sale/<int:sales_record_id>", methods=["POST"])
@login_required
def api_user_reverse_sale(sales_record_id):
    """API端點：普通用戶取消自己的銷售記錄"""
    try:
        print(f"收到取消銷售記錄請求: {sales_record_id}")
        
        # 檢查銷售記錄是否存在
        sales_record = db.session.get(SalesRecord, sales_record_id)
        if not sales_record:
            print(f"找不到銷售記錄 {sales_record_id}")
            return jsonify({
                'status': 'error',
                'message': f'找不到銷售記錄 {sales_record_id}'
            }), 404
        
        print(f"找到銷售記錄: 客戶ID={sales_record.customer_id}, RMB={sales_record.rmb_amount}")
        
        # 檢查用戶權限（只能取消自己的記錄或管理員可以取消所有記錄）
        if not current_user.is_admin and sales_record.operator_id != current_user.id:
            print(f"權限檢查失敗: 用戶ID={current_user.id}, 記錄操作者ID={sales_record.operator_id}")
            return jsonify({
                'status': 'error',
                'message': '您只能取消自己的銷售記錄'
            }), 403
        
        # 檢查是否有FIFO分配記錄
        allocations = db.session.execute(
            db.select(FIFOSalesAllocation)
            .filter(FIFOSalesAllocation.sales_record_id == sales_record_id)
        ).scalars().all()
        
        print(f"找到 {len(allocations)} 個FIFO分配記錄")
        
        # 執行簡化的取消操作
        try:
            # 先嘗試簡化的取消邏輯
            success = FIFOService.simple_reverse_sale_allocation(sales_record_id)
            if success:
                print(f"簡化取消成功")
                return jsonify({
                    'status': 'success',
                    'message': f'成功取消銷售記錄 {sales_record_id}，已完全刪除相關數據'
                })
            else:
                print(f"簡化取消失敗，嘗試完整取消")
                # 如果簡化取消失敗，嘗試完整的取消邏輯
                success = FIFOService.reverse_sale_allocation(sales_record_id)
                if success:
                    return jsonify({
                        'status': 'success',
                        'message': f'成功取消銷售記錄 {sales_record_id}，已完全刪除相關數據'
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': f'取消銷售記錄 {sales_record_id} 失敗，可能是因為該記錄已有相關分配或無法回滾'
                    }), 400
        except Exception as reverse_error:
            print(f"取消銷售記錄時發生錯誤: {reverse_error}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': f'取消銷售記錄時發生錯誤: {str(reverse_error)}'
            }), 400
    except Exception as e:
        print(f"用戶取消銷售記錄失敗: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'取消失敗: {e}'
        }), 500


@app.route("/api/reverse-purchase-inventory/<int:purchase_record_id>", methods=["POST"])
@admin_required
def api_reverse_purchase_inventory(purchase_record_id):
    """API端點：完全回滾買入記錄"""
    try:
        success = FIFOService.reverse_purchase_inventory(purchase_record_id)
        if success:
            return jsonify({
                'status': 'success',
                'message': f'成功取消買入記錄 {purchase_record_id}，已完全刪除相關數據'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'取消買入記錄 {purchase_record_id} 失敗，可能已有銷售分配'
            }), 400
    except Exception as e:
        print(f"取消買入記錄失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': f'取消失敗: {e}'
        }), 500


@app.route("/api/reverse-card-purchase/<int:card_purchase_id>", methods=["POST"])
@admin_required
def api_reverse_card_purchase(card_purchase_id):
    """API端點：回滾刷卡記錄"""
    try:
        # 查找刷卡記錄
        card_purchase = db.session.get(CardPurchase, card_purchase_id)
        if not card_purchase:
            return jsonify({
                'status': 'error',
                'message': f'找不到刷卡記錄 {card_purchase_id}'
            }), 404
        
        # 刪除刷卡記錄
        db.session.delete(card_purchase)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'成功取消刷卡記錄 {card_purchase_id}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"回滾刷卡記錄失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': f'回滾失敗: {e}'
        }), 500


@app.route("/admin/update_cash_account", methods=["POST"])
@login_required
def admin_update_cash_account():
    action = request.form.get("action")
    try:
        if action == "add_holder":
            name = request.form.get("name", "").strip()

            # --- 關鍵修正：我們不再獲取也不再檢查 holder_type ---
            if not name:
                flash("持有人名稱為必填項。", "danger")
                return redirect(url_for('cash_management'))
            
            existing_holder = db.session.execute(
                db.select(Holder).filter_by(name=name)
            ).scalar_one_or_none()
            if existing_holder:
                flash(f'錯誤：持有人 "{name}" 已經存在。', "danger")
                return redirect(url_for('cash_management'))
            
            # 我們直接創建，type 會自動使用模型中定義的 default='CUSTOMER'
            new_holder = Holder(name=name)
            db.session.add(new_holder)
            db.session.commit()
            flash(f'持有人 "{name}" 已成功新增！', "success")
            return redirect(url_for('cash_management', refresh='true'))

        elif action == "delete_holder":
            holder_id = int(request.form.get("holder_id"))
            holder = db.session.get(Holder, holder_id)
            if holder:
                if holder.cash_accounts:
                    flash(
                        f'無法刪除！持有人 "{holder.name}" 名下尚有現金帳戶。', "danger"
                    )
                    return redirect(url_for('cash_management'))
                
                db.session.delete(holder)
                db.session.commit()
                flash(f'持有人 "{holder.name}" 已被刪除。', "success")
                return redirect(url_for('cash_management'))
            else:
                flash("找不到該持有人。", "warning")
                return redirect(url_for('cash_management'))

        elif action == "add_account":
            holder_id = int(request.form.get("holder_id"))
            name = request.form.get("name", "").strip()
            currency = request.form.get("currency")
            balance = float(request.form.get("initial_balance", 0.0))
            if not all([holder_id, name, currency]):
                flash("持有人、帳戶名稱和幣別為必填項。", "danger")
                return redirect(url_for('cash_management'))
            
            new_account = CashAccount(
                holder_id=holder_id, name=name, currency=currency, balance=balance
            )
            db.session.add(new_account)
            db.session.commit()
            flash(f'帳戶 "{name}" 已成功新增！', "success")
            return redirect(url_for('cash_management', refresh='true'))

        elif action == "delete_account":
            account_id = int(request.form.get("account_id"))
            account = db.session.get(CashAccount, account_id)
            if account:
                if account.balance != 0:
                    flash(
                        f'無法刪除！帳戶 "{account.name}" 尚有 {account.balance:,.2f} 的餘額。',
                        "danger",
                    )
                    return redirect(url_for('cash_management'))
                
                db.session.delete(account)
                db.session.commit()
                flash(f'帳戶 "{account.name}" 已被刪除。', "success")
                return redirect(url_for('cash_management'))
            else:
                flash("找不到該帳戶。", "warning")
                return redirect(url_for('cash_management'))

        elif action == "add_movement":
            account_id = int(request.form.get("account_id"))
            amount = float(request.form.get("amount"))
            is_decrease = request.form.get("is_decrease") == "true"
            withdraw_type = request.form.get("withdraw_type", "asset")  # 默認為資產提款
            note = request.form.get("note", "").strip()
            account = db.session.get(CashAccount, account_id)
            if account:
                if is_decrease:
                    # 直接使用資料庫中的帳戶餘額進行檢查
                    actual_balance = float(account.balance)
                    
                    if actual_balance is None:
                        actual_balance = account.balance  # 備用方案
                    
                    if actual_balance < amount:
                        flash(f"餘額不足，無法提出 {amount:,.2f}。當前可用餘額: {actual_balance:,.2f}", "danger")
                        return redirect(url_for('cash_management'))
                    else:
                        # 處理提款
                        account.balance -= amount
                        
                        # 根據提款類型設置描述
                        if withdraw_type == "profit":
                            description = "利潤提款"
                            if note:
                                description += f" | {note}"
                        else:  # asset
                            description = "資產提款"
                            if note:
                                description += f" | {note}"
                        
                        # 如果是RMB帳戶，需要按FIFO原則扣減庫存
                        if account.currency == "RMB":
                            try:
                                # 按FIFO順序扣減庫存
                                FIFOService.reduce_rmb_inventory_fifo(amount, f"外部提款 - {account.name}")
                                description += f" | 已按FIFO扣減庫存"
                            except ValueError as e:
                                # 庫存不足，回滾帳戶餘額變更
                                account.balance += amount
                                flash(f"庫存不足，無法提款: {e}", "danger")
                                return redirect(url_for('cash_management'))
                            except Exception as e:
                                # 其他錯誤，回滾帳戶餘額變更
                                account.balance += amount
                                flash(f"扣減庫存失敗: {e}", "danger")
                                return redirect(url_for('cash_management'))
                        
                        # 計算當前總利潤（用於記錄變動前後利潤）
                        current_total_profit = 0.0
                        if withdraw_type == "profit":
                            # 計算當前銷售利潤總和
                            all_sales = (
                                db.session.execute(db.select(SalesRecord))
                                .scalars()
                                .all()
                            )
                            
                            for sale in all_sales:
                                profit_info = FIFOService.calculate_profit_for_sale(sale)
                                if profit_info:
                                    current_total_profit += profit_info.get('profit_twd', 0.0)
                            
                            # 扣除之前的利潤提款
                            try:
                                previous_profit_withdrawals = (
                                    db.session.execute(
                                        db.select(LedgerEntry)
                                        .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
                                        .filter(LedgerEntry.id != None)  # 排除當前記錄
                                    )
                                    .scalars()
                                    .all()
                                )
                            except Exception as e:
                                if "profit_before does not exist" in str(e):
                                    print("警告: 查詢之前的利潤提款記錄時缺少欄位，跳過查詢")
                                    db.session.rollback()
                                    previous_profit_withdrawals = []
                                else:
                                    db.session.rollback()
                                    raise e
                            
                            previous_withdrawals = sum(entry.amount for entry in previous_profit_withdrawals)
                            current_total_profit -= previous_withdrawals
                        
                        # 創建流水記錄
                        entry_type = "PROFIT_WITHDRAW" if withdraw_type == "profit" else "ASSET_WITHDRAW"
                        entry = LedgerEntry(
                            entry_type=entry_type,
                            account_id=account.id,
                            amount=amount,  # 提款金額
                            description=description,
                            operator_id=current_user.id,
                        )
                        
                        # 如果是利潤提款，記錄詳細利潤信息（如果欄位存在）
                        if withdraw_type == "profit":
                            # 安全地設置利潤詳細信息
                            if hasattr(entry, 'profit_before'):
                                entry.profit_before = current_total_profit
                                entry.profit_after = current_total_profit - amount
                                entry.profit_change = -amount  # 負數表示減少
                                print(f"DEBUG: 利潤提款記錄 - 變動前: {entry.profit_before:.2f}, 變動後: {entry.profit_after:.2f}, 變動: {entry.profit_change:.2f}")
                            else:
                                print("WARNING: 利潤詳細欄位不存在，跳過詳細記錄")
                        else:
                            # 資產提款不影響利潤，設為 None（如果欄位存在）
                            if hasattr(entry, 'profit_before'):
                                entry.profit_before = None
                                entry.profit_after = None
                                entry.profit_change = None
                        
                        # 調試信息：檢查提款記錄
                        print(f"DEBUG: 創建提款記錄 - 金額: {amount}, 帳戶: {account.name}, 類型: WITHDRAW")
                        db.session.add(entry)
                        db.session.commit()
                        
                        # 觸發全局數據同步（重新整理整個資料庫）
                        try:
                            from global_sync import sync_entire_database
                            sync_entire_database(db.session)
                            print(" 提款操作後全局數據同步完成")
                        except Exception as sync_error:
                            print(f"全局數據同步失敗: {sync_error}")
                        
                        success_msg = f'已從 "{account.name}" 提出 {amount:,.2f}'
                        if account.currency == "RMB":
                            success_msg += '（已同步扣減庫存）'
                        success_msg += '，並已記錄流水。'
                        
                        flash(success_msg, "success")
                        return redirect(url_for('cash_management'))
                else:
                    # 處理存款
                    account.balance += amount
                    
                    # 獲取成本匯率（僅RMB帳戶需要）
                    rmb_cost_rate = request.form.get("rmb_cost_rate")
                    
                    # 將備註信息存儲在description中，用分隔符分離
                    description = "外部存款"
                    if note:
                        description += f" | {note}"
                    
                    # 如果是RMB帳戶且提供了成本匯率，創建虛擬買入記錄
                    if account.currency == "RMB" and rmb_cost_rate:
                        try:
                            cost_rate = float(rmb_cost_rate)
                            twd_cost = amount * cost_rate
                            
                            # 檢查是否為純利潤庫存
                            is_pure_profit = request.form.get("is_pure_profit") == "true"
                            
                            # 創建虛擬買入記錄（外部存入）
                            virtual_purchase = PurchaseRecord(
                                channel_id=None,  # 沒有渠道
                                payment_account_id=None,  # 沒有付款帳戶
                                deposit_account_id=account.id,
                                rmb_amount=amount,
                                exchange_rate=cost_rate,
                                twd_cost=twd_cost,
                                operator_id=current_user.id
                            )
                            # 標記描述，便於前端與清單顯示
                            try:
                                virtual_purchase.description = (
                                    f"手續費入庫（純利潤庫存）" if is_pure_profit else f"外部存款入庫"
                                )
                            except Exception:
                                pass
                            db.session.add(virtual_purchase)
                            db.session.flush()  # 獲取 ID
                            
                            # 創建對應的FIFO庫存記錄
                            created_inventory = FIFOService.create_inventory_from_purchase(virtual_purchase)
                            
                            if is_pure_profit:
                                description += f" | 純利潤庫存（成本匯率: {cost_rate:.4f}）"
                            else:
                                description += f" | 成本匯率: {cost_rate:.4f}"
                            
                        except (ValueError, TypeError) as e:
                            flash(f"成本匯率格式錯誤: {e}", "danger")
                            return redirect(url_for('cash_management'))
                        except Exception as e:
                            flash(f"創建庫存記錄失敗: {e}", "danger")
                            return redirect(url_for('cash_management'))
                    
                    elif account.currency == "RMB" and not rmb_cost_rate:
                        flash("RMB帳戶存款必須提供成本匯率！", "danger")
                        return redirect(url_for('cash_management'))
                    
                    # 創建流水記錄
                    entry = LedgerEntry(
                        entry_type="DEPOSIT",
                        account_id=account.id,
                        amount=amount,
                        description=description,
                        operator_id=current_user.id,
                    )
                    db.session.add(entry)
                    db.session.commit()
                    
                    # 觸發全局數據同步（重新整理整個資料庫）
                    try:
                        from global_sync import sync_entire_database
                        sync_entire_database(db.session)
                        print(" 存款操作後全局數據同步完成")
                    except Exception as sync_error:
                        print(f"全局數據同步失敗: {sync_error}")
                    
                    success_msg = f'已向 "{account.name}" 存入 {amount:,.2f}'
                    if account.currency == "RMB" and rmb_cost_rate:
                        success_msg += f'（成本匯率: {rmb_cost_rate}）'
                    success_msg += '，並已記錄流水和庫存。'
                    
                    # 如果是 AJAX 來源（例如純利潤入庫），回傳 JSON 給前端以保存 inventory/purchase id
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        try:
                            inv = db.session.execute(
                                db.select(FIFOInventory).filter_by(purchase_record_id=virtual_purchase.id)
                            ).scalars().first()
                            return jsonify({
                                'status': 'success',
                                'message': success_msg,
                                'purchase_record_id': virtual_purchase.id,
                                'inventory_id': inv.id if inv else None
                            })
                        except Exception as e:
                            return jsonify({'status': 'success', 'message': success_msg})
                    else:
                        flash(success_msg, "success")
                        return redirect(url_for('cash_management'))

        elif action == "reverse_pure_profit":
            # 回滾純利潤庫存（未售出才可回滾）
            try:
                purchase_record_id = int(request.form.get('purchase_record_id', 0))
            except Exception:
                return jsonify({'status': 'error', 'message': 'purchase_record_id 無效'}), 400
            if not purchase_record_id:
                return jsonify({'status': 'error', 'message': '缺少 purchase_record_id'}), 400

            try:
                print(f"開始回滾純利潤庫存，purchase_record_id: {purchase_record_id}")
                
                # 先檢查買入記錄是否存在
                purchase_record = db.session.get(PurchaseRecord, purchase_record_id)
                if not purchase_record:
                    return jsonify({'status': 'error', 'message': f'找不到買入記錄 {purchase_record_id}'}), 404
                
                print(f"找到買入記錄: channel={purchase_record.channel_id}, payment_account={purchase_record.payment_account_id}, twd_cost={purchase_record.twd_cost}")
                
                # 檢查是否為純利潤庫存
                is_pure_profit = (purchase_record.channel is None and 
                                purchase_record.payment_account is None and 
                                purchase_record.twd_cost == 0)
                
                if not is_pure_profit:
                    return jsonify({'status': 'error', 'message': '該記錄不是純利潤庫存，無法使用此API回滾'}), 400
                
                # 檢查FIFO庫存是否存在
                inventory = (
                    db.session.execute(
                        db.select(FIFOInventory)
                        .filter(FIFOInventory.purchase_record_id == purchase_record_id)
                    )
                    .scalars()
                    .first()
                )
                
                if inventory:
                    # 檢查是否有銷售分配
                    allocations = (
                        db.session.execute(
                            db.select(FIFOSalesAllocation)
                            .filter(FIFOSalesAllocation.fifo_inventory_id == inventory.id)
                        )
                        .scalars()
                        .all()
                    )
                    
                    print(f"檢查銷售分配: 找到 {len(allocations)} 個分配記錄")
                    
                    if allocations:
                        return jsonify({'status': 'error', 'message': f'該批庫存已有 {len(allocations)} 個銷售分配，無法回滾'}), 400
                
                # 執行回滾
                ok = FIFOService.reverse_purchase_inventory(purchase_record_id)
                if ok:
                    return jsonify({'status': 'success', 'message': '純利潤庫存已回滾'}), 200
                else:
                    return jsonify({'status': 'error', 'message': '回滾失敗，請檢查日誌'}), 500
                    
            except Exception as e:
                print(f"回滾純利潤庫存失敗: {e}")
                return jsonify({'status': 'error', 'message': f'回滾失敗: {e}'}), 500

        elif action == "transfer_funds":
            from_id = int(request.form.get("from_account_id"))
            to_id = int(request.form.get("to_account_id"))
            amount = float(request.form.get("transfer_amount"))
            if from_id == to_id:
                flash("來源與目標帳戶不可相同！", "danger")
                return redirect(url_for('cash_management'))
            
            from_account = db.session.get(CashAccount, from_id)
            to_account = db.session.get(CashAccount, to_id)
            if from_account.balance < amount:
                flash(f'來源帳戶 "{from_account.name}" 餘額不足。', "danger")
                return redirect(url_for('cash_management'))
            else:
                    from_account.balance -= amount
                    to_account.balance += amount

                    out_entry = LedgerEntry(
                        entry_type="TRANSFER_OUT",
                        account_id=from_account.id,
                        amount=amount,
                        description=f"轉出至 {to_account.name}",
                        operator_id=current_user.id,
                    )
                    in_entry = LedgerEntry(
                        entry_type="TRANSFER_IN",
                        account_id=to_account.id,
                        amount=amount,
                        description=f"從 {from_account.name} 轉入",
                        operator_id=current_user.id,
                    )
                    db.session.add_all([out_entry, in_entry])

                    db.session.commit()
                    flash(
                        f'成功從 "{from_account.name}" 轉帳 {amount:,.2f} 到 "{to_account.name}"，並已記錄流水！',
                        "success",
                    )
                    return redirect(url_for('cash_management', refresh='true'))

        else:
            flash("未知的操作指令。", "warning")
            return redirect(url_for('cash_management'))

    except Exception as e:
        db.session.rollback()
        print(f"!! 現金帳戶更新失敗: {e}")
        import traceback

        traceback.print_exc()
        flash("操作失敗，發生未知錯誤或輸入格式不正確。", "danger")

    return redirect(url_for("cash_management"))


# ===================================================================
# 7. AJAX API 路由 (買入頁面的功能)
# ===================================================================
@app.route("/admin/add_purchase_channel_ajax", methods=["POST"])
@admin_required
def add_purchase_channel_ajax():
    data = request.get_json()
    customer_name = data.get("customer_name", "").strip()
    if not customer_name:
        return jsonify({"status": "error", "message": "渠道名稱不可為空。"}), 400

    existing = User.query.filter_by(username=customer_name).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.session.commit()
            return jsonify(
                {
                    "status": "success",
                    "message": f'渠道 "{customer_name}" 已恢復。',
                    "customer": {"id": existing.id, "username": existing.username},
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f'名為 "{customer_name}" 的渠道已存在。',
                    }
                ),
                409,
            )

    new_channel = User(username=customer_name, is_admin=False, is_active=True)
    db.session.add(new_channel)
    db.session.commit()
    return jsonify(
        {
            "status": "success",
            "message": "新增成功！",
            "customer": {"id": new_channel.id, "username": new_channel.username},
        }
    )


@app.route("/admin/delete_purchase_channel_ajax", methods=["POST"])
@admin_required
def delete_purchase_channel_ajax():
    data = request.get_json()
    customer_id = data.get("customer_id")
    channel = db.session.get(User, customer_id)
    if channel and not channel.is_admin:
        channel.is_active = False
        db.session.commit()
        return jsonify({"status": "success", "deleted_name": channel.username})
    return jsonify({"status": "error", "message": "找不到或無法刪除該渠道。"}), 404


@app.route("/api/record_purchase", methods=["POST"])
@login_required  # 或者 @admin_required
def record_purchase_api():
    data = request.get_json()
    try:
        payment_account_id = int(data.get("payment_account_id"))
        deposit_account_id = int(data.get("deposit_account_id"))
        rmb_amount = float(data.get("rmb_amount"))
        exchange_rate = float(data.get("exchange_rate"))
        channel_id = data.get("channel_id")
        channel_name_manual = data.get("channel_name_manual", "").strip()

        if not (channel_id or channel_name_manual):
            return (
                jsonify({"status": "error", "message": "請選擇或輸入一個購買渠道。"}),
                400,
            )
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "輸入的資料格式不正確。"}), 400

    try:
        payment_account = db.session.get(CashAccount, payment_account_id)
        deposit_account = db.session.get(CashAccount, deposit_account_id)

        if not payment_account or payment_account.currency != "TWD":
            return jsonify({"status": "error", "message": "無效的 TWD 付款帳戶。"}), 404
        if not deposit_account or deposit_account.currency != "RMB":
            return jsonify({"status": "error", "message": "無效的 RMB 入庫帳戶。"}), 404

        twd_cost = rmb_amount * exchange_rate
        if payment_account.balance < twd_cost:
            return jsonify({"status": "error", "message": f"付款帳戶餘額不足！"}), 400

        final_channel_id = None
        if channel_id:
            final_channel_id = int(channel_id)
        elif channel_name_manual:
            existing_channel = db.session.execute(
                db.select(Channel).filter_by(name=channel_name_manual)
            ).scalar_one_or_none()
            if existing_channel:
                final_channel_id = existing_channel.id
            else:
                new_channel_obj = Channel(name=channel_name_manual)
                db.session.add(new_channel_obj)
                db.session.flush()
                final_channel_id = new_channel_obj.id

        # --- 核心操作 ---
        payment_account.balance -= twd_cost
        deposit_account.balance += rmb_amount

        new_purchase = PurchaseRecord(
            payment_account_id=payment_account.id,
            deposit_account_id=deposit_account.id,
            channel_id=final_channel_id,
            channel_name_manual=channel_name_manual if not channel_id else None,
            rmb_amount=rmb_amount,
            exchange_rate=exchange_rate,
            twd_cost=twd_cost,
            operator_id=current_user.id,
        )
        db.session.add(new_purchase)

        # 提交所有變更
        db.session.commit()

        return jsonify(
            {"status": "success", "message": "交易成功！資金與庫存皆已更新。"}
        )

    except Exception as e:
        db.session.rollback()
        print(f"!! 買入 API 發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        return (
            jsonify({"status": "error", "message": "資料庫儲存失敗，請聯繫管理員。"}),
            500,
        )


@app.route("/admin/update_transaction_note", methods=["POST"])
@admin_required
def admin_update_transaction_note():
    data = request.get_json()
    tx_id = data.get("tx_id")
    note = data.get("note", "").strip()

    tx = Transaction.query.get(tx_id)
    if not tx:
        return jsonify({"status": "error", "message": "找不到該交易紀錄"}), 404

    tx.note = note
    db.session.commit()

    return jsonify({"status": "success", "message": "備註已更新"})


@app.route("/admin/update_transaction_status", methods=["POST"])
@admin_required
def admin_update_transaction_status():
    data = request.get_json()
    tx_id = data.get("tx_id")
    new_status = data.get("new_status")

    tx = Transaction.query.get(tx_id)
    if not tx:
        return jsonify({"status": "error", "message": "找不到該交易紀錄"}), 404

    tx.status = new_status
    db.session.commit()

    return jsonify(
        {"status": "success", "message": "狀態已更新", "new_status": new_status}
    )


def record_sale_cost(sale_rmb_amount):
    remaining = sale_rmb_amount
    cost = 0.0

    # 查詢 FIFO 用的 buy-in 紀錄（剩餘 RMB > 0）
    purchases = (
        Transaction.query.filter(
            Transaction.transaction_type == "buy", Transaction.status == "已入帳"
        )
        .order_by(Transaction.order_time.asc())
        .all()
    )

    for purchase in purchases:
        used_rmb = (purchase.total_cost or 0) / (
            purchase.cost_per_unit or purchase.buy_rate or 1e-8
        )
        available_rmb = purchase.rmb_amount - used_rmb
        if available_rmb <= 0:
            continue

        use_rmb = min(remaining, available_rmb)
        unit_cost = purchase.cost_per_unit or purchase.buy_rate or 0
        cost += use_rmb * unit_cost
        remaining -= use_rmb

        # 更新這筆 buy 的 total_cost（選擇性記錄）
        purchase.total_cost = (purchase.total_cost or 0) + use_rmb * unit_cost
        purchase.cost_per_unit = unit_cost
        db.session.add(purchase)

        if remaining <= 0:
            break

    average_cost = cost / sale_rmb_amount if sale_rmb_amount > 0 else 0
    return average_cost, cost








@app.route("/api/frequent_customers", methods=["GET"])
@login_required
def get_frequent_customers():
    """獲取常用客戶列表"""
    try:
        print(f"API調用: get_frequent_customers by user {current_user.username}")
        
        # 先檢查Customer表
        frequent_customers = (
            db.session.execute(
                db.select(Customer).filter_by(is_active=True).order_by(Customer.name)
            )
            .scalars()
            .all()
        )
        
        print(f"Customer表中找到 {len(frequent_customers)} 個客戶:")
        for customer in frequent_customers:
            print(f"  - {customer.name} (ID: {customer.id})")
        

        
        # 轉換為可序列化的格式
        customers_data = []
        for customer in frequent_customers:
            customers_data.append({
                'id': customer.id,
                'name': customer.name,
                'is_active': customer.is_active
            })
        
        return jsonify({
            'status': 'success',
            'customers': customers_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'獲取常用客戶列表失敗: {str(e)}'
        }), 500


# ===================================================================
# 利潤管理 API 端點
# ===================================================================

@app.route("/api/total-profit", methods=["GET"])
@login_required
def api_total_profit():
    """計算系統總利潤的API，使用FIFO計算邏輯確保準確性"""
    try:
        # 使用FIFO計算邏輯，確保與實際銷售和成本數據一致
        print("DEBUG: 開始使用FIFO計算總利潤")
        
        # 獲取所有銷售記錄
        all_sales = (
            db.session.execute(
                db.select(SalesRecord)
                .order_by(SalesRecord.created_at.desc())
            )
            .scalars()
            .all()
        )
        
        print(f"DEBUG: 找到 {len(all_sales)} 筆銷售記錄")
        
        if len(all_sales) == 0:
            print("DEBUG: 沒有任何銷售記錄，返回零利潤")
            return jsonify({
                'status': 'success',
                'data': {
                    'total_profit_twd': 0.0,
                    'message': '系統中沒有銷售記錄，無法計算利潤'
                }
            })
        
        # 使用FIFO計算每筆銷售的利潤
        total_profit_twd = 0.0
        total_revenue_twd = 0.0
        total_cost_twd = 0.0
        
        for sale in all_sales:
            print(f"DEBUG: 處理銷售記錄 ID: {sale.id}, 客戶: {sale.customer.name if sale.customer else 'N/A'}")
            profit_info = FIFOService.calculate_profit_for_sale(sale)
            print(f"DEBUG: 利潤計算結果: {profit_info}")
            
            if profit_info:
                sale_profit = profit_info.get('profit_twd', 0.0)
                sale_cost = profit_info.get('total_cost_twd', 0.0)
                
                total_profit_twd += sale_profit
                total_cost_twd += sale_cost
                total_revenue_twd += sale.twd_amount
                
                print(f"DEBUG: 銷售 {sale.id} - 利潤: {sale_profit}, 成本: {sale_cost}, 收入: {sale.twd_amount}")
            else:
                print(f"DEBUG: 銷售記錄 {sale.id} 無法計算利潤")
        
        # 扣除利潤提款記錄
        try:
            profit_withdrawals = (
                db.session.execute(
                    db.select(LedgerEntry)
                    .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
                )
                .scalars()
                .all()
            )
            total_profit_withdrawals = sum(abs(entry.amount) for entry in profit_withdrawals)  # 提款記錄的amount是負數
            total_profit_twd -= total_profit_withdrawals
            print(f"DEBUG: 利潤提款總計: {total_profit_withdrawals:.2f}")
        except Exception as e:
            print(f"DEBUG: 查詢利潤提款記錄失敗: {e}")
            total_profit_withdrawals = 0.0
        
        print(f"DEBUG: 最終利潤計算 - 銷售利潤: {total_profit_twd + total_profit_withdrawals:.2f}, 利潤提款: {total_profit_withdrawals:.2f}, 最終利潤: {total_profit_twd:.2f}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_profit_twd': round(total_profit_twd, 2),
                'total_revenue_twd': round(total_revenue_twd, 2),
                'total_cost_twd': round(total_cost_twd, 2),
                'total_profit_withdrawals': round(total_profit_withdrawals, 2),
                'message': f'系統總利潤：{total_profit_twd:.2f} TWD（收入：{total_revenue_twd:.2f} TWD，成本：{total_cost_twd:.2f} TWD，提款：{total_profit_withdrawals:.2f} TWD）'
            }
        })
        
    except Exception as e:
        print(f"計算總利潤失敗: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'計算總利潤時發生錯誤: {str(e)}'
        }), 500


@app.route("/api/profit/add", methods=["POST"])
@login_required
def api_profit_add():
    """API: 增加利潤"""
    try:
        data = request.get_json()
        account_id = data.get("account_id")
        amount = float(data.get("amount", 0))
        transaction_type = data.get("transaction_type", "PROFIT_EARNED")
        description = data.get("description")
        note = data.get("note")
        related_transaction_id = data.get("related_transaction_id")
        related_transaction_type = data.get("related_transaction_type")
        
        if not account_id or amount <= 0:
            return jsonify({"status": "error", "message": "無效的帳戶ID或金額"}), 400
        
        result = ProfitService.add_profit(
            account_id=account_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            note=note,
            related_transaction_id=related_transaction_id,
            related_transaction_type=related_transaction_type,
            operator_id=current_user.id
        )
        
        if result["success"]:
            return jsonify({"status": "success", "data": result})
        else:
            return jsonify({"status": "error", "message": result["message"]}), 400
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"增加利潤失敗: {str(e)}"}), 500


@app.route("/api/profit/withdraw", methods=["POST"])
@login_required
def api_profit_withdraw():
    """API: 提取利潤 - 從系統總利潤中扣除"""
    try:
        data = request.get_json()
        amount = float(data.get("amount", 0))
        description = data.get("description", "利潤提款")
        note = data.get("note", "")
        
        if amount <= 0:
            return jsonify({"status": "error", "message": "無效的提款金額"}), 400
        
        # 計算當前總利潤（與總利潤API保持一致的邏輯）
        total_profit = 0.0
        all_sales = db.session.execute(db.select(SalesRecord)).scalars().all()
        
        for sale in all_sales:
            profit_info = FIFOService.calculate_profit_for_sale(sale)
            if profit_info:
                total_profit += profit_info.get('profit_twd', 0.0)
        
        # 扣除之前的利潤提款
        try:
            previous_withdrawals = db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
            ).scalars().all()
        except Exception as e:
            if "profit_before does not exist" in str(e):
                print("警告: 利潤提款API查詢 PROFIT_WITHDRAW 記錄時缺少欄位，跳過查詢")
                db.session.rollback()
                previous_withdrawals = []
            else:
                db.session.rollback()
                raise e
        
        total_withdrawals = sum(entry.amount for entry in previous_withdrawals)
        current_profit = total_profit - total_withdrawals
        
        print(f"DEBUG: 利潤提款檢查 - 總銷售利潤: {total_profit:.2f}, 已提款: {total_withdrawals:.2f}, 可用利潤: {current_profit:.2f}, 提款金額: {amount:.2f}")
        
        if current_profit < amount:
            print(f"DEBUG: 提款失敗 - 餘額不足: 可用 {current_profit:.2f} < 提款 {amount:.2f}")
            return jsonify({"status": "error", "message": f"利潤餘額不足，當前可用利潤: NT$ {current_profit:.2f}"}), 400
        
        # 創建利潤提款記錄
        entry = LedgerEntry(
            entry_type="PROFIT_WITHDRAW",
            amount=-amount,  # 負數表示扣除
            description=f"{description} - {note}" if note else description,
            operator_id=current_user.id,
            profit_before=current_profit,
            profit_after=current_profit - amount,
            profit_change=-amount
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": f"利潤提款成功: NT$ {amount:.2f}",
            "data": {
                "amount": amount,
                "profit_before": current_profit,
                "profit_after": current_profit - amount,
                "transaction_id": entry.id
            }
        })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"提取利潤失敗: {str(e)}"}), 500


@app.route("/api/profit/adjust", methods=["POST"])
@login_required
def api_profit_adjust():
    """API: 調整利潤餘額"""
    try:
        data = request.get_json()
        account_id = data.get("account_id")
        new_balance = float(data.get("new_balance", 0))
        description = data.get("description")
        note = data.get("note")
        
        if not account_id:
            return jsonify({"status": "error", "message": "無效的帳戶ID"}), 400
        
        result = ProfitService.adjust_profit(
            account_id=account_id,
            new_balance=new_balance,
            description=description,
            note=note,
            operator_id=current_user.id
        )
        
        if result["success"]:
            return jsonify({"status": "success", "data": result})
        else:
            return jsonify({"status": "error", "message": result["message"]}), 400
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"調整利潤失敗: {str(e)}"}), 500


@app.route("/api/profit/history", methods=["GET"])
@login_required
def api_profit_history():
    """API: 獲取利潤變動歷史 - 從LedgerEntry中獲取利潤提款記錄"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)  # 每頁10筆
        limit = per_page
        
        # 查詢所有利潤相關記錄（包含利潤提款和利潤扣除）
        try:
            # 先查詢總數
            total_query = (
                db.select(db.func.count(LedgerEntry.id))
                .filter(
                    (LedgerEntry.entry_type == "PROFIT_WITHDRAW") |
                    (LedgerEntry.entry_type == "PROFIT_DEDUCT") |
                    (LedgerEntry.entry_type == "PROFIT_EARNED") |
                    (LedgerEntry.description.like("%利潤提款%")) |
                    (LedgerEntry.description.like("%利潤扣除%")) |
                    (LedgerEntry.description.like("%售出利潤%"))
                )
            )
            total_count = db.session.execute(total_query).scalar()
            
            # 計算分頁
            total_pages = (total_count + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            # 查詢分頁數據
            profit_entries = (
                db.session.execute(
                    db.select(LedgerEntry)
                    .filter(
                        (LedgerEntry.entry_type == "PROFIT_WITHDRAW") |
                        (LedgerEntry.entry_type == "PROFIT_DEDUCT") |
                        (LedgerEntry.entry_type == "PROFIT_EARNED") |
                        (LedgerEntry.description.like("%利潤提款%")) |
                        (LedgerEntry.description.like("%利潤扣除%")) |
                        (LedgerEntry.description.like("%售出利潤%"))
                    )
                    .order_by(LedgerEntry.entry_date.desc())
                    .offset(offset)
                    .limit(per_page)
                )
                .scalars()
                .all()
            )
            
            print(f"DEBUG: api_profit_history 查詢到 {len(profit_entries)} 筆記錄")
            for entry in profit_entries:
                print(f"DEBUG: 記錄 - 類型: {entry.entry_type}, 金額: {entry.amount}, 描述: {entry.description}")
                print(f"DEBUG: 利潤欄位 - profit_before: {getattr(entry, 'profit_before', 'None')}, profit_after: {getattr(entry, 'profit_after', 'None')}, profit_change: {getattr(entry, 'profit_change', 'None')}")
        except Exception as e:
            if "profit_before does not exist" in str(e):
                print("警告: 利潤歷史API查詢 PROFIT_WITHDRAW 記錄時缺少欄位，返回空記錄")
                db.session.rollback()
                profit_entries = []
            else:
                db.session.rollback()
                raise e
        
        # 構建返回數據
        transactions = []
        print(f"DEBUG: 找到 {len(profit_entries)} 筆利潤記錄")
        
        # 計算當前總利潤（用於餘額計算）
        try:
            # 使用FIFO計算當前總利潤
            all_sales = (
                db.session.execute(
                    db.select(SalesRecord)
                )
                .scalars()
                .all()
            )
            
            fifo_total_profit = 0.0
            for sale in all_sales:
                profit_info = FIFOService.calculate_profit_for_sale(sale)
                if profit_info:
                    fifo_total_profit += profit_info.get('profit_twd', 0.0)
            
            # 扣除利潤提款
            profit_withdraw_entries = (
                db.session.execute(
                    db.select(LedgerEntry)
                    .filter(LedgerEntry.entry_type == "PROFIT_WITHDRAW")
                )
                .scalars()
                .all()
            )
            total_profit_withdrawals = sum(abs(entry.amount) for entry in profit_withdraw_entries)
            
            current_total_profit = fifo_total_profit - total_profit_withdrawals
            print(f"DEBUG: 當前總利潤 (FIFO計算): {current_total_profit:.2f}")
        except Exception as e:
            print(f"DEBUG: 計算當前總利潤失敗: {e}")
            current_total_profit = 0.0
        
        for entry in profit_entries:
            print(f"DEBUG: 處理記錄 - 類型: {entry.entry_type}, 描述: {entry.description}, 金額: {entry.amount}")
            
            # 判斷是否為提款或扣除（應該顯示為負數）
            is_withdrawal = (
                entry.entry_type == "PROFIT_WITHDRAW" or
                entry.entry_type == "PROFIT_DEDUCT" or
                "利潤提款" in (entry.description or "") or
                "利潤扣除" in (entry.description or "")
            )
            
            # 根據記錄類型確定金額正負
            display_amount = entry.amount
            if is_withdrawal and entry.amount > 0:
                display_amount = -entry.amount  # 提款和扣除應該顯示為負數
            
            print(f"DEBUG: 記錄處理結果 - 是否提款: {is_withdrawal}, 顯示金額: {display_amount}")
            
            # 如果profit_before和profit_after為空，嘗試計算
            balance_before = getattr(entry, 'profit_before', None)
            balance_after = getattr(entry, 'profit_after', None)
            
            if balance_before is None or balance_after is None:
                # 使用當前總利潤作為基準，根據記錄類型計算
                if entry.entry_type == "PROFIT_EARNED":
                    # 利潤入庫：餘額增加
                    balance_after = current_total_profit
                    balance_before = balance_after - entry.amount
                elif entry.entry_type == "PROFIT_WITHDRAW":
                    # 利潤提款：餘額減少
                    balance_before = current_total_profit + abs(entry.amount)
                    balance_after = current_total_profit
                else:
                    # 其他情況：使用當前總利潤
                    balance_before = current_total_profit
                    balance_after = current_total_profit
            
            transactions.append({
                "id": entry.id,
                "transaction_type": entry.entry_type or "利潤變動",
                "amount": display_amount,  # 根據類型調整正負
                "balance_before": balance_before,
                "balance_after": balance_after,
                "description": entry.description,
                "note": getattr(entry, 'note', None),
                "operator_name": entry.operator.username if entry.operator else "未知",
                "created_at": entry.entry_date.isoformat()
            })
        
        return jsonify({
            "status": "success", 
            "data": {
                "success": True,
                "transactions": transactions,
                "pagination": {
                    "current_page": page,
                    "per_page": per_page,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        })
            
    except Exception as e:
        print(f"獲取利潤歷史失敗: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"獲取利潤歷史失敗: {str(e)}"}), 500


@app.route("/api/calculate_profit", methods=["POST"])
@login_required
def api_calculate_profit():
    """計算售出利潤預覽"""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "無效的請求格式。"}), 400
    
    try:
        rmb_amount = float(data.get("rmb_amount", 0))
        exchange_rate = float(data.get("exchange_rate", 0))
        
        if rmb_amount <= 0 or exchange_rate <= 0:
            return jsonify({"status": "error", "message": "售出金額和匯率必須大於0。"}), 400
        
        # 計算售出收入
        revenue_twd = rmb_amount * exchange_rate
        
        # 使用FIFO服務計算庫存成本
        profit_info = FIFOService.calculate_profit_preview(rmb_amount, exchange_rate)
        
        if profit_info:
            return jsonify({
                "status": "success",
                "data": {
                    "rmb_amount": rmb_amount,
                    "exchange_rate": exchange_rate,
                    "revenue_twd": revenue_twd,
                    "total_cost_twd": profit_info["total_cost_twd"],
                    "profit_twd": profit_info["profit_twd"],
                    "profit_margin": profit_info["profit_margin"],
                    "cost_breakdown": profit_info["cost_breakdown"]
                }
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "庫存不足，無法計算利潤。"
            }), 400
            
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "輸入的資料格式不正確。"}), 400
    except Exception as e:
        print(f"!! Error in api_calculate_profit: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "伺服器內部錯誤，計算失敗。"}), 500


# 🚨 危險的資料庫清空API已被禁用！
@app.route("/api/clear-all-data", methods=["POST"])
@login_required
def api_clear_all_data():
    """手動清空所有測試數據 - 僅供公測使用"""
    # 安全檢查：僅管理員可使用
    if not current_user.is_admin:
        return jsonify({"status": "error", "message": "權限不足，僅管理員可執行此操作。"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "無效的請求格式。"}), 400
    
    # 雙重確認機制
    confirmation = data.get("confirmation")
    if confirmation != "CONFIRM_CLEAR_ALL_DATA":
        return jsonify({"status": "error", "message": "確認碼錯誤，操作已取消。"}), 400
    
    try:
        print(f"管理員 {current_user.username} 開始執行數據清空操作...")
        
        # 關鍵修復：按照外鍵依賴關係的正確順序清空數據
        
        # 1. 首先清空 transactions 表 (引用 sales_records)
        transactions_count = 0
        try:
            transactions_count = db.session.execute(db.select(func.count()).select_from(db.text('transactions'))).scalar()
            db.session.execute(db.text('DELETE FROM transactions'))
            print(f"已清空 {transactions_count} 筆交易記錄")
        except Exception as transactions_error:
            print(f"Transactions表清空失敗或不存在: {transactions_error}")
        
        # 2. 清空 FIFO 銷售分配記錄 (引用 fifo_inventory)
        fifo_sales_allocations_count = 0
        try:
            fifo_sales_allocations_count = db.session.execute(db.select(func.count()).select_from(db.text('fifo_sales_allocations'))).scalar()
            db.session.execute(db.text('DELETE FROM fifo_sales_allocations'))
            print(f"已清空 {fifo_sales_allocations_count} 筆FIFO銷售分配記錄")
        except Exception as fifo_sales_error:
            print(f"FIFO銷售分配表清空失敗或不存在: {fifo_sales_error}")
        
        # 3. 清空 FIFO 庫存記錄 (引用 purchase_records)
        fifo_count = 0
        try:
            fifo_count = db.session.execute(db.select(func.count()).select_from(db.text('fifo_inventory'))).scalar()
            db.session.execute(db.text('DELETE FROM fifo_inventory'))
            print(f"已清空 {fifo_count} 筆FIFO庫存記錄")
        except Exception as fifo_error:
            print(f"FIFO庫存表清空失敗或不存在: {fifo_error}")
        
        # 4. 清空售出訂單 (被 transactions 引用)
        sales_count = db.session.execute(db.select(func.count(SalesRecord.id))).scalar()
        db.session.execute(db.delete(SalesRecord))
        print(f"已清空 {sales_count} 筆售出訂單")
        
        # 5. 清空買入訂單 (現在沒有外鍵依賴了)
        purchase_count = db.session.execute(db.select(func.count(PurchaseRecord.id))).scalar()
        db.session.execute(db.delete(PurchaseRecord))
        print(f"已清空 {purchase_count} 筆買入訂單")
        
        # 6. 清空現金流水記錄 (LedgerEntry, CashLog)
        ledger_count = db.session.execute(db.select(func.count(LedgerEntry.id))).scalar()
        db.session.execute(db.delete(LedgerEntry))
        print(f"已清空 {ledger_count} 筆帳本記錄")
        
        cash_log_count = db.session.execute(db.select(func.count(CashLog.id))).scalar()
        db.session.execute(db.delete(CashLog))
        print(f"已清空 {cash_log_count} 筆現金日誌")
        
        # 7. 清空刷卡記錄 (如果存在)
        card_purchase_count = 0
        try:
            card_purchase_count = db.session.execute(db.select(func.count(CardPurchase.id))).scalar()
            db.session.execute(db.delete(CardPurchase))
            print(f"已清空 {card_purchase_count} 筆刷卡記錄")
        except Exception as card_error:
            print(f"刷卡記錄表清空失敗或不存在: {card_error}")
        
        # 8. 清空所有帳戶金額 (將餘額設為0，但保留帳戶結構)
        accounts = db.session.execute(db.select(CashAccount)).scalars().all()
        account_count = 0
        for account in accounts:
            if account.balance != 0:
                print(f"  清空帳戶: {account.name} ({account.currency}) 餘額: {account.balance} -> 0")
                account.balance = 0
                account_count += 1
        print(f"已清空 {account_count} 個帳戶的餘額")
        
        # 9. 清空應收帳款 (將客戶的應收帳款設為0，但保留客戶記錄)
        customers = db.session.execute(db.select(Customer)).scalars().all()
        receivable_count = 0
        for customer in customers:
            if customer.total_receivables_twd > 0:
                print(f"  清空客戶應收: {customer.name} 應收款: {customer.total_receivables_twd} -> 0")
                customer.total_receivables_twd = 0
                receivable_count += 1
        print(f"已清空 {receivable_count} 位客戶的應收帳款")
        
        # 提交所有更改
        db.session.commit()
        
        total_message = f"數據清空完成！清空了 {purchase_count} 筆買入、{sales_count} 筆售出、{account_count} 個帳戶餘額、{ledger_count} 筆帳本記錄、{cash_log_count} 筆現金日誌、{receivable_count} 位客戶應收帳款、{fifo_count} 筆FIFO庫存、{fifo_sales_allocations_count} 筆FIFO分配、{transactions_count} 筆交易記錄、{card_purchase_count} 筆刷卡記錄。"
        print(f" {total_message}")
        
        return jsonify({
            "status": "success", 
            "message": total_message,
            "details": {
                "purchases_cleared": purchase_count,
                "sales_cleared": sales_count,
                "accounts_cleared": account_count,
                "ledger_entries_cleared": ledger_count,
                "cash_logs_cleared": cash_log_count,
                "receivables_cleared": receivable_count,
                "fifo_cleared": fifo_count,
                "fifo_sales_allocations_cleared": fifo_sales_allocations_count,
                "transactions_cleared": transactions_count,
                "card_purchases_cleared": card_purchase_count
            }
        })
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"數據清空失敗: {e}"
        print(f"{error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": error_msg}), 500


@app.route("/api/users", methods=["GET"])
@login_required
def api_users():
    """獲取用戶列表API"""
    try:
        users = db.session.execute(
            db.select(User.id, User.username)
            .order_by(User.username)
        ).all()
        
        users_data = [{'id': user.id, 'username': user.username} for user in users]
        
        return jsonify({
            'status': 'success',
            'users': users_data
        })
        
    except Exception as e:
        print(f"獲取用戶列表失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': f'獲取用戶列表失敗: {e}'
        }), 500


@app.route("/api/delete_audit_logs", methods=["GET"])
@login_required
def api_delete_audit_logs():
    """獲取刪除記錄審計API"""
    try:
        # 獲取查詢參數
        table_name = request.args.get('table_name', '')
        operator_id = request.args.get('operator_id', '')
        limit = int(request.args.get('limit', 20))
        
        # 限制查詢數量
        limit = min(limit, 100)  # 最多100筆
        
        # 構建查詢
        query = db.select(DeleteAuditLog)
        
        if table_name:
            query = query.filter(DeleteAuditLog.table_name == table_name)
        
        if operator_id:
            try:
                operator_id_int = int(operator_id)
                query = query.filter(DeleteAuditLog.operator_id == operator_id_int)
            except ValueError:
                pass
        
        # 排序和限制
        query = query.order_by(DeleteAuditLog.deleted_at.desc()).limit(limit)
        
        # 執行查詢
        try:
            audit_logs = db.session.execute(query).scalars().all()
        except Exception as e:
            if "does not exist" in str(e) and "delete_audit_logs" in str(e):
                print("警告: delete_audit_logs 表格不存在，返回空結果")
                db.session.rollback()
                audit_logs = []
            else:
                db.session.rollback()
                raise e
        
        # 轉換為字典格式
        logs_data = []
        for log in audit_logs:
            try:
                import json
                deleted_data = json.loads(log.deleted_data) if log.deleted_data else {}
            except:
                deleted_data = {}
            
            try:
                balance_changes = json.loads(log.balance_changes) if log.balance_changes else None
            except:
                balance_changes = None
            
            log_dict = {
                'id': log.id,
                'table_name': log.table_name,
                'record_id': log.record_id,
                'deleted_data': deleted_data,
                'operation_type': log.operation_type,
                'description': log.description,
                'operator_name': log.operator_name,
                'deleted_at': log.deleted_at.isoformat() if log.deleted_at else None,
                'ip_address': log.ip_address,
                'balance_changes': balance_changes
            }
            logs_data.append(log_dict)
        
        # 獲取總數（用於計數）
        try:
            total_count = db.session.execute(db.select(func.count(DeleteAuditLog.id))).scalar()
        except Exception as e:
            if "does not exist" in str(e) and "delete_audit_logs" in str(e):
                print("警告: delete_audit_logs 表格不存在，總數設為0")
                db.session.rollback()
                total_count = 0
            else:
                db.session.rollback()
                raise e
        
        return jsonify({
            'status': 'success',
            'logs': logs_data,
            'total': total_count,
            'limit': limit
        })
        
    except Exception as e:
        print(f"獲取刪除記錄審計失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': f'獲取刪除記錄失敗: {e}'
        }), 500


@app.route("/api/delete-account", methods=["POST"])
@login_required
def api_delete_account():
    """刪除現金帳戶的 API 端點"""
    if not current_user.is_admin:
        return jsonify({"status": "error", "message": "權限不足，僅管理員可執行此操作。"}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "無效的請求格式。"}), 400
        
        account_id = data.get("account_id")
        if not account_id:
            return jsonify({"status": "error", "message": "帳戶ID為必填項。"}), 400
        
        # 確保 account_id 是整數類型
        try:
            account_id = int(account_id)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "帳戶ID格式無效，必須是數字。"}), 400
        
        # 查詢帳戶
        account = db.session.get(CashAccount, account_id)
        if not account:
            return jsonify({"status": "error", "message": "找不到指定的帳戶。"}), 404
        
        # 檢查帳戶餘額
        if account.balance != 0:
            return jsonify({
                "status": "error", 
                "message": f'無法刪除！帳戶 "{account.name}" 尚有 {account.balance:,.2f} 的餘額。'
            }), 400
        
        # 檢查外鍵約束 - 檢查是否有其他表引用此帳戶
        try:
            # 檢查 LedgerEntry 表
            ledger_count = db.session.execute(
                db.select(func.count(LedgerEntry.id)).filter(LedgerEntry.account_id == account_id)
            ).scalar()
            
            if ledger_count > 0:
                return jsonify({
                    "status": "error",
                    "message": f'無法刪除！帳戶 "{account.name}" 仍有 {ledger_count} 筆帳本記錄，請先處理這些記錄。'
                }), 400
            
            # 檢查 CashLog 表（注意：CashLog 目前沒有 account_id 欄位）
            # 暫時跳過這個檢查，因為 CashLog 表結構已更改
            cash_log_count = 0
            
            # 檢查其他可能的外鍵引用（如果有其他表的話）
            # 這裡可以根據實際的資料庫結構添加更多檢查
            
        except Exception as check_error:
            print(f"檢查外鍵約束時出錯: {check_error}")
            # 如果檢查失敗，我們不應該繼續，而是返回錯誤
            return jsonify({
                "status": "error",
                "message": f'檢查帳戶約束時出錯，無法安全刪除帳戶 "{account.name}"。'
            }), 500
        
        # 所有檢查通過，開始刪除帳戶
        try:
            account_name = account.name
            db.session.delete(account)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": f'帳戶 "{account_name}" 已成功刪除！'
            })
            
        except Exception as delete_error:
            db.session.rollback()
            print(f"刪除帳戶時出錯: {delete_error}")
            
            # 檢查是否是外鍵約束錯誤
            if "ForeignKeyViolation" in str(delete_error) or "foreign key constraint" in str(delete_error).lower():
                error_msg = f'無法刪除帳戶 "{account.name}"，該帳戶仍被其他記錄引用。請先處理相關的帳本記錄或現金流水記錄。'
            elif "InFailedSqlTransaction" in str(delete_error):
                error_msg = f'資料庫事務錯誤，請重新嘗試刪除帳戶 "{account.name}"。'
            else:
                error_msg = f"刪除帳戶失敗: {delete_error}"
            
            return jsonify({"status": "error", "message": error_msg}), 500
        
    except Exception as e:
        # 確保事務被回滾
        try:
            db.session.rollback()
        except:
            pass  # 如果回滾也失敗，我們無能為力
        
        print(f"刪除帳戶時發生嚴重錯誤: {e}")
        return jsonify({"status": "error", "message": "刪除帳戶時發生嚴重錯誤，請稍後重試。"}), 500


@app.route("/api/settlement", methods=["POST"])
@login_required
def api_settlement():
    """處理應收帳款銷帳"""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "無效的請求格式。"}), 400

    try:
        # 1. 獲取並驗證資料
        customer_id = int(data.get("customer_id"))
        amount = float(data.get("amount"))
        account_id = int(data.get("account_id"))
        note = data.get("note", "")

        if not all([customer_id, amount > 0, account_id]):
            return jsonify({"status": "error", "message": "客戶ID、銷帳金額和收款帳戶都必須正確填寫。"}), 400

        # 2. 查詢資料庫物件
        customer = db.session.get(Customer, customer_id)
        account = db.session.get(CashAccount, account_id)

        if not customer:
            return jsonify({"status": "error", "message": "找不到指定的客戶。"}), 400
        if not account:
            return jsonify({"status": "error", "message": f"找不到帳戶 ID {account_id}，該帳戶可能已被刪除。"}), 400
        if not account.is_active:
            return jsonify({"status": "error", "message": f"帳戶「{account.name}」已停用，無法使用。"}), 400
        if account.currency != "TWD":
            return jsonify({"status": "error", "message": f"帳戶「{account.name}」的幣種是 {account.currency}，不是台幣帳戶。"}), 400
        if amount > customer.total_receivables_twd:
            return jsonify({
                "status": "error", 
                "message": f"銷帳金額超過應收帳款！客戶應收 {customer.total_receivables_twd:,.2f}，但銷帳 {amount:,.2f}。"
            }), 400

        # 3. 核心業務邏輯
        # 更新客戶應收帳款
        customer.total_receivables_twd -= amount
        
        # 更新收款帳戶餘額
        account.balance += amount
        
        # 創建銷帳記錄（LedgerEntry）
        settlement_entry = LedgerEntry(
            account_id=account.id,
            entry_type="SETTLEMENT",
            amount=amount,
            entry_date=datetime.utcnow(),
            description=f"客戶「{customer.name}」銷帳收款 - {note}" if note else f"客戶「{customer.name}」銷帳收款",
            operator_id=current_user.id
        )
        db.session.add(settlement_entry)
        
        # 創建現金流水記錄（CashLog）- 暫時不設置 account_id
        settlement_cash_log = CashLog(
            type="SETTLEMENT",
            amount=amount,
            time=datetime.utcnow(),
            description=f"客戶「{customer.name}」銷帳收款 - {note}" if note else f"客戶「{customer.name}」銷帳收款",
            operator_id=current_user.id
        )
        db.session.add(settlement_cash_log)
        
        # 提交事務
        db.session.commit()
        
        # 強制刷新對象狀態
        db.session.refresh(customer)
        db.session.refresh(account)

        return jsonify({
            "status": "success",
            "message": f"銷帳成功！客戶「{customer.name}」已收款 NT$ {amount:,.2f}，應收帳款餘額：NT$ {customer.total_receivables_twd:,.2f}。"
        })

    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "輸入的資料格式不正確。"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"!! Error in api_settlement: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "伺服器內部錯誤，操作失敗。"}), 500


@app.route("/api/customers/manage")
@login_required
def api_customers_manage():
    """API端點：獲取所有客戶用於管理"""
    try:
        # 獲取所有客戶（包括已停用的）
        customers = (
            db.session.execute(
                db.select(Customer)
                .order_by(Customer.is_active.desc(), Customer.id.desc())
            )
            .scalars()
            .all()
        )
        
        customers_data = []
        for customer in customers:
            customers_data.append({
                'id': customer.id,
                'name': customer.name,
                'is_active': customer.is_active,
                'total_receivables_twd': customer.total_receivables_twd
            })
        
        return jsonify({
            'status': 'success',
            'customers': customers_data
        })
        
    except Exception as e:
        print(f"獲取客戶管理數據失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': f'獲取客戶數據失敗: {e}'
        }), 500


@app.route("/api/customers/<int:customer_id>/delete", methods=["POST"])
@login_required
def api_customer_delete(customer_id):
    """API端點：刪除（停用）客戶"""
    try:
        customer = db.session.get(Customer, customer_id)
        if not customer:
            return jsonify({"status": "error", "message": "找不到指定的客戶。"}), 404
        
        # 檢查客戶是否還有應收帳款
        if customer.total_receivables_twd > 0:
            return jsonify({
                "status": "error", 
                "message": f"無法刪除客戶「{customer.name}」，該客戶還有 NT$ {customer.total_receivables_twd:,.2f} 的應收帳款。"
            }), 400
        
        # 設為停用而非真正刪除
        customer.is_active = False
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"客戶「{customer.name}」已成功停用。"
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"刪除客戶失敗: {e}")
        return jsonify({
            "status": "error",
            "message": f"刪除客戶失敗: {e}"
        }), 500


@app.route("/api/customers/<int:customer_id>/restore", methods=["POST"])
@login_required
def api_customer_restore(customer_id):
    """API端點：恢復客戶"""
    try:
        customer = db.session.get(Customer, customer_id)
        if not customer:
            return jsonify({"status": "error", "message": "找不到指定的客戶。"}), 404
        
        # 恢復客戶
        customer.is_active = True
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"客戶「{customer.name}」已成功恢復。"
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"恢復客戶失敗: {e}")
        return jsonify({
            "status": "error",
            "message": f"恢復客戶失敗: {e}"
        }), 500


@app.route("/api/customer/transactions/<int:customer_id>")
@login_required
def api_customer_transactions(customer_id):
    """API端點：獲取特定客戶的交易紀錄"""
    try:
        # 獲取客戶信息（使用Customer模型，因為應收帳款在Customer表中）
        customer = db.session.get(Customer, customer_id)
        if not customer:
            return jsonify({"status": "error", "message": "找不到指定的客戶。"}), 404
        
        # 獲取該客戶的所有銷售記錄（通過customer_id關聯）
        sales_records = (
            db.session.execute(
                db.select(SalesRecord)
                .filter(SalesRecord.customer_id == customer_id)
                .order_by(SalesRecord.created_at.desc())
            )
            .scalars()
            .all()
        )
        
        # 獲取該客戶的應收帳款變動記錄（通過LedgerEntry）
        # 查詢所有銷帳記錄，然後在Python中過濾包含客戶名稱的記錄
        try:
            all_settlements = (
                db.session.execute(
                    db.select(LedgerEntry)
                    .filter(LedgerEntry.entry_type == "SETTLEMENT")
                    .order_by(LedgerEntry.entry_date.desc())
                )
                .scalars()
                .all()
            )
        except Exception as e:
            if "profit_before does not exist" in str(e):
                print("警告: 查詢 SETTLEMENT 記錄時缺少欄位，跳過查詢")
                db.session.rollback()
                all_settlements = []
            else:
                db.session.rollback()
                raise e
        
        # 在Python中過濾包含客戶名稱的記錄
        receivable_entries = [
            entry for entry in all_settlements 
            if customer.name in entry.description
        ]
        
        # 調試：打印查詢到的銷帳記錄
        print(f"查詢銷帳記錄:")
        print(f"  - 客戶名稱: {customer.name}")
        print(f"  - 所有銷帳記錄數量: {len(all_settlements)}")
        print(f"  - 過濾後包含客戶名稱的銷帳記錄數量: {len(receivable_entries)}")
        
        # 打印所有銷帳記錄的描述，幫助調試
        if len(all_settlements) > 0:
            print(f"  - 所有銷帳記錄描述:")
            for entry in all_settlements:
                print(f"    * {entry.description}")
        
        if len(receivable_entries) > 0:
            print(f"  - 匹配的銷帳記錄描述:")
            for entry in receivable_entries:
                print(f"    * {entry.description}")
        
        # 直接使用數據庫中存儲的應收帳款值，確保與現金管理頁面一致
        total_receivables = customer.total_receivables_twd
        
        # 整理交易紀錄
        transactions = []
        
        # 添加銷售記錄
        for sale in sales_records:
            # 計算銷售利潤
            profit_info = FIFOService.calculate_profit_for_sale(sale)
            profit_twd = profit_info['profit_twd'] if profit_info else 0
            
            transactions.append({
                'id': sale.id,
                'type': '售出',
                'date': sale.created_at.strftime('%Y-%m-%d %H:%M'),
                'description': f'售出 RMB {sale.rmb_amount:,.2f}',
                'rmb_amount': sale.rmb_amount,
                'twd_amount': sale.twd_amount,
                'profit_twd': profit_twd,
                'status': '已售出',
                'category': 'sales'
            })
        
        # 添加銷帳記錄
        for entry in receivable_entries:
            transactions.append({
                'id': entry.id,
                'type': '銷帳',
                'date': entry.entry_date.strftime('%Y-%m-%d %H:%M'),
                'description': entry.description,
                'rmb_amount': 0,
                'twd_amount': entry.amount,
                'profit_twd': 0,
                'status': '已收款',
                'category': 'settlement'
            })
        
        # 按日期排序
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        print(f"客戶 {customer.name} 的交易紀錄:")
        print(f"  - 銷售記錄數量: {len(sales_records)}")
        print(f"  - 銷帳記錄數量: {len(receivable_entries)}")
        print(f"  - 總交易數量: {len(transactions)}")
        print(f"  - 當前應收帳款: {total_receivables}")
        
        return jsonify({
            'status': 'success',
            'customer_name': customer.name,
            'total_receivables_twd': total_receivables,  # 修正欄位名稱
            'transactions': transactions
        })
        
    except Exception as e:
        print(f"獲取客戶交易紀錄失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': f'獲取交易紀錄失敗: {e}'
        }), 500


@app.route("/sales_action", methods=["POST"])
@admin_required
def sales_action():
    action = request.form.get("action")

    try:
        if action == "create_order":
            customer_name = request.form.get("customer_name")
            customer_id = request.form.get("user_id")

            target_customer = None
            if customer_id:
                target_customer = db.session.get(Customer, int(customer_id))
            elif customer_name:
                target_customer = Customer.query.filter_by(name=customer_name).first()
                if not target_customer:
                    target_customer = Customer(name=customer_name, is_active=True)
                    db.session.add(target_customer)
                    db.session.flush()  # 取得 ID

            if not target_customer:
                return (
                    jsonify({"status": "error", "message": "客戶名稱或ID為必填"}),
                    400,
                )

            rmb = float(request.form.get("rmb_sell_amount"))
            rate = float(request.form.get("exchange_rate"))
            order_date_str = request.form.get("order_date")
            twd = rmb * rate

            # 更新客戶應收帳款
            target_customer.total_receivables_twd += twd

            new_sale = SalesRecord(
                customer_id=target_customer.id,
                rmb_amount=rmb,
                exchange_rate=rate,
                twd_amount=twd,
                sale_date=date.fromisoformat(order_date_str),
                status="PENDING",  # 假設初始狀態為 PENDING
            )
            db.session.add(new_sale)
            
            # 分配FIFO庫存
            try:
                db.session.flush()  # 獲取 new_sale.id
                FIFOService.allocate_inventory_for_sale(new_sale)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({"status": "error", "message": f"庫存分配失敗: {e}"}), 500

            transaction_data = {
                "id": new_sale.id,
                "username": target_customer.name,
                "rmb_order_amount": "%.2f" % new_sale.rmb_amount,
                "twd_expected_payment": "%.2f" % new_sale.twd_amount,
                "order_time": new_sale.sale_date.isoformat(),
            }
            return jsonify(
                {
                    "status": "success",
                    "message": "訂單創建成功！",
                    "transaction": transaction_data,
                }
            )

        elif action == "delete_order":
            tx_id = request.form.get("transaction_id")
            sale_to_delete = db.session.get(SalesRecord, int(tx_id))
            if not sale_to_delete:
                return jsonify({"status": "error", "message": "找不到該訂單"}), 404

            # --- 關鍵修正：正確回滾銷售分配和應收帳款 ---
            try:
                # 1. 回滾客戶應收帳款
                customer = sale_to_delete.customer
                if customer:
                    customer.total_receivables_twd -= sale_to_delete.twd_amount
                
                # 2. 回滾FIFO庫存分配
                allocations = db.session.execute(
                    db.select(FIFOSalesAllocation).filter_by(sales_record_id=sale_to_delete.id)
                ).scalars().all()
                
                for allocation in allocations:
                    # 恢復庫存
                    inventory = allocation.fifo_inventory
                    inventory.remaining_rmb += allocation.allocated_rmb
                    
                    # 刪除分配記錄
                    db.session.delete(allocation)
                
                # 3. 刪除銷售記錄
                db.session.delete(sale_to_delete)
                db.session.commit()
                
                return jsonify(
                    {"status": "success", "message": "訂單已成功取消，應收帳款和庫存已回滾。", "deleted_id": tx_id}
                )
            except Exception as e:
                db.session.rollback()
                return jsonify(
                    {"status": "error", "message": f"取消訂單時發生錯誤: {str(e)}"}
                ), 500

        else:
            return jsonify({"status": "error", "message": "無效的操作"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"伺服器錯誤: {str(e)}"}), 500


@app.route("/api/channels", methods=["GET"])
@admin_required
def get_channels():
    channels = Channel.query.filter_by(is_active=True).order_by(Channel.name).all()
    return jsonify([{"id": c.id, "name": c.name} for c in channels])


@app.route("/api/channels/public", methods=["GET"])
@login_required
def get_channels_public():
    """允許登入用戶獲取渠道列表，用於買入頁面"""
    channels = Channel.query.filter_by(is_active=True).order_by(Channel.name).all()
    return jsonify([{"id": c.id, "name": c.name} for c in channels])


@app.route("/api/channel", methods=["POST", "DELETE"])
@login_required
def manage_channel():
    data = request.get_json()
    if request.method == "POST":
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"status": "error", "message": "渠道名稱不可為空"}), 400
        if Channel.query.filter_by(name=name).first():
            return jsonify({"status": "error", "message": "此渠道已存在"}), 409

        new_channel = Channel(name=name)
        db.session.add(new_channel)
        db.session.commit()
        return jsonify(
            {
                "status": "success",
                "message": "渠道新增成功",
                "channel": {"id": new_channel.id, "name": new_channel.name},
            }
        )

    if request.method == "DELETE":
        channel_id = data.get("id")
        channel = db.session.get(Channel, channel_id)
        if not channel:
            return jsonify({"status": "error", "message": "找不到該渠道"}), 404

        # 軟刪除
        channel.is_active = False
        db.session.commit()
        return jsonify({"status": "success", "message": "渠道已刪除"})


@app.route("/export_test.html", methods=["GET"])
def export_test_page():
    """提供數據導出測試頁面"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>數據庫導出測試</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; max-height: 400px; }
        .status { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1> 數據庫導出測試</h1>
    
    <p>點擊下面的按鈕來導出您的本地數據庫數據：</p>
    
    <button onclick="exportData()">📥 導出數據庫數據</button>
    <button onclick="downloadAsJson()">💾 下載為JSON文件</button>
    
    <div id="status"></div>
    <div id="result"></div>

    <script>
        let exportedData = null;
        
        async function exportData() {
            const statusDiv = document.getElementById('status');
            const resultDiv = document.getElementById('result');
            
            statusDiv.innerHTML = '<div class="status">正在導出數據...</div>';
            resultDiv.innerHTML = '';
            
            try {
                const response = await fetch('/api/export_database');
                
                if (response.ok) {
                    exportedData = await response.json();
                    
                    // 顯示統計信息
                    const stats = `
                        <div class="status success">
                             導出成功！<br>
                            👥 用戶: ${exportedData.users ? exportedData.users.length : 0} 個<br>
                            🏢 持有人: ${exportedData.holders ? exportedData.holders.length : 0} 個<br>
                             現金帳戶: ${exportedData.cash_accounts ? exportedData.cash_accounts.length : 0} 個<br>
                             客戶: ${exportedData.customers ? exportedData.customers.length : 0} 個<br>
                            📡 渠道: ${exportedData.channels ? exportedData.channels.length : 0} 個
                        </div>
                    `;
                    statusDiv.innerHTML = stats;
                    
                    // 顯示詳細數據
                    resultDiv.innerHTML = `
                        <h3>📋 導出的數據：</h3>
                        <pre>${JSON.stringify(exportedData, null, 2)}</pre>
                    `;
                    
                } else {
                    const error = await response.text();
                    statusDiv.innerHTML = `<div class="status error"> 導出失敗: ${error}</div>`;
                }
                
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error"> 請求失敗: ${error.message}</div>`;
            }
        }
        
        function downloadAsJson() {
            if (!exportedData) {
                alert('請先導出數據！');
                return;
            }
            
            const dataStr = JSON.stringify(exportedData, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `database_export_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
            link.click();
            
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>'''


@app.route("/api/export_database", methods=["GET"])
def export_database_api():
    """通過API導出數據庫數據"""
    try:
        export_data = {
            "export_time": datetime.utcnow().isoformat(),
            "users": [],
            "holders": [],
            "cash_accounts": [],
            "customers": [],
            "channels": []
        }
        
        # 導出用戶
        users = db.session.execute(db.select(User)).scalars().all()
        for user in users:
            export_data["users"].append({
                "username": user.username,
                "is_admin": user.is_admin,
                "is_active": user.is_active
            })
        
        # 導出持有人
        holders = db.session.execute(db.select(Holder)).scalars().all()
        for holder in holders:
            export_data["holders"].append({
                "name": holder.name,
                "is_active": holder.is_active
            })
        
        # 導出現金帳戶
        accounts = db.session.execute(db.select(CashAccount)).scalars().all()
        for account in accounts:
            export_data["cash_accounts"].append({
                "name": account.name,
                "currency": account.currency,
                "balance": float(account.balance),
                "holder_name": account.holder.name if account.holder else None
            })
        
        # 導出客戶
        try:
            customers = db.session.execute(db.select(Customer)).scalars().all()
            for customer in customers:
                export_data["customers"].append({
                    "name": customer.name,
                    "is_active": customer.is_active,
                    "total_receivables_twd": float(customer.total_receivables_twd)
                })
        except Exception:
            pass
        
        # 導出渠道
        try:
            channels = db.session.execute(db.select(Channel)).scalars().all()
            for channel in channels:
                export_data["channels"].append({
                    "name": channel.name,
                    "is_active": channel.is_active
                })
        except Exception:
            pass
        
        return jsonify(export_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/import_database", methods=["POST"])
def import_database_api():
    """通過API導入數據庫數據"""
    try:
        import os
        import json
        
        # 尋找導出文件
        json_files = [f for f in os.listdir('.') if f.startswith('database_export') and f.endswith('.json')]
        
        if not json_files:
            return jsonify({"error": "未找到數據導出文件 (database_export*.json)"}), 400
            
        # 使用最新的文件
        json_file = sorted(json_files)[-1]
        
        # 讀取JSON數據
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        import_stats = {
            "users_imported": 0,
            "holders_imported": 0,
            "accounts_imported": 0,
            "customers_imported": 0,
            "channels_imported": 0,
            "users_updated": 0,
            "accounts_updated": 0,
            "customers_updated": 0
        }
        
        # 1. 導入用戶
        for user_data in data.get('users', []):
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                user = User(
                    username=user_data['username'],
                    password_hash='pbkdf2:sha256:260000$default$hash',  # 默認密碼hash
                    is_admin=user_data.get('is_admin', False),
                    is_active=user_data.get('is_active', True)
                )
                db.session.add(user)
                import_stats["users_imported"] += 1
            else:
                import_stats["users_updated"] += 1
        
        # 2. 導入持有人
        for holder_data in data.get('holders', []):
            existing_holder = Holder.query.filter_by(name=holder_data['name']).first()
            if not existing_holder:
                holder = Holder(
                    name=holder_data['name'],
                    is_active=holder_data.get('is_active', True)
                )
                db.session.add(holder)
                import_stats["holders_imported"] += 1
        
        # 提交持有人數據，以便後續引用
        db.session.commit()
        
        # 3. 導入現金帳戶
        for account_data in data.get('cash_accounts', []):
            existing_account = CashAccount.query.filter_by(name=account_data['name']).first()
            if not existing_account:
                # 查找對應的持有人
                holder = None
                if account_data.get('holder_name'):
                    holder = Holder.query.filter_by(name=account_data['holder_name']).first()
                
                account = CashAccount(
                    name=account_data['name'],
                    currency=account_data['currency'],
                    balance=account_data.get('balance', 0.0),
                    holder_id=holder.id if holder else None
                )
                db.session.add(account)
                import_stats["accounts_imported"] += 1
            else:
                # 更新餘額
                existing_account.balance = account_data.get('balance', 0.0)
                import_stats["accounts_updated"] += 1
        
        # 4. 導入客戶
        for customer_data in data.get('customers', []):
            existing_customer = Customer.query.filter_by(name=customer_data['name']).first()
            if not existing_customer:
                customer = Customer(
                    name=customer_data['name'],
                    is_active=customer_data.get('is_active', True),
                    total_receivables_twd=customer_data.get('total_receivables_twd', 0.0)
                )
                db.session.add(customer)
                import_stats["customers_imported"] += 1
            else:
                # 更新應收帳款
                existing_customer.total_receivables_twd = customer_data.get('total_receivables_twd', 0.0)
                import_stats["customers_updated"] += 1
        
        # 5. 導入渠道
        for channel_data in data.get('channels', []):
            existing_channel = Channel.query.filter_by(name=channel_data['name']).first()
            if not existing_channel:
                channel = Channel(
                    name=channel_data['name'],
                    is_active=channel_data.get('is_active', True)
                )
                db.session.add(channel)
                import_stats["channels_imported"] += 1
        
        # 最終提交
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "數據導入完成",
            "file_used": json_file,
            "statistics": import_stats,
            "total_data": {
                "users": len(data.get('users', [])),
                "holders": len(data.get('holders', [])),
                "cash_accounts": len(data.get('cash_accounts', [])),
                "customers": len(data.get('customers', [])),
                "channels": len(data.get('channels', []))
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"導入失敗: {str(e)}"}), 500


@app.route("/api/fix_database", methods=["POST"])
def fix_database_api():
    """修復數據庫表結構和基礎數據"""
    try:
        # 確保所有表都存在
        db.create_all()
        
        # 檢查並創建基本數據
        result = {
            "tables_created": True,
            "admin_user_exists": False,
            "sample_data_created": False
        }
        
        # 檢查是否有管理員用戶
        admin_user = User.query.filter_by(is_admin=True).first()
        if admin_user:
            result["admin_user_exists"] = True
        else:
            # 創建默認管理員用戶
            try:
                default_admin = User(
                    username="admin",
                    password_hash="pbkdf2:sha256:260000$salt$hash",
                    is_admin=True,
                    is_active=True
                )
                db.session.add(default_admin)
                db.session.commit()
                result["admin_user_created"] = True
            except Exception:
                pass
        
        # 嘗試導入數據（如果有導出文件）
        import os
        json_files = [f for f in os.listdir('.') if f.startswith('database_export') and f.endswith('.json')]
        
        if json_files:
            try:
                import json
                json_file = sorted(json_files)[-1]
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 快速導入關鍵數據
                imported_count = 0
                
                # 導入持有人
                for holder_data in data.get('holders', []):
                    if not Holder.query.filter_by(name=holder_data['name']).first():
                        holder = Holder(name=holder_data['name'], is_active=True)
                        db.session.add(holder)
                        imported_count += 1
                
                db.session.commit()
                
                # 導入現金帳戶
                for account_data in data.get('cash_accounts', []):
                    if not CashAccount.query.filter_by(name=account_data['name']).first():
                        holder = Holder.query.filter_by(name=account_data.get('holder_name')).first()
                        account = CashAccount(
                            name=account_data['name'],
                            currency=account_data['currency'],
                            balance=account_data.get('balance', 0.0),
                            holder_id=holder.id if holder else None
                        )
                        db.session.add(account)
                        imported_count += 1
                
                db.session.commit()
                result["data_imported"] = imported_count
                result["import_file"] = json_file
                
            except Exception as import_error:
                result["import_error"] = str(import_error)
        
        return jsonify({
            "status": "success",
            "message": "數據庫修復完成",
            "details": result
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error", 
            "message": f"修復失敗: {str(e)}"
        }), 500


@app.route("/debug_database.html", methods=["GET"])
def debug_database_page():
    """資料庫診斷頁面"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>資料庫診斷</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .info { background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .error { background: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <h1> 資料庫診斷</h1>
        <div id="result"></div>
        <button onclick="diagnose()">開始診斷</button>
    </div>

    <script>
        async function diagnose() {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '<div class="info">正在診斷...</div>';
            
            try {
                const response = await fetch('/api/debug_database');
                const data = await response.json();
                
                let html = '<h3> 診斷結果：</h3>';
                
                if (data.database_type) {
                    html += `<div class="info"><strong>資料庫類型：</strong> ${data.database_type}</div>`;
                }
                
                if (data.database_url) {
                    html += `<div class="info"><strong>資料庫URL：</strong> ${data.database_url}</div>`;
                }
                
                if (data.tables_count !== undefined) {
                    html += `<div class="info"><strong>資料表數量：</strong> ${data.tables_count}</div>`;
                }
                
                if (data.records_count) {
                    html += '<div class="info"><strong>記錄數量：</strong>';
                    for (const [table, count] of Object.entries(data.records_count)) {
                        html += `<br>${table}: ${count} 筆`;
                    }
                    html += '</div>';
                }
                
                if (data.environment) {
                    html += `<div class="info"><strong>環境變數：</strong><pre>${JSON.stringify(data.environment, null, 2)}</pre></div>`;
                }
                
                if (data.error) {
                    html += `<div class="error"><strong>錯誤：</strong> ${data.error}</div>`;
                }
                
                resultDiv.innerHTML = html;
                
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">診斷失敗: ${error.message}</div>`;
            }
        }
    </script>
</body>
</html>'''


@app.route("/api/debug_database", methods=["GET"])
def debug_database_api():
    """資料庫診斷API"""
    try:
        result = {}
        
        # 檢查資料庫類型
        database_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'postgresql' in database_url or 'postgres' in database_url:
            result['database_type'] = 'PostgreSQL'
        elif 'sqlite' in database_url:
            result['database_type'] = 'SQLite'
        else:
            result['database_type'] = 'Unknown'
        
        # 資料庫URL（隱藏敏感資訊）
        if database_url:
            if 'postgresql' in database_url:
                # 隱藏密碼
                import re
                masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', database_url)
                result['database_url'] = masked_url
            else:
                result['database_url'] = database_url
        
        # 檢查環境變數
        result['environment'] = {
            'DATABASE_URL_SET': bool(os.environ.get('DATABASE_URL')),
            'SECRET_KEY_SET': bool(os.environ.get('SECRET_KEY')),
            'RENDER_SERVICE_ID': os.environ.get('RENDER_SERVICE_ID', 'Not Set'),
        }
        
        # 檢查資料表
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        result['tables_count'] = len(tables)
        result['tables'] = tables
        
        # 檢查記錄數量
        records_count = {}
        try:
            records_count['users'] = db.session.execute(db.text('SELECT COUNT(*) FROM user')).scalar()
            records_count['holders'] = db.session.execute(db.text('SELECT COUNT(*) FROM holders')).scalar()
            records_count['cash_accounts'] = db.session.execute(db.text('SELECT COUNT(*) FROM cash_accounts')).scalar()
            records_count['sales_records'] = db.session.execute(db.text('SELECT COUNT(*) FROM sales_records')).scalar()
        except Exception as e:
            records_count['error'] = str(e)
        
        result['records_count'] = records_count
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/import_data.html", methods=["GET"])
def import_data_page():
    """提供數據導入頁面"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>數據庫導入 - Render</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        button { padding: 15px 30px; background: #28a745; color: white; border: none; cursor: pointer; font-size: 16px; border-radius: 5px; margin: 10px; }
        button:hover { background: #218838; }
        button:disabled { background: #6c757d; cursor: not-allowed; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; max-height: 400px; border: 1px solid #dee2e6; }
        .status { margin: 15px 0; padding: 15px; border-radius: 5px; font-weight: bold; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        h1 { color: #343a40; text-align: center; }
        .stats { display: flex; flex-wrap: wrap; gap: 15px; margin: 20px 0; }
        .stat-card { flex: 1; min-width: 150px; padding: 15px; background: #e9ecef; border-radius: 5px; text-align: center; }
        .stat-number { font-size: 24px; font-weight: bold; color: #007bff; }
        .stat-label { font-size: 12px; color: #6c757d; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="container">
        <h1> 數據庫同步 - Render部署</h1>
        
        <div class="info">
            <strong>說明：</strong>此工具會將您的本地數據庫數據導入到Render的雲端數據庫中，確保兩邊數據同步。
        </div>
        
        <button onclick="importData()" id="importBtn">🚀 開始導入數據</button>
        
        <div id="status"></div>
        <div id="result"></div>
    </div>

    <script>
        async function importData() {
            const statusDiv = document.getElementById('status');
            const resultDiv = document.getElementById('result');
            const importBtn = document.getElementById('importBtn');
            
            // 禁用按鈕
            importBtn.disabled = true;
            importBtn.textContent = '⏳ 正在導入...';
            
            statusDiv.innerHTML = '<div class="status info"> 正在導入數據，請稍候...</div>';
            resultDiv.innerHTML = '';
            
            try {
                const response = await fetch('/api/import_database', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const data = await response.json();
                
                if (response.ok && data.status === 'success') {
                    // 顯示成功信息
                    statusDiv.innerHTML = '<div class="status success"> 數據導入成功完成！</div>';
                    
                    // 顯示統計信息
                    const stats = data.statistics;
                    const totalData = data.total_data;
                    
                    resultDiv.innerHTML = `
                        <h3> 導入統計：</h3>
                        <div class="stats">
                            <div class="stat-card">
                                <div class="stat-number">${stats.users_imported}</div>
                                <div class="stat-label">新增用戶</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.holders_imported}</div>
                                <div class="stat-label">新增持有人</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.accounts_imported}</div>
                                <div class="stat-label">新增帳戶</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.customers_imported}</div>
                                <div class="stat-label">新增客戶</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.channels_imported}</div>
                                <div class="stat-label">新增渠道</div>
                            </div>
                        </div>
                        
                        <h3> 更新統計：</h3>
                        <div class="stats">
                            <div class="stat-card">
                                <div class="stat-number">${stats.accounts_updated}</div>
                                <div class="stat-label">帳戶餘額更新</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${stats.customers_updated}</div>
                                <div class="stat-label">客戶應收更新</div>
                            </div>
                        </div>
                        
                        <div class="success">
                            <strong>導入完成！</strong><br>
                            使用文件: ${data.file_used}<br>
                            現在您可以訪問您的應用程式，應該能看到本地的所有數據了！
                        </div>
                        
                        <h3>📋 詳細結果：</h3>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    `;
                    
                } else {
                    statusDiv.innerHTML = `<div class="status error"> 導入失敗: ${data.error || '未知錯誤'}</div>`;
                    if (data.error) {
                        resultDiv.innerHTML = `<pre>錯誤詳情: ${data.error}</pre>`;
                    }
                }
                
            } catch (error) {
                statusDiv.innerHTML = `<div class="status error"> 請求失敗: ${error.message}</div>`;
                resultDiv.innerHTML = `<pre>錯誤詳情: ${error.stack}</pre>`;
            } finally {
                // 重新啟用按鈕
                importBtn.disabled = false;
                importBtn.textContent = '🚀 開始導入數據';
            }
        }
    </script>
</body>
</html>'''


@app.route("/api/customer", methods=["POST", "DELETE"])
@login_required
def manage_customer():
    """客戶管理API - 仿照manage_channel的邏輯"""
    data = request.get_json()
    if request.method == "POST":
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"status": "error", "message": "客戶名稱不可為空"}), 400
        if Customer.query.filter_by(name=name).first():
            return jsonify({"status": "error", "message": "此客戶已存在"}), 409

        new_customer = Customer(name=name, is_active=True)
        db.session.add(new_customer)
        db.session.commit()
        return jsonify(
            {
                "status": "success",
                "message": "客戶新增成功",
                "customer": {"id": new_customer.id, "name": new_customer.name},
            }
        )




    if request.method == "DELETE":
        customer_id = data.get("id")
        customer = db.session.get(Customer, customer_id)
        if not customer:
            return jsonify({"status": "error", "message": "找不到該客戶"}), 404

        # 軟刪除
        customer.is_active = False
        db.session.commit()
        return jsonify({"status": "success", "message": "客戶已刪除"})


# API 1: 獲取現金管理的總資產數據，用於實時更新
@app.route("/api/cash_management/transactions", methods=["GET"])
@login_required  
def get_cash_management_transactions():
    """獲取現金管理的分頁流水記錄（優化版本）"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 50)  # 限制每頁最多50筆
        
        print(f"DEBUG: 現金管理API請求 - 頁碼: {page}, 每頁: {per_page}")
        
        # 優化：限制查詢數量，避免一次性載入所有數據
        limit = per_page * 5  # 增加查詢數量以確保包含所有記錄類型
        
        # 獲取流水記錄數據（限制數量）
        purchases = db.session.execute(
            db.select(PurchaseRecord)
            .options(
                db.selectinload(PurchaseRecord.payment_account),
                db.selectinload(PurchaseRecord.deposit_account),
                db.selectinload(PurchaseRecord.channel)
            )
            .order_by(PurchaseRecord.purchase_date.desc())
            .limit(limit)
        ).scalars().all()
        
        sales = db.session.execute(
            db.select(SalesRecord)
            .options(
                db.selectinload(SalesRecord.customer),
                db.selectinload(SalesRecord.rmb_account)
            )
            .order_by(SalesRecord.created_at.desc())
            .limit(limit)
        ).scalars().all()
        
        print(f"DEBUG: 查詢到 {len(purchases)} 筆買入記錄, {len(sales)} 筆銷售記錄")
        
        # 安全地查詢 LedgerEntry，處理可能缺少的欄位
        try:
            misc_entries = db.session.execute(
                db.select(LedgerEntry)
                .options(db.selectinload(LedgerEntry.account))
            ).scalars().all()
        except Exception as e:
            if "profit_before does not exist" in str(e):
                print("警告: ledger_entries 表格缺少利潤欄位，跳過查詢")
                db.session.rollback()  # 回滾失敗的事務
                misc_entries = []
                db.session.begin()  # 開始新事務
            else:
                db.session.rollback()  # 回滾失敗的事務
                raise e
        
        # 確保在乾淨的事務中查詢 cash_logs
        try:
            cash_logs = db.session.execute(db.select(CashLog)).scalars().all()
        except Exception as e:
            print(f"警告: cash_logs 查詢失敗: {e}")
            db.session.rollback()
            cash_logs = []

        unified_stream = []
        
        # 處理買入記錄
        for p in purchases:
            if p.payment_account and p.deposit_account:
                channel_name = "未知渠道"
                if p.channel:
                    channel_name = p.channel.name
                elif hasattr(p, 'channel_name_manual') and p.channel_name_manual:
                    channel_name = p.channel_name_manual
                
                # 計算出款戶餘額變化
                payment_balance_before = p.payment_account.balance + p.twd_cost
                payment_balance_after = p.payment_account.balance
                payment_balance_change = -p.twd_cost
                
                # 計算入款戶餘額變化
                deposit_balance_before = p.deposit_account.balance - p.rmb_amount
                deposit_balance_after = p.deposit_account.balance
                deposit_balance_change = p.rmb_amount
                
                unified_stream.append({
                    "type": "買入",
                    "date": p.purchase_date.isoformat(),
                    "description": f"向 {channel_name} 買入",
                    "twd_change": -p.twd_cost,
                    "rmb_change": p.rmb_amount,
                    "operator": p.operator.username if p.operator else "未知",
                    "payment_account": p.payment_account.name if p.payment_account else "N/A",
                    "deposit_account": p.deposit_account.name if p.deposit_account else "N/A",
                    "note": p.note if hasattr(p, 'note') and p.note else None,
                    # 新增：出款戶餘額變化
                    "payment_account_balance": {
                        "before": payment_balance_before,
                        "change": payment_balance_change,
                        "after": payment_balance_after
                    },
                    # 新增：入款戶餘額變化
                    "deposit_account_balance": {
                        "before": deposit_balance_before,
                        "change": deposit_balance_change,
                        "after": deposit_balance_after
                    }
                })

        # 優化：批量計算所有銷售的利潤，避免重複計算
        print("DEBUG: 開始批量計算銷售利潤...")
        
        # 預計算所有銷售的利潤
        sales_profits = {}
        running_profit = 0.0
        
        # 按時間順序處理銷售記錄
        sorted_sales = sorted(sales, key=lambda x: x.created_at)
        
        for s in sorted_sales:
            if s.customer:
                try:
                    profit_info = FIFOService.calculate_profit_for_sale(s)
                    profit = profit_info['profit_twd'] if profit_info else 0
                    
                    # 計算變動前的利潤（累積）
                    profit_before = running_profit
                    running_profit += profit
                    profit_after = running_profit
                    
                    sales_profits[s.id] = {
                        'profit': profit,
                        'profit_before': profit_before,
                        'profit_after': profit_after
                    }
                    
                except Exception as e:
                    print(f"DEBUG: 計算銷售{s.id}利潤失敗: {e}")
                    sales_profits[s.id] = {
                        'profit': 0,
                        'profit_before': running_profit,
                        'profit_after': running_profit
                    }
        
        print(f"DEBUG: 批量計算完成，處理了 {len(sales_profits)} 筆銷售記錄")
        
        # 處理售出記錄
        for s in sales:
            if s.customer:
                # 使用預計算的利潤數據
                profit_data = sales_profits.get(s.id, {'profit': 0, 'profit_before': 0, 'profit_after': 0})
                profit = profit_data['profit']
                profit_before = profit_data['profit_before']
                profit_after = profit_data['profit_after']
                
                # 計算RMB帳戶餘額變化
                rmb_balance_before = s.rmb_account.balance + s.rmb_amount if s.rmb_account else 0
                rmb_balance_after = s.rmb_account.balance if s.rmb_account else 0
                rmb_balance_change = -s.rmb_amount
                
                unified_stream.append({
                    "type": "售出",
                    "date": s.created_at.isoformat(),
                    "description": f"售予 {s.customer.name}",
                    "twd_change": 0,  # 售出時TWD變動為0，不直接影響總台幣金額
                    "rmb_change": -s.rmb_amount,  # RMB變動：售出金額
                    "operator": s.operator.username if s.operator else "未知",
                    "profit": profit,
                    "payment_account": s.rmb_account.name if s.rmb_account else "N/A",  # 出款戶：RMB帳戶
                    "deposit_account": "應收帳款",  # 入款戶：應收帳款
                    "note": s.note if hasattr(s, 'note') and s.note else None,
                    # 出款戶餘額變化（RMB帳戶）：售出金額
                    "payment_account_balance": {
                        "before": rmb_balance_before,
                        "change": rmb_balance_change,  # -s.rmb_amount
                        "after": rmb_balance_after
                    },
                    # 入款戶餘額變化（應收帳款）：應收帳款之變動
                    "deposit_account_balance": {
                        "before": 0,  # 應收帳款變動前
                        "change": s.twd_amount,  # 應收帳款增加（台幣金額）
                        "after": s.twd_amount  # 應收帳款變動後
                    },
                    # 利潤變動記錄
                    "profit_change": profit,  # 利潤之變動
                    "profit_change_detail": {
                        "before": profit_before,
                        "change": profit,
                        "after": profit_after
                    }
                })

        # 處理其他記帳記錄（包含利潤提款）
        for entry in misc_entries:
            if entry.entry_type not in ["BUY_IN_DEBIT", "BUY_IN_CREDIT", "SETTLEMENT"]:
                twd_change = 0
                rmb_change = 0
                
                if entry.account and entry.account.currency == "TWD":
                    if entry.entry_type in ["DEPOSIT", "TRANSFER_IN", "SETTLEMENT"]:
                        twd_change = entry.amount
                    else:
                        twd_change = -entry.amount
                elif entry.account and entry.account.currency == "RMB":
                    rmb_change = (
                        entry.amount
                        if entry.entry_type in ["DEPOSIT", "TRANSFER_IN"]
                        else -entry.amount
                    )

                # 設置出入款帳戶
                payment_account = "N/A"
                deposit_account = "N/A"
                
                if entry.entry_type in ["DEPOSIT"]:
                    payment_account = "外部存款"
                    deposit_account = entry.account.name if entry.account else "N/A"
                elif entry.entry_type in ["WITHDRAW"]:
                    payment_account = entry.account.name if entry.account else "N/A"
                    deposit_account = "外部提款"
                elif entry.entry_type in ["TRANSFER_OUT"]:
                    payment_account = entry.account.name if entry.account else "N/A"
                    if "轉出至" in entry.description:
                        deposit_account = entry.description.replace("轉出至 ", "")
                    else:
                        deposit_account = "N/A"
                elif entry.entry_type in ["TRANSFER_IN"]:
                    deposit_account = entry.account.name if entry.account else "N/A"
                    if "從" in entry.description and "轉入" in entry.description:
                        payment_account = entry.description.replace("從 ", "").replace(" 轉入", "")
                    else:
                        payment_account = "N/A"
                elif entry.entry_type in ["PROFIT_WITHDRAW"]:
                    payment_account = "系統利潤"
                    deposit_account = "利潤提款"

                # 計算帳戶餘額變化
                payment_account_balance = None
                deposit_account_balance = None
                
                if entry.account:
                    # 計算當前帳戶的餘額變化
                    if entry.entry_type in ["DEPOSIT", "TRANSFER_IN", "SETTLEMENT"]:
                        # 增加餘額的交易
                        account_balance_before = entry.account.balance - entry.amount
                        account_balance_after = entry.account.balance
                        account_balance_change = entry.amount
                    else:
                        # 減少餘額的交易
                        account_balance_before = entry.account.balance + entry.amount
                        account_balance_after = entry.account.balance
                        account_balance_change = -entry.amount
                    
                    # 根據交易類型設置對應的帳戶餘額變化
                    if entry.entry_type in ["DEPOSIT", "TRANSFER_IN", "SETTLEMENT"]:
                        # 入款戶餘額變化
                        deposit_account_balance = {
                            "before": account_balance_before,
                            "change": account_balance_change,
                            "after": account_balance_after
                        }
                    elif entry.entry_type in ["WITHDRAW", "TRANSFER_OUT"]:
                        # 出款戶餘額變化
                        payment_account_balance = {
                            "before": account_balance_before,
                            "change": account_balance_change,
                            "after": account_balance_after
                        }
                    elif entry.entry_type in ["PROFIT_WITHDRAW"]:
                        # 利潤提款不影響帳戶餘額
                        pass
                
                # 構建基本記錄
                record = {
                    "type": entry.entry_type,
                    "date": entry.entry_date.isoformat(),
                    "description": entry.description,
                    "twd_change": twd_change,
                    "rmb_change": rmb_change,
                    "operator": entry.operator.username if entry.operator else "未知",
                    "payment_account": payment_account,
                    "deposit_account": deposit_account,
                    "note": getattr(entry, 'note', None),
                }
                
                # 添加帳戶餘額變化信息
                if payment_account_balance:
                    record["payment_account_balance"] = payment_account_balance
                if deposit_account_balance:
                    record["deposit_account_balance"] = deposit_account_balance
                
                # 如果是利潤相關記錄，添加詳細利潤信息
                if entry.entry_type == "PROFIT_WITHDRAW":
                    # 安全地獲取利潤詳細信息（處理欄位可能不存在的情況）
                    profit_before = getattr(entry, 'profit_before', None)
                    profit_after = getattr(entry, 'profit_after', None)
                    profit_change = getattr(entry, 'profit_change', None)
                    
                    # 為利潤提款設置特殊的類型顯示和金額變化
                    record["type"] = "利潤提款"
                    record["twd_change"] = -abs(entry.amount)  # 利潤提款的金額變化（負數）
                    
                    record["profit_before"] = profit_before
                    record["profit_after"] = profit_after
                    record["profit_change"] = profit_change
                    record["profit"] = profit_change  # 保持向後兼容
                    
                    # 新增：詳細的利潤變動記錄
                    record["profit_change_detail"] = {
                        "before": profit_before,
                        "change": profit_change,
                        "after": profit_after,
                        "description": "利潤提款"
                    }
                elif entry.entry_type == "PROFIT_EARNED":
                    # 利潤入庫記錄處理
                    profit_before = getattr(entry, 'profit_before', None)
                    profit_after = getattr(entry, 'profit_after', None)
                    profit_change = getattr(entry, 'profit_change', None)
                    
                    # 設置利潤入庫的顯示
                    record["type"] = "利潤入庫"
                    record["twd_change"] = 0  # 利潤入庫不直接影響TWD餘額
                    record["rmb_change"] = 0  # 利潤入庫不直接影響RMB餘額
                    
                    # 設置出款戶和入款戶
                    record["payment_account"] = "系統利潤"
                    record["deposit_account"] = "利潤帳戶"
                    
                    # 利潤變動信息
                    record["profit_before"] = profit_before
                    record["profit_after"] = profit_after
                    record["profit_change"] = profit_change
                    record["profit"] = profit_change
                    
                    # 詳細的利潤變動記錄
                    record["profit_change_detail"] = {
                        "before": profit_before,
                        "change": profit_change,
                        "after": profit_after,
                        "description": "售出利潤"
                    }
                
                unified_stream.append(record)

        # 處理現金日誌記錄
        for log in cash_logs:
            if log.type != "BUY_IN":
                twd_change = 0
                rmb_change = 0
                
                if log.type == "CARD_PURCHASE":
                    twd_change = -log.amount
                    payment_account = "刷卡"
                    deposit_account = "N/A"
                elif log.type == "SETTLEMENT":
                    twd_change = log.amount
                    payment_account = "客戶付款"
                    deposit_account = "N/A"
                    
                    # 查找對應的LedgerEntry來獲取帳戶信息
                    matching_entry = None
                    for entry in misc_entries:
                        if (entry.entry_type == "SETTLEMENT" and 
                            entry.description == log.description and
                            abs((entry.entry_date - log.time).total_seconds()) < 30):  # 放寬時間範圍到30秒
                            matching_entry = entry
                            break
                    
                    # 如果還是找不到，嘗試通過金額和時間匹配
                    if not matching_entry:
                        for entry in misc_entries:
                            if (entry.entry_type == "SETTLEMENT" and 
                                abs(entry.amount - log.amount) < 0.01 and  # 金額匹配
                                abs((entry.entry_date - log.time).total_seconds()) < 60):  # 1分鐘內
                                matching_entry = entry
                                break
                    
                    if matching_entry and matching_entry.account:
                        deposit_account = matching_entry.account.name
                    else:
                        deposit_account = "現金帳戶"
                else:
                    payment_account = "N/A"
                    deposit_account = "N/A"

                # 構建基本記錄
                record = {
                    "type": log.type,
                    "date": log.time.isoformat(),
                    "description": log.description,
                    "twd_change": twd_change,
                    "rmb_change": rmb_change,
                    "operator": log.operator.username if log.operator else "未知",
                    "payment_account": payment_account,
                    "deposit_account": deposit_account,
                    "note": getattr(log, 'note', None),
                }
                
                # 添加帳戶餘額變化信息（針對SETTLEMENT類型）
                if log.type == "SETTLEMENT":
                    if matching_entry and matching_entry.account:
                        # 使用找到的 LedgerEntry 對應的帳戶
                        account_balance_before = matching_entry.account.balance - twd_change
                        account_balance_after = matching_entry.account.balance
                        record["account_balance"] = {
                            "before": account_balance_before,
                            "change": twd_change,
                            "after": account_balance_after
                        }
                        # 同時添加入款戶餘額變化信息
                        record["deposit_account_balance"] = {
                            "before": account_balance_before,
                            "change": twd_change,
                            "after": account_balance_after,
                            "account_name": matching_entry.account.name
                        }
                    else:
                        # 如果找不到對應的 LedgerEntry，嘗試從描述中推斷帳戶
                        # 或者使用默認的帳戶餘額變化計算
                        record["account_balance"] = {
                            "before": 0.0,  # 暫時設為0，需要進一步優化
                            "change": twd_change,
                            "after": twd_change
                        }
                        record["deposit_account_balance"] = {
                            "before": 0.0,
                            "change": twd_change,
                            "after": twd_change,
                            "account_name": deposit_account
                        }
                
                unified_stream.append(record)

        # 按日期排序（新的在前）
        unified_stream.sort(key=lambda x: x["date"], reverse=True)
        
        # 獲取所有帳戶
        all_accounts_obj = (
            db.session.execute(db.select(CashAccount).order_by(CashAccount.holder_id))
            .scalars()
            .all()
        )
        
        # 計算當前實際的帳戶總餘額
        actual_total_twd = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "TWD"
        )
        actual_total_rmb = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "RMB"
        )
        
        # 計算累積餘額（從實際餘額開始倒推）
        running_twd_balance = actual_total_twd
        running_rmb_balance = actual_total_rmb
        
        # 從最新的交易開始，向前倒推每筆交易前的餘額
        for record in unified_stream:
            # 記錄此筆交易後的餘額（當前累積餘額）
            record["running_twd_balance"] = running_twd_balance
            record["running_rmb_balance"] = running_rmb_balance
            
            # 計算此筆交易前的餘額（為下一筆交易準備）
            running_twd_balance -= (record.get("twd_change", 0) or 0)
            running_rmb_balance -= (record.get("rmb_change", 0) or 0)
        
        # 重新按日期倒序排列（新的在前）
        unified_stream.sort(key=lambda x: x["date"], reverse=True)
        
        # 計算分頁
        total_records = len(unified_stream)
        total_pages = (total_records + per_page - 1) // per_page
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_records = unified_stream[start_index:end_index]

        return jsonify({
            "status": "success",
            "data": {
                "transactions": paginated_records,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_records": total_records,
                    "per_page": per_page,
                    "has_prev": page > 1,
                    "has_next": page < total_pages
                }
            }
        })
    
    except Exception as e:
        print(f"獲取分頁流水記錄時出錯: {e}")
        return jsonify({"status": "error", "message": f"系統錯誤: {str(e)}"}), 500


@app.route("/api/cash_management/transactions_simple", methods=["GET"])
@login_required  
def get_cash_management_transactions_simple():
    """獲取現金管理的簡化流水記錄（快速版本）"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 20)  # 限制更少
        
        print(f"DEBUG: 簡化API請求 - 頁碼: {page}, 每頁: {per_page}")
        
        # 增加查詢數量以確保包含所有記錄類型
        limit = per_page * 3
        
        # 獲取最近的銷售記錄
        sales = db.session.execute(
            db.select(SalesRecord)
            .options(
                db.selectinload(SalesRecord.customer),
                db.selectinload(SalesRecord.rmb_account)
            )
            .order_by(SalesRecord.created_at.desc())
            .limit(limit)
        ).scalars().all()
        
        # 獲取最近的買入記錄
        purchases = db.session.execute(
            db.select(PurchaseRecord)
            .options(
                db.selectinload(PurchaseRecord.payment_account),
                db.selectinload(PurchaseRecord.deposit_account),
                db.selectinload(PurchaseRecord.channel)
            )
            .order_by(PurchaseRecord.purchase_date.desc())
            .limit(limit)
        ).scalars().all()
        
        # 獲取最近的LedgerEntry記錄（包含內部轉帳等）
        try:
            misc_entries = db.session.execute(
                db.select(LedgerEntry)
                .options(db.selectinload(LedgerEntry.account))
                .order_by(LedgerEntry.entry_date.desc())
                .limit(limit)
            ).scalars().all()
        except Exception as e:
            print(f"DEBUG: 簡化API查詢LedgerEntry失敗: {e}")
            misc_entries = []
        
        unified_stream = []
        
        # 處理買入記錄（簡化版）
        for p in purchases:
            if p.payment_account and p.deposit_account:
                channel_name = "未知渠道"
                if p.channel:
                    channel_name = p.channel.name
                elif hasattr(p, 'channel_name_manual') and p.channel_name_manual:
                    channel_name = p.channel_name_manual
                
                unified_stream.append({
                    "type": "買入",
                    "date": p.purchase_date.isoformat(),
                    "description": f"向 {channel_name} 買入",
                    "twd_change": -p.twd_cost,
                    "rmb_change": p.rmb_amount,
                    "operator": p.operator.username if p.operator else "未知",
                    "payment_account": p.payment_account.name if p.payment_account else "N/A",
                    "deposit_account": p.deposit_account.name if p.deposit_account else "N/A",
                    "note": p.note if hasattr(p, 'note') and p.note else None,
                    "profit": 0,  # 買入不產生利潤
                    "profit_change_detail": None
                })
        
        # 處理銷售記錄（簡化版，不計算複雜的利潤變動）
        for s in sales:
            if s.customer:
                # 簡化利潤計算
                try:
                    profit_info = FIFOService.calculate_profit_for_sale(s)
                    profit = profit_info['profit_twd'] if profit_info else 0
                except Exception as e:
                    print(f"DEBUG: 簡化API計算銷售{s.id}利潤失敗: {e}")
                    profit = 0
                
                # 計算RMB帳戶餘額變化
                rmb_balance_before = s.rmb_account.balance + s.rmb_amount if s.rmb_account else 0
                rmb_balance_after = s.rmb_account.balance if s.rmb_account else 0
                rmb_balance_change = -s.rmb_amount
                
                unified_stream.append({
                    "type": "售出",
                    "date": s.created_at.isoformat(),
                    "description": f"售予 {s.customer.name}",
                    "twd_change": 0,  # 售出時TWD變動為0，不直接影響總台幣金額
                    "rmb_change": -s.rmb_amount,  # RMB變動：售出金額
                    "operator": s.operator.username if s.operator else "未知",
                    "profit": profit,
                    "payment_account": s.rmb_account.name if s.rmb_account else "N/A",  # 出款戶：RMB帳戶
                    "deposit_account": "應收帳款",  # 入款戶：應收帳款
                    "note": s.note if hasattr(s, 'note') and s.note else None,
                    # 出款戶餘額變化（RMB帳戶）：售出金額
                    "payment_account_balance": {
                        "before": rmb_balance_before,
                        "change": rmb_balance_change,  # -s.rmb_amount
                        "after": rmb_balance_after
                    },
                    # 入款戶餘額變化（應收帳款）：應收帳款之變動
                    "deposit_account_balance": {
                        "before": 0,  # 應收帳款變動前
                        "change": s.twd_amount,  # 應收帳款增加（台幣金額）
                        "after": s.twd_amount  # 應收帳款變動後
                    },
                    "profit_change_detail": {
                        "before": 0,  # 簡化處理
                        "change": profit,
                        "after": profit
                    }
                })
        
        # 處理LedgerEntry記錄（簡化版）
        for entry in misc_entries:
            if entry.entry_type not in ["BUY_IN_DEBIT", "BUY_IN_CREDIT", "SETTLEMENT"]:
                twd_change = 0
                rmb_change = 0
                
                if entry.account and entry.account.currency == "TWD":
                    if entry.entry_type in ["DEPOSIT", "TRANSFER_IN", "SETTLEMENT"]:
                        twd_change = entry.amount
                    else:
                        twd_change = -entry.amount
                elif entry.account and entry.account.currency == "RMB":
                    rmb_change = (
                        entry.amount
                        if entry.entry_type in ["DEPOSIT", "TRANSFER_IN"]
                        else -entry.amount
                    )
                
                # 設置出入款帳戶
                payment_account = "N/A"
                deposit_account = "N/A"
                
                if entry.entry_type in ["DEPOSIT"]:
                    payment_account = "外部存款"
                    deposit_account = entry.account.name if entry.account else "N/A"
                elif entry.entry_type in ["WITHDRAW"]:
                    payment_account = entry.account.name if entry.account else "N/A"
                    deposit_account = "外部提款"
                elif entry.entry_type in ["TRANSFER_OUT"]:
                    payment_account = entry.account.name if entry.account else "N/A"
                    if "轉出至" in entry.description:
                        deposit_account = entry.description.replace("轉出至 ", "")
                    else:
                        deposit_account = "N/A"
                elif entry.entry_type in ["TRANSFER_IN"]:
                    deposit_account = entry.account.name if entry.account else "N/A"
                    if "從" in entry.description and "轉入" in entry.description:
                        payment_account = entry.description.replace("從 ", "").replace(" 轉入", "")
                    else:
                        payment_account = "N/A"
                elif entry.entry_type in ["PROFIT_WITHDRAW"]:
                    payment_account = "系統利潤"
                    deposit_account = "利潤提款"
                elif entry.entry_type in ["PROFIT_EARNED"]:
                    payment_account = "系統利潤"
                    deposit_account = "利潤帳戶"
                
                # 計算帳戶餘額變化（簡化版）
                payment_account_balance = None
                deposit_account_balance = None
                
                if entry.account:
                    if entry.entry_type in ["DEPOSIT", "TRANSFER_IN", "SETTLEMENT"]:
                        account_balance_before = entry.account.balance - entry.amount
                        account_balance_after = entry.account.balance
                        account_balance_change = entry.amount
                        deposit_account_balance = {
                            "before": account_balance_before,
                            "change": account_balance_change,
                            "after": account_balance_after
                        }
                    elif entry.entry_type in ["WITHDRAW", "TRANSFER_OUT"]:
                        account_balance_before = entry.account.balance + entry.amount
                        account_balance_after = entry.account.balance
                        account_balance_change = -entry.amount
                        payment_account_balance = {
                            "before": account_balance_before,
                            "change": account_balance_change,
                            "after": account_balance_after
                        }
                
                record = {
                    "type": entry.entry_type,
                    "date": entry.entry_date.isoformat(),
                    "description": entry.description,
                    "twd_change": twd_change,
                    "rmb_change": rmb_change,
                    "operator": entry.operator.username if entry.operator else "未知",
                    "payment_account": payment_account,
                    "deposit_account": deposit_account,
                    "note": getattr(entry, 'note', None),
                }
                
                # 添加帳戶餘額變化信息
                if payment_account_balance:
                    record["payment_account_balance"] = payment_account_balance
                if deposit_account_balance:
                    record["deposit_account_balance"] = deposit_account_balance
                
                # 如果是利潤相關記錄，添加詳細利潤信息
                if entry.entry_type == "PROFIT_EARNED":
                    # 利潤入庫記錄處理
                    profit_before = getattr(entry, 'profit_before', None)
                    profit_after = getattr(entry, 'profit_after', None)
                    profit_change = getattr(entry, 'profit_change', None)
                    
                    # 設置利潤入庫的顯示
                    record["type"] = "利潤入庫"
                    record["twd_change"] = 0  # 利潤入庫不直接影響TWD餘額
                    record["rmb_change"] = 0  # 利潤入庫不直接影響RMB餘額
                    
                    # 利潤變動信息
                    record["profit_before"] = profit_before
                    record["profit_after"] = profit_after
                    record["profit_change"] = profit_change
                    record["profit"] = profit_change
                    
                    # 詳細的利潤變動記錄
                    record["profit_change_detail"] = {
                        "before": profit_before,
                        "change": profit_change,
                        "after": profit_after,
                        "description": "售出利潤"
                    }
                
                unified_stream.append(record)
        
        # 按時間排序
        unified_stream.sort(key=lambda x: x['date'], reverse=True)
        
        # 分頁
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_records = unified_stream[start_idx:end_idx]
        
        print(f"DEBUG: 簡化API返回 {len(paginated_records)} 筆記錄")
        
        return jsonify({
            "status": "success",
            "data": {
                "records": paginated_records,
                "pagination": {
                    "current_page": page,
                    "per_page": per_page,
                    "total_count": len(unified_stream),
                    "total_pages": (len(unified_stream) + per_page - 1) // per_page,
                    "has_next": end_idx < len(unified_stream),
                    "has_prev": page > 1
                }
            }
        })
        
    except Exception as e:
        print(f"簡化API錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"系統錯誤: {str(e)}"}), 500


@app.route("/api/cash_management/totals", methods=["GET"])
@login_required
def get_cash_management_totals():
    """獲取現金管理的總資產數據，用於實時更新"""
    try:
        # 獲取所有現金帳戶
        all_accounts_obj = (
            db.session.execute(db.select(CashAccount).order_by(CashAccount.holder_id))
            .scalars()
            .all()
        )

        # 獲取所有交易記錄來計算累積餘額
        purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
        sales = db.session.execute(
            db.select(SalesRecord)
            .options(
                db.selectinload(SalesRecord.customer),
                db.selectinload(SalesRecord.rmb_account)
            )
        ).scalars().all()
        # 安全地查詢 LedgerEntry，處理可能缺少的欄位
        try:
            misc_entries = db.session.execute(
                db.select(LedgerEntry)
                .options(db.selectinload(LedgerEntry.account))
            ).scalars().all()
        except Exception as e:
            if "profit_before does not exist" in str(e):
                print("警告: ledger_entries 表格缺少利潤欄位，跳過查詢")
                db.session.rollback()  # 回滾失敗的事務
                misc_entries = []
                db.session.begin()  # 開始新事務
            else:
                db.session.rollback()  # 回滾失敗的事務
                raise e
        # 確保在乾淨的事務中查詢 cash_logs
        try:
            cash_logs = db.session.execute(db.select(CashLog)).scalars().all()
        except Exception as e:
            print(f"警告: cash_logs 查詢失敗: {e}")
            db.session.rollback()
            cash_logs = []

        # 構建統一的交易流
        unified_stream = []
        
        # 處理買入記錄
        for p in purchases:
            if p.payment_account and p.deposit_account:
                unified_stream.append({
                    "type": "買入",
                    "date": p.purchase_date.isoformat(),
                    "twd_change": -p.twd_cost,
                    "rmb_change": p.rmb_amount,
                })
        
        # 處理銷售記錄
        for s in sales:
            if s.customer:
                unified_stream.append({
                    "type": "售出",
                    "date": s.created_at.isoformat(),
                    "twd_change": 0,  # 售出不直接增加現金，而是增加應收帳款
                    "rmb_change": -s.rmb_amount,
                })
        
        # 處理其他記帳記錄
        for entry in misc_entries:
            if entry.entry_type not in ["BUY_IN_DEBIT", "BUY_IN_CREDIT"]:
                twd_change = 0
                rmb_change = 0
                
                if entry.account and entry.account.currency == "TWD":
                    if entry.entry_type in ["DEPOSIT", "TRANSFER_IN", "SETTLEMENT"]:
                        twd_change = entry.amount
                    else:
                        twd_change = -entry.amount
                elif entry.account and entry.account.currency == "RMB":
                    rmb_change = (
                        entry.amount
                        if entry.entry_type in ["DEPOSIT", "TRANSFER_IN"]
                        else -entry.amount
                    )
                
                unified_stream.append({
                    "type": entry.entry_type,
                    "date": entry.entry_date.isoformat(),
                    "twd_change": twd_change,
                    "rmb_change": rmb_change,
                })
        
        # 處理現金日誌記錄
        for log in cash_logs:
            if log.type != "BUY_IN":
                twd_change = 0
                rmb_change = 0
                
                if log.type == "CARD_PURCHASE":
                    twd_change = -log.amount
                elif log.type == "SETTLEMENT":
                    twd_change = log.amount
                
                unified_stream.append({
                    "type": log.type,
                    "date": log.time.isoformat(),
                    "twd_change": twd_change,
                    "rmb_change": rmb_change,
                })
        
        # 計算總資產
        total_twd = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "TWD"
        )
        total_rmb = sum(
            acc.balance for acc in all_accounts_obj if acc.currency == "RMB"
        )

        # 查詢應收帳款數據
        customers_with_receivables = (
            db.session.execute(
                db.select(Customer)
                .filter_by(is_active=True)
                .filter(Customer.total_receivables_twd > 0)
                .order_by(Customer.total_receivables_twd.desc())
            )
            .scalars()
            .all()
        )
        
        total_receivables = sum(c.total_receivables_twd for c in customers_with_receivables)

        return jsonify({
            'total_twd': float(total_twd),
            'total_rmb': float(total_rmb),
            'total_receivables_twd': float(total_receivables),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"獲取現金管理總資產數據時發生錯誤: {e}")
        return jsonify({'error': '獲取數據失敗'}), 500


@app.route("/user-management")
@admin_required  # 只有 admin 可以訪問這個頁面
def user_management():
    """使用者管理頁面"""
    try:
        # 查詢除了自己 (admin) 以外的所有使用者
        all_users = (
            db.session.execute(
                db.select(User).filter(User.username != "admin").order_by(User.username)
            )
            .scalars()
            .all()
        )

        return render_template("user_management.html", users=all_users)

    except Exception as e:
        flash(f"載入使用者管理頁面時發生錯誤: {e}", "danger")
        return render_template("user_management.html", users=[])


@app.route("/api/add-user", methods=["POST"])
@admin_required  # 只有 admin 可以執行這個操作
def api_add_user():
    """處理新增使用者的請求"""
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "無效的請求格式。"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    # --- 後端驗證 ---
    if not username or not password:
        return jsonify({"status": "error", "message": "用戶名和密碼皆為必填項。"}), 400

    if len(password) < 4:  # 增加一個簡單的密碼長度檢查
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "為安全起見，密碼長度至少需要 4 個字元。",
                }
            ),
            400,
        )

    if db.session.execute(
        db.select(User).filter_by(username=username)
    ).scalar_one_or_none():
        return (
            jsonify(
                {"status": "error", "message": f'用戶名 "{username}" 已經被註冊。'}
            ),
            409,
        )  # 409 Conflict

    try:
        new_user = User(username=username, role="operator")
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return jsonify(
            {"status": "success", "message": f'使用者 "{username}" 已成功創建！'}
        )

    except Exception as e:
        db.session.rollback()
        print(f"!! Error in api_add_user: {e}")
        return (
            jsonify({"status": "error", "message": "伺服器內部錯誤，新增失敗。"}),
            500,
        )


@app.route("/api/delete_user/<int:user_id>", methods=["DELETE"])
@admin_required  # 只有 admin 可以執行這個操作
def api_delete_user(user_id):
    """處理刪除使用者的請求"""
    try:
        # 查詢要刪除的使用者
        user_to_delete = db.session.get(User, user_id)
        
        if not user_to_delete:
            return jsonify({"status": "error", "message": "找不到指定的使用者。"}), 404
        
        # 防止刪除自己
        if user_to_delete.username == current_user.username:
            return jsonify({"status": "error", "message": "不能刪除自己的帳號。"}), 400
        
        # 防止刪除其他 admin 用戶
        if user_to_delete.role == "admin":
            return jsonify({"status": "error", "message": "不能刪除管理員帳號。"}), 400
        
        # 記錄刪除操作
        username = user_to_delete.username
        print(f"管理員 {current_user.username} 正在刪除使用者 {username}")
        
        # 執行刪除
        db.session.delete(user_to_delete)
        db.session.commit()

        return jsonify({
            "status": "success", 
            "message": f'使用者 "{username}" 已成功刪除！'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error", 
            "message": "伺服器內部錯誤，刪除失敗。"
        }), 500


# ===================================================================
# 7. 輔助函數
# ===================================================================

def calculate_account_balances_from_transactions(holders_obj, all_accounts_obj, unified_stream):
    """基於交易紀錄計算每個持有人的帳戶餘額，確保與總資產完全一致"""
    # 初始化持有人帳戶數據
    accounts_by_holder = {}
    for holder in holders_obj:
        accounts_by_holder[holder.id] = {
            "holder_name": holder.name,
            "accounts": [],
            "total_twd": 0,
            "total_rmb": 0,
        }
    
    # 為每個帳戶創建餘額追蹤器，從0開始
    account_balances = {}
    for acc in all_accounts_obj:
        account_balances[acc.id] = {
            'holder_id': acc.holder_id,
            'name': acc.name,
            'currency': acc.currency,
            'current_balance': 0  # 從0開始，基於交易紀錄計算
        }
    
    # 從最早的交易開始，向後累積計算每個帳戶的餘額
    # 注意：unified_stream 已經按日期排序（新的在前），所以需要反轉
    for transaction in reversed(unified_stream):
        payment_account = transaction.get('payment_account')
        deposit_account = transaction.get('deposit_account')
        twd_change = transaction.get('twd_change', 0) or 0
        rmb_change = transaction.get('rmb_change', 0) or 0
        
        # 處理出款帳戶（通常是減少餘額）
        if payment_account != 'N/A':
            for acc_id, acc_info in account_balances.items():
                if acc_info['name'] == payment_account:
                    if acc_info['currency'] == 'TWD' and twd_change != 0:
                        acc_info['current_balance'] += twd_change
                    elif acc_info['currency'] == 'RMB' and rmb_change != 0:
                        acc_info['current_balance'] += rmb_change
                    break
        
        # 處理入款帳戶（通常是增加餘額）
        if deposit_account != 'N/A':
            for acc_id, acc_info in account_balances.items():
                if acc_info['name'] == deposit_account:
                    if acc_info['currency'] == 'TWD' and twd_change != 0:
                        acc_info['current_balance'] += twd_change
                    elif acc_info['currency'] == 'RMB' and rmb_change != 0:
                        acc_info['current_balance'] += rmb_change
                    break
        
        # 特殊處理：如果沒有明確的出款/入款帳戶，但有金額變動
        # 這通常發生在現金日誌或記帳記錄中
        if payment_account == 'N/A' and deposit_account == 'N/A':
            # 根據交易類型推斷影響的帳戶
            if transaction.get('type') == 'SETTLEMENT':
                # 銷帳：TWD增加，影響TWD帳戶
                for acc_id, acc_info in account_balances.items():
                    if acc_info['currency'] == 'TWD':
                        acc_info['current_balance'] += twd_change
                        break
            elif transaction.get('type') == 'DEPOSIT':
                # 存款：根據幣種影響對應帳戶
                if twd_change != 0:
                    for acc_id, acc_info in account_balances.items():
                        if acc_info['currency'] == 'TWD':
                            acc_info['current_balance'] += twd_change
                            break
                if rmb_change != 0:
                    for acc_id, acc_info in account_balances.items():
                        if acc_info['currency'] == 'RMB':
                            acc_info['current_balance'] += rmb_change
                            break
    
    # 構建 accounts_by_holder 數據結構
    for acc_id, acc_info in account_balances.items():
        holder_id = acc_info['holder_id']
        if holder_id in accounts_by_holder:
            # 添加帳戶信息
            accounts_by_holder[holder_id]["accounts"].append({
                "id": acc_id,
                "name": acc_info['name'],
                "currency": acc_info['currency'],
                "balance": acc_info['current_balance'],  # 使用基於交易紀錄計算的餘額
            })
            
            # 累計持有人總餘額
            if acc_info['currency'] == "TWD":
                accounts_by_holder[holder_id]["total_twd"] += acc_info['current_balance']
            elif acc_info['currency'] == "RMB":
                accounts_by_holder[holder_id]["total_rmb"] += acc_info['current_balance']
    
    return accounts_by_holder


def get_account_balances_for_dropdowns():
    """獲取基於交易紀錄的帳戶餘額，供下拉選單使用"""
    try:
        # 獲取所有持有人和帳戶
        holders_obj = (
            db.session.execute(db.select(Holder).filter_by(is_active=True))
            .scalars()
            .all()
        )
        all_accounts_obj = (
            db.session.execute(db.select(CashAccount).order_by(CashAccount.holder_id))
            .scalars()
            .all()
        )

        # 獲取所有交易記錄
        purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
        sales = db.session.execute(
            db.select(SalesRecord)
            .options(
                db.selectinload(SalesRecord.customer),
                db.selectinload(SalesRecord.rmb_account)
            )
        ).scalars().all()
        # 安全地查詢 LedgerEntry，處理可能缺少的欄位
        try:
            misc_entries = db.session.execute(
                db.select(LedgerEntry)
                .options(db.selectinload(LedgerEntry.account))
            ).scalars().all()
        except Exception as e:
            if "profit_before does not exist" in str(e):
                print("警告: ledger_entries 表格缺少利潤欄位，跳過查詢")
                db.session.rollback()  # 回滾失敗的事務
                misc_entries = []
                db.session.begin()  # 開始新事務
            else:
                db.session.rollback()  # 回滾失敗的事務
                raise e
        # 確保在乾淨的事務中查詢 cash_logs
        try:
            cash_logs = db.session.execute(db.select(CashLog)).scalars().all()
        except Exception as e:
            print(f"警告: cash_logs 查詢失敗: {e}")
            db.session.rollback()
            cash_logs = []

        # 構建統一的交易流
        unified_stream = []
        
        # 處理買入記錄
        for p in purchases:
            if p.payment_account and p.deposit_account:
                unified_stream.append({
                    "type": "買入",
                    "date": p.purchase_date.isoformat(),
                    "twd_change": -p.twd_cost,
                    "rmb_change": p.rmb_amount,
                    "payment_account": p.payment_account.name,
                    "deposit_account": p.deposit_account.name,
                })
        
        # 處理銷售記錄
        for s in sales:
            if s.customer:
                unified_stream.append({
                    "type": "售出",
                    "date": s.created_at.isoformat(),
                    "twd_change": 0,  # 售出不直接增加現金，而是增加應收帳款
                    "rmb_change": -s.rmb_amount,
                    "payment_account": "N/A",
                    "deposit_account": "N/A",
                })
        
        # 處理其他記帳記錄
        for entry in misc_entries:
            if entry.entry_type not in ["BUY_IN_DEBIT", "BUY_IN_CREDIT"]:
                twd_change = 0
                rmb_change = 0
                
                if entry.account and entry.account.currency == "TWD":
                    if entry.entry_type in ["DEPOSIT", "TRANSFER_IN", "SETTLEMENT"]:
                        twd_change = entry.amount
                    else:
                        twd_change = -entry.amount
                elif entry.account and entry.account.currency == "RMB":
                    rmb_change = (
                        entry.amount
                        if entry.entry_type in ["DEPOSIT", "TRANSFER_IN"]
                        else -entry.amount
                    )
                
                unified_stream.append({
                    "type": entry.entry_type,
                    "date": entry.entry_date.isoformat(),
                    "twd_change": twd_change,
                    "rmb_change": rmb_change,
                    "payment_account": entry.account.name if entry.account else "N/A",
                    "deposit_account": "N/A",
                })
        
        # 處理現金日誌記錄
        for log in cash_logs:
            if log.type != "BUY_IN":
                twd_change = 0
                rmb_change = 0
                
                if log.type == "CARD_PURCHASE":
                    twd_change = -log.amount
                elif log.type == "SETTLEMENT":
                    twd_change = log.amount
                
                unified_stream.append({
                    "type": log.type,
                    "date": log.time.isoformat(),
                    "twd_change": twd_change,
                    "rmb_change": rmb_change,
                    "payment_account": "N/A",
                    "deposit_account": "N/A",
                })
        
        # 按日期排序並計算累積餘額
        unified_stream.sort(key=lambda x: x["date"], reverse=True)
        
        # 為每個帳戶創建餘額追蹤器，從0開始
        account_balances = {}
        for acc in all_accounts_obj:
            account_balances[acc.id] = {
                'holder_id': acc.holder_id,
                'name': acc.name,
                'currency': acc.currency,
                'current_balance': 0  # 從0開始，基於交易紀錄計算
            }
        
        # 從最早的交易開始，向後累積計算每個帳戶的餘額
        for transaction in reversed(unified_stream):
            payment_account = transaction.get('payment_account')
            deposit_account = transaction.get('deposit_account')
            twd_change = transaction.get('twd_change', 0) or 0
            rmb_change = transaction.get('rmb_change', 0) or 0
            
            # 處理出款帳戶（通常是減少餘額）
            if payment_account != 'N/A':
                for acc_id, acc_info in account_balances.items():
                    if acc_info['name'] == payment_account:
                        if acc_info['currency'] == 'TWD' and twd_change != 0:
                            acc_info['current_balance'] += twd_change
                        elif acc_info['currency'] == 'RMB' and rmb_change != 0:
                            acc_info['current_balance'] += rmb_change
                            break
                    
            # 處理入款帳戶（通常是增加餘額）
            if deposit_account != 'N/A':
                for acc_id, acc_info in account_balances.items():
                    if acc_info['name'] == deposit_account:
                        if acc_info['currency'] == 'TWD' and twd_change != 0:
                            acc_info['current_balance'] += twd_change
                        elif acc_info['currency'] == 'RMB' and rmb_change != 0:
                            acc_info['current_balance'] += rmb_change
                        break
            
            # 特殊處理：如果沒有明確的出款/入款帳戶，但有金額變動
            if payment_account == 'N/A' and deposit_account == 'N/A':
                if transaction.get('type') == 'SETTLEMENT':
                    # 銷帳：TWD增加，影響TWD帳戶
                    for acc_id, acc_info in account_balances.items():
                        if acc_info['currency'] == 'TWD':
                            acc_info['current_balance'] += twd_change
                            break
                elif transaction.get('type') == 'DEPOSIT':
                    # 存款：根據幣種影響對應帳戶
                    if twd_change != 0:
                        for acc_id, acc_info in account_balances.items():
                            if acc_info['currency'] == 'TWD':
                                acc_info['current_balance'] += twd_change
                                break
                    if rmb_change != 0:
                        for acc_id, acc_info in account_balances.items():
                            if acc_info['currency'] == 'RMB':
                                acc_info['current_balance'] += rmb_change
                                break
        
        # 構建分組的帳戶數據
        owner_twd_accounts_grouped = []
        owner_rmb_accounts_grouped = []
        
        for holder in holders_obj:
            twd_accs = []
            rmb_accs = []
            
            for acc in all_accounts_obj:
                if acc.holder_id == holder.id and acc.is_active:
                    # 使用基於交易紀錄計算的餘額
                    current_balance = account_balances.get(acc.id, {}).get('current_balance', 0)
                    
                    if acc.currency == "TWD":
                        twd_accs.append({
                            "id": acc.id,
                            "name": acc.name,
                            "balance": float(current_balance),
                            "currency": acc.currency,
                            "is_active": acc.is_active
                        })
                    elif acc.currency == "RMB":
                        rmb_accs.append({
                            "id": acc.id,
                            "name": acc.name,
                            "balance": float(current_balance),
                            "currency": acc.currency,
                            "is_active": acc.is_active
                        })
            
            if twd_accs:
                owner_twd_accounts_grouped.append({
                    "holder_name": holder.name, 
                    "accounts": twd_accs
                })
            if rmb_accs:
                owner_rmb_accounts_grouped.append({
                    "holder_name": holder.name, 
                    "accounts": rmb_accs
                })
        
        return owner_twd_accounts_grouped, owner_rmb_accounts_grouped
        
    except Exception as e:
        print(f"獲取帳戶餘額時發生錯誤: {e}")
        return [], []


def get_accurate_account_balances():
    """獲取準確的帳戶餘額，使用帳戶ID匹配，確保計算準確性"""
    try:
        # 獲取所有持有人和帳戶
        holders_obj = (
            db.session.execute(db.select(Holder).filter_by(is_active=True))
            .scalars()
            .all()
        )
        all_accounts_obj = (
            db.session.execute(db.select(CashAccount).order_by(CashAccount.holder_id))
            .scalars()
            .all()
        )

        # 獲取所有交易記錄
        purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
        sales = db.session.execute(
            db.select(SalesRecord)
            .options(
                db.selectinload(SalesRecord.customer),
                db.selectinload(SalesRecord.rmb_account)
            )
        ).scalars().all()
        # 安全地查詢 LedgerEntry，處理可能缺少的欄位
        try:
            misc_entries = db.session.execute(
                db.select(LedgerEntry)
                .options(db.selectinload(LedgerEntry.account))
            ).scalars().all()
        except Exception as e:
            if "profit_before does not exist" in str(e):
                print("警告: ledger_entries 表格缺少利潤欄位，跳過查詢")
                db.session.rollback()  # 回滾失敗的事務
                misc_entries = []
                db.session.begin()  # 開始新事務
            else:
                db.session.rollback()  # 回滾失敗的事務
                raise e
        # 確保在乾淨的事務中查詢 cash_logs
        try:
            cash_logs = db.session.execute(db.select(CashLog)).scalars().all()
        except Exception as e:
            print(f"警告: cash_logs 查詢失敗: {e}")
            db.session.rollback()
            cash_logs = []

        # 構建統一的交易流，使用帳戶ID而不是名稱
        unified_stream = []
        
        # 處理買入記錄
        for p in purchases:
            if p.payment_account and p.deposit_account:
                unified_stream.append({
                    "type": "買入",
                    "date": p.purchase_date.isoformat(),
                    "twd_change": -p.twd_cost,
                    "rmb_change": p.rmb_amount,
                    "payment_account_id": p.payment_account.id,
                    "deposit_account_id": p.deposit_account.id,
                    "payment_account_name": p.payment_account.name,
                    "deposit_account_name": p.deposit_account.name,
                })
        
        # 處理銷售記錄
        for s in sales:
            if s.customer:
                unified_stream.append({
                    "type": "售出",
                    "date": s.created_at.isoformat(),
                    "twd_change": 0,  # 售出不直接增加現金，而是增加應收帳款
                    "rmb_change": -s.rmb_amount,
                    "payment_account_id": None,
                    "deposit_account_id": None,
                    "payment_account_name": "N/A",
                    "deposit_account_name": "N/A",
                })
        
        # 處理其他記帳記錄
        for entry in misc_entries:
            if entry.entry_type not in ["BUY_IN_DEBIT", "BUY_IN_CREDIT"]:
                twd_change = 0
                rmb_change = 0
                
                if entry.account and entry.account.currency == "TWD":
                    if entry.entry_type in ["DEPOSIT", "TRANSFER_IN", "SETTLEMENT"]:
                        twd_change = entry.amount
                    else:
                        twd_change = -entry.amount
                elif entry.account and entry.account.currency == "RMB":
                    rmb_change = (
                        entry.amount
                        if entry.entry_type in ["DEPOSIT", "TRANSFER_IN"]
                        else -entry.amount
                    )
                
                unified_stream.append({
                    "type": entry.entry_type,
                    "date": entry.entry_date.isoformat(),
                    "twd_change": twd_change,
                    "rmb_change": rmb_change,
                    "payment_account_id": entry.account.id if entry.account else None,
                    "deposit_account_id": None,
                    "payment_account_name": entry.account.name if entry.account else "N/A",
                    "deposit_account_name": "N/A",
                })
        
        # 處理現金日誌記錄
        for log in cash_logs:
            if log.type != "BUY_IN":
                twd_change = 0
                rmb_change = 0
                
                if log.type == "CARD_PURCHASE":
                    twd_change = -log.amount
                elif log.type == "SETTLEMENT":
                    twd_change = log.amount
                
                unified_stream.append({
                    "type": log.type,
                    "date": log.time.isoformat(),
                    "twd_change": twd_change,
                    "rmb_change": rmb_change,
                    "payment_account_id": None,
                    "deposit_account_id": None,
                    "payment_account_name": "N/A",
                    "deposit_account_name": "N/A",
                })
        
        # 按日期排序（從舊到新）
        unified_stream.sort(key=lambda x: x["date"])
        
        # 為每個帳戶創建餘額追蹤器，從0開始
        account_balances = {}
        for acc in all_accounts_obj:
            account_balances[acc.id] = {
                'holder_id': acc.holder_id,
                'name': acc.name,
                'currency': acc.currency,
                'current_balance': 0  # 從0開始，基於交易紀錄計算
            }
        
        print(f"調試：開始處理 {len(unified_stream)} 筆交易...")
        
        # 按時間順序處理每筆交易，累積計算每個帳戶的餘額
        for i, transaction in enumerate(unified_stream):
            payment_account_id = transaction.get('payment_account_id')
            deposit_account_id = transaction.get('deposit_account_id')
            twd_change = transaction.get('twd_change', 0) or 0
            rmb_change = transaction.get('rmb_change', 0) or 0
            
            # 處理出款帳戶（通常是減少餘額）
            if payment_account_id and payment_account_id in account_balances:
                acc_info = account_balances[payment_account_id]
                if acc_info['currency'] == 'TWD' and twd_change != 0:
                    old_balance = acc_info['current_balance']
                    acc_info['current_balance'] += twd_change
                    print(f" 交易 {i+1}: {acc_info['name']} TWD {old_balance:,.2f} -> {acc_info['current_balance']:,.2f} (變動: {twd_change:,.2f})")
                elif acc_info['currency'] == 'RMB' and rmb_change != 0:
                    old_balance = acc_info['current_balance']
                    acc_info['current_balance'] += rmb_change
                    print(f" 交易 {i+1}: {acc_info['name']} RMB {old_balance:,.2f} -> {acc_info['current_balance']:,.2f} (變動: {rmb_change:,.2f})")
            
            # 處理入款帳戶（通常是增加餘額）
            if deposit_account_id and deposit_account_id in account_balances:
                acc_info = account_balances[deposit_account_id]
                if acc_info['currency'] == 'TWD' and twd_change != 0:
                    old_balance = acc_info['current_balance']
                    acc_info['current_balance'] += twd_change
                    print(f" 交易 {i+1}: {acc_info['name']} TWD {old_balance:,.2f} -> {acc_info['current_balance']:,.2f} (變動: {twd_change:,.2f})")
                elif acc_info['currency'] == 'RMB' and rmb_change != 0:
                    old_balance = acc_info['current_balance']
                    acc_info['current_balance'] += rmb_change
                    print(f" 交易 {i+1}: {acc_info['name']} RMB {old_balance:,.2f} -> {acc_info['current_balance']:,.2f} (變動: {rmb_change:,.2f})")
            
            # 特殊處理：如果沒有明確的出款/入款帳戶，但有金額變動
            if not payment_account_id and not deposit_account_id:
                if transaction.get('type') == 'SETTLEMENT':
                    # 銷帳：TWD增加，影響第一個TWD帳戶
                    for acc_id, acc_info in account_balances.items():
                        if acc_info['currency'] == 'TWD':
                            acc_info['current_balance'] += twd_change
                            break
                elif transaction.get('type') == 'DEPOSIT':
                    # 存款：根據幣種影響對應帳戶
                    if twd_change != 0:
                        for acc_id, acc_info in account_balances.items():
                            if acc_info['currency'] == 'TWD':
                                acc_info['current_balance'] += twd_change
                                break
                    if rmb_change != 0:
                        for acc_id, acc_info in account_balances.items():
                            if acc_info['currency'] == 'RMB':
                                acc_info['current_balance'] += rmb_change
                                break
        
        # 構建分組的帳戶數據
        owner_twd_accounts_grouped = []
        owner_rmb_accounts_grouped = []
        
        for holder in holders_obj:
            twd_accs = []
            rmb_accs = []
            
            for acc in all_accounts_obj:
                if acc.holder_id == holder.id and acc.is_active:
                    # 使用基於交易紀錄計算的餘額
                    current_balance = account_balances.get(acc.id, {}).get('current_balance', 0)
                    
                    if acc.currency == "TWD":
                        twd_accs.append({
                            "id": acc.id,
                            "name": acc.name,
                            "balance": float(current_balance),
                            "currency": acc.currency,
                            "is_active": acc.is_active
                        })
                    elif acc.currency == "RMB":
                        rmb_accs.append({
                            "id": acc.id,
                            "name": acc.name,
                            "balance": float(current_balance),
                            "currency": acc.currency,
                            "is_active": acc.is_active
                        })
            
            if twd_accs:
                owner_twd_accounts_grouped.append({
                    "holder_name": holder.name, 
                    "accounts": twd_accs
                })
            if rmb_accs:
                owner_rmb_accounts_grouped.append({
                    "holder_name": holder.name, 
                    "accounts": rmb_accs
                })
        
        return owner_twd_accounts_grouped, owner_rmb_accounts_grouped
        
    except Exception as e:
        print(f"獲取準確帳戶餘額時發生錯誤: {e}")
        return [], []


# ===================================================================
# 8. 數據修復 API 路由
# ===================================================================

@app.route("/api/admin/data-recovery", methods=["POST"])
def remote_data_recovery():
    """遠程數據修復 API 端點"""
    try:
        # 檢查是否有管理員權限（這裡可以根據您的權限系統調整）
        # 例如檢查 session 或 token
        
        print(" 開始遠程數據修復...")
        
        # 檢查資料庫連接
        try:
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            print(" 資料庫連接正常")
        except Exception as db_error:
            print(f"資料庫連接失敗: {db_error}")
            return jsonify({
                "status": "error",
                "message": f"資料庫連接失敗: {str(db_error)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 1. 修復庫存數據（基於實際的 FIFOInventory 結構）
        print("📦 修復庫存數據...")
        try:
            inventories = FIFOInventory.query.all()
            print(f"找到 {len(inventories)} 個庫存批次")
        except Exception as inv_error:
            print(f"查詢庫存數據失敗: {inv_error}")
            return jsonify({
                "status": "error",
                "message": f"查詢庫存數據失敗: {str(inv_error)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        inventory_fixes = []
        for inventory in inventories:
            # 計算實際的已出帳數量（通過 FIFOSalesAllocation）
            actual_issued = db.session.query(func.sum(FIFOSalesAllocation.allocated_rmb)).filter(
                FIFOSalesAllocation.fifo_inventory_id == inventory.id
            ).scalar() or 0
            
            # 更新庫存記錄
            old_remaining = inventory.remaining_rmb
            
            # 基於實際分配計算剩餘數量
            inventory.remaining_rmb = inventory.rmb_amount - actual_issued
            
            inventory_fixes.append({
                "batch_id": inventory.id,
                "original": inventory.rmb_amount,
                "old_remaining": old_remaining,
                "new_remaining": inventory.remaining_rmb,
                "allocated_rmb": actual_issued
            })
        
        # 2. 修復現金帳戶餘額
        print(" 修復現金帳戶餘額...")
        try:
            cash_accounts = CashAccount.query.all()
            print(f"找到 {len(cash_accounts)} 個現金帳戶")
        except Exception as cash_error:
            print(f"查詢現金帳戶失敗: {cash_error}")
            return jsonify({
                "status": "error",
                "message": f"查詢現金帳戶失敗: {str(cash_error)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        account_fixes = []
        for account in cash_accounts:
            old_balance = account.balance
            
            if account.currency == "TWD":
                # TWD 帳戶餘額計算
                payment_amount = PurchaseRecord.query.filter(
                    PurchaseRecord.payment_account_id == account.id
                ).with_entities(func.sum(PurchaseRecord.twd_cost)).scalar() or 0
                
                ledger_debits = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.account_id == account.id,
                        LedgerEntry.entry_type.in_(['WITHDRAW', 'TRANSFER_OUT', 'CARD_PURCHASE'])
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                ledger_credits = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.account_id == account.id,
                        LedgerEntry.entry_type.in_(['DEPOSIT', 'TRANSFER_IN', 'SETTLEMENT'])
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                new_balance = 0 - payment_amount - ledger_debits + ledger_credits
                
            elif account.currency == "RMB":
                # RMB 帳戶餘額計算
                deposit_amount = PurchaseRecord.query.filter(
                    PurchaseRecord.deposit_account_id == account.id
                ).with_entities(func.sum(PurchaseRecord.rmb_amount)).scalar() or 0
                
                sales_amount = SalesRecord.query.filter(
                    SalesRecord.rmb_account_id == account.id
                ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                
                ledger_debits = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.account_id == account.id,
                        LedgerEntry.entry_type.in_(['WITHDRAW', 'TRANSFER_OUT'])
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                ledger_credits = LedgerEntry.query.filter(
                    and_(
                        LedgerEntry.account_id == account.id,
                        LedgerEntry.entry_type.in_(['DEPOSIT', 'TRANSFER_IN'])
                    )
                ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                
                new_balance = 0 + deposit_amount - sales_amount - ledger_debits + ledger_credits
            
            account.balance = new_balance
            
            account_fixes.append({
                "account_id": account.id,
                "account_name": account.name,
                "currency": account.currency,
                "old_balance": old_balance,
                "new_balance": new_balance
            })
        
        # 3. 修復客戶應收帳款
        print("📋 修復客戶應收帳款...")
        try:
            customers = Customer.query.all()
            print(f"找到 {len(customers)} 個客戶")
        except Exception as cust_error:
            print(f"查詢客戶數據失敗: {cust_error}")
            return jsonify({
                "status": "error",
                "message": f"查詢客戶數據失敗: {str(cust_error)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        customer_fixes = []
        for customer in customers:
            old_receivables = customer.total_receivables_twd
            
            # 總銷售金額
            total_sales = SalesRecord.query.filter(
                SalesRecord.customer_id == customer.id
            ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
            
            # 已收款金額 - 由於 LedgerEntry 沒有 customer_id 字段，暫時設為 0
            # TODO: 需要根據實際的數據結構來計算已收款金額
            received_amount = 0
            
            # 應收帳款餘額
            receivables_balance = total_sales - received_amount
            customer.total_receivables_twd = receivables_balance
            
            customer_fixes.append({
                "customer_id": customer.id,
                "customer_name": customer.name,
                "old_receivables": old_receivables,
                "new_receivables": receivables_balance,
                "total_sales": total_sales,
                "received_amount": received_amount
            })
        
        # 提交所有更改
        db.session.commit()
        
        # 4. 驗證修復結果
        total_original = FIFOInventory.query.with_entities(func.sum(FIFOInventory.rmb_amount)).scalar() or 0
        total_remaining = FIFOInventory.query.with_entities(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
        
        total_twd = CashAccount.query.filter_by(currency="TWD").with_entities(func.sum(CashAccount.balance)).scalar() or 0
        total_rmb = CashAccount.query.filter_by(currency="RMB").with_entities(func.sum(CashAccount.balance)).scalar() or 0
        
        total_receivables = Customer.query.with_entities(func.sum(Customer.total_receivables_twd)).scalar() or 0
        
        print(" 遠程數據修復完成！")
        
        return jsonify({
            "status": "success",
            "message": "數據修復完成",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "inventory_batches_fixed": len(inventory_fixes),
                "cash_accounts_fixed": len(account_fixes),
                "customers_fixed": len(customer_fixes)
            },
            "final_status": {
                "inventory": {
                    "total_original": total_original,
                    "total_remaining": total_remaining
                },
                "cash_accounts": {
                    "total_twd": total_twd,
                    "total_rmb": total_rmb
                },
                "receivables": total_receivables
            },
            "details": {
                "inventory_fixes": inventory_fixes,
                "account_fixes": account_fixes,
                "customer_fixes": customer_fixes
            }
        })

    except Exception as e:
        print(f"遠程數據修復失敗: {e}")
        traceback.print_exc()
        db.session.rollback()
        
        return jsonify({
            "status": "error",
            "message": f"數據修復失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

# 添加狀態檢查 API
@app.route("/api/admin/data-status", methods=["GET"])
def get_data_status():
    """獲取當前數據狀態"""
    try:
        # 庫存狀態
        total_inventories = FIFOInventory.query.count()
        total_original = FIFOInventory.query.with_entities(func.sum(FIFOInventory.rmb_amount)).scalar() or 0
        total_remaining = FIFOInventory.query.with_entities(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
        
        # 計算已分配數量
        total_allocated = db.session.query(func.sum(FIFOSalesAllocation.allocated_rmb)).scalar() or 0
        
        # 現金帳戶狀態
        twd_accounts = CashAccount.query.filter_by(currency="TWD").count()
        rmb_accounts = CashAccount.query.filter_by(currency="RMB").count()
        total_twd = CashAccount.query.filter_by(currency="TWD").with_entities(func.sum(CashAccount.balance)).scalar() or 0
        total_rmb = CashAccount.query.filter_by(currency="RMB").with_entities(func.sum(CashAccount.balance)).scalar() or 0
        
        # 客戶狀態
        total_customers = Customer.query.count()
        total_receivables = Customer.query.with_entities(func.sum(Customer.total_receivables_twd)).scalar() or 0
        
        return jsonify({
                "status": "success",
            "timestamp": datetime.now().isoformat(),
                "data": {
                "inventory": {
                    "total_batches": total_inventories,
                    "total_original": total_original,
                    "total_remaining": total_remaining,
                    "total_allocated": total_allocated,
                    "consistency_check": abs(total_original - total_allocated - total_remaining) < 0.01
                },
                "cash_accounts": {
                    "twd_accounts": twd_accounts,
                    "rmb_accounts": rmb_accounts,
                    "total_twd": total_twd,
                    "total_rmb": total_rmb
                },
                "customers": {
                    "total_customers": total_customers,
                    "total_receivables": total_receivables
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"獲取數據狀態失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

# 添加修復頁面路由
@app.route("/admin_data_recovery")
def admin_data_recovery():
    return render_template("admin_data_recovery.html")

# ===================================================================
# 臨時獨立頁面：儲值與餘額計算（前端本地儲存，與系統資料完全獨立）
# ===================================================================
@app.route("/independent-balance")
@login_required
def independent_balance():
    try:
        rmb_accounts = (
            db.session.execute(
                db.select(CashAccount).filter_by(currency="RMB", is_active=True).order_by(CashAccount.holder_id)
            )
            .scalars()
            .all()
        )
    except Exception:
        rmb_accounts = []
    return render_template("independent_balance.html", rmb_accounts=rmb_accounts)

# ===================================================================
# 9. 啟動器
# ===================================================================
if __name__ == "__main__":
    app.run(debug=True)
