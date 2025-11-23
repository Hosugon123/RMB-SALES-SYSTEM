#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復刪除記錄未正確回滾的餘額
根據刪除審計日誌計算並修復餘額

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

from app import app, db
from app import (
    CashAccount, PurchaseRecord, SalesRecord, 
    DeleteAuditLog, LedgerEntry
)

def calculate_fixes():
    """計算需要修復的金額"""
    
    fixes = {}
    
    with app.app_context():
        # 獲取所有刪除審計日誌
        try:
            audit_logs = db.session.execute(
                db.select(DeleteAuditLog)
                .order_by(DeleteAuditLog.deleted_at.desc())
            ).scalars().all()
        except Exception as e:
            if "does not exist" in str(e) and "delete_audit_logs" in str(e):
                print("[ERROR] 刪除審計日誌表不存在")
                return fixes
            else:
                print(f"[ERROR] 獲取刪除審計日誌失敗: {e}")
                return fixes
        
        # 分析每筆刪除記錄
        for log in audit_logs:
            try:
                deleted_data = json.loads(log.deleted_data) if log.deleted_data else {}
                balance_changes = json.loads(log.balance_changes) if log.balance_changes else None
                
                if log.table_name == 'purchase_records':
                    # 買入記錄刪除
                    purchase_id = deleted_data.get('id') or log.record_id
                    rmb_amount = deleted_data.get('rmb_amount', 0)
                    twd_cost = deleted_data.get('twd_cost', 0)
                    deposit_account_id = deleted_data.get('deposit_account_id')
                    payment_account_id = deleted_data.get('payment_account_id')
                    
                    # 檢查RMB帳戶回滾
                    if deposit_account_id and rmb_amount > 0:
                        if deposit_account_id not in fixes:
                            fixes[deposit_account_id] = {
                                'account': db.session.get(CashAccount, deposit_account_id),
                                'rmb_fix': 0,
                                'twd_fix': 0,
                                'issues': []
                            }
                        
                        # 檢查是否正確回滾
                        if balance_changes:
                            found = False
                            if isinstance(balance_changes, list):
                                for change in balance_changes:
                                    if change.get('account_id') == deposit_account_id:
                                        found = True
                                        change_amount = change.get('change', 0)
                                        # 應該減少 rmb_amount
                                        if abs(change_amount + rmb_amount) > 0.01:
                                            # 沒有正確回滾
                                            fix_amount = -(change_amount + rmb_amount)
                                            fixes[deposit_account_id]['rmb_fix'] += fix_amount
                                            fixes[deposit_account_id]['issues'].append({
                                                'type': 'purchase',
                                                'record_id': purchase_id,
                                                'expected': -rmb_amount,
                                                'actual': change_amount,
                                                'fix': fix_amount
                                            })
                                        break
                            
                            if not found:
                                # 沒有餘額變化記錄，需要回滾
                                fixes[deposit_account_id]['rmb_fix'] -= rmb_amount
                                fixes[deposit_account_id]['issues'].append({
                                    'type': 'purchase',
                                    'record_id': purchase_id,
                                    'expected': -rmb_amount,
                                    'actual': None,
                                    'fix': -rmb_amount,
                                    'note': '沒有餘額變化記錄'
                                })
                        else:
                            # 沒有餘額變化記錄，需要回滾
                            fixes[deposit_account_id]['rmb_fix'] -= rmb_amount
                            fixes[deposit_account_id]['issues'].append({
                                'type': 'purchase',
                                'record_id': purchase_id,
                                'expected': -rmb_amount,
                                'actual': None,
                                'fix': -rmb_amount,
                                'note': '沒有餘額變化記錄'
                            })
                    
                    # 檢查台幣帳戶回滾
                    if payment_account_id and twd_cost > 0:
                        if payment_account_id not in fixes:
                            fixes[payment_account_id] = {
                                'account': db.session.get(CashAccount, payment_account_id),
                                'rmb_fix': 0,
                                'twd_fix': 0,
                                'issues': []
                            }
                        
                        # 檢查是否正確回滾
                        if balance_changes:
                            found = False
                            if isinstance(balance_changes, list):
                                for change in balance_changes:
                                    if change.get('account_id') == payment_account_id:
                                        found = True
                                        change_amount = change.get('change', 0)
                                        # 應該增加 twd_cost
                                        if abs(change_amount - twd_cost) > 0.01:
                                            # 沒有正確回滾
                                            fix_amount = twd_cost - change_amount
                                            fixes[payment_account_id]['twd_fix'] += fix_amount
                                            fixes[payment_account_id]['issues'].append({
                                                'type': 'purchase',
                                                'record_id': purchase_id,
                                                'expected': twd_cost,
                                                'actual': change_amount,
                                                'fix': fix_amount
                                            })
                                        break
                            
                            if not found:
                                # 沒有餘額變化記錄，需要回滾
                                fixes[payment_account_id]['twd_fix'] += twd_cost
                                fixes[payment_account_id]['issues'].append({
                                    'type': 'purchase',
                                    'record_id': purchase_id,
                                    'expected': twd_cost,
                                    'actual': None,
                                    'fix': twd_cost,
                                    'note': '沒有餘額變化記錄'
                                })
                        else:
                            # 沒有餘額變化記錄，需要回滾
                            fixes[payment_account_id]['twd_fix'] += twd_cost
                            fixes[payment_account_id]['issues'].append({
                                'type': 'purchase',
                                'record_id': purchase_id,
                                'expected': twd_cost,
                                'actual': None,
                                'fix': twd_cost,
                                'note': '沒有餘額變化記錄'
                            })
                
                elif log.table_name == 'sales_records':
                    # 售出記錄刪除
                    sale_id = deleted_data.get('id') or log.record_id
                    rmb_amount = deleted_data.get('rmb_amount', 0)
                    rmb_account_id = deleted_data.get('rmb_account_id')
                    
                    # 檢查RMB帳戶回滾
                    if rmb_account_id and rmb_amount > 0:
                        if rmb_account_id not in fixes:
                            fixes[rmb_account_id] = {
                                'account': db.session.get(CashAccount, rmb_account_id),
                                'rmb_fix': 0,
                                'twd_fix': 0,
                                'issues': []
                            }
                        
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
                                            # 沒有正確回滾
                                            fix_amount = rmb_amount - change_amount
                                            fixes[rmb_account_id]['rmb_fix'] += fix_amount
                                            fixes[rmb_account_id]['issues'].append({
                                                'type': 'sale',
                                                'record_id': sale_id,
                                                'expected': rmb_amount,
                                                'actual': change_amount,
                                                'fix': fix_amount
                                            })
                                        break
                            
                            if not found:
                                # 沒有餘額變化記錄，需要回滾
                                fixes[rmb_account_id]['rmb_fix'] += rmb_amount
                                fixes[rmb_account_id]['issues'].append({
                                    'type': 'sale',
                                    'record_id': sale_id,
                                    'expected': rmb_amount,
                                    'actual': None,
                                    'fix': rmb_amount,
                                    'note': '沒有餘額變化記錄'
                                })
                        else:
                            # 沒有餘額變化記錄，需要回滾
                            fixes[rmb_account_id]['rmb_fix'] += rmb_amount
                            fixes[rmb_account_id]['issues'].append({
                                'type': 'sale',
                                'record_id': sale_id,
                                'expected': rmb_amount,
                                'actual': None,
                                'fix': rmb_amount,
                                'note': '沒有餘額變化記錄'
                            })
                
            except Exception as e:
                print(f"[WARN] 處理審計日誌 {log.id} 失敗: {e}")
                continue
    
    return fixes

def fix_account_balances(auto_fix=False):
    """修復帳戶餘額"""
    
    print("=" * 80)
    print("修復刪除記錄回滾問題")
    print("=" * 80)
    print()
    
    with app.app_context():
        # 檢測資料庫類型（需要在 app_context 中）
        try:
            database_url = str(db.engine.url)
            is_postgresql = 'postgresql' in database_url.lower()
            is_local = 'sqlite' in database_url.lower() or '///' in database_url
            
            if is_postgresql:
                print(f"[INFO] 使用部署環境資料庫 (PostgreSQL)")
                print(f"連接字串: {database_url[:60]}...")
            elif is_local:
                print(f"[INFO] 使用本地資料庫 (SQLite)")
                print(f"資料庫路徑: {database_url}")
            else:
                print(f"[INFO] 資料庫類型: {database_url[:60]}...")
        except Exception as e:
            print(f"[INFO] 無法檢測資料庫類型: {e}")
        print()
        # 計算需要修復的金額
        fixes = calculate_fixes()
        
        if not fixes:
            print("[OK] 沒有需要修復的問題")
            return
        
        # 顯示需要修復的帳戶
        print(f"發現 {len(fixes)} 個帳戶需要修復：")
        print()
        
        total_fixes = []
        for account_id, fix_data in fixes.items():
            account = fix_data['account']
            if not account:
                continue
            
            rmb_fix = fix_data['rmb_fix']
            twd_fix = fix_data['twd_fix']
            
            if rmb_fix == 0 and twd_fix == 0:
                continue
            
            current_balance = account.balance
            new_balance = current_balance
            
            if account.currency == 'RMB' and rmb_fix != 0:
                new_balance = current_balance + rmb_fix
            elif account.currency == 'TWD' and twd_fix != 0:
                new_balance = current_balance + twd_fix
            
            print(f"帳戶: {account.name} (ID: {account_id}, {account.currency})")
            print(f"  當前餘額: {current_balance:,.2f}")
            
            if account.currency == 'RMB' and rmb_fix != 0:
                print(f"  RMB調整: {rmb_fix:+,.2f}")
            if account.currency == 'TWD' and twd_fix != 0:
                print(f"  TWD調整: {twd_fix:+,.2f}")
            
            print(f"  調整後餘額: {new_balance:,.2f}")
            print(f"  問題記錄數: {len(fix_data['issues'])}")
            print()
            
            total_fixes.append({
                'account_id': account_id,
                'account': account,
                'rmb_fix': rmb_fix,
                'twd_fix': twd_fix,
                'current_balance': current_balance,
                'new_balance': new_balance,
                'issues': fix_data['issues']
            })
        
        if not total_fixes:
            print("[OK] 沒有需要修復的問題")
            return
        
        # 確認修復
        if not auto_fix:
            print("=" * 80)
            response = input("確認執行修復？(yes/no): ").strip().lower()
            if response != 'yes':
                print("取消修復")
                return
        
        # 執行修復
        print()
        print("開始修復...")
        print()
        
        try:
            for fix in total_fixes:
                account = fix['account']
                rmb_fix = fix['rmb_fix']
                twd_fix = fix['twd_fix']
                
                # 記錄原始餘額
                old_balance = account.balance
                
                # 調整餘額
                if account.currency == 'RMB' and rmb_fix != 0:
                    account.balance += rmb_fix
                elif account.currency == 'TWD' and twd_fix != 0:
                    account.balance += twd_fix
                
                # 創建LedgerEntry記錄修復操作
                try:
                    from app import get_safe_operator_id
                    operator_id = get_safe_operator_id()
                except:
                    operator_id = 1
                
                # 確定調整金額
                fix_amount = rmb_fix if account.currency == 'RMB' else twd_fix
                
                if fix_amount != 0:
                    entry = LedgerEntry(
                        entry_type='DEPOSIT' if fix_amount > 0 else 'WITHDRAW',
                        account_id=account.id,
                        amount=abs(fix_amount),
                        description=f"修復刪除記錄回滾問題：調整 {len(fix['issues'])} 筆記錄的餘額",
                        operator_id=operator_id,
                        entry_date=datetime.utcnow()
                    )
                    db.session.add(entry)
                
                print(f"✅ 修復帳戶 {account.name}:")
                print(f"   餘額: {old_balance:,.2f} -> {account.balance:,.2f}")
                print(f"   調整: {fix_amount:+,.2f} {account.currency}")
            
            # 提交所有變更
            db.session.commit()
            print()
            print("=" * 80)
            print("[OK] 修復完成！")
            print("=" * 80)
            
        except Exception as e:
            db.session.rollback()
            print()
            print("=" * 80)
            print(f"[ERROR] 修復失敗: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='修復刪除記錄回滾問題')
    parser.add_argument('--auto-fix', action='store_true', help='自動修復，不需要確認')
    args = parser.parse_args()
    
    fix_account_balances(auto_fix=args.auto_fix)

