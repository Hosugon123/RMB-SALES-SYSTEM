import os
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
from datetime import datetime, date
from sqlalchemy import func

# ===================================================================
# 2. App、資料庫、遷移與登入管理器的初始化
# ===================================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "a_very_very_secret_key_that_is_long_and_secure"
)
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, "instance")
os.makedirs(instance_path, exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    instance_path, "sales_system_v4.db"
)  # 使用新檔名以示區別
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "請先登入以存取此頁面。"
login_manager.login_message_category = "info"

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
# FIFO 服務類
# ===================================================================

class FIFOService:
    """FIFO庫存管理服務類"""
    
    @staticmethod
    def create_inventory_from_purchase(purchase_record):
        """從買入記錄創建FIFO庫存"""
        try:
            # 計算單位成本（台幣）
            unit_cost_twd = purchase_record.twd_cost / purchase_record.rmb_amount
            
            # 創建FIFO庫存記錄
            fifo_inventory = FIFOInventory(
                purchase_record_id=purchase_record.id,
                rmb_amount=purchase_record.rmb_amount,
                remaining_rmb=purchase_record.rmb_amount,  # 初始時剩餘數量等於買入數量
                unit_cost_twd=unit_cost_twd,
                exchange_rate=purchase_record.exchange_rate,
                purchase_date=purchase_record.purchase_date
            )
            
            db.session.add(fifo_inventory)
            db.session.commit()
            
            print(f"✅ 已創建FIFO庫存記錄: {fifo_inventory}")
            return fifo_inventory
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 創建FIFO庫存失敗: {e}")
            raise
    
    @staticmethod
    def allocate_sales_to_inventory(sales_record, rmb_amount):
        """為銷售記錄分配FIFO庫存"""
        try:
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
                
                # 累計成本
                total_cost += allocation.allocated_cost_twd
                remaining_to_allocate -= allocate_from_this_batch
                
                allocations.append(allocation)
                db.session.add(allocation)
                
                print(f"📦 從庫存批次 {inventory.id} 分配 {allocate_from_this_batch} RMB，成本 {allocation.allocated_cost_twd} TWD")
            
            if remaining_to_allocate > 0:
                raise ValueError(f"庫存不足，還需要 {remaining_to_allocate} RMB")
            
            db.session.commit()
            print(f"✅ FIFO分配完成，總成本: {total_cost} TWD")
            
            return {
                'allocations': allocations,
                'total_cost': total_cost,
                'total_rmb': rmb_amount
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ FIFO分配失敗: {e}")
            raise
    
    @staticmethod
    def get_current_inventory():
        """獲取當前庫存狀態"""
        try:
            inventory = (
                db.session.execute(
                    db.select(FIFOInventory)
                    .filter(FIFOInventory.remaining_rmb > 0)
                    .order_by(FIFOInventory.purchase_date.asc())
                )
                .scalars()
                .all()
            )
            
            inventory_summary = []
            for inv in inventory:
                inventory_summary.append({
                    'id': inv.id,
                    'purchase_date': inv.purchase_date.strftime('%Y-%m-%d'),
                    'channel': inv.purchase_record.channel.name if inv.purchase_record.channel else 'N/A',
                    'original_rmb': inv.rmb_amount,
                    'remaining_rmb': inv.remaining_rmb,
                    'unit_cost_twd': inv.unit_cost_twd,
                    'exchange_rate': inv.exchange_rate,
                    'total_value_twd': inv.remaining_rmb * inv.unit_cost_twd
                })
            
            return inventory_summary
            
        except Exception as e:
            print(f"❌ 獲取庫存狀態失敗: {e}")
            return []
    
    @staticmethod
    def calculate_profit_for_sale(sales_record):
        """計算某筆銷售的利潤"""
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
                return None
            
            # 計算總成本
            total_cost = sum(allocation.allocated_cost_twd for allocation in allocations)
            
            # 計算利潤
            profit = sales_record.twd_amount - total_cost
            
            return {
                'sales_amount': sales_record.twd_amount,
                'total_cost': total_cost,
                'profit': profit,
                'profit_margin': (profit / sales_record.twd_amount * 100) if sales_record.twd_amount > 0 else 0,
                'allocations': [
                    {
                        'inventory_id': allocation.fifo_inventory_id,
                        'allocated_rmb': allocation.allocated_cost_twd,
                        'allocated_cost': allocation.allocated_cost_twd,
                        'purchase_date': allocation.fifo_inventory.purchase_date.strftime('%Y-%m-%d')
                    }
                    for allocation in allocations
                ]
            }
            
        except Exception as e:
            print(f"❌ 計算利潤失敗: {e}")
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
            url_for("admin_dashboard" if current_user.is_admin else "cash_management")
        )
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return redirect(url_for("index"))
        else:
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
@admin_required
def admin_dashboard():
    """儀表板頁面"""
    try:
        total_twd_cash = (
            db.session.execute(
                db.select(func.sum(CashAccount.balance)).filter(
                    CashAccount.currency == "TWD"
                )
            ).scalar()
            or 0.0
        )
        total_rmb_stock = (
            db.session.execute(
                db.select(func.sum(CashAccount.balance)).filter(
                    CashAccount.currency == "RMB"
                )
            ).scalar()
            or 0.0
        )

        latest_purchase = (
            db.session.execute(
                db.select(PurchaseRecord).order_by(PurchaseRecord.purchase_date.desc())
            )
            .scalars()
            .first()
        )
        current_buy_rate = latest_purchase.exchange_rate if latest_purchase else 4.5

        estimated_total_assets_twd = total_twd_cash + (
            total_rmb_stock * current_buy_rate
        )

        total_unsettled_amount_twd = (
            db.session.execute(
                db.select(func.sum(Customer.total_receivables_twd))
            ).scalar()
            or 0.0
        )
        chart_data = {
            "labels": ["台幣現金", "人民幣庫存(估值)"],
            "values": [total_twd_cash, (total_rmb_stock * current_buy_rate)],
        }

        return render_template(
            "admin.html",
            total_twd_cash=total_twd_cash,
            total_rmb_stock=total_rmb_stock,
            current_buy_rate=current_buy_rate,
            estimated_total_assets_twd=estimated_total_assets_twd,
            total_unsettled_amount_twd=total_unsettled_amount_twd,
            chart_data=chart_data,  # <--- 確保傳遞
        )
    except Exception as e:
        flash(f"載入儀表板數據時發生錯誤: {e}", "danger")
        # 在錯誤情況下，也要提供一個包含 chart_data 的預設上下文
        return render_template(
            "admin.html",
            total_twd_cash=0,
            total_rmb_stock=0,
            current_buy_rate=4.5,
            estimated_total_assets_twd=0,
            total_unsettled_amount_twd=0,
            chart_data={"labels": [], "values": []},  # <--- 確保傳遞
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

        owner_rmb_accounts_grouped = []
        for holder in holders_with_rmb_accounts:
            rmb_accs = [
                acc
                for acc in holder.cash_accounts
                if acc.currency == "RMB" and acc.is_active
            ]
            if rmb_accs:
                owner_rmb_accounts_grouped.append(
                    {"holder_name": holder.name, "accounts": rmb_accs}
                )

        # 3. 查詢最近 10 筆未結清 (is_settled = False) 的銷售紀錄
        recent_unsettled_sales = (
            db.session.execute(
                db.select(SalesRecord)
                .filter_by(is_settled=False)
                .order_by(SalesRecord.created_at.desc())
                .limit(10)
            )
            .scalars()
            .all()
        )

        # --- 將所有查詢到的資料傳遞給前端模板 ---
        return render_template(
            "sales_entry.html",
            customers=customers,
            owner_rmb_accounts_grouped=owner_rmb_accounts_grouped,
            recent_unsettled_sales=recent_unsettled_sales,
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

        # 更新帳戶和客戶餘額
        rmb_account.balance -= rmb_amount
        customer.total_receivables_twd += twd_amount

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
        db.session.commit()

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
        print(f"!!! Error in api_sales_entry: {e}")
        import traceback

        traceback.print_exc()
        return (
            jsonify({"status": "error", "message": "伺服器內部錯誤，操作失敗。"}),
            500,
        )


@app.route("/admin/cash_management")
@admin_required
def cash_management():
    try:
        page = request.args.get("page", 1, type=int)

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
                    }
                )
                if acc.currency == "TWD":
                    accounts_by_holder[acc.holder_id]["total_twd"] += acc.balance
                elif acc.currency == "RMB":
                    accounts_by_holder[acc.holder_id]["total_rmb"] += acc.balance

        purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
        sales = db.session.execute(db.select(SalesRecord)).scalars().all()
        misc_entries = db.session.execute(db.select(LedgerEntry)).scalars().all()
        cash_logs = db.session.execute(db.select(CashLog)).scalars().all()

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
                    }
                )
        for s in sales:
            if s.customer:
                unified_stream.append(
                    {
                        "type": "售出",
                        "date": s.created_at.isoformat(),
                        "description": f"售予 {s.customer.name}",
                        "twd_change": s.twd_amount,
                        "rmb_change": -s.rmb_amount,
                        "operator": s.operator.username if s.operator else "未知",
                    }
                )
        for entry in misc_entries:
            twd_change = 0
            rmb_change = 0
            
            # 優化：移除對BUY_IN_DEBIT和BUY_IN_CREDIT的特殊處理
            # 因為買入交易現在只使用PurchaseRecord，不需要額外的LedgerEntry
            
            # 處理其他類型的記帳記錄
            if entry.account and entry.account.currency == "TWD":
                twd_change = (
                    entry.amount
                    if entry.entry_type in ["DEPOSIT", "TRANSFER_IN"]
                    else -entry.amount
                )
            elif entry.account and entry.account.currency == "RMB":
                rmb_change = (
                    entry.amount
                    if entry.entry_type in ["DEPOSIT", "TRANSFER_IN"]
                    else -entry.amount
                )
            
            # 只顯示非買入相關的記帳記錄
            if entry.entry_type not in ["BUY_IN_DEBIT", "BUY_IN_CREDIT"]:
                unified_stream.append(
                    {
                        "type": entry.entry_type,
                        "date": entry.entry_date.isoformat(),
                        "description": entry.description,
                        "twd_change": twd_change,
                        "rmb_change": rmb_change,
                        "operator": entry.operator.username if entry.operator else "未知",
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
            else:
                # 其他類型的現金日誌
                twd_change = 0
                rmb_change = 0
            
            # 只顯示非買入相關的現金日誌
            if log.type != "BUY_IN":
                unified_stream.append(
                    {
                        "type": log.type,
                        "date": log.time.isoformat(),
                        "description": log.description,
                        "twd_change": twd_change,
                        "rmb_change": rmb_change,
                        "operator": log.operator.username if log.operator else "未知",
                    }
                )

        unified_stream.sort(key=lambda x: x["date"], reverse=True)

        per_page = 10
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

        # --- 關鍵修正：確保您傳遞的是正確的分頁後數據 ---
        return render_template(
            "cash_management.html",
            total_twd=total_twd,
            total_rmb=total_rmb,
            total_receivables=total_receivables,
            customers_with_receivables=customers_with_receivables,
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
                }
                for a in all_accounts_obj
            ],
        )
    except Exception as e:
        print(f"!!! 現金管理頁面發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        flash("載入現金管理數據時發生嚴重錯誤。", "danger")
        return render_template(
            "cash_management.html",
            total_twd=0,
            total_rmb=0,
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

        owner_twd_accounts_grouped = []
        owner_rmb_accounts_grouped = []
        for holder in holders_with_accounts:
            twd_accs = [
                {
                    "id": acc.id,
                    "name": acc.name,
                    "balance": float(acc.balance),
                    "currency": acc.currency,
                    "is_active": acc.is_active
                }
                for acc in holder.cash_accounts
                if acc.currency == "TWD" and acc.is_active
            ]
            rmb_accs = [
                {
                    "id": acc.id,
                    "name": acc.name,
                    "balance": float(acc.balance),
                    "currency": acc.currency,
                    "is_active": acc.is_active
                }
                for acc in holder.cash_accounts
                if acc.currency == "RMB" and acc.is_active
            ]

            if twd_accs:
                owner_twd_accounts_grouped.append(
                    {"holder_name": holder.name, "accounts": twd_accs}
                )
            if rmb_accs:
                owner_rmb_accounts_grouped.append(
                    {"holder_name": holder.name, "accounts": rmb_accs}
                )

        recent_purchases = (
            db.session.execute(
                db.select(PurchaseRecord)
                .options(
                    db.selectinload(PurchaseRecord.channel),
                    db.selectinload(PurchaseRecord.payment_account),
                    db.selectinload(PurchaseRecord.deposit_account),
                    db.selectinload(PurchaseRecord.operator)
                )
                .order_by(PurchaseRecord.purchase_date.desc())
                .limit(10)
            )
            .scalars()
            .all()
        )
        
        # 轉換為可序列化的格式
        recent_purchases_serializable = []
        for record in recent_purchases:
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
        )

    except Exception as e:
        flash(f"載入買入頁面時發生嚴重錯誤: {e}", "danger")
        # 即使出錯，也回傳一個安全的空頁面，避免程式崩潰
        return render_template(
            "buy_in.html",
            channels=[],
            owner_twd_accounts_grouped=[],
            owner_rmb_accounts_grouped=[],
            recent_purchases=[],
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
                payment_account_id = int(data.get("payment_account_id"))
                deposit_account_id = int(data.get("deposit_account_id"))
                rmb_amount = float(data.get("rmb_amount"))
                exchange_rate = float(data.get("exchange_rate"))
                channel_id = data.get("channel_id")  # 可能為空字符串、null或數字
                channel_name_manual = data.get("channel_name_manual", "").strip()
            except (ValueError, TypeError, AttributeError):
                return (
                    jsonify({"status": "error", "message": "輸入的資料格式不正確。"}),
                    400,
                )

            if not all(
                [
                    payment_account_id,
                    deposit_account_id,
                    rmb_amount > 0,
                    exchange_rate > 0,
                ]
            ):
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "所有帳戶和金額欄位都必須正確填寫。",
                        }
                    ),
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
            payment_account = db.session.get(CashAccount, payment_account_id)
            deposit_account = db.session.get(CashAccount, deposit_account_id)

            if not payment_account or payment_account.currency != "TWD":
                return (
                    jsonify({"status": "error", "message": "無效的 TWD 付款帳戶。"}),
                    400,
                )
            if not deposit_account or deposit_account.currency != "RMB":
                return (
                    jsonify({"status": "error", "message": "無效的 RMB 入庫帳戶。"}),
                    400,
                )

            # 3. 核心業務邏輯
            twd_cost = rmb_amount * exchange_rate
            if payment_account.balance < twd_cost:
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
            payment_account.balance -= twd_cost
            deposit_account.balance += rmb_amount

            # 創建採購紀錄
            new_purchase = PurchaseRecord(
                payment_account_id=payment_account.id,
                deposit_account_id=deposit_account.id,
                channel_id=final_channel_id,
                rmb_amount=rmb_amount,
                exchange_rate=exchange_rate,
                twd_cost=twd_cost,
                operator_id=current_user.id,  # <--- V4.0 核心功能！
            )
            db.session.add(new_purchase)
            db.session.flush()  # 立即獲取ID，以便創建FIFO庫存

            # 創建FIFO庫存記錄
            try:
                FIFOService.create_inventory_from_purchase(new_purchase)
                print(f"✅ 已為買入記錄 {new_purchase.id} 創建FIFO庫存")
            except Exception as e:
                print(f"❌ 創建FIFO庫存失敗: {e}")
                # 即使FIFO創建失敗，也不影響主要交易
                pass

            # 優化：移除重複的記帳記錄，只保留主要的PurchaseRecord
            # 因為PurchaseRecord已經包含了完整的交易信息，不需要額外的LedgerEntry和CashLog
            
            db.session.commit()

            return jsonify(
                {
                    "status": "success",
                    "message": f"交易成功！已從 {payment_account.name} 付款，並將 RMB 存入 {deposit_account.name}。",
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
        print(f"!!! Error in api_buy_in: {e}")  # 在後端印出詳細錯誤
        import traceback

        traceback.print_exc()
        return (
            jsonify({"status": "error", "message": "伺服器內部錯誤，操作失敗。"}),
            500,
        )


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
        customer = db.session.get(Holder, customer_id)
        twd_account = db.session.get(CashAccount, twd_account_id)

        # --- 2. 業務邏輯驗證 ---
        if not customer or customer.type != "CUSTOMER":
            return jsonify({"status": "error", "message": "無效的客戶 ID。"}), 404
        if not twd_account or customer.currency != "TWD":
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

        # 創建現金日誌記錄
        cash_log = CashLog(
            type="CUSTOMER_PAYMENT",
            description=f"客戶 {customer.name} 付款 {payment_amount:,.2f} TWD",
            amount=payment_amount,
            operator_id=current_user.id,
        )
        db.session.add(cash_log)

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
            transaction = Transaction(
                sales_record_id=sale.id,
                twd_account_id=twd_account.id,
                amount=settle_amount,
                note=f"客戶付款沖銷 - 訂單 #{sale.id}",
            )
            db.session.add(transaction)

        db.session.commit()

        # 準備回應訊息
        if settled_sales:
            settled_ids = [s.id for s in settled_sales]
            message = f"付款成功！已沖銷 {len(settled_sales)} 筆訂單 (ID: {', '.join(map(str, settled_ids))})"
        else:
            message = "付款成功！但沒有可沖銷的訂單。"

        return jsonify({"status": "success", "message": message})

    except Exception as e:
        db.session.rollback()
        print(f"!!! Error in process_payment_api: {e}")
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
        
        # 計算總庫存價值
        total_rmb = sum(item['remaining_rmb'] for item in inventory_data)
        total_value_twd = sum(item['total_value_twd'] for item in inventory_data)
        
        # 獲取最近的銷售記錄（用於展示利潤計算）
        recent_sales = (
            db.session.execute(
                db.select(SalesRecord)
                .options(db.selectinload(SalesRecord.customer))
                .order_by(SalesRecord.created_at.desc())
                .limit(10)
            )
            .scalars()
            .all()
        )
        
        # 計算每筆銷售的利潤
        sales_with_profit = []
        for sale in recent_sales:
            profit_info = FIFOService.calculate_profit_for_sale(sale)
            if profit_info:
                sales_with_profit.append({
                    'id': sale.id,
                    'customer_name': sale.customer.name if sale.customer else 'N/A',
                    'rmb_amount': sale.rmb_amount,
                    'twd_amount': sale.twd_amount,
                    'created_at': sale.created_at.strftime('%Y-%m-%d'),
                    'profit': profit_info['profit'],
                    'profit_margin': profit_info['profit_margin'],
                    'total_cost': profit_info['total_cost']
                })
        
        return render_template(
            "fifo_inventory.html",
            inventory_data=inventory_data,
            total_rmb=total_rmb,
            total_value_twd=total_value_twd,
            sales_with_profit=sales_with_profit
        )
        
    except Exception as e:
        flash(f"載入FIFO庫存頁面時發生錯誤: {e}", "danger")
        return render_template(
            "fifo_inventory.html",
            inventory_data=[],
            total_rmb=0,
            total_value_twd=0,
            sales_with_profit=[]
        )


@app.route("/admin/update_cash_account", methods=["POST"])
@admin_required
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
            return redirect(url_for('cash_management'))

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
            return redirect(url_for('cash_management'))

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
            account = db.session.get(CashAccount, account_id)
            if account:
                if is_decrease:
                    if account.balance < amount:
                        flash(f"餘額不足，無法提出 {amount}。", "danger")
                        return redirect(url_for('cash_management'))
                    else:
                        account.balance -= amount
                        entry = LedgerEntry(
                            entry_type="WITHDRAW",
                            account_id=account.id,
                            amount=amount,
                            description=f"外部提款",
                            operator_id=current_user.id,
                        )
                        db.session.add(entry)
                        db.session.commit()
                        flash(
                            f'已從 "{account.name}" 提出 {amount:,.2f}，並已記錄流水。',
                            "success",
                        )
                        return redirect(url_for('cash_management'))
                else:
                    account.balance += amount
                    entry = LedgerEntry(
                        entry_type="DEPOSIT",
                        account_id=account.id,
                        amount=amount,
                        description=f"外部存款",
                        operator_id=current_user.id,
                    )
                    db.session.add(entry)
                    db.session.commit()
                    flash(
                        f'已向 "{account.name}" 存入 {amount:,.2f}，並已記錄流水。',
                        "success",
                    )
                    return redirect(url_for('cash_management'))

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
                    return redirect(url_for('cash_management'))

        else:
            flash("未知的操作指令。", "warning")
            return redirect(url_for('cash_management'))

    except Exception as e:
        db.session.rollback()
        print(f"!!! 現金帳戶更新失敗: {e}")
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
        print(f"!!! 買入 API 發生錯誤: {e}")
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


@app.route("/add_customer_ajax", methods=["POST"])
@admin_required
def add_customer_ajax():
    data = request.get_json()
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"status": "error", "message": "未提供用戶名"}), 400

    # 我們假設客戶也是一種 Holder
    existing_user = Holder.query.filter_by(name=username).first()
    if existing_user:
        return jsonify({"status": "error", "message": "此客戶名稱已存在"}), 409

    new_customer = Holder(name=username)
    db.session.add(new_customer)
    db.session.commit()

    customer_data = {"id": new_customer.id, "username": new_customer.name}
    return jsonify(
        {"status": "success", "message": "客戶新增成功", "customer": customer_data}
    )


@app.route("/delete_customer_ajax", methods=["POST"])
@admin_required
def delete_customer_ajax():
    data = request.get_json()
    customer_id = data.get("customer_id")

    customer_to_deactivate = db.session.get(Holder, int(customer_id))
    if not customer_to_deactivate:
        return jsonify({"status": "error", "message": "找不到該客戶"}), 404

    customer_to_deactivate.is_active = False  # 軟刪除
    db.session.commit()

    return jsonify({"status": "success", "message": "客戶已從常用列表移除"})


@app.route("/api/customers/frequent", methods=["GET"])
@login_required
def get_frequent_customers():
    """獲取常用客戶列表"""
    try:
        # 獲取所有活躍的客戶（常用客戶）
        frequent_customers = (
            db.session.execute(
                db.select(Customer).filter_by(is_active=True).order_by(Customer.name)
            )
            .scalars()
            .all()
        )
        
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
        if not account or account.currency != "TWD":
            return jsonify({"status": "error", "message": "無效的台幣收款帳戶。"}), 400
        if amount > customer.total_receivables_twd:
            return jsonify({"status": "error", "message": f"銷帳金額超過應收帳款！客戶應收 {customer.total_receivables_twd:,.2f}，但銷帳 {amount:,.2f}。"}), 400

        # 3. 核心業務邏輯
        # 更新客戶應收帳款
        customer.total_receivables_twd -= amount
        
        # 更新收款帳戶餘額
        account.balance += amount
        
        # 創建銷帳記錄
        settlement_entry = LedgerEntry(
            account_id=account.id,
            entry_type="SETTLEMENT",
            amount=amount,
            entry_date=datetime.utcnow(),
            description=f"客戶「{customer.name}」銷帳收款 - {note}" if note else f"客戶「{customer.name}」銷帳收款",
            operator_id=current_user.id
        )
        db.session.add(settlement_entry)
        
        # 創建現金日誌記錄
        cash_log = CashLog(
            type="SETTLEMENT",
            amount=amount,
            time=datetime.utcnow(),
            description=f"客戶「{customer.name}」銷帳收款 - {note}" if note else f"客戶「{customer.name}」銷帳收款",
            operator_id=current_user.id
        )
        db.session.add(cash_log)
        
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"銷帳成功！客戶「{customer.name}」已收款 NT$ {amount:,.2f}，應收帳款餘額：NT$ {customer.total_receivables_twd:,.2f}。"
        })

    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "輸入的資料格式不正確。"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"!!! Error in api_settlement: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "伺服器內部錯誤，操作失敗。"}), 500


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
                target_customer = db.session.get(Holder, int(customer_id))
            elif customer_name:
                target_customer = Holder.query.filter_by(name=customer_name).first()
                if not target_customer:
                    target_customer = Holder(name=customer_name)
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

            new_sale = SalesRecord(
                customer_id=target_customer.id,
                rmb_amount=rmb,
                exchange_rate=rate,
                twd_amount=twd,
                sale_date=date.fromisoformat(order_date_str),
                status="PENDING",  # 假設初始狀態為 PENDING
            )
            db.session.add(new_sale)
            db.session.commit()

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

            db.session.delete(sale_to_delete)
            db.session.commit()
            return jsonify(
                {"status": "success", "message": "訂單已刪除。", "deleted_id": tx_id}
            )

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
@admin_required
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


# API 2: 根據持有人 ID，查詢其名下的帳戶
@app.route("/api/cash_management/accounts_by_holder/<int:holder_id>", methods=["GET"])
@admin_required
def get_accounts_by_holder_api(holder_id):
    # --- 偵錯印記 1：看看我們收到了什麼請求 ---
    print("\n" + "=" * 20 + " 開始執行 get_accounts_by_holder_api " + "=" * 20)
    print(f">>> 請求的持有人 ID (holder_id): {holder_id}")

    try:
        # --- 偵錯印記 2：執行資料庫查詢 ---
        print(f">>> 準備查詢 holder_id 為 {holder_id} 的所有 active CashAccount...")
        accounts = (
            CashAccount.query.filter_by(holder_id=holder_id, is_active=True)
            .order_by(CashAccount.account_name)
            .all()
        )

        # --- 偵錯印記 3：看看查詢到了多少筆資料 ---
        print(f">>> 查詢完畢，共找到 {len(accounts)} 個帳戶。")

        # --- 偵錯印記 4：準備要回傳給前端的資料 ---
        print(">>> 準備開始打包 JSON 資料...")
        accounts_data = [
            {
                "id": acc.id,
                "name": acc.account_name,
                "currency": acc.currency,
                "balance": acc.balance,
            }
            for acc in accounts
        ]
        print(f">>> 已成功打包 JSON 資料: {accounts_data}")

        print(
            "=" * 20 + " 結束執行 get_accounts_by_holder_api (成功) " + "=" * 20 + "\n"
        )
        # (關鍵修正) 我們需要確保回傳的是一個合法的 JSON Response
        return jsonify(accounts_data)

    except Exception as e:
        # --- 偵錯印記 5 (如果發生了連我們都沒想到的錯誤) ---
        print(f"\n!!! 在 get_accounts_by_holder_api 中發生了嚴重錯誤 !!!")
        print(f"!!! 錯誤類型: {type(e).__name__}")
        print(f"!!! 錯誤訊息: {e}")
        import traceback

        traceback.print_exc()  # 印出完整的錯誤堆疊

        # (關鍵修正) 即使出錯，也要回傳一個合法的 JSON 錯誤訊息
        return jsonify({"status": "error", "message": f"伺服器內部查詢錯誤: {e}"}), 500


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
        print(f"!!! Error in api_add_user: {e}")
        return (
            jsonify({"status": "error", "message": "伺服器內部錯誤，新增失敗。"}),
            500,
        )


# ===================================================================
# 8. 啟動器
# ===================================================================
if __name__ == "__main__":
    app.run(debug=True)
