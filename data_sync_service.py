#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據同步服務 - 統一管理所有數據異動
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

class DataSyncService:
    """數據同步服務類 - 確保所有相關數據的一致性"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    def sync_all_data(self) -> Dict[str, Any]:
        """同步所有數據，返回同步結果報告"""
        self.logger.info("🔄 開始全量數據同步...")
        
        sync_results = {
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'details': {},
            'errors': []
        }
        
        try:
            # 1. 同步帳戶餘額與流水記錄
            account_sync = self.sync_account_balances()
            sync_results['details']['account_sync'] = account_sync
            
            # 2. 同步庫存與帳戶餘額
            inventory_sync = self.sync_inventory_balances()
            sync_results['details']['inventory_sync'] = inventory_sync
            
            # 3. 同步應收帳款
            receivable_sync = self.sync_receivables()
            sync_results['details']['receivable_sync'] = receivable_sync
            
            # 4. 同步總資產計算
            asset_sync = self.sync_total_assets()
            sync_results['details']['asset_sync'] = asset_sync
            
            # 5. 驗證數據一致性
            consistency_check = self.verify_data_consistency()
            sync_results['details']['consistency_check'] = consistency_check
            
            self.logger.info("✅ 全量數據同步完成")
            
        except Exception as e:
            self.logger.error(f"❌ 數據同步失敗: {e}")
            sync_results['status'] = 'error'
            sync_results['errors'].append(str(e))
        
        return sync_results
    
    def sync_account_balances(self) -> Dict[str, Any]:
        """同步帳戶餘額與流水記錄"""
        self.logger.info("🔄 同步帳戶餘額...")
        
        try:
            # 計算每個帳戶的理論餘額（從流水記錄累積）
            self.db.execute(text("""
                UPDATE cash_accounts 
                SET balance = (
                    SELECT COALESCE(SUM(
                        CASE 
                            WHEN currency = 'TWD' THEN twd_change
                            WHEN currency = 'RMB' THEN rmb_change
                            ELSE 0
                        END
                    ), 0)
                    FROM ledger_entries 
                    WHERE account_id = cash_accounts.id
                )
                WHERE is_active = 1
            """))
            
            self.db.commit()
            
            # 獲取同步結果
            result = self.db.execute(text("""
                SELECT 
                    ca.currency,
                    COUNT(*) as account_count,
                    SUM(ca.balance) as total_balance
                FROM cash_accounts ca
                WHERE ca.is_active = 1
                GROUP BY ca.currency
            """)).fetchall()
            
            return {
                'status': 'success',
                'accounts_updated': sum(row.account_count for row in result),
                'currency_totals': {row.currency: row.total_balance for row in result}
            }
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"❌ 帳戶餘額同步失敗: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def sync_inventory_balances(self) -> Dict[str, Any]:
        """同步庫存與帳戶餘額"""
        self.logger.info("🔄 同步庫存餘額...")
        
        try:
            # 檢查庫存與帳戶餘額的一致性
            inventory_check = self.db.execute(text("""
                SELECT 
                    fi.id,
                    fi.remaining_rmb,
                    fi.purchase_record_id,
                    pr.deposit_account_id,
                    ca.balance as account_balance
                FROM fifo_inventory fi
                LEFT JOIN purchase_records pr ON fi.purchase_record_id = pr.id
                LEFT JOIN cash_accounts ca ON pr.deposit_account_id = ca.id
                WHERE fi.remaining_rmb > 0
            """)).fetchall()
            
            # 計算庫存總和
            total_inventory_rmb = sum(row.remaining_rmb for row in inventory_check)
            
            # 計算RMB帳戶總餘額
            rmb_accounts_total = self.db.execute(text("""
                SELECT SUM(balance) 
                FROM cash_accounts 
                WHERE currency = 'RMB' AND is_active = 1
            """)).scalar() or 0
            
            # 檢查差異
            difference = rmb_accounts_total - total_inventory_rmb
            
            return {
                'status': 'success',
                'total_inventory_rmb': total_inventory_rmb,
                'total_rmb_accounts': rmb_accounts_total,
                'difference': difference,
                'is_consistent': abs(difference) <= 0.01,
                'inventory_records': len(inventory_check)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 庫存餘額同步失敗: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def sync_receivables(self) -> Dict[str, Any]:
        """同步應收帳款"""
        self.logger.info("🔄 同步應收帳款...")
        
        try:
            # 從銷售記錄重新計算應收帳款
            self.db.execute(text("""
                UPDATE customers 
                SET total_receivables_twd = (
                    SELECT COALESCE(SUM(twd_amount), 0)
                    FROM sales_records 
                    WHERE customer_id = customers.id 
                    AND status = 'pending'
                )
                WHERE is_active = 1
            """))
            
            self.db.commit()
            
            # 獲取總應收帳款
            total_receivables = self.db.execute(text("""
                SELECT SUM(total_receivables_twd) 
                FROM customers 
                WHERE is_active = 1
            """)).scalar() or 0
            
            return {
                'status': 'success',
                'total_receivables': total_receivables,
                'customers_updated': self.db.execute(text("SELECT COUNT(*) FROM customers WHERE is_active = 1")).scalar()
            }
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"❌ 應收帳款同步失敗: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def sync_total_assets(self) -> Dict[str, Any]:
        """同步總資產計算"""
        self.logger.info("🔄 同步總資產...")
        
        try:
            # 計算總TWD資產
            total_twd = self.db.execute(text("""
                SELECT SUM(balance) 
                FROM cash_accounts 
                WHERE currency = 'TWD' AND is_active = 1
            """)).scalar() or 0
            
            # 計算總RMB資產
            total_rmb = self.db.execute(text("""
                SELECT SUM(balance) 
                FROM cash_accounts 
                WHERE currency = 'RMB' AND is_active = 1
            "")).scalar() or 0
            
            # 計算總應收帳款
            total_receivables = self.db.execute(text("""
                SELECT SUM(total_receivables_twd) 
                FROM customers 
                WHERE is_active = 1
            "")).scalar() or 0
            
            return {
                'status': 'success',
                'total_twd': total_twd,
                'total_rmb': total_rmb,
                'total_receivables': total_receivables,
                'total_assets_twd': total_twd + total_receivables
            }
            
        except Exception as e:
            self.logger.error(f"❌ 總資產同步失敗: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def verify_data_consistency(self) -> Dict[str, Any]:
        """驗證數據一致性"""
        self.logger.info("🔍 驗證數據一致性...")
        
        try:
            issues = []
            
            # 檢查1: 庫存與帳戶餘額一致性
            inventory_issue = self.check_inventory_consistency()
            if inventory_issue:
                issues.append(inventory_issue)
            
            # 檢查2: 流水記錄完整性
            ledger_issue = self.check_ledger_completeness()
            if ledger_issue:
                issues.append(ledger_issue)
            
            # 檢查3: 外鍵關聯完整性
            foreign_key_issue = self.check_foreign_key_integrity()
            if foreign_key_issue:
                issues.append(foreign_key_issue)
            
            return {
                'status': 'success',
                'issues_found': len(issues),
                'issues': issues,
                'is_consistent': len(issues) == 0
            }
            
        except Exception as e:
            self.logger.error(f"❌ 數據一致性驗證失敗: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def check_inventory_consistency(self) -> Optional[Dict[str, Any]]:
        """檢查庫存一致性"""
        try:
            # 檢查是否有庫存記錄但沒有對應的買入記錄
            orphaned_inventory = self.db.execute(text("""
                SELECT COUNT(*) 
                FROM fifo_inventory fi
                LEFT JOIN purchase_records pr ON fi.purchase_record_id = pr.id
                WHERE pr.id IS NULL
            """)).scalar()
            
            if orphaned_inventory > 0:
                return {
                    'type': 'orphaned_inventory',
                    'severity': 'high',
                    'message': f'發現 {orphaned_inventory} 個孤立的庫存記錄',
                    'count': orphaned_inventory
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 庫存一致性檢查失敗: {e}")
            return {'type': 'check_error', 'severity': 'high', 'message': str(e)}
    
    def check_ledger_completeness(self) -> Optional[Dict[str, Any]]:
        """檢查流水記錄完整性"""
        try:
            # 檢查是否有帳戶但沒有對應的流水記錄
            accounts_without_ledger = self.db.execute(text("""
                SELECT COUNT(*) 
                FROM cash_accounts ca
                LEFT JOIN ledger_entries le ON ca.id = le.account_id
                WHERE le.id IS NULL AND ca.is_active = 1
            """)).scalar()
            
            if accounts_without_ledger > 0:
                return {
                    'type': 'incomplete_ledger',
                    'severity': 'medium',
                    'message': f'發現 {accounts_without_ledger} 個帳戶沒有流水記錄',
                    'count': accounts_without_ledger
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 流水記錄完整性檢查失敗: {e}")
            return {'type': 'check_error', 'severity': 'high', 'message': str(e)}
    
    def check_foreign_key_integrity(self) -> Optional[Dict[str, Any]]:
        """檢查外鍵關聯完整性"""
        try:
            # 檢查庫存分配記錄的外鍵完整性
            broken_allocations = self.db.execute(text("""
                SELECT COUNT(*) 
                FROM fifo_sales_allocations fsa
                LEFT JOIN fifo_inventory fi ON fsa.fifo_inventory_id = fi.id
                LEFT JOIN sales_records sr ON fsa.sales_record_id = sr.id
                WHERE fi.id IS NULL OR sr.id IS NULL
            """)).scalar()
            
            if broken_allocations > 0:
                return {
                    'type': 'broken_foreign_keys',
                    'severity': 'high',
                    'message': f'發現 {broken_allocations} 個破損的外鍵關聯',
                    'count': broken_allocations
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 外鍵完整性檢查失敗: {e}")
            return {'type': 'check_error', 'severity': 'high', 'message': str(e)}
    
    def auto_fix_common_issues(self) -> Dict[str, Any]:
        """自動修復常見問題"""
        self.logger.info("🔧 開始自動修復常見問題...")
        
        fixes_applied = []
        
        try:
            # 修復1: 清理孤立的庫存記錄
            orphaned_count = self.db.execute(text("""
                DELETE FROM fifo_inventory 
                WHERE purchase_record_id NOT IN (SELECT id FROM purchase_records)
            """)).rowcount
            
            if orphaned_count > 0:
                fixes_applied.append(f"清理了 {orphaned_count} 個孤立的庫存記錄")
            
            # 修復2: 清理破損的庫存分配記錄
            broken_allocations = self.db.execute(text("""
                DELETE FROM fifo_sales_allocations 
                WHERE fifo_inventory_id NOT IN (SELECT id FROM fifo_inventory)
                OR sales_record_id NOT IN (SELECT id FROM sales_records)
            """)).rowcount
            
            if broken_allocations > 0:
                fixes_applied.append(f"清理了 {broken_allocations} 個破損的庫存分配記錄")
            
            # 修復3: 重置為0的負餘額帳戶
            negative_balances = self.db.execute(text("""
                UPDATE cash_accounts 
                SET balance = 0 
                WHERE balance < 0 AND is_active = 1
            """)).rowcount
            
            if negative_balances > 0:
                fixes_applied.append(f"重置了 {negative_balances} 個負餘額帳戶")
            
            self.db.commit()
            
            return {
                'status': 'success',
                'fixes_applied': fixes_applied,
                'total_fixes': len(fixes_applied)
            }
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"❌ 自動修復失敗: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """獲取同步狀態"""
        try:
            # 獲取最後一次同步時間
            last_sync = getattr(self, '_last_sync_time', None)
            
            # 獲取數據統計
            stats = {
                'total_accounts': self.db.execute(text("SELECT COUNT(*) FROM cash_accounts WHERE is_active = 1")).scalar(),
                'total_inventory_records': self.db.execute(text("SELECT COUNT(*) FROM fifo_inventory")).scalar(),
                'total_sales_records': self.db.execute(text("SELECT COUNT(*) FROM sales_records")).scalar(),
                'total_customers': self.db.execute(text("SELECT COUNT(*) FROM customers WHERE is_active = 1")).scalar()
            }
            
            return {
                'last_sync': last_sync,
                'current_stats': stats,
                'sync_available': True
            }
            
        except Exception as e:
            self.logger.error(f"❌ 獲取同步狀態失敗: {e}")
            return {'status': 'error', 'message': str(e)}
