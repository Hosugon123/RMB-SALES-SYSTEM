import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy import Float
from flask import request, jsonify

# ===================================================================
# 1. App、資料庫、登入管理器 的基礎設定
# ===================================================================
app = Flask(__name__)

# --- App Config ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_very_secret_key_that_is_long')
basedir = os.path.abspath(os.path.dirname(__file__))
# 建立一個名為 'instance' 的子資料夾來存放資料庫 (這是 Flask 的推薦做法)
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)
# 明確地將資料庫路徑指向 instance/sales.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- 初始化擴充 ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "請先登入以存取此頁面。"
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ===================================================================
# 2. 資料庫模型 (Class) 定義
# ===================================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
    
class Holder(db.Model):
    __tablename__ = 'holders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False, default='CUSTOMER')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    total_receivables_twd = db.Column(db.Float, nullable=False, default=0.0)
    cash_accounts = db.relationship('CashAccount', back_populates='holder', lazy=True, cascade="all, delete-orphan")
    sales_as_customer = db.relationship('SalesRecord', back_populates='customer', lazy=True, foreign_keys='SalesRecord.customer_id')
    
class CashAccount(db.Model):
    __tablename__ = 'cash_accounts'
    id = db.Column(db.Integer, primary_key=True)
    holder_id = db.Column(db.Integer, db.ForeignKey('holders.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    holder = db.relationship('Holder', back_populates='cash_accounts', lazy=True)

class Channel(db.Model):
    __tablename__ = 'channels'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    purchase_records = db.relationship('PurchaseRecord', back_populates='channel', lazy=True)
    
class PurchaseRecord(db.Model):
    __tablename__ = 'purchase_records'
    id = db.Column(db.Integer, primary_key=True)
    payment_account_id = db.Column(db.Integer, db.ForeignKey('cash_accounts.id'), nullable=True)
    deposit_account_id = db.Column(db.Integer, db.ForeignKey('cash_accounts.id'), nullable=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channels.id'), nullable=True)
    channel_name_manual = db.Column(db.String(100), nullable=True)
    rmb_amount = db.Column(db.Float, nullable=False)
    exchange_rate = db.Column(db.Float, nullable=False)
    twd_cost = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, server_default=func.now())
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    channel = db.relationship('Channel', back_populates='purchase_records', lazy=True)
    payment_account = db.relationship('CashAccount', foreign_keys=[payment_account_id])
    deposit_account = db.relationship('CashAccount', foreign_keys=[deposit_account_id])
    operator = db.relationship('User')

class SalesRecord(db.Model):
    __tablename__ = 'sales_records'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('holders.id'), nullable=False)
    rmb_account_id = db.Column(db.Integer, db.ForeignKey('cash_accounts.id'), nullable=True)
    rmb_amount = db.Column(db.Float, nullable=False)
    exchange_rate = db.Column(db.Float, nullable=False)
    twd_amount = db.Column(db.Float, nullable=False)
    due_amount_twd = db.Column(db.Float, nullable=False, default=0.0)
    paid_amount_twd = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='UNPAID')
    created_at = db.Column(db.DateTime, server_default=func.now())
    customer = db.relationship('Holder', back_populates='sales_as_customer', lazy=True, foreign_keys=[customer_id])
    transactions = db.relationship('Transaction', back_populates='sales_record', lazy=True, cascade="all, delete-orphan")

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    sales_record_id = db.Column(db.Integer, db.ForeignKey('sales_records.id'), nullable=False)
    twd_account_id = db.Column(db.Integer, db.ForeignKey('cash_accounts.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, server_default=func.now())
    note = db.Column(db.String(200))
    sales_record = db.relationship('SalesRecord', back_populates='transactions', lazy=True)
    twd_account = db.relationship('CashAccount', lazy=True)
    
class LedgerEntry(db.Model):
    __tablename__ = 'ledger_entries'
    id = db.Column(db.Integer, primary_key=True)
    entry_type = db.Column(db.String(50), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('cash_accounts.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    entry_date = db.Column(db.DateTime, server_default=func.now())
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account = db.relationship('CashAccount')
    operator = db.relationship('User')
    

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("您沒有權限存取此頁面。", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
                          
@app.cli.command("init-db")
def init_db_command():
    """
    清除現有資料並重新建立所有表格，並初始化基礎數據。
    """
    # 1. 刪除所有現有的表格
    db.drop_all()
    # 2. 根據最新的模型定義，創建所有表格
    db.create_all()

    print(">>> 資料庫表格已成功建立！")

    # 3. 在所有表格都創建完成後，才安全地檢查並創建 admin 用戶
    admin_user = User(username='admin', is_admin=True, is_active=True)
    admin_user.set_password('1234') # 為了方便測試，暫用 '1234'
    db.session.add(admin_user)
    print(">>> 預設管理員 'admin' 已建立。")

    # 4. 建立基礎的「持有人 (Holder)」
    owner = Holder(name='我方資金', type='OWNER')
    default_customer = Holder(name='預設客戶A', type='CUSTOMER')
    db.session.add_all([owner, default_customer])
    print(">>> 基礎持有人 '我方資金' 和 '預設客戶A' 已建立。")

    # 5. 提交所有初始化數據
    db.session.commit()
    print(">>> 資料庫初始化完成！")


@app.route('/api/buy_in_operations', methods=['POST'])
@login_required # 或者 @admin_required，根據您的權限設定
def buy_in_operations_api():
    """
    處理所有來自「買入」頁面的後端 API 操作，包括：
    - 記錄一筆採購 (record_purchase)
    - 新增常用渠道 (add_channel)
    - 刪除常用渠道 (delete_channel)
    """
    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "無效的請求格式。"}), 400

    action = data.get('action')
    if not action:
        return jsonify({"status": "error", "message": "缺少 'action' 指令。"}), 400

    try:
        # === 記錄一筆採購 (record_purchase) ===
        if action == 'record_purchase':
            payment_account_id = data.get('payment_account_id')
            deposit_account_id = data.get('deposit_account_id')
            rmb_amount_str = data.get('rmb_amount')
            exchange_rate_str = data.get('exchange_rate')

            if not all([payment_account_id, deposit_account_id, rmb_amount_str, exchange_rate_str]):
                return jsonify({'status': 'error', 'message': '缺少必要參數：付款帳戶、存款帳戶、金額或匯率。'}), 400

            try:
                rmb_amount = float(rmb_amount_str)
                exchange_rate = float(exchange_rate_str)
                if rmb_amount <= 0 or exchange_rate <= 0:
                    raise ValueError("金額和匯率必須是正數。")
            except (ValueError, TypeError):
                return jsonify({'status': 'error', 'message': '金額或匯率格式錯誤。'}), 400

            payment_account = db.session.get(CashAccount, int(payment_account_id))
            deposit_account = db.session.get(CashAccount, int(deposit_account_id))
            
            if not payment_account or payment_account.currency != 'TWD':
                return jsonify({'status': 'error', 'message': '無效的 TWD 付款帳戶。'}), 400
            if not deposit_account or deposit_account.currency != 'RMB':
                return jsonify({'status': 'error', 'message': '無效的 RMB 存款帳戶。'}), 400

            twd_cost = rmb_amount * exchange_rate
            if payment_account.balance < twd_cost:
                return jsonify({'status': 'error', 'message': f'TWD 帳戶餘額不足，需要 {twd_cost:.2f}，但僅剩 {payment_account.balance:.2f}。'}), 400
            
            # 核心操作：扣款、存款
            payment_account.balance -= twd_cost
            deposit_account.balance += rmb_amount

            # 記錄流水
            # (假設您有一個 PurchaseRecord 模型來記錄流水)
            new_purchase = PurchaseRecord(
                payment_account_id=payment_account.id,
                deposit_account_id=deposit_account.id,
                rmb_amount=rmb_amount,
                exchange_rate=exchange_rate,
                twd_cost=twd_cost,
                # ... 其他您想記錄的欄位
            )
            db.session.add(new_purchase)
            db.session.commit()
            
            return jsonify({'status': 'success', 'message': f'成功買入 ¥{rmb_amount:.2f}，花費 NT$ {twd_cost:.2f}。'})

        # === 新增常用渠道 (add_channel) ===
        elif action == 'add_channel':
            name = data.get('name', '').strip()
            if not name:
                return jsonify({'status': 'error', 'message': '渠道名稱不可為空。'}), 400
            
            existing = db.session.execute(db.select(Channel).filter_by(name=name)).scalar_one_or_none()
            if existing:
                return jsonify({'status': 'error', 'message': f'渠道 "{name}" 已存在。'}), 409

            new_channel = Channel(name=name)
            db.session.add(new_channel)
            db.session.commit()
            return jsonify({'status': 'success', 'message': f'渠道 "{name}" 已新增。'})
            
        # === 刪除常用渠道 (delete_channel) ===
        elif action == 'delete_channel':
            channel_id = data.get('channel_id')
            if not channel_id:
                return jsonify({'status': 'error', 'message': '缺少渠道 ID。'}), 400
            
            channel = db.session.get(Channel, int(channel_id))
            if not channel:
                return jsonify({'status': 'error', 'message': '找不到該渠道。'}), 404
            
            # 軟刪除 (推薦) 或硬刪除
            # 這裡我們用硬刪除做範例
            db.session.delete(channel)
            db.session.commit()
            return jsonify({'status': 'success', 'message': f'渠道 "{channel.name}" 已被刪除。'})

        else:
            return jsonify({'status': 'error', 'message': f"未知的操作: '{action}'"}), 400

    except Exception as e:
        db.session.rollback()
        print(f"Error in buy_in_operations_api: {e}")
        return jsonify({'status': 'error', 'message': '伺服器內部錯誤，操作失敗。'}), 500

@app.route('/buy')
@login_required
def buy_in():
    # 修正查詢，不再過濾 user_id
    channels = db.session.execute(db.select(Channel).filter_by(is_active=True).order_by(Channel.name)).scalars().all()
    holders = db.session.execute(db.select(Holder).filter_by(is_active=True, type='OWNER')).scalars().all()
    
    # 查詢最近的買入紀錄用於顯示
    recent_purchases_query = db.select(PurchaseRecord).order_by(PurchaseRecord.purchase_date.desc()).limit(10)
    recent_purchases = db.session.execute(recent_purchases_query).scalars().all()

    return render_template(
        'buy_in.html',
        channels=channels,
        holders=holders,
        records=recent_purchases
    )

@app.route('/card_purchase', methods=['GET', 'POST'])
@login_required
def card_purchase():
    """
    處理刷卡採購的頁面。
    GET: 顯示表單和近期的刷卡採購紀錄。
    POST: 接收表單資料，並將其記錄為一筆 PurchaseRecord。
    """
    if request.method == 'POST':
        try:
            # --- 1. 從表單獲取並驗證資料 ---
            supplier_name = request.form.get('supplier', '').strip()
            purchase_date_str = request.form.get('purchase_date')
            rmb_amount_str = request.form.get('rmb_amount')
            twd_cost_str = request.form.get('twd_equivalent') # 前端傳來的是台幣總成本

            if not all([supplier_name, purchase_date_str, rmb_amount_str, twd_cost_str]):
                flash('所有欄位都必須填寫。', 'danger')
                return redirect(url_for('card_purchase'))

            rmb_amount = float(rmb_amount_str)
            twd_cost = float(twd_cost_str)
            
            # 手續費和匯率計算 (與您舊邏輯保持一致)
            rmb_with_fee = rmb_amount * 1.03
            calculated_rate = twd_cost / rmb_with_fee if rmb_with_fee > 0 else 0
            
            purchase_date = date.fromisoformat(purchase_date_str)
            
        except (ValueError, TypeError):
            flash('輸入的金額或日期格式不正確。', 'danger')
            return redirect(url_for('card_purchase'))

        try:
            # --- 2. 處理「渠道/供應商」 ---
            # 檢查這個供應商是否已經是我們的常用渠道
            channel = db.session.execute(db.select(Channel).filter_by(name=supplier_name)).scalar_one_or_none()
            if not channel:
                # 如果不是，就自動新增一個
                channel = Channel(name=supplier_name)
                db.session.add(channel)
                db.session.flush() # 為了立即獲取 channel.id

            # --- 3. 創建 PurchaseRecord 流水帳 ---
            # 對於刷卡，我們沒有明確的 TWD 扣款帳戶和 RMB 入庫帳戶
            # 所以我們將 account_id 設為一個特殊值或 None，這裡我們先設為 None (需要模型允許)
            # 為了能運行，我們需要確保模型中的 account_id 欄位可以為空
            
            # 假設我們在現金管理中有一個叫「信用卡」的虛擬帳戶，ID為-1(需要先建立)
            # 這裡我們先簡化處理，假設付款/入款帳戶都指向操作員本身(ID=1)
            # 在真實應用中，這裡需要更嚴謹的設計
            
            # 為了能讓程式碼跑起來，我們做一個簡化：
            # 假設刷卡交易不影響任何現金帳戶，所以相關ID都設為一個預留值，例如 0
            # 注意: 這需要 PurchaseRecord 的 foreign_keys 欄位可以為空 (nullable=True)
            # 我們來修改 PurchaseRecord 模型讓它可以為空

            new_purchase = PurchaseRecord(
                payment_account_id=None, # 刷卡不從現金帳戶扣款
                deposit_account_id=None, # 刷卡購入的點數/服務不計入RMB庫存
                channel_id=channel.id,
                channel_name_manual=supplier_name, # 將供應商名稱記錄下來
                rmb_amount=rmb_amount,
                exchange_rate=calculated_rate,
                twd_cost=twd_cost,
                purchase_date=purchase_date,
                operator_id=current_user.id
            )

            db.session.add(new_purchase)
            db.session.commit()
            
            flash(f'成功登錄一筆對「{supplier_name}」的刷卡採購紀錄！', 'success')
            return redirect(url_for('card_purchase'))
            
        except Exception as e:
            db.session.rollback()
            print(f"!!! 刷卡採購儲存失敗: {e}")
            flash('資料庫錯誤，儲存失敗，請聯繫管理員。', 'danger')
            return redirect(url_for('card_purchase'))


    # --- 處理 GET 請求 ---
    page = request.args.get('page', 1, type=int)
    # 查詢 PurchaseRecord，並篩選出那些看起來像刷卡紀錄的 (例如 account_id 為 None)
    query = db.select(PurchaseRecord).where(PurchaseRecord.payment_account_id == None).order_by(PurchaseRecord.purchase_date.desc())
    purchases_pagination = db.paginate(query, page=page, per_page=10, error_out=False)
    
    today = date.today().isoformat()
    return render_template('card_purchase.html', today=today, purchases=purchases_pagination)


# ===================================================================
# 3. 自訂裝飾器
# ===================================================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("您沒有權限存取此頁面。", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ===================================================================
# 5. 核心路由
# ===================================================================
@app.route('/')
def index():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # --- 偵錯印記 1：看看我們收到了什麼 ---
        print("\n" + "="*20 + " 開始登入驗證 " + "="*20)
        print(f">>> 表單提交的使用者名稱: '{username}'")
        print(f">>> 表單提交的密碼: '{password}'")

        user = User.query.filter_by(username=username).first()

        # --- 偵錯印記 2：看看有沒有找到這個使用者 ---
        print(f">>> 在資料庫中找到的 user 物件: {user}")

        if user:
            # --- 偵錯印記 3：如果找到了，看看它的屬性和密碼雜湊值 ---
            print(f">>> 找到的使用者 ID: {user.id}, 使用者名稱: {user.username}, 是否為管理員: {user.is_admin}")
            print(f">>> 資料庫中儲存的密碼雜湊值: {user.password_hash}")
            
            # --- 偵錯印記 4：執行密碼比對，看看結果是 True 還是 False ---
            is_password_correct = user.check_password(password)
            print(f">>> 密碼驗證結果 (check_password): {is_password_correct}")

            if is_password_correct:
                print(">>> 驗證成功！準備登入並跳轉...")
                login_user(user, remember=True)
                return redirect(url_for('index'))
            else:
                print(">>> 驗證失敗：密碼錯誤。")
        else:
            print(">>> 驗證失敗：找不到使用者。")

        flash('無效的使用者名稱或密碼。', 'danger')
        print("="*20 + " 結束登入驗證 " + "="*20 + "\n")
        
    return render_template('login.html')
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功登出。', 'success')
    return redirect(url_for('login'))

# ===================================================================
# 6. 主要功能頁面路由
# ===================================================================
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    try:
        # --- 我們用最安全的方式，一個個計算指標 ---
        total_twd_cash = db.session.query(func.sum(CashAccount.balance)).filter(CashAccount.currency == 'TWD').scalar() or 0.0
        total_rmb_stock = db.session.query(func.sum(CashAccount.balance)).filter(CashAccount.currency == 'RMB').scalar() or 0.0
        
        latest_purchase = db.session.execute(db.select(PurchaseRecord).order_by(PurchaseRecord.purchase_date.desc())).scalar_one_or_none()
        current_buy_rate = latest_purchase.exchange_rate if latest_purchase else 4.5
        estimated_total_assets_twd = total_twd_cash + (total_rmb_stock * current_buy_rate)

        pending_sales_records = db.session.execute(db.select(SalesRecord).filter(SalesRecord.status != 'PAID')).scalars().all()
        total_unsettled_amount_twd = sum(sale.due_amount_twd for sale in pending_sales_records)
        recent_pending_sales = pending_sales_records[:5]
        
        # --- 為了 100% 確保成功，我們先傳遞一個空的圖表數據 ---
        chart_data = {'labels': [], 'values': []}

        return render_template(
            'admin.html',
            total_twd_cash=total_twd_cash,
            total_rmb_stock=total_rmb_stock,
            current_buy_rate=current_buy_rate,
            estimated_total_assets_twd=estimated_total_assets_twd,
            total_unsettled_amount_twd=total_unsettled_amount_twd,
            recent_pending_sales=recent_pending_sales,
            chart_data=chart_data
        )

    except Exception as e:
        # --- 即便出錯，我們也確保提供一個完整的、可渲染的上下文 ---
        flash('載入儀表板數據時發生錯誤，部分數據可能無法顯示。', 'danger')
        empty_chart_data = {'labels': [], 'values': []}
        return render_template(
            'admin.html',
            total_twd_cash=0, total_rmb_stock=0, current_buy_rate=4.5,
            estimated_total_assets_twd=0, total_unsettled_amount_twd=0,
            recent_pending_sales=[], chart_data=empty_chart_data
        )

        
# (其他頁面路由的 placeholder，您可以後續將它們的邏輯用 ORM 實現)
@app.route('/sales_entry')
@login_required
def sales_entry():
    # 查詢客戶
    customers = db.session.execute(db.select(Holder).filter_by(is_active=True, type='CUSTOMER').order_by(Holder.name)).scalars().all()
    # 查詢我方 RMB 帳戶
    rmb_accounts = db.session.execute(db.select(CashAccount).join(Holder).filter(Holder.type == 'OWNER', CashAccount.currency == 'RMB')).scalars().all()
    # 查詢待處理訂單，並修正排序欄位
    pending_sales = db.session.execute(db.select(SalesRecord).filter(SalesRecord.status != 'PAID').order_by(SalesRecord.created_at.desc())).scalars().all()

    return render_template(
        'sales_entry.html',
        customers=customers,
        rmb_accounts=rmb_accounts,
        pending_sales=pending_sales
    )

@app.route('/api/sales_operations', methods=['POST'])
@admin_required # 假設您有這個裝飾器
def sales_operations_api():
    """
    處理銷售相關的所有後端 API 操作，包括：
    - 創建銷售訂單 (create_order)
    - 新增常用客戶 (add_customer)
    - 刪除常用客戶 (delete_customer)
    """
    data = request.get_json()

    # --- 1. 輸入驗證 ---
    if not data:
        return jsonify({
            "status": "error",
            "message": "請求格式錯誤，必須是有效的 JSON。"
        }), 400

    action = data.get('action')
    if not action:
        return jsonify({
            "status": "error",
            "message": "缺少必要的操作指令 'action'。"
        }), 400

    try:
        # --- 2. 根據 action 執行不同邏輯 ---

        # === 創建新訂單 (create_order) ===
        if action == 'create_order':
            # 獲取並驗證必要參數
            customer_id = data.get('holder_id')
            rmb_account_id = data.get('rmb_account_id')
            rmb_amount_str = data.get('rmb_amount')
            exchange_rate_str = data.get('exchange_rate')

            if not all([customer_id, rmb_account_id, rmb_amount_str, exchange_rate_str]):
                return jsonify({'status': 'error', 'message': '缺少必要參數：客戶、RMB帳戶、金額或匯率。'}), 400

            # 轉換資料型態並驗證
            try:
                customer_id = int(customer_id)
                rmb_account_id = int(rmb_account_id)
                rmb_amount = float(rmb_amount_str)
                exchange_rate = float(exchange_rate_str)
                if rmb_amount <= 0 or exchange_rate <= 0:
                    raise ValueError("金額和匯率必須是正數。")
            except (ValueError, TypeError):
                return jsonify({'status': 'error', 'message': '金額或匯率格式錯誤，請輸入有效的數字。'}), 400

            # 查詢資料庫物件
            customer = db.session.get(Holder, customer_id)
            rmb_account = db.session.get(CashAccount, rmb_account_id)

            if not customer or customer.type != 'CUSTOMER':
                return jsonify({'status': 'error', 'message': '無效的客戶 ID。'}), 404
            if not rmb_account or rmb_account.currency != 'RMB':
                return jsonify({'status': 'error', 'message': '無效的 RMB 庫存帳戶。'}), 400
            if rmb_account.balance < rmb_amount:
                return jsonify({'status': 'error', 'message': f'RMB 庫存不足，目前僅剩 {rmb_account.balance}。'}), 400

            # 核心業務邏輯
            twd_amount = round(rmb_amount * exchange_rate, 2) # 計算 TWD 金額，四捨五入到小數第二位
            
            rmb_account.balance -= rmb_amount  # 扣減 RMB 庫存
            customer.total_receivables_twd += twd_amount  # 增加客戶的總應收款

            new_sale = SalesRecord(
                customer_id=customer.id,
                rmb_account_id=rmb_account.id, # 建議也記錄是從哪個RMB帳戶出貨的
                rmb_amount=rmb_amount,
                exchange_rate=exchange_rate,
                twd_amount=twd_amount,
                due_amount_twd=twd_amount  # 初始待收金額等於訂單總額
            )
            
            db.session.add(new_sale)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f'訂單創建成功！客戶 {customer.name} 新增應收款 TWD {twd_amount:.2f}。'
            })

        # === 新增常用客戶 (add_customer) ===
        elif action == 'add_customer':
            customer_name = data.get('name', '').strip()
            if not customer_name:
                return jsonify({'status': 'error', 'message': '客戶名稱不可為空。'}), 400
            
            # 檢查客戶是否已存在
            existing_customer = db.session.execute(db.select(Holder).filter_by(name=customer_name, type='CUSTOMER')).scalar_one_or_none()
            if existing_customer:
                return jsonify({'status': 'error', 'message': f'客戶 "{customer_name}" 已經存在。'}), 409 # 409 Conflict

            new_customer = Holder(
                name=customer_name,
                type='CUSTOMER',
                total_receivables_twd=0
            )
            db.session.add(new_customer)
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': f'客戶 "{customer_name}" 已成功新增。',
                'customer': { # 返回新客戶的資料給前端，方便即時更新UI
                    'id': new_customer.id,
                    'name': new_customer.name
                }
            })

        # === 刪除常用客戶 (delete_customer) ===
        elif action == 'delete_customer':
            customer_id = data.get('holder_id')
            if not customer_id:
                return jsonify({'status': 'error', 'message': '缺少客戶 ID。'}), 400
            
            try:
                customer_id = int(customer_id)
            except (ValueError, TypeError):
                return jsonify({'status': 'error', 'message': '客戶 ID 格式錯誤。'}), 400

            customer_to_delete = db.session.get(Holder, customer_id)

            if not customer_to_delete:
                return jsonify({'status': 'error', 'message': '找不到該客戶。'}), 404
            
            # 安全檢查：如果客戶還有欠款，不允許刪除
            if customer_to_delete.total_receivables_twd > 0:
                return jsonify({
                    'status': 'error',
                    'message': f'無法刪除客戶 "{customer_to_delete.name}"，該客戶尚有 {customer_to_delete.total_receivables_twd:.2f} TWD 的應收款未結清。'
                }), 400
            
            # 安全檢查：如果客戶有關聯的銷售紀錄，也建議不要直接刪除，或是做軟刪除
            # 這裡我們先假設可以直接刪除
            
            db.session.delete(customer_to_delete)
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': f'客戶 "{customer_to_delete.name}" 已被刪除。'
            })
        
        # 如果 action 不是以上任何一種
        else:
            return jsonify({'status': 'error', 'message': f"未知的操作指令: '{action}'"}), 400

    except Exception as e:
        db.session.rollback()
        # 在伺服器端印出詳細錯誤，方便 debug
        print(f"An error occurred in sales_operations_api: {e}")
        # 返回一個通用的錯誤訊息給前端
        return jsonify({'status': 'error', 'message': '伺服器內部錯誤，操作失敗。'}), 500
    

@app.route('/admin/cash_management')
@admin_required
def cash_management():
    try:
        page = request.args.get('page', 1, type=int)

        holders_obj = db.session.execute(db.select(Holder).filter_by(is_active=True)).scalars().all()
        all_accounts_obj = db.session.execute(db.select(CashAccount).order_by(CashAccount.holder_id)).scalars().all()

        total_twd = sum(acc.balance for acc in all_accounts_obj if acc.currency == 'TWD')
        total_rmb = sum(acc.balance for acc in all_accounts_obj if acc.currency == 'RMB')
        
        accounts_by_holder = {}
        for acc in all_accounts_obj:
            if acc.holder_id not in accounts_by_holder:
                accounts_by_holder[acc.holder_id] = {'holder_name': acc.holder.name, 'accounts': [], 'total_twd': 0, 'total_rmb': 0}
            accounts_by_holder[acc.holder_id]['accounts'].append({'id': acc.id, 'name': acc.name, 'currency': acc.currency, 'balance': acc.balance})
            if acc.currency == 'TWD':
                accounts_by_holder[acc.holder_id]['total_twd'] += acc.balance
            elif acc.currency == 'RMB':
                accounts_by_holder[acc.holder_id]['total_rmb'] += acc.balance

        purchases = db.session.execute(db.select(PurchaseRecord)).scalars().all()
        sales = db.session.execute(db.select(SalesRecord)).scalars().all()
        misc_entries = db.session.execute(db.select(LedgerEntry)).scalars().all()
        
        unified_stream = []
        for p in purchases:
            if p.payment_account and p.deposit_account:
                unified_stream.append({'type': '買入', 'date': p.purchase_date.isoformat(), 'description': f"向 {p.channel_name_manual or p.channel.name} 買入", 'twd_change': -p.twd_cost, 'rmb_change': p.rmb_amount})
        for s in sales:
            if s.customer:
                unified_stream.append({'type': '售出', 'date': s.created_at.isoformat(), 'description': f"售予 {s.customer.name}", 'twd_change': s.twd_amount, 'rmb_change': -s.rmb_amount})
        for entry in misc_entries:
            twd_change = 0
            rmb_change = 0
            if entry.account.currency == 'TWD':
                twd_change = entry.amount if entry.entry_type in ['DEPOSIT', 'TRANSFER_IN'] else -entry.amount
            else:
                rmb_change = entry.amount if entry.entry_type in ['DEPOSIT', 'TRANSFER_IN'] else -entry.amount
            unified_stream.append({'type': entry.entry_type, 'date': entry.entry_date.isoformat(), 'description': entry.description, 'twd_change': twd_change, 'rmb_change': rmb_change})

        unified_stream.sort(key=lambda x: x['date'], reverse=True)
        
        per_page = 10
        total_items = len(unified_stream)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_items = unified_stream[start:end]
        
        from math import ceil
        pagination = {
            'page': page, 'per_page': per_page, 'total': total_items,
            'pages': ceil(total_items / per_page),
            'has_prev': page > 1, 'has_next': page * per_page < total_items,
            'prev_num': page - 1, 'next_num': page + 1
        }
        
        # --- 關鍵修正：確保您傳遞的是正確的分頁後數據 ---
        return render_template(
            'cash_management.html',
            total_twd=total_twd, total_rmb=total_rmb,
            accounts_by_holder=accounts_by_holder,
            movements=paginated_items,     # <-- 傳遞分頁後的當前頁數據
            pagination=pagination,         # <-- 傳遞分頁控制對象
            holders=[{'id': h.id, 'name': h.name} for h in holders_obj],
            owner_accounts=[{'id': a.id, 'name': a.name, 'currency': a.currency, 'holder_id': a.holder_id} for a in all_accounts_obj]
        )
    except Exception as e:
        print(f"!!! 現金管理頁面發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        flash('載入現金管理數據時發生嚴重錯誤。', 'danger')
        return render_template('cash_management.html', total_twd=0, total_rmb=0, accounts_by_holder={}, movements=[], holders=[], owner_accounts=[], pagination=None)
    

@app.route('/api/process_payment', methods=['POST'])
@admin_required
def process_payment_api():
    """
    處理客戶付款（銷帳）的後端 API。
    接收客戶 ID、付款金額和收款帳戶，然後自動沖銷該客戶名下最早的未付訂單。
    """
    data = request.get_json()
    try:
        customer_id = int(data.get('customer_id'))
        payment_amount = float(data.get('payment_amount'))
        twd_account_id = int(data.get('twd_account_id')) # 收款到哪個我方 TWD 帳戶
    except (ValueError, TypeError, AttributeError):
        return jsonify({'status': 'error', 'message': '輸入的資料格式不正確。'}), 400

    if not all([customer_id, payment_amount > 0, twd_account_id]):
        return jsonify({'status': 'error', 'message': '客戶、付款金額和收款帳戶皆為必填。'}), 400

    try:
        # --- 1. 獲取核心物件 ---
        customer = db.session.get(Holder, customer_id)
        twd_account = db.session.get(CashAccount, twd_account_id)
        
        # --- 2. 業務邏輯驗證 ---
        if not customer or customer.type != 'CUSTOMER':
            return jsonify({'status': 'error', 'message': '無效的客戶 ID。'}), 404
        if not twd_account or twd_account.currency != 'TWD':
            return jsonify({'status': 'error', 'message': '無效的 TWD 收款帳戶。'}), 400
        if customer.total_receivables_twd < payment_amount:
            return jsonify({'status': 'error', 'message': f'付款金額超過總欠款！客戶總欠款為 {customer.total_receivables_twd:,.2f} TWD。'}), 400

        # --- 3. 查找該客戶所有未結清的訂單，按日期升序排列 ---
        unpaid_orders = db.session.execute(
            db.select(SalesRecord)
            .filter_by(customer_id=customer_id)
            .filter(SalesRecord.status != 'PAID')
            .order_by(SalesRecord.created_at.asc())
        ).scalars().all()
        
        remaining_payment = payment_amount
        
        # --- 4. 核心沖銷邏輯 ---
        for order in unpaid_orders:
            if remaining_payment <= 0:
                break

            payment_for_this_order = min(remaining_payment, order.due_amount_twd)
            
            # A. 建立一筆新的銷帳流水 (Transaction)
            new_transaction = Transaction(
                sales_record_id=order.id,
                twd_account_id=twd_account.id,
                amount=payment_for_this_order,
                note=f"沖銷訂單 #{order.id}"
            )
            db.session.add(new_transaction)
            
            # B. 更新訂單狀態 (這部分邏輯可以被 models.py 中的自動化事件監聽器取代)
            # 但為了清晰，我們也可以在這裡手動計算
            order.paid_amount_twd += payment_for_this_order
            order.due_amount_twd -= payment_for_this_order
            if order.due_amount_twd < 0.01: # 處理浮點數精度問題
                order.status = 'PAID'
            else:
                order.status = 'PARTIALLY_PAID'

            remaining_payment -= payment_for_this_order

        # C. 更新收款的 TWD 帳戶餘額
        twd_account.balance += payment_amount
        
        # D. 更新客戶的總應收款
        customer.total_receivables_twd -= payment_amount

        # --- 5. 提交所有變更 ---
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': f'銷帳成功！共處理 {payment_amount:,.2f} TWD。'})

    except Exception as e:
        db.session.rollback()
        print(f"!!! 銷帳 API 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': '資料庫儲存失敗，請聯繫管理員。'}), 500

@app.route('/admin/update_cash_account', methods=['POST'])
@admin_required
def admin_update_cash_account():
    action = request.form.get('action')
    try:
        if action == 'add_holder':
            name = request.form.get('name', '').strip()
            
            # --- 關鍵修正：我們不再獲取也不再檢查 holder_type ---
            if not name:
                flash('持有人名稱為必填項。', 'danger')
            else:
                existing_holder = db.session.execute(db.select(Holder).filter_by(name=name)).scalar_one_or_none()
                if existing_holder:
                    flash(f'錯誤：持有人 "{name}" 已經存在。', 'danger')
                else:
                    # 我們直接創建，type 會自動使用模型中定義的 default='CUSTOMER'
                    new_holder = Holder(name=name) 
                    db.session.add(new_holder)
                    db.session.commit()
                    flash(f'持有人 "{name}" 已成功新增！', 'success')
        
        elif action == 'delete_holder':
            holder_id = int(request.form.get('holder_id'))
            holder = db.session.get(Holder, holder_id)
            if holder:
                if holder.cash_accounts:
                     flash(f'無法刪除！持有人 "{holder.name}" 名下尚有現金帳戶。', 'danger')
                else:
                    db.session.delete(holder)
                    db.session.commit()
                    flash(f'持有人 "{holder.name}" 已被刪除。', 'success')
            else:
                 flash('找不到該持有人。', 'warning')

        elif action == 'add_account':
            holder_id = int(request.form.get('holder_id'))
            name = request.form.get('name', '').strip()
            currency = request.form.get('currency')
            balance = float(request.form.get('initial_balance', 0.0))
            if not all([holder_id, name, currency]):
                flash('持有人、帳戶名稱和幣別為必填項。', 'danger')
            else:
                new_account = CashAccount(holder_id=holder_id, name=name, currency=currency, balance=balance)
                db.session.add(new_account)
                db.session.commit()
                flash(f'帳戶 "{name}" 已成功新增！', 'success')

        elif action == 'delete_account':
            account_id = int(request.form.get('account_id'))
            account = db.session.get(CashAccount, account_id)
            if account:
                if account.balance != 0:
                    flash(f'無法刪除！帳戶 "{account.name}" 尚有 {account.balance:,.2f} 的餘額。', 'danger')
                else:
                    db.session.delete(account)
                    db.session.commit()
                    flash(f'帳戶 "{account.name}" 已被刪除。', 'success')
            else:
                flash('找不到該帳戶。', 'warning')

        elif action == 'add_movement':
            account_id = int(request.form.get('account_id'))
            amount = float(request.form.get('amount'))
            is_decrease = request.form.get('is_decrease') == 'true'
            account = db.session.get(CashAccount, account_id)
            if account:
                if is_decrease:
                    if account.balance < amount:
                        flash(f'餘額不足，無法提出 {amount}。', 'danger')
                    else:
                        account.balance -= amount
                        entry = LedgerEntry(entry_type='WITHDRAW', account_id=account.id, amount=amount, description=f"外部提款", operator_id=current_user.id)
                        db.session.add(entry)
                        db.session.commit()
                        flash(f'已從 "{account.name}" 提出 {amount:,.2f}，並已記錄流水。', 'success')
                else:
                    account.balance += amount
                    entry = LedgerEntry(entry_type='DEPOSIT', account_id=account.id, amount=amount, description=f"外部存款", operator_id=current_user.id)
                    db.session.add(entry)
                    db.session.commit()
                    flash(f'已向 "{account.name}" 存入 {amount:,.2f}，並已記錄流水。', 'success')

        elif action == 'transfer_funds':
            from_id = int(request.form.get('from_account_id'))
            to_id = int(request.form.get('to_account_id'))
            amount = float(request.form.get('transfer_amount'))
            if from_id == to_id:
                flash('來源與目標帳戶不可相同！', 'danger')
            else:
                from_account = db.session.get(CashAccount, from_id)
                to_account = db.session.get(CashAccount, to_id)
                if from_account.balance < amount:
                    flash(f'來源帳戶 "{from_account.name}" 餘額不足。', 'danger')
                else:
                    from_account.balance -= amount
                    to_account.balance += amount
                    
                    out_entry = LedgerEntry(entry_type='TRANSFER_OUT', account_id=from_account.id, amount=amount, description=f"轉出至 {to_account.name}", operator_id=current_user.id)
                    in_entry = LedgerEntry(entry_type='TRANSFER_IN', account_id=to_account.id, amount=amount, description=f"從 {from_account.name} 轉入", operator_id=current_user.id)
                    db.session.add_all([out_entry, in_entry])
                    
                    db.session.commit()
                    flash(f'成功從 "{from_account.name}" 轉帳 {amount:,.2f} 到 "{to_account.name}"，並已記錄流水！', 'success')
        
        else:
            flash('未知的操作指令。', 'warning')

    except Exception as e:
        db.session.rollback()
        print(f"!!! 現金帳戶更新失敗: {e}")
        import traceback
        traceback.print_exc()
        flash('操作失敗，發生未知錯誤或輸入格式不正確。', 'danger')
    
    return redirect(url_for('cash_management'))

# ===================================================================
# 7. AJAX API 路由 (買入頁面的功能)
# ===================================================================
@app.route('/admin/add_purchase_channel_ajax', methods=['POST'])
@admin_required
def add_purchase_channel_ajax():
    data = request.get_json()
    customer_name = data.get('customer_name', '').strip()
    if not customer_name: return jsonify({'status': 'error', 'message': '渠道名稱不可為空。'}), 400

    existing = User.query.filter_by(username=customer_name).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.session.commit()
            return jsonify({'status': 'success', 'message': f'渠道 "{customer_name}" 已恢復。', 'customer': {'id': existing.id, 'username': existing.username}})
        else:
            return jsonify({'status': 'error', 'message': f'名為 "{customer_name}" 的渠道已存在。'}), 409
    
    new_channel = User(username=customer_name, is_admin=False, is_active=True)
    db.session.add(new_channel)
    db.session.commit()
    return jsonify({'status': 'success', 'message': '新增成功！', 'customer': {'id': new_channel.id, 'username': new_channel.username}})

@app.route('/admin/delete_purchase_channel_ajax', methods=['POST'])
@admin_required
def delete_purchase_channel_ajax():
    data = request.get_json()
    customer_id = data.get('customer_id')
    channel = db.session.get(User, customer_id)
    if channel and not channel.is_admin:
        channel.is_active = False
        db.session.commit()
        return jsonify({'status': 'success', 'deleted_name': channel.username})
    return jsonify({'status': 'error', 'message': '找不到或無法刪除該渠道。'}), 404

@app.route('/api/record_purchase', methods=['POST'])
@login_required # 或者 @admin_required
def record_purchase_api():
    data = request.get_json()
    try:
        payment_account_id = int(data.get('payment_account_id'))
        deposit_account_id = int(data.get('deposit_account_id'))
        rmb_amount = float(data.get('rmb_amount'))
        exchange_rate = float(data.get('exchange_rate'))
        channel_id = data.get('channel_id')
        channel_name_manual = data.get('channel_name_manual', '').strip()

        if not (channel_id or channel_name_manual):
             return jsonify({'status': 'error', 'message': '請選擇或輸入一個購買渠道。'}), 400
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': '輸入的資料格式不正確。'}), 400

    try:
        payment_account = db.session.get(CashAccount, payment_account_id)
        deposit_account = db.session.get(CashAccount, deposit_account_id)

        if not payment_account or payment_account.currency != 'TWD':
            return jsonify({'status': 'error', 'message': '無效的 TWD 付款帳戶。'}), 404
        if not deposit_account or deposit_account.currency != 'RMB':
            return jsonify({'status': 'error', 'message': '無效的 RMB 入庫帳戶。'}), 404

        twd_cost = rmb_amount * exchange_rate
        if payment_account.balance < twd_cost:
            return jsonify({'status': 'error', 'message': f'付款帳戶餘額不足！'}), 400

        final_channel_id = None
        if channel_id:
            final_channel_id = int(channel_id)
        elif channel_name_manual:
            existing_channel = db.session.execute(db.select(Channel).filter_by(name=channel_name_manual)).scalar_one_or_none()
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
            operator_id=current_user.id
        )
        db.session.add(new_purchase)
        
        # 提交所有變更
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '交易成功！資金與庫存皆已更新。'})

    except Exception as e:
        db.session.rollback()
        print(f"!!! 買入 API 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': '資料庫儲存失敗，請聯繫管理員。'}), 500

@app.route('/admin/update_transaction_note', methods=['POST'])
@admin_required
def admin_update_transaction_note():
    data = request.get_json()
    tx_id = data.get("tx_id")
    note = data.get("note", "").strip()

    tx = Transaction.query.get(tx_id)
    if not tx:
        return jsonify({'status': 'error', 'message': '找不到該交易紀錄'}), 404

    tx.note = note
    db.session.commit()

    return jsonify({'status': 'success', 'message': '備註已更新'})

@app.route('/admin/update_transaction_status', methods=['POST'])
@admin_required
def admin_update_transaction_status():
    data = request.get_json()
    tx_id = data.get("tx_id")
    new_status = data.get("new_status")

    tx = Transaction.query.get(tx_id)
    if not tx:
        return jsonify({'status': 'error', 'message': '找不到該交易紀錄'}), 404

    tx.status = new_status
    db.session.commit()

    return jsonify({'status': 'success', 'message': '狀態已更新', 'new_status': new_status})

#@app.route('/admin/update_movement_note', methods=['POST'])
#@admin_required
#def admin_update_movement_note():
#    data = request.get_json()
#    movement_id = data.get("movement_id")
#    note = data.get("note", "").strip()
#    movement = FundMovement.query.get(movement_id)
#    if not movement:
#        return jsonify({'status': 'error', 'message': '找不到該資金異動紀錄'}), 404

#    movement.note = note
#    db.session.commit()

#    return jsonify({'status': 'success', 'message': '備註已更新'})

# ===================================================================
# fun
# ===================================================================
    

#def get_exchange_rate(currency: str = "TWD", rate_type: str = "sell") -> float:
    """
    根據幣別與匯率類型（buy/sell）取得最新匯率。
    如果查無資料，會回傳 fallback 值或 0.0。

    :param currency: 幣別名稱（預設 TWD）
    :param rate_type: 要取得買入匯率 (buy) 還是售出匯率 (sell)
    :return: 浮點數匯率值
    """
    rate_type = rate_type.lower()
    currency = currency.upper()

    if currency != "TWD":
        # 目前只支援 TWD，如需擴充，這裡可加入其他貨幣邏輯
        return 0.0

    # 查找最新一筆匯率記錄
    latest_rate = ExchangeRate.query.order_by(ExchangeRate.last_updated.desc()).first()

    if not latest_rate:
        return 0.0

    if rate_type == "buy":
        return latest_rate.buy_rate
    else:
        return latest_rate.sell_rate
    
def record_sale_cost(sale_rmb_amount):
    remaining = sale_rmb_amount
    cost = 0.0

    # 查詢 FIFO 用的 buy-in 紀錄（剩餘 RMB > 0）
    purchases = Transaction.query.filter(
        Transaction.transaction_type == 'buy',
        Transaction.status == '已入帳'
    ).order_by(Transaction.order_time.asc()).all()

    for purchase in purchases:
        used_rmb = (purchase.total_cost or 0) / (purchase.cost_per_unit or purchase.buy_rate or 1e-8)
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

@app.route('/add_customer_ajax', methods=['POST'])
@admin_required
def add_customer_ajax():
    data = request.get_json()
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'status': 'error', 'message': '未提供用戶名'}), 400
    
    # 我們假設客戶也是一種 Holder
    existing_user = Holder.query.filter_by(name=username).first()
    if existing_user:
        return jsonify({'status': 'error', 'message': '此客戶名稱已存在'}), 409

    new_customer = Holder(name=username)
    db.session.add(new_customer)
    db.session.commit()

    customer_data = {'id': new_customer.id, 'username': new_customer.name}
    return jsonify({'status': 'success', 'message': '客戶新增成功', 'customer': customer_data})

@app.route('/delete_customer_ajax', methods=['POST'])
@admin_required
def delete_customer_ajax():
    data = request.get_json()
    customer_id = data.get('customer_id')
    
    customer_to_deactivate = db.session.get(Holder, int(customer_id))
    if not customer_to_deactivate:
         return jsonify({'status': 'error', 'message': '找不到該客戶'}), 404
    
    customer_to_deactivate.is_active = False # 軟刪除
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '客戶已從常用列表移除'})

@app.route('/sales_action', methods=['POST'])
@admin_required
def sales_action():
    action = request.form.get('action')

    try:
        if action == 'create_order':
            customer_name = request.form.get('customer_name')
            customer_id = request.form.get('user_id')

            target_customer = None
            if customer_id:
                target_customer = db.session.get(Holder, int(customer_id))
            elif customer_name:
                target_customer = Holder.query.filter_by(name=customer_name).first()
                if not target_customer:
                    target_customer = Holder(name=customer_name)
                    db.session.add(target_customer)
                    db.session.flush() # 取得 ID
            
            if not target_customer:
                return jsonify({'status': 'error', 'message': '客戶名稱或ID為必填'}), 400

            rmb = float(request.form.get('rmb_sell_amount'))
            rate = float(request.form.get('exchange_rate'))
            order_date_str = request.form.get('order_date')
            twd = rmb * rate

            new_sale = SalesRecord(
                customer_id=target_customer.id,
                rmb_amount=rmb,
                exchange_rate=rate,
                twd_amount=twd,
                sale_date=date.fromisoformat(order_date_str),
                status='PENDING' # 假設初始狀態為 PENDING
            )
            db.session.add(new_sale)
            db.session.commit()

            transaction_data = {
                'id': new_sale.id,
                'username': target_customer.name,
                'rmb_order_amount': "%.2f" % new_sale.rmb_amount,
                'twd_expected_payment': "%.2f" % new_sale.twd_amount,
                'order_time': new_sale.sale_date.isoformat()
            }
            return jsonify({'status': 'success', 'message': '訂單創建成功！', 'transaction': transaction_data})

        elif action == 'delete_order':
            tx_id = request.form.get('transaction_id')
            sale_to_delete = db.session.get(SalesRecord, int(tx_id))
            if not sale_to_delete:
                return jsonify({'status': 'error', 'message': '找不到該訂單'}), 404
            
            db.session.delete(sale_to_delete)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '訂單已刪除。', 'deleted_id': tx_id})
            
        else:
            return jsonify({'status': 'error', 'message': '無效的操作'}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'伺服器錯誤: {str(e)}'}), 500


@app.route('/api/channels', methods=['GET'])
@admin_required
def get_channels():
    channels = Channel.query.filter_by(is_active=True).order_by(Channel.name).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in channels])

@app.route('/api/channel', methods=['POST', 'DELETE'])
@admin_required
def manage_channel():
    data = request.get_json()
    if request.method == 'POST':
        name = data.get('name', '').strip()
        if not name: return jsonify({'status': 'error', 'message': '渠道名稱不可為空'}), 400
        if Channel.query.filter_by(name=name).first(): return jsonify({'status': 'error', 'message': '此渠道已存在'}), 409
        
        new_channel = Channel(name=name)
        db.session.add(new_channel)
        db.session.commit()
        return jsonify({'status': 'success', 'message': '渠道新增成功', 'channel': {'id': new_channel.id, 'name': new_channel.name}})

    if request.method == 'DELETE':
        channel_id = data.get('id')
        channel = db.session.get(Channel, channel_id)
        if not channel: return jsonify({'status': 'error', 'message': '找不到該渠道'}), 404
        
        # 軟刪除
        channel.is_active = False 
        db.session.commit()
        return jsonify({'status': 'success', 'message': '渠道已刪除'})


# #@app.route('/api/cash_management/initial_data', methods=['GET'])
# #@admin_required
# #def get_initial_cash_data():
# #    try:
#         # (關鍵修正) 在函式開頭，加入計算總額的邏輯
#         all_accounts_query = CashAccount.query.all()
#         total_twd = sum(acc.balance for acc in all_accounts_query if acc.currency == 'TWD')
#         total_rmb = sum(acc.balance for acc in all_accounts_query if acc.currency == 'RMB')
#         latest_totals = {'twd': total_twd, 'rmb': total_rmb}

#         # 查詢持有人 (邏輯不變)
#         holders = Holder.query.filter_by(is_active=True).order_by(Holder.name).all()
        
#         # 查詢資金流水 (帶分頁) (邏輯不變)
#         page = request.args.get('page', 1, type=int)
#         pagination = 
#         .query.order_by(FundMovement.move_date.desc()).paginate(
#             page=page, per_page=10, error_out=False
#         )
#         movements = pagination.items
        
#         # 打包所有資料
#         holders_data = [{'id': h.id, 'name': h.name} for h in holders]
#         all_accounts_data = [{'id': acc.id, 'name': f"{acc.holder.name} {acc.account_name}", 'currency': acc.currency} for acc in all_accounts_query]
#         movements_data = [
#             {
#                 'date': move.move_date.strftime('%Y-%m-%d %H:%M'),
#                 'type': move.move_type,
#                 'amount': move.amount,
#                 'currency': move.currency,
#                 'from': move.from_account,
#                 'to': move.to_account,
#                 'note': move.note,
#                 'operator': move.operator
#             } for move in movements
#         ]
        
#         # (關鍵修正) 將計算好的 latest_totals，打包到回傳的 JSON 中
#         return jsonify({
#             'status': 'success',
#             'totals': latest_totals, # <-- 確保這一項存在
#             'holders': holders_data,
#             'all_accounts': all_accounts_data,
#             'movements': movements_data,
#             'pagination': {
#                 'page': pagination.page,
#                 'pages': pagination.pages,
#                 'has_prev': pagination.has_prev,
#                 'has_next': pagination.has_next,
#                 'prev_num': pagination.prev_num,
#                 'next_num': pagination.next_num
#             }
#         })
# #    except Exception as e:
# #        return jsonify({'status': 'error', 'message': str(e)}), 500

# API 2: 根據持有人 ID，查詢其名下的帳戶
@app.route('/api/cash_management/accounts_by_holder/<int:holder_id>', methods=['GET'])
@admin_required
def get_accounts_by_holder_api(holder_id):
    # --- 偵錯印記 1：看看我們收到了什麼請求 ---
    print("\n" + "="*20 + " 開始執行 get_accounts_by_holder_api " + "="*20)
    print(f">>> 請求的持有人 ID (holder_id): {holder_id}")

    try:
        # --- 偵錯印記 2：執行資料庫查詢 ---
        print(f">>> 準備查詢 holder_id 為 {holder_id} 的所有 active CashAccount...")
        accounts = CashAccount.query.filter_by(holder_id=holder_id, is_active=True).order_by(CashAccount.account_name).all()
        
        # --- 偵錯印記 3：看看查詢到了多少筆資料 ---
        print(f">>> 查詢完畢，共找到 {len(accounts)} 個帳戶。")

        # --- 偵錯印記 4：準備要回傳給前端的資料 ---
        print(">>> 準備開始打包 JSON 資料...")
        accounts_data = [
            {
                'id': acc.id,
                'name': acc.account_name,
                'currency': acc.currency,
                'balance': acc.balance
            } 
            for acc in accounts
        ]
        print(f">>> 已成功打包 JSON 資料: {accounts_data}")
        
        print("="*20 + " 結束執行 get_accounts_by_holder_api (成功) " + "="*20 + "\n")
        # (關鍵修正) 我們需要確保回傳的是一個合法的 JSON Response
        return jsonify(accounts_data)

    except Exception as e:
        # --- 偵錯印記 5 (如果發生了連我們都沒想到的錯誤) ---
        print(f"\n!!! 在 get_accounts_by_holder_api 中發生了嚴重錯誤 !!!")
        print(f"!!! 錯誤類型: {type(e).__name__}")
        print(f"!!! 錯誤訊息: {e}")
        import traceback
        traceback.print_exc() # 印出完整的錯誤堆疊
        
        # (關鍵修正) 即使出錯，也要回傳一個合法的 JSON 錯誤訊息
        return jsonify({'status': 'error', 'message': f'伺服器內部查詢錯誤: {e}'}), 500
    

# API 3: 負責處理所有來自 Modal 的操作請求，並在成功後返回最新的總資產
#@app.route('/api/cash_management/operations', methods=['POST'])
#@admin_required
#def manage_cash_operations_api():
    data = request.get_json()
    action = data.get('action')

    try:
        # === Holder & Account Management (新增/刪除的邏輯不變) ===
        if action == 'add_holder':
            # ... (此處邏輯與您現有的版本完全相同)
            name = data.get('name', '').strip()
            if not name: return jsonify({'status': 'error', 'message': '持有人名稱不可為空'}), 400
            if Holder.query.filter_by(name=name).first(): return jsonify({'status': 'error', 'message': '此持有人已存在'}), 409
            new_holder = Holder(name=name)
            db.session.add(new_holder)

        elif action == 'delete_holder':
            # ... (此處邏輯與您現有的版本完全相同)
            holder_id = data.get('id')
            holder = db.session.get(Holder, holder_id)
            if holder: db.session.delete(holder)
        
        elif action == 'add_account':
            # ... (此處邏輯與您現有的版本完全相同)
            holder_id = data.get('holder_id')
            name = data.get('name', '').strip()
            currency = data.get('currency')
            if not all([holder_id, name, currency]): return jsonify({'status': 'error', 'message': '資料不完整'}), 400
            new_account = CashAccount(holder_id=holder_id, account_name=name, currency=currency)
            db.session.add(new_account)

        elif action == 'delete_account':
            # ... (此處邏輯與您現有的版本完全相同)
            account_id = data.get('id')
            account = db.session.get(CashAccount, account_id)
            if account: db.session.delete(account)
            
        # === Fund Operations (資金操作的邏輯不變) ===
        elif action == 'update_balance':
            # ... (此處邏輯與您現有的版本完全相同)
            account_id = int(data.get('account_id'))
            new_balance = float(data.get('new_balance'))
            account = db.session.get(CashAccount, account_id)
            account.balance = new_balance
            db.session.add(FundMovement(move_type='餘額校準', amount=new_balance, currency=account.currency, to_account=f"{account.holder.name} {account.account_name}", operator=current_user.username, note=data.get('note', '手動修改餘額')))
        
        elif action == 'add_movement':
            # ... (此處邏輯與您現有的版本完全相同)
            account_id = int(data.get('account_id'))
            amount = float(data.get('amount'))
            is_decrease = data.get('is_decrease') == 'true'
            note = data.get('note', '')
            account = db.session.get(CashAccount, account_id)
            if is_decrease:
                account.balance -= amount
                db.session.add(FundMovement(move_type='支出', amount=amount, currency=account.currency, from_account=f"{account.holder.name} {account.account_name}", operator=current_user.username, note=note))
            else:
                account.balance += amount
                db.session.add(FundMovement(move_type='存入', amount=amount, currency=account.currency, to_account=f"{account.holder.name} {account.account_name}", operator=current_user.username, note=note))

        elif action == 'transfer_funds':
            # ... (此處邏-輯與您現有的版本完全相同)
            from_id = int(data.get('from_account_id'))
            to_id = int(data.get('to_account_id'))
            amount = float(data.get('transfer_amount'))
            from_acc = db.session.get(CashAccount, from_id)
            to_acc = db.session.get(CashAccount, to_id)
            if from_acc.currency != to_acc.currency: return jsonify({'status': 'error', 'message': '不同幣別帳戶不可撥交'}), 400
            from_acc.balance -= amount
            to_acc.balance += amount
            db.session.add(FundMovement(move_type='內部撥交', amount=amount, currency=from_acc.currency, from_account=f"{from_acc.holder.name} {from_acc.account_name}", to_account=f"{to_acc.holder.name} {to_acc.account_name}", operator=current_user.username, note=data.get('note')))

        else:
             return jsonify({'status': 'error', 'message': '無效的操作'}), 400

        # === (關鍵修正) 在所有操作的最後，提交變更並重新計算總額 ===
        db.session.commit()

        # 重新查詢所有帳戶，計算最新的總資產
        all_accounts = CashAccount.query.all()
        total_twd = sum(acc.balance for acc in all_accounts if acc.currency == 'TWD')
        total_rmb = sum(acc.balance for acc in all_accounts if acc.currency == 'RMB')
        latest_totals = {'twd': total_twd, 'rmb': total_rmb}
        
        # 將最新的總資產，連同成功訊息一起返回給前端
        return jsonify({
            'status': 'success', 
            'message': '操作成功',
            'totals': latest_totals 
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'伺服器錯誤: {str(e)}'}), 500

# ===================================================================
# 8. 啟動器
# ===================================================================
if __name__ == '__main__':
    app.run(debug=True)