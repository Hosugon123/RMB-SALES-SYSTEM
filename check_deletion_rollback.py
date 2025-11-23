#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查刪除記錄是否正確回滾餘額
分析刪除審計日誌，找出未正確回滾的記錄並計算修復金額

支持本地和部署環境：
- 如果設置了 DATABASE_URL 環境變數，使用部署環境資料庫
- 否則使用本地 SQLite 資料庫
"""

import sys
import os
import json
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 在導入 app 之前設置資料庫連接（如果需要）
# app.py 會自動檢測 DATABASE_URL 環境變數

from app import app, db
from app import (
    CashAccount, PurchaseRecord, SalesRecord, 
    DeleteAuditLog, FIFOInventory, FIFOSalesAllocation
)

def analyze_deletion_rollback():
    """分析刪除記錄的回滾情況"""
    
    # 檢測資料庫類型
    database_url = str(db.engine.url) if hasattr(db, 'engine') else "unknown"
    is_postgresql = 'postgresql' in database_url.lower()
    is_local = 'sqlite' in database_url.lower() or '///' in database_url
    
    print("=" * 80)
    print("檢查刪除記錄回滾情況")
    print("=" * 80)
    print()
    
    if is_postgresql:
        print(f"[INFO] 使用部署環境資料庫 (PostgreSQL)")
        print(f"連接字串: {database_url[:60]}...")
    elif is_local:
        print(f"[INFO] 使用本地資料庫 (SQLite)")
        print(f"資料庫路徑: {database_url}")
    else:
        print(f"[INFO] 資料庫類型: {database_url[:60]}...")
    print()
    
    with app.app_context():
        # 1. 獲取所有刪除審計日誌
        try:
            audit_logs = db.session.execute(
                db.select(DeleteAuditLog)
                .order_by(DeleteAuditLog.deleted_at.desc())
            ).scalars().all()
            
            print(f"找到 {len(audit_logs)} 筆刪除審計日誌")
            print()
            
        except Exception as e:
            if "does not exist" in str(e) and "delete_audit_logs" in str(e):
                print("[ERROR] 刪除審計日誌表不存在，無法檢查")
                return
            else:
                print(f"[ERROR] 獲取刪除審計日誌失敗: {e}")
                return
        
        # 2. 分析每筆刪除記錄
        issues = []
        purchase_deletions = []
        sale_deletions = []
        
        for log in audit_logs:
            try:
                deleted_data = json.loads(log.deleted_data) if log.deleted_data else {}
                balance_changes = json.loads(log.balance_changes) if log.balance_changes else None
                
                if log.table_name == 'purchase_records':
                    purchase_deletions.append({
                        'log': log,
                        'deleted_data': deleted_data,
                        'balance_changes': balance_changes
                    })
                elif log.table_name == 'sales_records':
                    sale_deletions.append({
                        'log': log,
                        'deleted_data': deleted_data,
                        'balance_changes': balance_changes
                    })
                    
            except Exception as e:
                print(f"[WARN] 解析審計日誌 {log.id} 失敗: {e}")
                continue
        
        print(f"買入記錄刪除: {len(purchase_deletions)} 筆")
        print(f"售出記錄刪除: {len(sale_deletions)} 筆")
        print()
        
        # 3. 檢查買入記錄刪除的回滾情況
        print("=" * 80)
        print("檢查買入記錄刪除回滾情況")
        print("=" * 80)
        print()
        
        purchase_issues = []
        for item in purchase_deletions:
            log = item['log']
            deleted_data = item['deleted_data']
            balance_changes = item['balance_changes']
            
            purchase_id = deleted_data.get('id') or log.record_id
            rmb_amount = deleted_data.get('rmb_amount', 0)
            twd_cost = deleted_data.get('twd_cost', 0)
            deposit_account_id = deleted_data.get('deposit_account_id')
            payment_account_id = deleted_data.get('payment_account_id')
            
            print(f"買入記錄 #{purchase_id} (刪除時間: {log.deleted_at})")
            print(f"  RMB金額: {rmb_amount:,.2f}")
            print(f"  台幣成本: {twd_cost:,.2f}")
            print(f"  RMB入帳帳戶ID: {deposit_account_id}")
            print(f"  台幣付款帳戶ID: {payment_account_id}")
            
            # 檢查是否有餘額變化記錄
            if balance_changes:
                print(f"  [OK] 有餘額變化記錄")
                if isinstance(balance_changes, list):
                    for change in balance_changes:
                        account_id = change.get('account_id')
                        account_name = change.get('account_name')
                        balance_before = change.get('balance_before')
                        balance_after = change.get('balance_after')
                        change_amount = change.get('change', 0)
                        
                        print(f"    帳戶: {account_name} (ID: {account_id})")
                        print(f"      刪除前餘額: {balance_before:,.2f}")
                        print(f"      刪除後餘額: {balance_after:,.2f}")
                        print(f"      變化: {change_amount:,.2f}")
                else:
                    print(f"    餘額變化: {balance_changes}")
            else:
                print(f"  [WARN] 沒有餘額變化記錄")
            
            # 檢查當前帳戶餘額是否正確
            if deposit_account_id:
                deposit_account = db.session.get(CashAccount, deposit_account_id)
                if deposit_account:
                    # 計算應該的餘額（如果記錄還在的話）
                    # 當前餘額 + 被刪除的RMB金額 = 應該的餘額（如果沒有刪除）
                    expected_balance_with_deletion = deposit_account.balance + rmb_amount
                    print(f"  RMB入帳帳戶: {deposit_account.name} (ID: {deposit_account_id})")
                    print(f"    當前餘額: {deposit_account.balance:,.2f}")
                    print(f"    如果記錄未刪除，餘額應該是: {expected_balance_with_deletion:,.2f}")
                    
                    # 檢查是否正確回滾
                    if balance_changes:
                        # 檢查餘額變化記錄中是否有這個帳戶
                        found = False
                        if isinstance(balance_changes, list):
                            for change in balance_changes:
                                if change.get('account_id') == deposit_account_id:
                                    found = True
                                    change_amount = change.get('change', 0)
                                    # 應該減少 rmb_amount
                                    if abs(change_amount + rmb_amount) > 0.01:
                                        purchase_issues.append({
                                            'type': 'purchase',
                                            'purchase_id': purchase_id,
                                            'account_id': deposit_account_id,
                                            'account_name': deposit_account.name,
                                            'currency': deposit_account.currency,
                                            'expected_change': -rmb_amount,
                                            'actual_change': change_amount,
                                            'difference': change_amount + rmb_amount,
                                            'deleted_at': log.deleted_at
                                        })
                                        print(f"    [ERROR] 餘額回滾不正確！")
                                        print(f"      應該減少: {rmb_amount:,.2f}")
                                        print(f"      實際變化: {change_amount:,.2f}")
                                        print(f"      差異: {change_amount + rmb_amount:,.2f}")
                                    else:
                                        print(f"    [OK] 餘額回滾正確")
                                    break
                        
                        if not found:
                            print(f"    [WARN] 餘額變化記錄中沒有找到此帳戶")
                    else:
                        # 沒有餘額變化記錄，檢查當前餘額
                        # 如果當前餘額 + rmb_amount 等於應該的餘額，說明沒有回滾
                        # 但這需要知道刪除前的餘額，所以只能標記為可疑
                        purchase_issues.append({
                            'type': 'purchase',
                            'purchase_id': purchase_id,
                            'account_id': deposit_account_id,
                            'account_name': deposit_account.name,
                            'currency': deposit_account.currency,
                            'expected_change': -rmb_amount,
                            'actual_change': None,
                            'difference': None,
                            'deleted_at': log.deleted_at,
                            'note': '沒有餘額變化記錄，無法確認是否回滾'
                        })
                        print(f"    [WARN] 無法確認是否正確回滾（沒有餘額變化記錄）")
            
            if payment_account_id:
                payment_account = db.session.get(CashAccount, payment_account_id)
                if payment_account:
                    expected_balance_with_deletion = payment_account.balance - twd_cost
                    print(f"  台幣付款帳戶: {payment_account.name} (ID: {payment_account_id})")
                    print(f"    當前餘額: {payment_account.balance:,.2f}")
                    print(f"    如果記錄未刪除，餘額應該是: {expected_balance_with_deletion:,.2f}")
                    
                    # 檢查是否正確回滾（應該增加 twd_cost）
                    if balance_changes:
                        found = False
                        if isinstance(balance_changes, list):
                            for change in balance_changes:
                                if change.get('account_id') == payment_account_id:
                                    found = True
                                    change_amount = change.get('change', 0)
                                    # 應該增加 twd_cost
                                    if abs(change_amount - twd_cost) > 0.01:
                                        purchase_issues.append({
                                            'type': 'purchase',
                                            'purchase_id': purchase_id,
                                            'account_id': payment_account_id,
                                            'account_name': payment_account.name,
                                            'currency': payment_account.currency,
                                            'expected_change': twd_cost,
                                            'actual_change': change_amount,
                                            'difference': change_amount - twd_cost,
                                            'deleted_at': log.deleted_at
                                        })
                                        print(f"    [ERROR] 餘額回滾不正確！")
                                        print(f"      應該增加: {twd_cost:,.2f}")
                                        print(f"      實際變化: {change_amount:,.2f}")
                                        print(f"      差異: {change_amount - twd_cost:,.2f}")
                                    else:
                                        print(f"    [OK] 餘額回滾正確")
                                    break
                        
                        if not found:
                            print(f"    [WARN] 餘額變化記錄中沒有找到此帳戶")
                    else:
                        purchase_issues.append({
                            'type': 'purchase',
                            'purchase_id': purchase_id,
                            'account_id': payment_account_id,
                            'account_name': payment_account.name,
                            'currency': payment_account.currency,
                            'expected_change': twd_cost,
                            'actual_change': None,
                            'difference': None,
                            'deleted_at': log.deleted_at,
                            'note': '沒有餘額變化記錄，無法確認是否回滾'
                        })
                        print(f"    [WARN] 無法確認是否正確回滾（沒有餘額變化記錄）")
            
            print()
        
        # 4. 檢查售出記錄刪除的回滾情況
        print("=" * 80)
        print("檢查售出記錄刪除回滾情況")
        print("=" * 80)
        print()
        
        sale_issues = []
        for item in sale_deletions:
            log = item['log']
            deleted_data = item['deleted_data']
            balance_changes = item['balance_changes']
            
            sale_id = deleted_data.get('id') or log.record_id
            rmb_amount = deleted_data.get('rmb_amount', 0)
            rmb_account_id = deleted_data.get('rmb_account_id')
            
            print(f"售出記錄 #{sale_id} (刪除時間: {log.deleted_at})")
            print(f"  RMB金額: {rmb_amount:,.2f}")
            
            if balance_changes:
                print(f"  [OK] 有餘額變化記錄")
            else:
                print(f"  [WARN] 沒有餘額變化記錄")
            
            # 檢查當前帳戶餘額是否正確
            if rmb_account_id:
                rmb_account = db.session.get(CashAccount, rmb_account_id)
                if rmb_account:
                    # 售出時從帳戶扣款，刪除時應該回補
                    expected_balance_with_deletion = rmb_account.balance - rmb_amount
                    print(f"  RMB扣款帳戶: {rmb_account.name} (ID: {rmb_account_id})")
                    print(f"    當前餘額: {rmb_account.balance:,.2f}")
                    print(f"    如果記錄未刪除，餘額應該是: {expected_balance_with_deletion:,.2f}")
                    
                    # 檢查是否正確回滾（應該增加 rmb_amount）
                    if balance_changes:
                        found = False
                        if isinstance(balance_changes, list):
                            for change in balance_changes:
                                if change.get('account_id') == rmb_account_id:
                                    found = True
                                    change_amount = change.get('change', 0)
                                    # 應該增加 rmb_amount
                                    if abs(change_amount - rmb_amount) > 0.01:
                                        sale_issues.append({
                                            'type': 'sale',
                                            'sale_id': sale_id,
                                            'account_id': rmb_account_id,
                                            'account_name': rmb_account.name,
                                            'currency': rmb_account.currency,
                                            'expected_change': rmb_amount,
                                            'actual_change': change_amount,
                                            'difference': change_amount - rmb_amount,
                                            'deleted_at': log.deleted_at
                                        })
                                        print(f"    [ERROR] 餘額回滾不正確！")
                                        print(f"      應該增加: {rmb_amount:,.2f}")
                                        print(f"      實際變化: {change_amount:,.2f}")
                                        print(f"      差異: {change_amount - rmb_amount:,.2f}")
                                    else:
                                        print(f"    [OK] 餘額回滾正確")
                                    break
                        
                        if not found:
                            print(f"    [WARN] 餘額變化記錄中沒有找到此帳戶")
                    else:
                        sale_issues.append({
                            'type': 'sale',
                            'sale_id': sale_id,
                            'account_id': rmb_account_id,
                            'account_name': rmb_account.name,
                            'currency': rmb_account.currency,
                            'expected_change': rmb_amount,
                            'actual_change': None,
                            'difference': None,
                            'deleted_at': log.deleted_at,
                            'note': '沒有餘額變化記錄，無法確認是否回滾'
                        })
                        print(f"    [WARN] 無法確認是否正確回滾（沒有餘額變化記錄）")
            
            print()
        
        # 5. 總結問題
        print("=" * 80)
        print("問題總結")
        print("=" * 80)
        print()
        
        all_issues = purchase_issues + sale_issues
        
        if not all_issues:
            print("[OK] 沒有發現餘額回滾問題！")
            return
        
        print(f"發現 {len(all_issues)} 個問題：")
        print()
        
        # 按帳戶分組
        account_issues = {}
        for issue in all_issues:
            account_id = issue['account_id']
            if account_id not in account_issues:
                account_issues[account_id] = {
                    'account_name': issue['account_name'],
                    'currency': issue['currency'],
                    'issues': []
                }
            account_issues[account_id]['issues'].append(issue)
        
        # 計算每個帳戶需要修復的金額
        fixes = []
        for account_id, data in account_issues.items():
            account = db.session.get(CashAccount, account_id)
            if not account:
                continue
            
            total_fix = 0
            print(f"帳戶: {data['account_name']} (ID: {account_id}, {data['currency']})")
            print(f"  當前餘額: {account.balance:,.2f}")
            print(f"  問題記錄:")
            
            for issue in data['issues']:
                if issue.get('difference') is not None:
                    # 有實際差異，需要修復
                    fix_amount = -issue['difference']  # 負的差異表示需要修復
                    total_fix += fix_amount
                    print(f"    - {issue['type']} #{issue.get('purchase_id') or issue.get('sale_id')}")  
                    print(f"      應該變化: {issue['expected_change']:,.2f}")
                    print(f"      實際變化: {issue['actual_change']:,.2f}")
                    print(f"      需要修復: {fix_amount:,.2f}")
                else:
                    # 沒有餘額變化記錄，假設沒有回滾，需要回滾
                    fix_amount = issue['expected_change']  # 應該的變化就是需要修復的金額
                    total_fix += fix_amount
                    print(f"    - {issue['type']} #{issue.get('purchase_id') or issue.get('sale_id')}")
                    print(f"      {issue.get('note', '沒有餘額變化記錄，假設未回滾')}")
                    print(f"      需要回滾: {fix_amount:,.2f}")
            
            if total_fix != 0:
                new_balance = account.balance + total_fix
                print(f"  需要調整金額: {total_fix:,.2f}")
                print(f"  調整後餘額: {new_balance:,.2f}")
                print()
                
                fixes.append({
                    'account_id': account_id,
                    'account_name': data['account_name'],
                    'currency': data['currency'],
                    'current_balance': account.balance,
                    'fix_amount': total_fix,
                    'new_balance': new_balance,
                    'issues': data['issues']
                })
            else:
                print()
        
        # 6. 生成修復建議
        if fixes:
            print("=" * 80)
            print("修復建議")
            print("=" * 80)
            print()
            print("以下帳戶需要修復餘額：")
            print()
            
            for fix in fixes:
                print(f"帳戶: {fix['account_name']} (ID: {fix['account_id']})")
                print(f"  當前餘額: {fix['current_balance']:,.2f} {fix['currency']}")
                print(f"  調整金額: {fix['fix_amount']:+,.2f} {fix['currency']}")
                print(f"  調整後餘額: {fix['new_balance']:,.2f} {fix['currency']}")
                print()
            
            print("執行修復請運行: python fix_deletion_rollback.py")
            print()

if __name__ == '__main__':
    analyze_deletion_rollback()

