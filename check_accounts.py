from app import app, db, CashAccount

with app.app_context():
    # 檢查 ID 為 23 的帳戶
    account_23 = db.session.get(CashAccount, 23)
    if account_23:
        print(f'帳戶 ID 23 存在:')
        print(f'  名稱: {account_23.name}')
        print(f'  幣種: {account_23.currency}')
        print(f'  餘額: {account_23.balance}')
        print(f'  狀態: {"啟用" if account_23.is_active else "停用"}')
        print(f'  持有人 ID: {account_23.holder_id}')
    else:
        print('帳戶 ID 23 不存在')
    
    # 列出所有 TWD 帳戶
    print('\n所有 TWD 帳戶:')
    twd_accounts = CashAccount.query.filter_by(currency='TWD').all()
    for acc in twd_accounts:
        print(f'  ID {acc.id}: {acc.name} - 餘額: {acc.balance} - 狀態: {"啟用" if acc.is_active else "停用"}')

