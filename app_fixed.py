# 修復數據修復 API 的問題
# 在 app.py 中找到以下函數並替換

@app.route("/api/admin/data-recovery", methods=["POST"])
def remote_data_recovery():
    """遠程數據修復 API 端點"""
    try:
        print("🔧 開始遠程數據修復...")
        
        # 檢查數據庫連接
        try:
            db.session.execute(db.text("SELECT 1"))
            print("✅ 數據庫連接正常")
        except Exception as db_error:
            print(f"❌ 數據庫連接失敗: {db_error}")
            return jsonify({
                "status": "error",
                "message": f"數據庫連接失敗: {str(db_error)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 1. 修復庫存數據
        print("📦 開始修復庫存數據...")
        try:
            # 檢查 FIFOInventory 表是否存在
            try:
                inventories = FIFOInventory.query.all()
                print(f"📦 找到 {len(inventories)} 個庫存批次")
            except Exception as table_error:
                print(f"❌ 查詢 FIFOInventory 表失敗: {table_error}")
                return jsonify({
                    "status": "error",
                    "message": f"查詢庫存表失敗: {str(table_error)}",
                    "timestamp": datetime.now().isoformat()
                }), 500
            
            inventory_fixes = []
            for inventory in inventories:
                try:
                    # 計算實際的已出帳數量
                    actual_issued = db.session.query(func.sum(FIFOSalesAllocation.allocated_rmb)).filter(
                        FIFOSalesAllocation.fifo_inventory_id == inventory.id
                    ).scalar() or 0
                    
                    old_remaining = inventory.remaining_rmb
                    new_remaining = inventory.rmb_amount - actual_issued
                    
                    inventory.remaining_rmb = new_remaining
                    
                    inventory_fixes.append({
                        "batch_id": inventory.id,
                        "original": inventory.rmb_amount,
                        "old_remaining": old_remaining,
                        "new_remaining": new_remaining,
                        "allocated_rmb": actual_issued
                    })
                except Exception as inv_error:
                    print(f"⚠️ 處理庫存批次 {inventory.id} 時出錯: {inv_error}")
                    continue
            
            print(f"✅ 庫存修復完成，共處理 {len(inventory_fixes)} 個批次")
            
        except Exception as inv_error:
            print(f"❌ 庫存修復失敗: {inv_error}")
            return jsonify({
                "status": "error",
                "message": f"庫存修復失敗: {str(inv_error)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 2. 修復現金帳戶餘額
        print("💰 開始修復現金帳戶餘額...")
        try:
            cash_accounts = CashAccount.query.all()
            print(f"💰 找到 {len(cash_accounts)} 個現金帳戶")
            
            account_fixes = []
            for account in cash_accounts:
                try:
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
                        
                        new_balance = (account.initial_balance or 0) - payment_amount - ledger_debits + ledger_credits
                        
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
                        
                        new_balance = (account.initial_balance or 0) + deposit_amount - sales_amount - ledger_debits + ledger_credits
                    else:
                        print(f"⚠️ 未知幣別: {account.currency}")
                        continue
                    
                    account.balance = new_balance
                    
                    account_fixes.append({
                        "account_id": account.id,
                        "account_name": account.account_name,
                        "currency": account.currency,
                        "old_balance": old_balance,
                        "new_balance": new_balance
                    })
                except Exception as acc_error:
                    print(f"⚠️ 處理帳戶 {account.id} 時出錯: {acc_error}")
                    continue
            
            print(f"✅ 現金帳戶修復完成，共處理 {len(account_fixes)} 個帳戶")
            
        except Exception as acc_error:
            print(f"❌ 現金帳戶修復失敗: {acc_error}")
            return jsonify({
                "status": "error",
                "message": f"現金帳戶修復失敗: {str(acc_error)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 3. 修復客戶應收帳款
        print("📋 開始修復客戶應收帳款...")
        try:
            customers = Customer.query.all()
            print(f"📋 找到 {len(customers)} 個客戶")
            
            customer_fixes = []
            for customer in customers:
                try:
                    old_receivables = customer.total_receivables_twd
                    
                    # 總銷售金額
                    total_sales = SalesRecord.query.filter(
                        SalesRecord.customer_id == customer.id
                    ).with_entities(func.sum(SalesRecord.rmb_amount)).scalar() or 0
                    
                    # 已收款金額
                    received_amount = LedgerEntry.query.filter(
                        and_(
                            LedgerEntry.customer_id == customer.id,
                            LedgerEntry.entry_type == 'SETTLEMENT'
                        )
                    ).with_entities(func.sum(LedgerEntry.amount)).scalar() or 0
                    
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
                except Exception as cust_error:
                    print(f"⚠️ 處理客戶 {customer.id} 時出錯: {cust_error}")
                    continue
            
            print(f"✅ 客戶修復完成，共處理 {len(customer_fixes)} 個客戶")
            
        except Exception as cust_error:
            print(f"❌ 客戶修復失敗: {cust_error}")
            return jsonify({
                "status": "error",
                "message": f"客戶修復失敗: {str(cust_error)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 提交所有更改
        print("💾 提交數據庫更改...")
        try:
            db.session.commit()
            print("✅ 數據庫更改已提交")
        except Exception as commit_error:
            print(f"❌ 提交數據庫更改失敗: {commit_error}")
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"提交數據庫更改失敗: {str(commit_error)}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 4. 驗證修復結果
        print("🔍 驗證修復結果...")
        try:
            total_original = FIFOInventory.query.with_entities(func.sum(FIFOInventory.rmb_amount)).scalar() or 0
            total_remaining = FIFOInventory.query.with_entities(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
            
            total_twd = CashAccount.query.filter_by(currency="TWD").with_entities(func.sum(CashAccount.balance)).scalar() or 0
            total_rmb = CashAccount.query.filter_by(currency="RMB").with_entities(func.sum(CashAccount.balance)).scalar() or 0
            
            total_receivables = Customer.query.with_entities(func.sum(Customer.total_receivables_twd)).scalar() or 0
            
            print(f"📊 修復後數據:")
            print(f"  庫存 - 原始: {total_original}, 剩餘: {total_remaining}")
            print(f"  現金 - TWD: {total_twd}, RMB: {total_rmb}")
            print(f"  應收: {total_receivables}")
            
        except Exception as verify_error:
            print(f"⚠️ 驗證修復結果時出錯: {verify_error}")
        
        print("✅ 遠程數據修復完成！")
        
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
        print(f"❌ 遠程數據修復失敗: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            db.session.rollback()
            print("✅ 數據庫事務已回滾")
        except Exception as rollback_error:
            print(f"⚠️ 回滾數據庫事務時出錯: {rollback_error}")
        
        return jsonify({
            "status": "error",
            "message": f"數據修復失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500
