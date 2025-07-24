import os
import datetime
from functools import wraps
import sqlite3
import math
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask import request, jsonify
import psycopg2
from psycopg2.extras import DictCursor
from flask import g
from . import db
from .models import Transaction
from datetime import datetime
from flask_login import current_user, login_required


app = Flask(__name__)
app.secret_key = 'asdf1234555' 
DATABASE = os.path.join(app.instance_path, 'sales_system.db')
DATABASE_URL = os.environ.get('DATABASE_URL')


instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)

db_path = os.path.join(instance_path, 'sales_system.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
# 1. 設定一個密鑰，用於保護 session 和 cookie
app.config['SECRET_KEY'] = 'dev' # 開發時可以使用 'dev'，部署時應更換為一個複雜的隨機字串

# 2. 設定資料庫檔案的路徑
#    'sqlite:///instance/sales_system.db' 的意思是：
#    - sqlite:///: 表示我們要使用 SQLite 資料庫
#    - instance/sales_system.db: 表示資料庫檔案將被存放在專案根目錄下的一個名為 'instance' 的資料夾中，
#      檔案名稱為 'sales_system.db'。
#      這個 instance 資料夾如果不存在，Flask 會在第一次執行時自動建立。
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/sales_system.db'

# 3. (可選但建議) 關閉一個即將被棄用的功能，可以節省資源並避免警告訊息
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    # User 是您在 models.py 或 app.py 中定義的使用者模型類別名稱
    # 請確保名稱完全一致
    return User.query.get(int(user_id))

os.makedirs(app.instance_path, exist_ok=True)

# --- 資料庫初始化函數 (與上一版相同) ---
def init_db():
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        
        # --- 建立所有 10 张表 ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT 0, accounts_receivable REAL NOT NULL DEFAULT 0.0,
                is_active BOOLEAN NOT NULL DEFAULT 1 
            )
        ''')
        cursor.execute('CREATE TABLE IF NOT EXISTS exchange_rates (id INTEGER PRIMARY KEY AUTOINCREMENT, buy_rate REAL NOT NULL, sell_rate REAL NOT NULL, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        cursor.execute('CREATE TABLE IF NOT EXISTS payment_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_name TEXT UNIQUE NOT NULL, channel_type TEXT NOT NULL, details TEXT, is_active BOOLEAN NOT NULL DEFAULT 1)')
        cursor.execute('CREATE TABLE IF NOT EXISTS outward_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_name TEXT UNIQUE NOT NULL, channel_type TEXT NOT NULL, details TEXT, current_balance_rmb REAL NOT NULL DEFAULT 0.0, is_active BOOLEAN NOT NULL DEFAULT 1, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        cursor.execute('CREATE TABLE IF NOT EXISTS cash_accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, account_name TEXT UNIQUE NOT NULL, currency TEXT NOT NULL, balance REAL NOT NULL DEFAULT 0.0, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, transaction_type TEXT NOT NULL,
                order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, rmb_amount REAL NOT NULL, twd_amount REAL NOT NULL,
                exchange_rate REAL NOT NULL, note TEXT, customer_id INTEGER, source_channel_id INTEGER, status TEXT,
                outward_channel_id INTEGER, actual_outward_rmb REAL,
                FOREIGN KEY (user_id) REFERENCES users (id), FOREIGN KEY (customer_id) REFERENCES users (id),
                FOREIGN KEY (source_channel_id) REFERENCES purchase_sources (id), FOREIGN KEY (outward_channel_id) REFERENCES outward_channels (id)
            )
        ''')
        
        cursor.execute('CREATE TABLE IF NOT EXISTS card_purchases (id INTEGER PRIMARY KEY AUTOINCREMENT, purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, card_type TEXT NOT NULL, twd_amount REAL NOT NULL, rmb_received REAL NOT NULL, twd_rate_effective REAL NOT NULL, transaction_fee REAL NOT NULL, cashback_amount REAL NOT NULL, net_cost_per_rmb REAL NOT NULL, supplier TEXT, handled_by TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS fund_movements (id INTEGER PRIMARY KEY AUTOINCREMENT, move_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, from_account_id INTEGER, to_account_id INTEGER, currency TEXT NOT NULL, amount REAL NOT NULL, source_type TEXT NOT NULL, description TEXT, handled_by TEXT, FOREIGN KEY (from_account_id) REFERENCES cash_accounts (id), FOREIGN KEY (to_account_id) REFERENCES cash_accounts (id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS dividends (id INTEGER PRIMARY KEY AUTOINCREMENT, dividend_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, amount REAL NOT NULL, currency TEXT NOT NULL DEFAULT "TWD", description TEXT, handled_by TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS purchase_sources (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1)')

        # --- 初始化预设资料 ---
        cursor.execute("SELECT * FROM users WHERE username = ?", ('admin',))
        if cursor.fetchone() is None:
            admin_password_hash = generate_password_hash('asdf1234555')
            cursor.execute("INSERT INTO users (username, password_hash, is_admin, is_active) VALUES (?, ?, ?, ?)", ('admin', admin_password_hash, 1, 1))
        
        initial_accounts = {
            '許 現金 (TWD)': 'TWD', '許 支付寶 (RMB)': 'RMB', '林 現金 (TWD)': 'TWD', '林 台新 (TWD)': 'TWD', '林 支付寶 (RMB)': 'RMB',
            '陳 現金 (TWD)': 'TWD', '陳 台新 (TWD)': 'TWD', '陳 台銀 (TWD)': 'TWD', '陳 支付寶 (RMB)': 'RMB', '陳 銀行卡 (RMB)': 'RMB', '成 台新 (TWD)': 'TWD'
        }
        for name, currency in initial_accounts.items():
            cursor.execute("SELECT id FROM cash_accounts WHERE account_name = ?", (name,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO cash_accounts (account_name, currency) VALUES (?, ?)", (name, currency))
        
        conn.commit()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True) # 用於軟刪除
    is_customer = db.Column(db.Boolean, default=False) # 區分是否為客戶/渠道
    
    # 讓密碼變成只能寫入、不能讀取
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    # 設定密碼時，自動進行雜湊加密
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # 驗證密碼是否正確
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# --- 輔助函式 (與上一版相同) ---
def get_db():
    """
    獲取資料庫連線。
    如果在 g (請求的全域物件) 中沒有 db 連線，就建立一個。
    優先使用 PostgreSQL (當 DATABASE_URL 存在時)，否則回退到本地 SQLite。
    """
    if 'db' not in g:
        if DATABASE_URL:
            # 在 Render.com 或其他雲端環境
            g.db = psycopg2.connect(DATABASE_URL)
        else:
            # 在本地開發環境
            instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
            os.makedirs(instance_path, exist_ok=True)
            db_path = os.path.join(instance_path, 'sales_system.db')
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row # 讓 SQLite 回傳的結果可以像字典一樣用欄位名存取
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """在請求處理結束後，自動關閉資料庫連線。"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# 輔助函式，用於統一 SQL 查詢語法
def query_db(query, args=(), one=False):
    """
    執行資料庫查詢，自動處理佔位符 '?' 或 '%s' 的轉換。
    - query: SQL 查詢語句 (統一使用 '?' 作為佔位符)
    - args: 查詢參數的元組
    - one: 如果為 True，則只返回第一條結果，否則返回所有結果
    """
    db = get_db()
    
    # 根據資料庫類型，轉換 SQL 查詢語句的佔位符
    if DATABASE_URL: # PostgreSQL 使用 %s
        query = query.replace('?', '%s')
    
    cur = db.cursor(cursor_factory=DictCursor if DATABASE_DOCKER_URL else None)
    cur.execute(query, args)
    
    # 獲取查詢結果
    results = cur.fetchall()
    
    # 提交事務（對於 SELECT 來說不是必須的，但對於 INSERT/UPDATE/DELETE 是）
    db.commit() 
    cur.close()
    
    if one:
        return results[0] if results else None
    return results

# ==============================================================================
#  使用者認證與權限 (Authentication & Authorization)
# ==============================================================================

def login_required(f):
    """裝飾器：確保使用者已登入。"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('請先登入！', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """裝飾器：確保使用者是管理員。"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 先檢查是否登入
        if 'user_id' not in session:
            flash('請先登入！', 'danger')
            return redirect(url_for('login'))
        # 再檢查是否為管理員
        if not session.get('is_admin'):
            flash('您沒有權限訪問此頁面！', 'danger')
            # 如果有一般使用者的儀表板，可以導向那裡
            # return redirect(url_for('user_dashboard')) 
            return redirect(url_for('index')) # 或者直接導回首頁
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
#  核心路由 (Core Routes)
# ==============================================================================

@app.route('/')
def index():
    if 'user_id' in session:
        # 如果是管理員，導向管理員儀表板，否則導向登出（或未來的使用者儀表板）
        return redirect(url_for('admin_dashboard') if session.get('is_admin') else url_for('logout'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 使用新的 query_db 函式來查詢
        user = query_db(
            "SELECT id, password_hash, is_admin, username FROM users WHERE username = ? AND is_active = 1",
            (username,),
            one=True
        )
        
        if user and check_password_hash(user['password_hash'], password):
            session.clear() # 登入前先清空 session，更安全
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            flash('登入成功！', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('用戶名或密碼不正確，或帳號已被停用！', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('您已成功登出！', 'info')
    return redirect(url_for('login'))

# --- 管理員路由 ---

# (此處到 `admin_sales_action` 之前的所有路由都與上一版相同，保持不動)
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db()
    total_assets_row = conn.execute("SELECT SUM(CASE WHEN currency = 'TWD' THEN balance ELSE 0 END) as twd, SUM(CASE WHEN currency = 'RMB' THEN balance ELSE 0 END) as rmb FROM cash_accounts").fetchone()
    rate_row = conn.execute("SELECT buy_rate FROM exchange_rates ORDER BY last_updated DESC LIMIT 1").fetchone()
    current_buy_rate = rate_row['buy_rate'] if rate_row else 0.0
    total_twd = total_assets_row['twd'] if total_assets_row and total_assets_row['twd'] else 0
    total_rmb_in_twd = (total_assets_row['rmb'] * current_buy_rate) if total_assets_row and total_assets_row['rmb'] else 0
    estimated_cash = total_twd + total_rmb_in_twd
    
    rmb_outward_row = conn.execute("SELECT SUM(current_balance_rmb) FROM outward_channels").fetchone()
    rmb_cash_row = conn.execute("SELECT SUM(balance) FROM cash_accounts WHERE currency = 'RMB'").fetchone()
    total_rmb_stock = (rmb_outward_row[0] or 0) + (rmb_cash_row[0] or 0)

    pending_transactions_count = conn.execute("SELECT COUNT(id) FROM transactions WHERE transaction_type = 'sell' AND status = '待收款'").fetchone()[0]
    unsettled_amount_row = conn.execute("SELECT SUM(twd_amount) FROM transactions WHERE transaction_type = 'sell' AND status = '待收款'").fetchone()
    total_unsettled_amount = unsettled_amount_row[0] if unsettled_amount_row and unsettled_amount_row[0] is not None else 0.0

    recent_pending_txs = conn.execute("""
        SELECT t.id, t.twd_amount, u.username FROM transactions t JOIN users u ON t.customer_id = u.id 
        WHERE t.transaction_type = 'sell' AND t.status = '待收款' AND u.is_active = 1 
        ORDER BY t.order_time DESC LIMIT 5
    """).fetchall()

    sales_data_rows = conn.execute("""
        SELECT strftime('%Y-%m', order_time) as month, SUM(rmb_amount) as total_sales FROM transactions 
        WHERE transaction_type = 'sell' AND status != '已取消' AND order_time >= date('now', '-6 months') 
        GROUP BY month ORDER BY month ASC
    """).fetchall()
    
    chart_labels = [row['month'] for row in sales_data_rows]
    chart_data = [row['total_sales'] for row in sales_data_rows]
    monthly_sales_data = {'labels': chart_labels, 'data': chart_data}
    
    conn.close()
    
    return render_template('admin.html', 
                           username=session['username'], estimated_cash=estimated_cash, 
                           pending_transactions_count=pending_transactions_count, 
                           total_unsettled_amount=total_unsettled_amount, 
                           total_rmb_stock=total_rmb_stock, 
                           recent_pending_txs=recent_pending_txs, 
                           monthly_sales_data=monthly_sales_data)

@app.route('/admin/card_accounting', methods=['GET', 'POST'])
@admin_required
def card_accounting():
    conn = get_db()
    if request.method == 'POST':
        try:
            purchase_date = request.form['purchase_date']
            rmb_amount = float(request.form['rmb_amount'])
            twd_equivalent = float(request.form['twd_equivalent'])
            supplier = request.form.get('supplier', '')
            handled_by = session['username']
            rmb_with_fee = rmb_amount * 1.03
            twd_rate_effective = twd_equivalent / rmb_with_fee if rmb_with_fee > 0 else 0
            net_twd_cost = twd_equivalent
            net_cost_per_rmb = net_twd_cost / rmb_amount if rmb_amount > 0 else 0
            conn.execute( 'INSERT INTO card_purchases (purchase_date, card_type, twd_amount, rmb_received, twd_rate_effective, transaction_fee, cashback_amount, net_cost_per_rmb, supplier, handled_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (purchase_date, '手動記帳', twd_equivalent, rmb_amount, twd_rate_effective, 0, 0, net_cost_per_rmb, supplier, handled_by))
            conn.execute("UPDATE exchange_rates SET buy_rate = ?, last_updated = ? WHERE id = 1", (twd_rate_effective, datetime.datetime.now()))
            conn.commit()
            flash(f'記帳成功！新的買入匯率已更新為 {twd_rate_effective:.4f}。', 'success')
        except Exception as e: flash(f'記帳失敗：{e}', 'danger')
        finally: conn.close()
        return redirect(url_for('card_accounting'))
    realtime_rates = conn.execute("SELECT buy_rate, sell_rate FROM exchange_rates ORDER BY last_updated DESC LIMIT 1").fetchone()
    all_purchases = conn.execute("SELECT * FROM card_purchases ORDER BY purchase_date DESC").fetchall()
    conn.close()
    return render_template('card_accounting.html', realtime_rates=realtime_rates, all_purchases=all_purchases, today=datetime.date.today().isoformat())

@app.route('/admin/update_rates_ajax', methods=['POST'])
@admin_required
def update_rates_ajax():
    try:
        data = request.get_json()
        new_buy_rate = float(data['buy_rate']); new_sell_rate = float(data['sell_rate'])
        if new_buy_rate <= 0 or new_sell_rate <= 0: return jsonify({'status': 'error', 'message': '匯率必須為正數'}), 400
        conn = get_db()
        conn.execute("UPDATE exchange_rates SET buy_rate = ?, sell_rate = ?, last_updated = ? WHERE id = 1", (new_buy_rate, new_sell_rate, datetime.datetime.now()))
        conn.commit(); conn.close()
        return jsonify({'status': 'success', 'message': '匯率更新成功!'})
    except Exception as e: return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/inventory_purchase', methods=['GET', 'POST'])
@admin_required
def inventory_purchase():
    conn = get_db()
    converted_amount, input_amount, input_currency, output_currency = None, None, None, None
    if request.method == 'POST':
        try:
            purchase_currency = request.form['purchase_currency']; purchase_amount = float(request.form['purchase_amount']); target_currency = request.form['target_currency']
            input_amount, input_currency, output_currency = purchase_amount, purchase_currency, target_currency
            rates = conn.execute("SELECT buy_rate, sell_rate FROM exchange_rates ORDER BY last_updated DESC LIMIT 1").fetchone()
            buy_rate, sell_rate = (rates['buy_rate'], rates['sell_rate']) if rates else (0.0, 0.0)
            if purchase_currency == 'TWD' and target_currency == 'RMB': converted_amount = purchase_amount / sell_rate if sell_rate > 0 else 0 
            elif purchase_currency == 'RMB' and target_currency == 'TWD': converted_amount = purchase_amount * buy_rate 
            else: flash('不支援的換算組合！', 'danger')
            if converted_amount is not None: flash(f'換算完成：{purchase_amount:.2f} {purchase_currency} = {converted_amount:.2f} {target_currency}。', 'info')
        except ValueError: flash('請輸入有效的數字金額。', 'danger')
    rates = conn.execute("SELECT buy_rate, sell_rate FROM exchange_rates ORDER BY last_updated DESC LIMIT 1").fetchone()
    conn.close()
    return render_template('inventory_purchase.html', current_buy_rate=rates['buy_rate'] if rates else 0.0, current_sell_rate=rates['sell_rate'] if rates else 0.0, converted_amount=converted_amount, input_amount=input_amount, input_currency=input_currency, output_currency=output_currency)

@app.route('/admin/add_customer_ajax', methods=['POST'])
@admin_required
def add_customer_ajax():
    data = request.get_json()
    new_username = data.get('username')

    # 【臥底回報 #1】讓我們看看收到的客戶名稱是什麼
    print(f"--- 收到新增請求：使用者名稱為 '{new_username}' ---")

    if not new_username:
        return jsonify({'status': 'error', 'message': '客戶名稱不能為空'}), 400

    conn = get_db()
    try:
        existing_user = conn.execute("SELECT id, is_active FROM users WHERE username = ?", (new_username,)).fetchone()

        if existing_user:
            # 【臥底回報 #2】如果使用者存在，讓我們看看他的狀態
            print(f"--- 資料庫中找到使用者：ID={existing_user['id']}, is_active={existing_user['is_active']} ---")

            if existing_user['is_active']:
                # 【臥底回報 #3】程式判斷此使用者為活躍狀態
                print("--- 判斷：使用者為活躍狀態，回傳「名稱已使用」錯誤。---")
                return jsonify({'status': 'error', 'message': '此客戶名稱已被使用'}), 400
            else:
                user_id_to_restore = existing_user['id']
                conn.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user_id_to_restore,))
                conn.commit()
                # 【臥底回報 #4】程式判斷應恢復使用者
                print("--- 判斷：使用者為非活躍狀態，執行恢復操作。---")
                return jsonify({
                    'status': 'success', 
                    'message': f'客戶 "{new_username}" 已成功恢復！',
                    'customer': {'id': user_id_to_restore, 'username': new_username}
                })
        else:
            # 【臥底回報 #5 - 如果上面的臥底沒出動，代表要新增】
            print("--- 判斷：資料庫中未找到使用者，執行全新新增操作。---")
            password_hash = generate_password_hash(data.get('password', 'asdf1234555'))
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash, is_admin, is_active) VALUES (?, ?, ?, ?)", 
                           (new_username, password_hash, 0, 1))
            new_user_id = cursor.lastrowid
            conn.commit()
            
            return jsonify({
                'status': 'success', 
                'message': f'客戶 "{new_username}" 新增成功!',
                'customer': {'id': new_user_id, 'username': new_username}
            })

    except Exception as e:
        conn.rollback()
        # 【臥底回報 #E - 如果發生任何錯誤】
        print(f"--- 發生未知錯誤：{e} ---")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/delete_customer_ajax', methods=['POST'])
@admin_required
def delete_customer_ajax():
    data = request.get_json()
    customer_id = data.get('customer_id')

    if not customer_id:
        return jsonify({'status': 'error', 'message': '未提供客戶ID'}), 400

    conn = get_db()
    try:
        # 檢查是否有 "待收款" 的交易，若有則不允許隱藏
        pending_tx = conn.execute("SELECT 1 FROM transactions WHERE user_id = ? AND status = '待收款' LIMIT 1", (customer_id,)).fetchone()
        if pending_tx:
            return jsonify({'status': 'error', 'message': '無法隱藏：該客戶尚有「待收款」的交易未完成。'}), 400
        
        # 【這就是被修正的地方】執行軟刪除：將 is_active 設為 0
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active = 0 WHERE id = ? AND is_admin = 0", (customer_id,))
        
        # 檢查是否有成功更新到資料 (rowcount > 0)
        if cursor.rowcount > 0:
            conn.commit()
            print(f"--- 成功軟刪除 (隱藏) 使用者 ID: {customer_id} ---") # 加入成功日誌
            return jsonify({'status': 'success', 'message': '客戶已從常用列表隱藏!'})
        else:
            # 如果 rowcount 是 0，代表沒有找到對應的 ID 或他不是一個普通用戶
            conn.rollback()
            print(f"--- 軟刪除失敗：找不到使用者 ID: {customer_id} 或該用戶為管理員 ---") # 加入失敗日誌
            return jsonify({'status': 'error', 'message': '找不到該客戶或該用戶是管理員'}), 404
            
    except Exception as e:
        conn.rollback()
        print(f"--- 軟刪除時發生未知錯誤：{e} ---") # 加入錯誤日誌
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/sales/action', methods=['POST'])
@admin_required
def admin_sales_action():
    conn = get_db()
    try:
        data = request.form
        action = data.get('action')
        
        if action == 'create_order':
            user_id = data.get('user_id')
            customer_name = data.get('customer_name')
            if not customer_name: raise ValueError("客戶名稱為必填欄位")

            if not user_id:
                existing_user = conn.execute("SELECT id, is_active FROM users WHERE username = ?", (customer_name,)).fetchone()
                if existing_user:
                    if not existing_user['is_active']:
                        conn.execute("UPDATE users SET is_active = 1 WHERE id = ?", (existing_user['id'],))
                    user_id = existing_user['id']
                else:
                    password_hash = generate_password_hash('asdf1234555')
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, password_hash, is_admin, is_active) VALUES (?, ?, ?, ?)", (customer_name, password_hash, 0, 1))
                    user_id = cursor.lastrowid
            
            rmb_sell_amount = float(data.get('rmb_sell_amount'))
            order_date = data.get('order_date', datetime.date.today().isoformat())
            sell_rate_at_order = float(data.get('exchange_rate')) 
            if rmb_sell_amount <= 0 or sell_rate_at_order <= 0: raise ValueError("售出金額或匯率必須為正數")
            twd_expected_payment = rmb_sell_amount * sell_rate_at_order
            cursor = conn.cursor()
            cursor.execute('INSERT INTO transactions (user_id, rmb_order_amount, twd_expected_payment, exchange_rate, order_time, status) VALUES (?, ?, ?, ?, ?, ?)',
                           (user_id, rmb_sell_amount, twd_expected_payment, sell_rate_at_order, order_date, '待收款'))
            new_tx_id = cursor.lastrowid
            conn.execute("UPDATE users SET accounts_receivable = accounts_receivable + ? WHERE id = ?", (twd_expected_payment, user_id))
            conn.commit()
            new_tx = conn.execute("SELECT t.*, u.username FROM transactions t JOIN users u ON t.user_id = u.id WHERE t.id = ?", (new_tx_id,)).fetchone()
            return jsonify({'status': 'success', 'message': f'訂單 #{new_tx_id} 創建成功!', 'transaction': dict(new_tx)})

        elif action == 'settle_order':
            transaction_id = data.get('transaction_id')
            # ... (結帳邏輯省略)
            return jsonify({'status': 'success', 'message': f'交易 #{transaction_id} 結帳成功!', 'settled_id': transaction_id})
        
        elif action == 'delete_order':
            transaction_id = data.get('transaction_id')
            # ... (刪除訂單邏輯省略)
            return jsonify({'status': 'success', 'message': f'訂單 #{transaction_id} 已成功刪除!', 'deleted_id': transaction_id})
        else:
            raise ValueError("無效的操作")

    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400
    finally:
        conn.close()
# (此處之後的所有路由都與上一版相同，保持不動)
@app.route('/admin/sales_entry')
@admin_required
def sales_entry():
    conn = get_db()
    customers = conn.execute("SELECT id, username FROM users WHERE is_admin = 0 AND is_active = 1 ORDER BY username").fetchall()
    rates = conn.execute("SELECT sell_rate FROM exchange_rates ORDER BY last_updated DESC LIMIT 1").fetchone()
    pending_sales = conn.execute("SELECT t.*, u.username FROM transactions t JOIN users u ON t.user_id = u.id WHERE t.status = '待收款' ORDER BY t.order_time DESC").fetchall()
    conn.close()
    return render_template('sales_entry.html', customers=customers, sell_rate=rates['sell_rate'] if rates else 0.0, pending_sales=pending_sales, today=datetime.date.today().isoformat())

@app.route('/admin/cash/update', methods=['POST'])
@admin_required
def admin_update_cash_account():
    conn = get_db()
    try:
        data = request.form; action = data.get('action'); handled_by = session['username']
        conn.execute("BEGIN TRANSACTION")
        if action == 'update_balance':
            account_id = data.get('account_id'); new_balance = float(data.get('new_balance'))
            conn.execute("UPDATE cash_accounts SET balance = ?, last_updated = ? WHERE id = ?", (new_balance, datetime.datetime.now(), account_id))
            message = "餘額更新成功！"
        elif action == 'add_movement':
            account_id = data.get('account_id'); amount = float(data.get('amount')); movement_type = data.get('movement_type'); description = data.get('description', ''); is_decrease = data.get('is_decrease') == 'true'
            account = conn.execute("SELECT currency FROM cash_accounts WHERE id = ?", (account_id,)).fetchone()
            if not account: raise ValueError("找不到指定的帳戶")
            final_amount = -abs(amount) if is_decrease else abs(amount)
            conn.execute("UPDATE cash_accounts SET balance = balance + ? WHERE id = ?", (final_amount, account_id))
            conn.execute('INSERT INTO fund_movements (to_account_id, currency, amount, source_type, description, handled_by) VALUES (?, ?, ?, ?, ?, ?)',(account_id, account['currency'], final_amount, movement_type, description, handled_by))
            message = "資金流動記錄成功！"
        elif action == 'transfer_funds':
            from_id = data.get('from_account_id'); to_id = data.get('to_account_id'); amount = float(data.get('transfer_amount'))
            if from_id == to_id: raise ValueError("來源和目標帳戶不能相同")
            from_acc = conn.execute("SELECT * FROM cash_accounts WHERE id = ?", (from_id,)).fetchone()
            to_acc = conn.execute("SELECT * FROM cash_accounts WHERE id = ?", (to_id,)).fetchone()
            if not from_acc or not to_acc or from_acc['currency'] != to_acc['currency']: raise ValueError("帳戶錯誤或幣別不符")
            if from_acc['balance'] < amount: raise ValueError("來源帳戶餘額不足")
            conn.execute("UPDATE cash_accounts SET balance = balance - ? WHERE id = ?", (amount, from_id))
            conn.execute("UPDATE cash_accounts SET balance = balance + ? WHERE id = ?", (amount, to_id))
            conn.execute('INSERT INTO fund_movements (from_account_id, to_account_id, currency, amount, source_type, handled_by) VALUES (?, ?, ?, ?, ?, ?)',(from_id, to_id, from_acc['currency'], amount, '內部撥交', handled_by))
            message = "資金撥交成功！"
        else: raise ValueError("無效的操作")
        conn.commit()
        all_accounts = conn.execute("SELECT * FROM cash_accounts ORDER BY currency, account_name").fetchall()
        accounts_list = [dict(row) for row in all_accounts]
        return jsonify({'status': 'success', 'message': message, 'accounts': accounts_list})
    except Exception as e: conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 400
    finally: conn.close()

@app.route('/admin/cash_management')
@admin_required
def cash_management():
    conn = get_db()
    all_accounts_rows = conn.execute("SELECT * FROM cash_accounts ORDER BY account_name").fetchall()
    total_twd = sum(acc['balance'] for acc in all_accounts_rows if acc['currency'] == 'TWD')
    total_rmb = sum(acc['balance'] for acc in all_accounts_rows if acc['currency'] == 'RMB')
    grouped_accounts = {}
    for account_row in all_accounts_rows:
        account = dict(account_row)
        account['formatted_balance'] = f"{account['balance']:,.2f}"
        person = account['account_name'].split(' ')[0]
        if person not in grouped_accounts: grouped_accounts[person] = []
        grouped_accounts[person].append(account)
    conn.close()
    return render_template('cash_management.html', total_twd=f"{total_twd:,.2f}", total_rmb=f"{total_rmb:,.2f}", grouped_accounts=grouped_accounts)

@app.route('/admin/exchange_rate', methods=['GET', 'POST'])
@admin_required
def admin_exchange_rate():
    conn = get_db()
    if request.method == 'POST':
        try:
            buy_rate = float(request.form['buy_rate']); sell_rate = float(request.form['sell_rate'])
            if buy_rate <= 0 or sell_rate <= 0: flash('匯率必須為正數！', 'danger')
            else:
                conn.execute("UPDATE exchange_rates SET buy_rate = ?, sell_rate = ?, last_updated = ? WHERE id = 1", (buy_rate, sell_rate, datetime.datetime.now()))
                conn.commit(); flash('匯率更新成功！', 'success')
        except ValueError: flash('請輸入有效的數字！', 'danger')
        except Exception as e: flash(f'更新失敗: {e}', 'danger')
        finally: conn.close()
        return redirect(url_for('admin_exchange_rate'))
    rates = conn.execute("SELECT buy_rate, sell_rate FROM exchange_rates ORDER BY last_updated DESC LIMIT 1").fetchone()
    conn.close()
    return render_template('exchange_rate.html', buy_rate=rates['buy_rate'] if rates else 0.0, sell_rate=rates['sell_rate'] if rates else 0.0)

# ===============================================================
# ==         API: Admin - Update Transaction Note (AJAX)       ==
# ===============================================================
@app.route('/admin/transaction/note/update', methods=['POST'])
@login_required
def admin_update_transaction_note():
    # 確保只有管理員可以操作
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '權限不足'}), 403

    # 獲取從前端發來的 JSON 數據
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '無效的請求，缺少資料'}), 400

    tx_id = data.get('tx_id')
    note_content = data.get('note')

    # 檢查交易 ID 是否存在
    if not tx_id:
        return jsonify({'status': 'error', 'message': '無效的請求，缺少交易ID'}), 400

    # 在資料庫中查找該筆交易
    transaction = Transaction.query.get(tx_id)
    if not transaction:
        return jsonify({'status': 'error', 'message': '找不到該筆交易'}), 404
    
    # 執行更新
    try:
        transaction.note = note_content
        db.session.commit()
        return jsonify({'status': 'success', 'message': '備註已成功更新！'})
    except Exception as e:
        # 如果發生錯誤，則回滾資料庫操作
        db.session.rollback()
        # 在伺服器日誌中記錄詳細錯誤，以便調試
        print(f"Error updating note for tx_id {tx_id}: {e}")
        return jsonify({'status': 'error', 'message': f'資料庫更新失敗'}), 500
    
# ===============================================================
# ==      API: Admin - Update Fund Movement Note (AJAX)        ==
# ===============================================================
@app.route('/admin/movement/note/update', methods=['POST'])
@login_required
def admin_update_movement_note():
    # 確保只有管理員可以操作
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '權限不足'}), 403

    # 獲取從前端發來的 JSON 數據
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '無效的請求，缺少資料'}), 400

    move_id = data.get('move_id')
    note_content = data.get('note')

    # 檢查調撥 ID 是否存在
    if not move_id:
        return jsonify({'status': 'error', 'message': '無效的請求，缺少調撥ID'}), 400

    # 在資料庫中查找該筆調撥紀錄
    # 注意：這裡我們假設您的調撥紀錄模型叫做 FundMovement
    # 如果您的模型名稱不同 (例如 Movement)，請修改下面的 'FundMovement'
    movement = FundMovement.query.get(move_id)
    if not movement:
        return jsonify({'status': 'error', 'message': '找不到該筆調撥紀錄'}), 404
    
    # 執行更新
    try:
        # 假設您的備註欄位叫做 description，如果不同請修改
        movement.description = note_content
        db.session.commit()
        return jsonify({'status': 'success', 'message': '調撥備註已成功更新！'})
    except Exception as e:
        # 如果發生錯誤，則回滾資料庫操作
        db.session.rollback()
        # 在伺服器日誌中記錄詳細錯誤，以便調試
        print(f"Error updating note for move_id {move_id}: {e}")
        return jsonify({'status': 'error', 'message': '資料庫更新失敗'}), 500
    
    # ===============================================================
# ==            API: Record Purchase (Buy) - AJAX              ==
# ===============================================================
@app.route('/admin/purchase/record', methods=['POST'])
@login_required # 我們仍然保留這個裝飾器
def record_purchase_ajax():
    # ==================== 這是唯一的修改點 ====================
    # 在執行任何操作前，先檢查使用者是否已通過認證。
    # current_user.is_authenticated 對於匿名用戶會返回 False。
    if not current_user.is_authenticated:
        # 回傳一個特定的 JSON 錯誤，讓前端可以提示使用者重新登入
        return jsonify({'status': 'error', 'message': '您的登入已過期，請重新登入後再試。', 'action': 'redirect'}), 401 # 401 Unauthorized
    # ========================================================

    # 現在我們可以安全地假設 current_user 是個真實的使用者物件了
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '權限不足'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '無效的請求，缺少 JSON 數據。'}), 400

    # (接下來的程式碼與上一版完全相同，保持不變)
    channel_name = data.get('channel_name')
    try:
        rmb_amount = float(data.get('rmb_amount', 0))
        buy_rate = float(data.get('buy_rate', 0))
        if rmb_amount <= 0 or buy_rate <= 0:
            raise ValueError("金額與匯率必須大於零")
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': '金額或匯率格式不正確。'}), 400

    if not channel_name:
        return jsonify({'status': 'error', 'message': '買入渠道名稱不可為空。'}), 400

    try:
        new_purchase = Transaction(
            transaction_type='buy',
            customer_name=channel_name,
            rmb_amount=rmb_amount,
            exchange_rate=buy_rate,
            twd_amount=rmb_amount * buy_rate,
            status='已完成',
            order_time=datetime.utcnow(),
            note=f"從 {channel_name} 買入",
            user_id=current_user.id # 假設您的模型有關聯 user_id
        )
        db.session.add(new_purchase)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'一筆從 {channel_name} 買入 ¥{rmb_amount:.2f} 的交易已成功記錄！'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error recording purchase with ORM: {e}") 
        return jsonify({'status': 'error', 'message': f'資料庫儲存失敗，請檢查後台日誌。'}), 500


# ===============================================================
# ==        API: Add Purchase Channel (User) - AJAX            ==
# ===============================================================
@app.route('/admin/add_purchase_channel_ajax', methods=['POST'])
@admin_required
def add_purchase_channel_ajax():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '無效的請求，缺少 JSON 數據。'}), 400

        customer_name = data.get('customer_name')
        if not customer_name or not customer_name.strip():
            return jsonify({'status': 'error', 'message': '渠道名稱不可為空。'}), 400
        
        customer_name = customer_name.strip()

        conn = get_db()
        existing_customer = conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 0", (customer_name,)
        ).fetchone()

        new_customer_id = None
        
        if existing_customer:
            conn.execute(
                "UPDATE users SET is_active = 1 WHERE id = ?", (existing_customer['id'],)
            )
            new_customer_id = existing_customer['id']
            message = f'渠道 "{customer_name}" 已成功從舊有紀錄中恢復！'
        else:
            active_customer = conn.execute(
                "SELECT id FROM users WHERE username = ? AND is_active = 1", (customer_name,)
            ).fetchone()
            if active_customer:
                 return jsonify({'status': 'error', 'message': f'名為 "{customer_name}" 的渠道已經存在。'}), 409

            # ==================== 這是最終的、唯一的修改點 ====================
            # 新增時，同時為 password_hash 提供一個非空的佔位符，以滿足 NOT NULL 約束
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash, is_admin, is_active) VALUES (?, ?, ?, ?)",
                (customer_name, 'placeholder_for_non_login_user', 0, 1) 
            )
            # =================================================================
            
            new_customer_id = cursor.lastrowid
            message = f'渠道 "{customer_name}" 已成功新增！'

        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': message,
            'customer': {
                'id': new_customer_id,
                'username': customer_name
            }
        })

    except Exception as e:
        print(f"Error in add_purchase_channel_ajax: {e}")
        return jsonify({'status': 'error', 'message': f'伺服器內部錯誤: {str(e)}'}), 500
# ===============================================================
# ==      API: Delete Purchase Channel (User) - AJAX           ==
# ===============================================================
@app.route('/admin/delete_purchase_channel_ajax', methods=['POST'])
@admin_required
def delete_purchase_channel_ajax():
    # 同樣使用 try...except 來捕捉所有可能的錯誤
    try:
        # 1. 安全地獲取前端發送的 JSON 數據
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '無效的請求，缺少 JSON 數據。'}), 400

        customer_id = data.get('customer_id')
        if not customer_id:
            return jsonify({'status': 'error', 'message': '未提供要刪除的渠道 ID。'}), 400

        # 2. 執行資料庫操作
        conn = get_db()
        
        # 在更新前，先查詢一次，獲取將要被刪除的渠道名稱，以便回傳給前端顯示
        customer_to_delete = conn.execute(
            "SELECT username FROM users WHERE id = ?", (customer_id,)
        ).fetchone()

        if not customer_to_delete:
            conn.close()
            return jsonify({'status': 'error', 'message': '找不到指定的渠道，可能已被刪除。'}), 404

        # 執行軟刪除 (Soft Delete)
        conn.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?", (customer_id,)
        )
        conn.commit()
        conn.close()

        deleted_name = customer_to_delete['username']

        # 3. 成功後，回傳一個標準的 JSON 響應給前端
        return jsonify({
            'status': 'success',
            'message': f'渠道 "{deleted_name}" 已被標記為非活躍。',
            'deleted_name': deleted_name # 將被刪除的名稱傳回，前端才能正確清空輸入框
        })

    except Exception as e:
        # 4. 如果發生任何錯誤，回傳 JSON 格式的錯誤訊息
        print(f"Error in delete_purchase_channel_ajax: {e}")
        return jsonify({'status': 'error', 'message': f'伺服器內部錯誤: {str(e)}'}), 500

@app.route('/admin/transactions/update', methods=['POST'])
@admin_required
def admin_update_transaction_status():
    data = request.form; action = data.get('action'); transaction_id = data.get('transaction_id'); handled_by = session['username']; now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not transaction_id or not action: return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400
    conn = get_db()
    try:
        conn.execute("BEGIN TRANSACTION")
        transaction = conn.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
        if not transaction: return jsonify({'status': 'error', 'message': '找不到此交易'}), 404
        if action == 'confirm_receipt' and transaction['status'] == '待收款':
            conn.execute("UPDATE transactions SET status = '已收款', handled_by_receipt = ?, receipt_time = ? WHERE id = ?", (handled_by, now_time, transaction_id))
            message = f'交易 #{transaction_id} 已確認收款！'
        elif action == 'confirm_outward' and transaction['status'] in ['已收款', '待匯出']:
            outward_channel_id = data.get('outward_channel_id'); actual_outward_rmb = float(data.get('actual_outward_rmb'))
            conn.execute("UPDATE transactions SET status = '已匯出', outward_channel_id = ?, actual_outward_rmb = ?, handled_by_outward = ?, outward_time = ? WHERE id = ?", (outward_channel_id, actual_outward_rmb, handled_by, now_time, transaction_id))
            conn.execute("UPDATE outward_channels SET current_balance_rmb = current_balance_rmb - ? WHERE id = ?", (actual_outward_rmb, outward_channel_id))
            message = f'交易 #{transaction_id} 已確認匯出！'
        elif action == 'mark_completed' and transaction['status'] == '已匯出':
            conn.execute("UPDATE transactions SET status = '已完成' WHERE id = ?", (transaction_id,)); message = f'交易 #{transaction_id} 已標記為完成！'
        elif action == 'cancel_transaction':
            conn.execute("UPDATE transactions SET status = '已取消', handled_by_receipt = ?, handled_by_outward = ? WHERE id = ?", (handled_by, handled_by, transaction_id))
            if transaction['status'] != '待收款': conn.execute("UPDATE users SET accounts_receivable = accounts_receivable + ? WHERE id = ?", (transaction['twd_expected_payment'], transaction['user_id']))
            if transaction['status'] == '已匯出' and transaction['outward_channel_id'] and transaction['actual_outward_rmb']: conn.execute("UPDATE outward_channels SET current_balance_rmb = current_balance_rmb + ? WHERE id = ?", (transaction['actual_outward_rmb'], transaction['outward_channel_id']))
            message = f'交易 #{transaction_id} 已取消。'
        else: return jsonify({'status': 'error', 'message': f'無效的操作或狀態不符 ({transaction["status"]})'}), 400
        conn.commit()
        new_status_row = conn.execute("SELECT status FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
        new_status = new_status_row['status'] if new_status_row else '未知'
        return jsonify({'status': 'success', 'message': message, 'new_status': new_status})
    except Exception as e: conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally: conn.close()
@app.route('/admin/transactions')
@admin_required
def admin_transactions():
    conn = get_db()
    sales_page = request.args.get('sales_page', 1, type=int)
    movements_page = request.args.get('movements_page', 1, type=int)
    cards_page = request.args.get('cards_page', 1, type=int)
    PER_PAGE = 10 

    query_sales = """
        SELECT t.id, t.transaction_type, t.rmb_amount, t.twd_amount, t.order_time, t.note, t.status,
               u_operator.username AS operator_name, ps.name AS source_channel_name, u_customer.username AS customer_name
        FROM transactions t
        JOIN users u_operator ON t.user_id = u_operator.id
        LEFT JOIN purchase_sources ps ON t.source_channel_id = ps.id
        LEFT JOIN users u_customer ON t.customer_id = u_customer.id
        WHERE t.transaction_type IN ('buy', 'sell')
    """
    total_sales_count = conn.execute(f"SELECT COUNT(*) FROM ({query_sales.replace('%', '%%')})").fetchone()[0]
    total_sales_pages = math.ceil(total_sales_count / PER_PAGE)
    sales_offset = (sales_page - 1) * PER_PAGE
    sales_transactions = conn.execute(f"{query_sales} ORDER BY t.order_time DESC LIMIT ? OFFSET ?", (PER_PAGE, sales_offset)).fetchall()

    total_movements_count = conn.execute("SELECT COUNT(id) FROM fund_movements").fetchone()[0]
    total_movements_pages = math.ceil(total_movements_count / PER_PAGE)
    movements_offset = (movements_page - 1) * PER_PAGE
    fund_movements = conn.execute("SELECT fm.*, fa.account_name as from_account_name, ta.account_name as to_account_name FROM fund_movements fm LEFT JOIN cash_accounts fa ON fm.from_account_id = fa.id LEFT JOIN cash_accounts ta ON fm.to_account_id = ta.id ORDER BY fm.move_date DESC LIMIT ? OFFSET ?", (PER_PAGE, movements_offset)).fetchall()

    total_cards_count = conn.execute("SELECT COUNT(id) FROM card_purchases").fetchone()[0]
    total_cards_pages = math.ceil(total_cards_count / PER_PAGE)
    cards_offset = (cards_page - 1) * PER_PAGE
    
    rates_row = conn.execute("SELECT sell_rate FROM exchange_rates ORDER BY last_updated DESC LIMIT 1").fetchone()
    current_sell_rate = rates_row['sell_rate'] if rates_row else 0.0
    
    card_purchases_raw = conn.execute("SELECT * FROM card_purchases ORDER BY purchase_date DESC LIMIT ? OFFSET ?", (PER_PAGE, cards_offset)).fetchall()
    card_purchases = []
    for cp in card_purchases_raw:
        cp_dict = dict(cp)
        profit = (current_sell_rate - cp_dict['net_cost_per_rmb']) * cp_dict['rmb_received']
        cp_dict['profit'] = profit
        card_purchases.append(cp_dict)

    outward_channels = conn.execute("SELECT id, channel_name FROM outward_channels WHERE is_active = 1").fetchall()
    conn.close()
    
    return render_template('transactions.html', 
                           sales_transactions=sales_transactions, fund_movements=fund_movements, card_purchases=card_purchases,
                           is_admin_view=True, outward_channels=outward_channels, current_sell_rate=current_sell_rate,
                           sales_page=sales_page, total_sales_pages=total_sales_pages,
                           movements_page=movements_page, total_movements_pages=total_movements_pages,
                           cards_page=cards_page, total_cards_pages=total_cards_pages)

@app.route('/general_ledger') # 找到這個路由
@admin_required
def general_ledger():
    try:
        conn = get_db()
        
        # ==================== 這是唯一的修改點 ====================
        # 確保只選擇 is_active 為 1 的用戶(渠道)，並按名稱排序
        customers = conn.execute(
            "SELECT id, username FROM users WHERE is_active = 1 ORDER BY username ASC"
        ).fetchall()
        # ========================================================
        
        conn.close()
        
        # 將查詢到的活躍渠道列表傳遞給前端樣板
        return render_template('general_ledger.html', customers=customers)
        
    except Exception as e:
        # 如果載入頁面時資料庫出錯，可以顯示一個錯誤頁面或返回一個提示
        print(f"Error loading general_ledger page: {e}")
        # 這裡可以根據您的需要返回一個錯誤頁面
        return "載入買入頁面時發生錯誤，請檢查後台日誌。", 500

@app.route('/admin/accounts_receivable')
@admin_required
def admin_accounts_receivable():
    conn = get_db()
    users_with_ar = conn.execute("SELECT username, accounts_receivable FROM users WHERE is_admin = 0 AND is_active = 1 ORDER BY accounts_receivable DESC").fetchall()
    conn.close()
    return render_template('accounts_receivable.html', users=users_with_ar)

@app.route('/admin/outward_channels', methods=['GET', 'POST'])
@admin_required
def admin_outward_channels():
    conn = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        try:
            if action == 'add_channel':
                conn.execute("INSERT INTO outward_channels (channel_name, channel_type, details, current_balance_rmb) VALUES (?, ?, ?, ?)", (request.form['channel_name'], request.form['channel_type'], request.form['details'], float(request.form.get('initial_balance', 0.0))))
                flash(f'匯出管道 "{request.form["channel_name"]}" 添加成功！', 'success')
            elif action == 'update_balance':
                conn.execute("UPDATE outward_channels SET current_balance_rmb = ?, last_updated = ? WHERE id = ?", (float(request.form['new_balance']), datetime.datetime.now(), request.form['channel_id']))
                flash('餘額更新成功！', 'success')
            elif action == 'toggle_active':
                is_active = request.form['is_active'] == 'true'
                conn.execute("UPDATE outward_channels SET is_active = ? WHERE id = ?", (is_active, request.form['channel_id']))
                flash('管道啟用狀態更新成功！', 'success')
            conn.commit()
        except Exception as e: conn.rollback(); flash(f'操作失敗：{e}', 'danger')
        finally: conn.close()
        return redirect(url_for('admin_outward_channels'))
    outward_channels = conn.execute("SELECT * FROM outward_channels ORDER BY channel_name").fetchall()
    conn.close()
    return render_template('outward_channels.html', outward_channels=outward_channels)

# --- 用戶路由 (與上一版相同) ---
@app.route('/user')
@login_required
def user_dashboard():
    if session.get('is_admin'): return redirect(url_for('admin_dashboard'))
    conn = get_db()
    rates_row = conn.execute("SELECT sell_rate FROM exchange_rates ORDER BY last_updated DESC LIMIT 1").fetchone()
    current_sell_rate = rates_row['sell_rate'] if rates_row else 0.0
    ar_row = conn.execute("SELECT accounts_receivable FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    accounts_receivable_amount = ar_row['accounts_receivable'] if ar_row else 0.0
    payment_channels = conn.execute("SELECT channel_name, details FROM payment_channels WHERE is_active = 1").fetchall()
    conn.close()
    return render_template('user.html', username=session['username'], sell_rate=current_sell_rate, accounts_receivable=accounts_receivable_amount, your_payment_channels=payment_channels)
@app.route('/user/buy_rmb', methods=['POST'])
@login_required
def buy_rmb():
    try:
        rmb_order_amount = float(request.form['rmb_order_amount'])
        customer_payment_note = request.form.get('customer_payment_note', '')
        if rmb_order_amount <= 0: flash('採購數量必須為正數！', 'danger'); return redirect(url_for('user_dashboard'))
    except ValueError: flash('請輸入有效的數字', 'danger'); return redirect(url_for('user_dashboard'))
    conn = get_db()
    try:
        rates = conn.execute("SELECT sell_rate FROM exchange_rates ORDER BY last_updated DESC LIMIT 1").fetchone()
        if not rates or rates['sell_rate'] <= 0: flash('目前無法下單，請聯繫管理員設定匯率。', 'danger'); return redirect(url_for('user_dashboard'))
        twd_expected_payment = rmb_order_amount * rates['sell_rate']
        conn.execute("BEGIN TRANSACTION")
        conn.execute("INSERT INTO transactions (user_id, rmb_order_amount, twd_expected_payment, exchange_rate, customer_payment_note) VALUES (?, ?, ?, ?, ?)", (session['user_id'], rmb_order_amount, twd_expected_payment, rates['sell_rate'], customer_payment_note))
        conn.execute("UPDATE users SET accounts_receivable = accounts_receivable + ? WHERE id = ?", (twd_expected_payment, session['user_id']))
        conn.commit()
        flash(f'成功下單！應付金額 NTD {twd_expected_payment:.2f}。', 'success')
    except Exception as e: conn.rollback(); flash(f'下單失敗: {e}', 'danger')
    finally: conn.close()
    return redirect(url_for('user_dashboard'))
@app.route('/user/transactions')
@login_required
def user_transactions():
    conn = get_db()
    transactions_rows = conn.execute("SELECT t.*, oc.channel_name AS outward_channel_name FROM transactions t LEFT JOIN outward_channels oc ON t.outward_channel_id = oc.id WHERE t.user_id = ? ORDER BY t.id DESC", (session['user_id'],)).fetchall()
    transactions_list = [dict(row) for row in transactions_rows]
    conn.close()
    return render_template('transactions.html', transactions=transactions_list, is_admin_view=False, is_user_view=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)