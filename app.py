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
            
            print(f"🔍 檢查資料庫表格: {existing_tables}")
            
            if 'user' not in existing_tables:
                # 只有當表格不存在時才創建
                print("📝 創建資料庫表格...")
                db.create_all()
                print("✅ 資料庫表格已創建")
            else:
                print("✅ 資料庫表格已存在")
                
                # 檢查現有數據
                try:
                    user_count = User.query.count()
                    print(f"👥 現有用戶數量: {user_count}")
                    
                    if user_count > 0:
                        print("✅ 資料庫中已有數據，跳過初始化")
                        return
                except Exception as e:
                    print(f"⚠️  檢查用戶數據時出錯: {e}")
            
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
                print("✅ 預設管理員帳戶創建成功")
                print("   用戶名: admin")
                print("   密碼: admin123")
                print("   ⚠️  請在首次登入後立即修改密碼！")
            else:
                print("✅ 管理員帳戶已存在")
                
    except Exception as e:
        print(f"❌ 資料庫初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

# 使用 Flask 3.x 兼容的方式初始化資料庫
@app.before_request
def before_request():
    """在每個請求前檢查資料庫是否已初始化"""
    if not hasattr(app, '_database_initialized'):
        print("🚀 首次請求，初始化資料庫...")
        init_database()
        app._database_initialized = True
        print("✅ 資料庫初始化完成")
    else:
        print("✅ 資料庫已初始化，跳過")

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
    operator = db.relationship("User", backref="sales_records")
    rmb_account = db.relationship("CashAccount", foreign_keys=[rmb_account_id])
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
# 新增：刪除帳戶API端點
# ===================================================================

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
        
        # 只要帳戶餘額為0，就允許刪除，不再檢查帳本記錄
        # 這是根據用戶需求：只要帳戶內無金額即可刪除此帳戶
        
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
            print(f"❌ 刪除帳戶時出錯: {delete_error}")
            
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
        
        print(f"❌ 刪除帳戶時發生嚴重錯誤: {e}")
        return jsonify({"status": "error", "message": "刪除帳戶時發生嚴重錯誤，請稍後重試。"}), 500


# ===================================================================
# 啟動器
# ===================================================================
if __name__ == "__main__":
    app.run(debug=True)

