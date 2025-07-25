import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date
from sqlalchemy import func

# ===================================================================
# 1. App、資料庫、登入管理器 的基礎設定
# ===================================================================
app = Flask(__name__)

# --- App Config ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_12345') # 從環境變數讀取更安全
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(instance_path, 'sales_system.db')}")
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
    # User 模型現在是唯一的，所以這裡可以正常工作
    return db.session.get(User, int(user_id))

# ===================================================================
# 2. 資料庫模型 (Class) 定義 - 【統一後的版本】
# ===================================================================

# 【模型一】使用者與客戶模型 (統一)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # 管理員登入用密碼
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_customer = db.Column(db.Boolean, default=True, nullable=False) # 標記是否為客戶
    is_active = db.Column(db.Boolean, default=True, nullable=False)   # 用於軟刪除

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        # 確保有密碼才能檢查
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False

# 【模型二】銷售紀錄模型 (統一)
class SalesRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rmb_amount = db.Column(db.Float, nullable=False)
    exchange_rate = db.Column(db.Float, nullable=False)
    twd_amount = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False, default='PENDING') # PENDING 或 COMPLETED
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    # 建立與 User 的關聯
    customer = db.relationship('User', backref=db.backref('sales', lazy=True))

    def __repr__(self):
        return f'<Sale {self.id} for Customer {self.customer_id}>'

# 【模型三】渠道/產品模型 (可選，但保留以備將來擴充)
class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

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
# 4. 資料庫初始化指令 - 【簡化後的版本】
# ===================================================================
@app.cli.command('init-db')
def init_db_command():
    db.drop_all()
    db.create_all()
    
    # 建立唯一的管理員帳號
    admin_user = User(
        username='admin',
        is_admin=True,
        is_customer=False, # 管理員不是客戶
        is_active=True
    )
    admin_user.set_password('asdf1234555') # 使用 set_password 方法
    db.session.add(admin_user)
    db.session.commit()
    print('資料庫已成功初始化，並創建了 admin 帳號。')

# ===================================================================
# 5. 核心路由 (登入/登出)
# ===================================================================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # 只允許活躍的 admin 登入
        user = User.query.filter_by(username=username, is_active=True, is_admin=True).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))
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
# 6. 主要功能頁面路由 - 【統一使用新模型的版本】
# ===================================================================
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # 使用 SalesRecord 模型重寫儀表板邏輯
    pending_orders_count = db.session.query(func.count(SalesRecord.id)).filter(SalesRecord.status == 'PENDING').scalar() or 0
    total_receivables_twd = db.session.query(func.sum(SalesRecord.twd_amount)).filter(SalesRecord.status == 'PENDING').scalar() or 0
    recent_pending_sales = SalesRecord.query.filter_by(status='PENDING').order_by(SalesRecord.sale_date.desc()).limit(5).all()

    # 以下指標暫時簡化，未來可擴充
    total_assets_twd = total_receivables_twd # 簡化資產為應收款
    total_rmb_stock = 0 # 暫時沒有買入功能

    return render_template('admin.html', 
                           total_assets_twd=total_assets_twd,
                           pending_orders_count=pending_orders_count,
                           total_receivables_twd=total_receivables_twd,
                           total_rmb_stock=total_rmb_stock,
                           # 將 recent_pending_txs 改名以匹配模板
                           recent_pending_txs=recent_pending_sales, 
                           # 確保 monthly_sales_data 存在
                           monthly_sales_data={'labels': [], 'data': []})

@app.route('/general_ledger')
@admin_required
def general_ledger():
    # 這裡應該顯示所有交易紀錄，我們用 SalesRecord
    all_sales = SalesRecord.query.order_by(SalesRecord.sale_date.desc()).all()
    return render_template('general_ledger.html', transactions=all_sales)

@app.route('/sales_entry', methods=['GET', 'POST'])
@login_required
def sales_entry():
    # 載入頁面 (GET)
    if request.method == 'GET':
        active_customers = User.query.filter_by(is_active=True, is_customer=True).order_by(User.username).all()
        pending_sales = SalesRecord.query.filter_by(status='PENDING').order_by(SalesRecord.sale_date.desc()).all()
        # 您可以設定一個預設匯率
        default_sell_rate = 4.85 

        return render_template(
            'sales_entry.html', 
            customers=active_customers, 
            pending_sales=pending_sales,
            today=date.today().isoformat(),
            sell_rate=default_sell_rate
        )
    
    # 提交表單 (POST)，這裡保留您原有的 /sales_action 邏輯，保持前端不變
    # 所以這個 POST 部分理論上不會被觸發，但保留也無妨
    return "This is a POST request to sales_entry", 405


# ===================================================================
# 7. AJAX API 路由 - 【統一使用新模型的版本】
# ===================================================================

# 【核心】處理新增/刪除訂單的 AJAX 路由
@app.route('/sales_action', methods=['POST'])
@login_required
def sales_action():
    action = request.form.get('action')

    if action == 'create_order':
        try:
            customer_name = request.form.get('customer_name','').strip()
            customer_id = request.form.get('user_id')
            
            if not customer_name:
                return jsonify({'status': 'error', 'message': '客戶名稱為必填'}), 400

            target_customer = None
            if customer_id:
                target_customer = db.session.get(User, int(customer_id))
            else:
                target_customer = User.query.filter_by(username=customer_name).first()
                if not target_customer:
                    target_customer = User(
                        username=customer_name, 
                        is_customer=True,
                        is_active=True
                        # 非管理員客戶沒有密碼
                    )
                    db.session.add(target_customer)
                    db.session.flush() # 取得新ID

            rmb = float(request.form.get('rmb_sell_amount'))
            rate = float(request.form.get('exchange_rate'))
            twd = rmb * rate

            new_sale = SalesRecord(
                customer_id=target_customer.id,
                rmb_amount=rmb, exchange_rate=rate, twd_amount=twd,
                sale_date=date.fromisoformat(request.form.get('order_date')),
                status='PENDING'
            )
            db.session.add(new_sale)
            db.session.commit()

            return jsonify({
                'status': 'success', 
                'message': '訂單創建成功！', 
                'transaction': {
                    'id': new_sale.id,
                    'username': target_customer.username,
                    'rmb_order_amount': "%.2f" % new_sale.rmb_amount,
                    'twd_expected_payment': "%.2f" % new_sale.twd_amount,
                    'order_time': new_sale.sale_date.isoformat()
                }
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'伺服器錯誤: {e}'}), 500

    elif action == 'delete_order':
        try:
            tx_id = request.form.get('transaction_id')
            sale_to_delete = db.session.get(SalesRecord, int(tx_id))
            if not sale_to_delete:
                return jsonify({'status': 'error', 'message': '找不到該訂單'}), 404
            
            db.session.delete(sale_to_delete)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '訂單已刪除。', 'deleted_id': tx_id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'刪除失敗: {e}'}), 500
            
    return jsonify({'status': 'error', 'message': '無效的操作'}), 400

# 【核心】處理新增/刪除常用客戶的 AJAX 路由
@app.route('/add_customer_ajax', methods=['POST'])
@login_required
def add_customer_ajax():
    data = request.get_json()
    username = data.get('username','').strip()
    if not username: return jsonify({'status': 'error', 'message': '未提供用戶名'}), 400
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'status': 'error', 'message': '此客戶名稱已存在'}), 409

    new_customer = User(username=username, is_customer=True, is_active=True)
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'status': 'success', 'message': '客戶新增成功', 'customer': {'id': new_customer.id, 'username': new_customer.username}})

@app.route('/delete_customer_ajax', methods=['POST'])
@login_required
def delete_customer_ajax():
    data = request.get_json()
    customer_id = data.get('customer_id')
    customer_to_deactivate = db.session.get(User, int(customer_id))
    if not customer_to_deactivate:
         return jsonify({'status': 'error', 'message': '找不到該客戶'}), 404
    
    customer_to_deactivate.is_active = False
    db.session.commit()
    return jsonify({'status': 'success', 'message': '客戶已從常用列表移除'})

# ===================================================================
# 8. 啟動器
# ===================================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)