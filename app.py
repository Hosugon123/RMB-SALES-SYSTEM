import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import math

# ===================================================================
# 1. App、資料庫、登入管理器 的基礎設定
# ===================================================================
app = Flask(__name__)

# --- App Config ---
app.config['SECRET_KEY'] = 'a_very_secret_key_that_should_be_changed_in_production'
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'sales_system.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- 初始化擴充 ---
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
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
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    accounts_receivable = db.Column(db.Float, default=0.0)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    rmb_amount = db.Column(db.Float, nullable=False)
    twd_amount = db.Column(db.Float, nullable=False)
    buy_rate = db.Column(db.Float)
    sell_rate = db.Column(db.Float)
    order_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    source_channel_name = db.Column(db.String(100))
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    operator_name = db.Column(db.String(80))
    note = db.Column(db.Text)
    customer = db.relationship('User', backref=db.backref('transactions', lazy=True))

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    id = db.Column(db.Integer, primary_key=True)
    buy_rate = db.Column(db.Float, nullable=False)
    sell_rate = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CashAccount(db.Model):
    __tablename__ = 'cash_accounts'
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(100), unique=True, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    balance = db.Column(db.Float, default=0.0)

# (其他模型如 FundMovement, CardPurchase 可在未來依此格式加入)

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
# 4. 資料庫初始化指令
# ===================================================================
@app.cli.command('init-db')
def init_db_command():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('asdf1234555', method='pbkdf2:sha256'),
            is_admin=True
        )
        db.session.add(admin_user)

        # 建立預設匯率
        default_rate = ExchangeRate(buy_rate=4.3, sell_rate=4.4)
        db.session.add(default_rate)

        # 建立預設現金帳戶
        initial_accounts = {'RMB現金': 'RMB', 'TWD現金': 'TWD'}
        for name, currency in initial_accounts.items():
            account = CashAccount(account_name=name, currency=currency, balance=0)
            db.session.add(account)

        db.session.commit()
    print('資料庫已成功初始化。')

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
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and user.is_admin and user.password_hash and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('登入失敗，請檢查帳號或密碼。', 'danger')
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
@admin_required
def admin_dashboard():
    # 這裡的邏輯需要用 ORM 重寫
    total_twd_cash = db.session.query(db.func.sum(CashAccount.balance)).filter(CashAccount.currency == 'TWD').scalar() or 0
    total_rmb_cash = db.session.query(db.func.sum(CashAccount.balance)).filter(CashAccount.currency == 'RMB').scalar() or 0
    
    rate = ExchangeRate.query.order_by(ExchangeRate.last_updated.desc()).first()
    current_buy_rate = rate.buy_rate if rate else 0
    
    total_assets_twd = total_twd_cash + (total_rmb_cash * current_buy_rate)
    pending_orders_count = Transaction.query.filter_by(status='待收款').count()
    total_receivables_twd = db.session.query(db.func.sum(Transaction.twd_amount)).filter_by(status='待收款').scalar() or 0
    recent_pending_txs = Transaction.query.filter_by(status='待收款').order_by(Transaction.order_time.desc()).limit(5).all()
    
    # 簡化圖表數據
    monthly_sales_data = {'labels': [], 'data': []}

    return render_template('admin.html', 
                           total_assets_twd=total_assets_twd,
                           pending_orders_count=pending_orders_count,
                           total_receivables_twd=total_receivables_twd,
                           total_rmb_stock=total_rmb_cash,
                           recent_pending_txs=recent_pending_txs,
                           monthly_sales_data=monthly_sales_data)

@app.route('/general_ledger')
@admin_required
def general_ledger():
    customers = User.query.filter_by(is_admin=False, is_active=True).order_by(User.username).all()
    return render_template('general_ledger.html', customers=customers)

# (其他頁面路由的 placeholder，您可以後續將它們的邏輯用 ORM 實現)
@app.route('/admin/sales_entry')
@admin_required
def sales_entry():
    # ... 未來實現 ...
    return "此頁面待開發"

@app.route('/admin/card_accounting')
@admin_required
def card_accounting():
    # ... 未來實現 ...
    return "此頁面待開發"

@app.route('/admin/transactions')
@admin_required
def admin_transactions():
    # ... 未來實現 ...
    return "此頁面待開發"

@app.route('/admin/cash_management')
@admin_required
def cash_management():
    # ... 未來實現 ...
    return "此頁面待開發"

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

@app.route('/record_purchase_ajax', methods=['POST'])
@admin_required
def record_purchase_ajax():
    data = request.get_json()
    try:
        channel_name = data.get('channel_name')
        rmb_amount = float(data.get('rmb_amount', 0))
        buy_rate = float(data.get('buy_rate', 0))
        if not all([channel_name, rmb_amount > 0, buy_rate > 0]):
            return jsonify({'status': 'error', 'message': '資料不完整或無效。'}), 400
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': '金額或匯率格式不正確。'}), 400

    try:
        new_purchase = Transaction(
            transaction_type='buy', status='已入帳',
            source_channel_name=channel_name,
            rmb_amount=rmb_amount, twd_amount=rmb_amount * buy_rate,
            buy_rate=buy_rate, operator_name=current_user.username,
            order_time=datetime.utcnow()
        )
        db.session.add(new_purchase)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'成功紀錄一筆從 "{channel_name}" 的買入交易！'})
    except Exception as e:
        db.session.rollback()
        print(f"Error in record_purchase_ajax: {e}")
        return jsonify({'status': 'error', 'message': f'資料庫儲存失敗: {str(e)}'}), 500

# ===================================================================
# 8. 啟動器
# ===================================================================
if __name__ == '__main__':
    app.run(debug=True)