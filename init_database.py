# 這是 init_database.py 的完整內容

# 從主應用程式導入需要的變數和模型
from app import app, db, User, ExchangeRate, Holder, CashAccount

print(">>> 正在啟動獨立初始化腳本...")

# 使用 app.app_context() 確保所有操作都在正確的 Flask 環境中執行
with app.app_context():
    print(">>> 已進入應用程式上下文。")
    
    # 步驟 1: 我們先刪除舊的資料庫，確保從一張白紙開始
    db.drop_all()
    print(">>> 已刪除所有舊表格。")
    
    # 步驟 2: 根據最新的模型定義，建立所有新表格
    db.create_all()
    print(">>> 已根據最新模型建立所有新表格。")
    
    # 步驟 3: 準備所有要寫入的預設資料
    
    # 準備 admin 使用者
    admin_user = User(
        username='admin',
        is_admin=True,
        is_active=True
    )
    admin_user.set_password('asdf1234555')
    db.session.add(admin_user)
    print(">>> 預設管理員 'admin' 已準備好加入。")

    # 準備預設匯率
    default_rate = ExchangeRate(buy_rate=4.3, sell_rate=4.4)
    db.session.add(default_rate)
    print(">>> 預設匯率已準備好加入。")
    
    # 準備預設持有人
    default_holder = Holder(name='預設持有人')
    db.session.add(default_holder)
    # 我們需要先 flush 一次，這樣 default_holder 才能獲得一個 id
    db.session.flush() 
    print(f">>> 預設持有人 '{default_holder.name}' 已準備好加入。")

    # 準備預設現金帳戶
    initial_accounts = {'TWD現金': 'TWD', 'RMB現金': 'RMB'}
    for name, currency in initial_accounts.items():
        account = CashAccount(
            holder_id=default_holder.id,
            account_name=name,
            currency=currency,
            balance=0
        )
        db.session.add(account)
    print(">>> 預設現金帳戶已準備好加入。")
    
    # 步驟 4: 一次性將所有準備好的資料寫入資料庫
    try:
        db.session.commit()
        print("\n*** 資料庫已成功初始化，並寫入所有預設資料！ ***\n")
    except Exception as e:
        print(f"\n!!! 寫入資料庫時發生嚴重錯誤: {e} !!!\n")
        # 如果發生錯誤，撤銷所有操作，保持資料庫乾淨
        db.session.rollback()