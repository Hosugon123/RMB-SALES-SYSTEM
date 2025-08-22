#!/usr/bin/env python3
"""
完善的庫存管理API
包含庫存操作、匯率管理、日誌記錄等功能
支持來源、流向、匯率驗證和現金帳戶餘額自動更新
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import text, func
from datetime import datetime
import traceback

# 創建藍圖
inventory_bp = Blueprint('inventory', __name__)

# 庫存狀態查詢
@inventory_bp.route('/api/inventory/status', methods=['GET'])
@login_required
def get_inventory_status():
    """獲取庫存狀態和詳細信息"""
    try:
        from app import db, FIFOInventory, PurchaseRecord, Channel
        
        # 查詢庫存概況
        summary_query = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_batches,
                COALESCE(SUM(remaining_rmb), 0) as total_rmb,
                COALESCE(SUM(remaining_rmb * exchange_rate), 0) as total_twd,
                CASE 
                    WHEN SUM(remaining_rmb) > 0 
                    THEN SUM(remaining_rmb * exchange_rate) / SUM(remaining_rmb)
                    ELSE 0 
                END as average_rate
            FROM fifo_inventory 
            WHERE remaining_rmb > 0
        """))
        
        summary = summary_query.fetchone()
        summary_dict = {
            'total_batches': summary.total_batches,
            'total_rmb': float(summary.total_rmb),
            'total_twd': float(summary.total_twd),
            'average_rate': float(summary.average_rate)
        }
        
        # 查詢詳細庫存信息
        inventory_query = db.session.execute(text("""
            SELECT 
                fi.id,
                fi.purchase_date,
                c.name as channel_name,
                fi.rmb_amount as original_rmb,
                fi.remaining_rmb,
                fi.rmb_amount - fi.remaining_rmb as allocated_rmb,
                fi.exchange_rate,
                fi.exchange_rate as current_rate,
                fi.created_at,
                fi.last_updated
            FROM fifo_inventory fi
            LEFT JOIN purchase_records pr ON fi.purchase_record_id = pr.id
            LEFT JOIN channels c ON pr.channel_id = c.id
            WHERE fi.remaining_rmb > 0
            ORDER BY fi.purchase_date ASC
        """))
        
        inventory = []
        for row in inventory_query:
            inventory.append({
                'id': row.id,
                'purchase_date': row.purchase_date.isoformat() if row.purchase_date else None,
                'channel_name': row.channel_name,
                'original_rmb': float(row.original_rmb),
                'remaining_rmb': float(row.remaining_rmb),
                'allocated_rmb': float(row.allocated_rmb),
                'exchange_rate': float(row.exchange_rate),
                'current_rate': float(row.current_rate),
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'updated_at': row.last_updated.isoformat() if row.last_updated else None
            })
        
        return jsonify({
            'status': 'success',
            'summary': summary_dict,
            'inventory': inventory
        })
        
    except Exception as e:
        current_app.logger.error(f"獲取庫存狀態失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'獲取庫存狀態失敗: {str(e)}'
        }), 500

# 獲取有庫存的批次
@inventory_bp.route('/api/inventory/batches', methods=['GET'])
@login_required
def get_inventory_batches():
    """獲取有庫存的批次列表"""
    try:
        from app import db, FIFOInventory
        
        batches = db.session.query(FIFOInventory).filter(
            FIFOInventory.remaining_rmb > 0
        ).order_by(FIFOInventory.purchase_date.asc()).all()
        
        batch_list = []
        for batch in batches:
            batch_list.append({
                'id': batch.id,
                'remaining_rmb': float(batch.remaining_rmb),
                'exchange_rate': float(batch.exchange_rate),
                'purchase_date': batch.purchase_date.isoformat() if batch.purchase_date else None
            })
        
        return jsonify({
            'status': 'success',
            'batches': batch_list
        })
        
    except Exception as e:
        current_app.logger.error(f"獲取庫存批次失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'獲取庫存批次失敗: {str(e)}'
        }), 500

# 獲取當前匯率
@inventory_bp.route('/api/inventory/current-rates', methods=['GET'])
@login_required
def get_current_rates():
    """獲取當前平均匯率"""
    try:
        from app import db, FIFOInventory
        
        # 計算加權平均匯率
        result = db.session.execute(text("""
            SELECT 
                CASE 
                    WHEN SUM(remaining_rmb) > 0 
                    THEN SUM(remaining_rmb * exchange_rate) / SUM(remaining_rmb)
                    ELSE 0 
                END as average_rate
            FROM fifo_inventory 
            WHERE remaining_rmb > 0
        """))
        
        average_rate = result.fetchone().average_rate or 0.0
        
        return jsonify({
            'status': 'success',
            'average_rate': float(average_rate)
        })
        
    except Exception as e:
        current_app.logger.error(f"獲取當前匯率失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'獲取當前匯率失敗: {str(e)}'
        }), 500

# 庫存操作日誌
@inventory_bp.route('/api/inventory/logs', methods=['GET'])
@login_required
def get_inventory_logs():
    """獲取庫存操作日誌"""
    try:
        from app import db
        
        # 查詢庫存操作日誌
        logs_query = db.session.execute(text("""
            SELECT 
                il.id,
                il.operation_type,
                il.batch_id,
                il.change_amount,
                il.balance_before,
                il.balance_after,
                il.note,
                il.created_at,
                il.exchange_rate,
                u.username as operator_name,
                COALESCE(sa.name, 'N/A') as source_account_name
            FROM inventory_logs il
            LEFT JOIN users u ON il.operator_id = u.id
            LEFT JOIN cash_accounts sa ON il.source_account_id = sa.id
            ORDER BY il.created_at DESC
            LIMIT 100
        """))
        
        logs = []
        for row in logs_query:
            logs.append({
                'id': row.id,
                'operation_type': row.operation_type,
                'batch_id': row.batch_id,
                'change_amount': float(row.change_amount),
                'balance_before': float(row.balance_before),
                'balance_after': float(row.balance_after),
                'note': row.note,
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'operator_name': row.operator_name,
                'exchange_rate': float(row.exchange_rate) if row.exchange_rate else 0.0,
                'source_account_name': row.source_account_name
            })
        
        return jsonify({
            'status': 'success',
            'logs': logs
        })
        
    except Exception as e:
        current_app.logger.error(f"獲取庫存日誌失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'獲取庫存日誌失敗: {str(e)}'
        }), 500

# 新增庫存
@inventory_bp.route('/api/inventory/add', methods=['POST'])
@login_required
def add_inventory():
    """新增庫存批次"""
    try:
        from app import db, FIFOInventory, PurchaseRecord, CashAccount
        
        data = request.get_json()
        
        # 驗證必填欄位
        required_fields = ['rmb_amount', 'exchange_rate', 'channel_id', 'payment_account_id', 'deposit_account_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必填欄位: {field}'
                }), 400
        
        rmb_amount = float(data['rmb_amount'])
        exchange_rate = float(data['exchange_rate'])
        channel_id = data.get('channel_id')
        payment_account_id = data.get('payment_account_id')
        deposit_account_id = data.get('deposit_account_id')
        note = data.get('note', '')
        
        # 驗證數據
        if rmb_amount <= 0:
            return jsonify({
                'status': 'error',
                'message': 'RMB數量必須大於0'
            }), 400
        
        if exchange_rate <= 0:
            return jsonify({
                'status': 'error',
                'message': '匯率必須大於0'
            }), 400
        
        # 檢查付款帳戶餘額
        payment_account = db.session.query(CashAccount).filter_by(id=payment_account_id).first()
        if not payment_account:
            return jsonify({
                'status': 'error',
                'message': '付款帳戶不存在'
            }), 400
        
        twd_cost = rmb_amount * exchange_rate
        if payment_account.balance < twd_cost:
            return jsonify({
                'status': 'error',
                'message': f'付款帳戶餘額不足，需要 NT${twd_cost:.2f}，當前餘額 NT${payment_account.balance:.2f}'
            }), 400
        
        # 檢查收款帳戶
        deposit_account = db.session.query(CashAccount).filter_by(id=deposit_account_id).first()
        if not deposit_account:
            return jsonify({
                'status': 'error',
                'message': '收款帳戶不存在'
            }), 400
        
        # 開始事務
        try:
            # 創建買入記錄
            purchase_record = PurchaseRecord(
                channel_id=channel_id,
                payment_account_id=payment_account_id,
                deposit_account_id=deposit_account_id,
                rmb_amount=rmb_amount,
                exchange_rate=exchange_rate,
                twd_cost=twd_cost,
                operator_id=current_user.id,
                note=note
            )
            
            db.session.add(purchase_record)
            db.session.flush()  # 獲取ID
            
            # 創建FIFO庫存記錄
            fifo_inventory = FIFOInventory(
                purchase_record_id=purchase_record.id,
                rmb_amount=rmb_amount,
                remaining_rmb=rmb_amount,
                unit_cost_twd=exchange_rate,
                exchange_rate=exchange_rate,
                purchase_date=datetime.utcnow()
            )
            
            db.session.add(fifo_inventory)
            
            # 更新現金帳戶餘額
            payment_account.balance -= twd_cost
            deposit_account.balance += rmb_amount
            
            # 記錄操作日誌
            log_entry = InventoryLog(
                operation_type='add',
                batch_id=fifo_inventory.id,
                change_amount=rmb_amount,
                balance_before=0,
                balance_after=rmb_amount,
                exchange_rate=exchange_rate,
                source_account_id=payment_account_id,
                note=f'新增庫存: {note}',
                operator_id=current_user.id
            )
            
            db.session.add(log_entry)
            
            # 提交事務
            db.session.commit()
            
            current_app.logger.info(f"用戶 {current_user.username} 新增庫存: {rmb_amount} RMB, 匯率: {exchange_rate}")
            
            return jsonify({
                'status': 'success',
                'message': f'成功新增庫存 {rmb_amount} RMB',
                'inventory_id': fifo_inventory.id
            })
            
        except Exception as e:
            db.session.rollback()
            raise e
        
    except Exception as e:
        current_app.logger.error(f"新增庫存失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'新增庫存失敗: {str(e)}'
        }), 500

# 庫存調整
@inventory_bp.route('/api/inventory/adjust', methods=['POST'])
@login_required
def adjust_inventory():
    """調整庫存數量"""
    try:
        from app import db, FIFOInventory, CashAccount
        
        data = request.get_json()
        
        # 驗證必填欄位
        required_fields = ['batch_id', 'adjust_type', 'amount', 'source_account_id', 'target_account_id', 'exchange_rate', 'reason']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必填欄位: {field}'
                }), 400
        
        batch_id = int(data['batch_id'])
        adjust_type = data['adjust_type']
        amount = float(data['amount'])
        source_account_id = data.get('source_account_id')
        target_account_id = data.get('target_account_id')
        exchange_rate = float(data['exchange_rate'])
        reason = data['reason']
        
        # 驗證數據
        if amount <= 0:
            return jsonify({
                'status': 'error',
                'message': '調整數量必須大於0'
            }), 400
        
        if exchange_rate <= 0:
            return jsonify({
                'status': 'error',
                'message': '匯率必須大於0'
            }), 400
        
        # 獲取庫存批次
        inventory = db.session.query(FIFOInventory).filter_by(id=batch_id).first()
        if not inventory:
            return jsonify({
                'status': 'error',
                'message': '找不到指定的庫存批次'
            }), 404
        
        # 記錄調整前的餘額
        balance_before = inventory.remaining_rmb
        
        # 開始事務
        try:
            # 根據調整類型進行操作
            if adjust_type == 'increase':
                # 增加庫存：檢查來源帳戶餘額
                source_account = db.session.query(CashAccount).filter_by(id=source_account_id).first()
                if not source_account:
                    return jsonify({
                        'status': 'error',
                        'message': '來源帳戶不存在'
                    }), 400
                
                if source_account.balance < amount:
                    return jsonify({
                        'status': 'error',
                        'message': f'來源帳戶餘額不足，需要 ¥{amount:.2f}，當前餘額 ¥{source_account.balance:.2f}'
                    }), 400
                
                # 更新庫存和帳戶餘額
                inventory.remaining_rmb += amount
                source_account.balance -= amount
                change_amount = amount
                balance_after = inventory.remaining_rmb
                
            elif adjust_type == 'decrease':
                # 減少庫存：檢查庫存餘額
                if inventory.remaining_rmb < amount:
                    return jsonify({
                        'status': 'error',
                        'message': f'庫存不足，當前餘額: {inventory.remaining_rmb} RMB'
                    }), 400
                
                # 更新庫存和帳戶餘額
                inventory.remaining_rmb -= amount
                target_account = db.session.query(CashAccount).filter_by(id=target_account_id).first()
                if target_account:
                    target_account.balance += amount
                
                change_amount = -amount
                balance_after = inventory.remaining_rmb
                
            elif adjust_type == 'write_off':
                # 庫存報銷：檢查庫存餘額
                if inventory.remaining_rmb < amount:
                    return jsonify({
                        'status': 'error',
                        'message': f'庫存不足，當前餘額: {inventory.remaining_rmb} RMB'
                    }), 400
                
                # 更新庫存和帳戶餘額
                inventory.remaining_rmb -= amount
                target_account = db.session.query(CashAccount).filter_by(id=target_account_id).first()
                if target_account:
                    target_account.balance += amount
                
                change_amount = -amount
                balance_after = inventory.remaining_rmb
                
            else:
                return jsonify({
                    'status': 'error',
                    'message': '無效的調整類型'
                }), 400
            
            # 記錄操作日誌
            log_entry = InventoryLog(
                operation_type='adjust',
                batch_id=batch_id,
                change_amount=change_amount,
                balance_before=balance_before,
                balance_after=balance_after,
                exchange_rate=exchange_rate,
                source_account_id=source_account_id if adjust_type == 'increase' else None,
                note=f'庫存調整({adjust_type}): {reason}',
                operator_id=current_user.id
            )
            
            db.session.add(log_entry)
            
            # 提交事務
            db.session.commit()
            
            current_app.logger.info(f"用戶 {current_user.username} 調整庫存: {adjust_type}, 數量: {amount} RMB, 批次: {batch_id}")
            
            return jsonify({
                'status': 'success',
                'message': f'成功調整庫存，類型: {adjust_type}, 數量: {amount} RMB'
            })
            
        except Exception as e:
            db.session.rollback()
            raise e
        
    except Exception as e:
        current_app.logger.error(f"庫存調整失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'庫存調整失敗: {str(e)}'
        }), 500

# 匯率變更
@inventory_bp.route('/api/inventory/exchange-rate', methods=['POST'])
@login_required
def change_exchange_rate():
    """變更匯率"""
    try:
        from app import db, FIFOInventory
        
        data = request.get_json()
        
        # 驗證必填欄位
        required_fields = ['rate_change_type', 'new_rate', 'reason']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必填欄位: {field}'
                }), 400
        
        rate_change_type = data['rate_change_type']
        old_rate = float(data.get('old_rate', 0))
        new_rate = float(data['new_rate'])
        reason = data['reason']
        
        # 驗證數據
        if new_rate <= 0:
            return jsonify({
                'status': 'error',
                'message': '新匯率必須大於0'
            }), 400
        
        # 開始事務
        try:
            if rate_change_type == 'global':
                # 全局匯率調整：更新所有活躍庫存批次
                active_batches = db.session.query(FIFOInventory).filter(
                    FIFOInventory.remaining_rmb > 0
                ).all()
                
                for batch in active_batches:
                    batch.exchange_rate = new_rate
                    
                    # 記錄匯率變更日誌
                    log_entry = InventoryLog(
                        operation_type='rate_change',
                        batch_id=batch.id,
                        change_amount=0,
                        balance_before=batch.remaining_rmb,
                        balance_after=batch.remaining_rmb,
                        exchange_rate=new_rate,
                        note=f'全局匯率調整: {old_rate:.4f} → {new_rate:.4f}, 原因: {reason}',
                        operator_id=current_user.id
                    )
                    db.session.add(log_entry)
                
            elif rate_change_type == 'batch':
                # 批次匯率調整
                batch_id = data.get('batch_id')
                if not batch_id:
                    return jsonify({
                        'status': 'error',
                        'message': '批次匯率調整需要指定批次ID'
                    }), 400
                
                batch = db.session.query(FIFOInventory).filter_by(id=batch_id).first()
                if not batch:
                    return jsonify({
                        'status': 'error',
                        'message': '找不到指定的庫存批次'
                    }), 404
                
                old_rate = batch.exchange_rate
                batch.exchange_rate = new_rate
                
                # 記錄匯率變更日誌
                log_entry = InventoryLog(
                    operation_type='rate_change',
                    batch_id=batch.id,
                    change_amount=0,
                    balance_before=batch.remaining_rmb,
                    balance_after=batch.remaining_rmb,
                    exchange_rate=new_rate,
                    note=f'批次匯率調整: {old_rate:.4f} → {new_rate:.4f}, 原因: {reason}',
                    operator_id=current_user.id
                )
                db.session.add(log_entry)
            
            # 提交事務
            db.session.commit()
            
            current_app.logger.info(f"用戶 {current_user.username} 變更匯率: {rate_change_type}, 新匯率: {new_rate}")
            
            return jsonify({
                'status': 'success',
                'message': f'成功變更匯率為 {new_rate:.4f}'
            })
            
        except Exception as e:
            db.session.rollback()
            raise e
        
    except Exception as e:
        current_app.logger.error(f"匯率變更失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'匯率變更失敗: {str(e)}'
        }), 500

# 庫存提款（完善的FIFO邏輯）
@inventory_bp.route('/api/inventory/withdraw', methods=['POST'])
@login_required
def withdraw_inventory():
    """按FIFO原則提款庫存"""
    try:
        from app import db, FIFOInventory, FIFOService
        
        data = request.get_json()
        
        # 驗證必填欄位
        required_fields = ['amount', 'reason']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必填欄位: {field}'
                }), 400
        
        withdraw_amount = float(data['amount'])
        reason = data['reason']
        
        if withdraw_amount <= 0:
            return jsonify({
                'status': 'error',
                'message': '提款金額必須大於0'
            }), 400
        
        # 檢查總庫存是否足夠
        total_inventory = db.session.query(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
        
        if total_inventory < withdraw_amount:
            return jsonify({
                'status': 'error',
                'message': f'庫存不足，需要 {withdraw_amount} RMB，可用 {total_inventory} RMB'
            }), 400
        
        # 按FIFO順序扣減庫存
        remaining_to_withdraw = withdraw_amount
        withdrawal_details = []
        
        # 按買入時間順序獲取有庫存的記錄
        inventory_batches = db.session.query(FIFOInventory).filter(
            FIFOInventory.remaining_rmb > 0
        ).order_by(FIFOInventory.purchase_date.asc()).all()
        
        for batch in inventory_batches:
            if remaining_to_withdraw <= 0:
                break
            
            # 計算從這批庫存中扣減多少
            withdraw_from_batch = min(remaining_to_withdraw, batch.remaining_rmb)
            
            # 記錄扣減前的餘額
            balance_before = batch.remaining_rmb
            
            # 更新庫存
            batch.remaining_rmb -= withdraw_from_batch
            batch.allocated_rmb += withdraw_from_batch
            batch.updated_at = datetime.now()
            
            # 記錄提款日誌
            log_entry = InventoryLog(
                operation_type='withdraw',
                batch_id=batch.id,
                change_amount=-withdraw_from_batch,
                balance_before=balance_before,
                balance_after=batch.remaining_rmb,
                note=f'庫存提款: {reason}',
                operator_id=current_user.id
            )
            
            db.session.add(log_entry)
            
            # 記錄提款詳情
            withdrawal_details.append({
                'batch_id': batch.id,
                'withdrawn_amount': withdraw_from_batch,
                'remaining_after': batch.remaining_rmb
            })
            
            remaining_to_withdraw -= withdraw_from_batch
        
        # 提交事務
        db.session.commit()
        
        current_app.logger.info(f"用戶 {current_user.username} 提款庫存: {withdraw_amount} RMB, 原因: {reason}")
        
        return jsonify({
            'status': 'success',
            'message': f'庫存提款成功，共提款 {withdraw_amount} RMB',
            'withdrawal_details': withdrawal_details
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"庫存提款失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'庫存提款失敗: {str(e)}'
        }), 500

# 庫存審計
@inventory_bp.route('/api/inventory/audit', methods=['POST'])
@login_required
def audit_inventory():
    """審計庫存一致性"""
    try:
        from app import db, FIFOInventory, CashAccount
        
        audit_results = []
        
        # 1. 檢查庫存總額與RMB帳戶餘額是否一致
        total_inventory_rmb = db.session.query(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
        total_rmb_accounts = db.session.query(func.sum(CashAccount.balance)).filter(
            CashAccount.currency == 'RMB'
        ).scalar() or 0
        
        inventory_account_diff = abs(total_inventory_rmb - total_rmb_accounts)
        
        if inventory_account_diff > 0.01:  # 允許0.01的誤差
            audit_results.append({
                'type': 'warning',
                'message': f'庫存與RMB帳戶餘額不一致',
                'details': {
                    'total_inventory_rmb': total_inventory_rmb,
                    'total_rmb_accounts': total_rmb_accounts,
                    'difference': inventory_account_diff
                }
            })
        else:
            audit_results.append({
                'type': 'success',
                'message': '庫存與RMB帳戶餘額一致',
                'details': {
                    'total_inventory_rmb': total_inventory_rmb,
                    'total_rmb_accounts': total_rmb_accounts
                }
            })
        
        # 2. 檢查是否有負餘額的庫存
        negative_inventory = db.session.query(FIFOInventory).filter(
            FIFOInventory.remaining_rmb < 0
        ).all()
        
        if negative_inventory:
            audit_results.append({
                'type': 'error',
                'message': f'發現 {len(negative_inventory)} 個負餘額庫存批次',
                'details': [{'batch_id': b.id, 'balance': b.remaining_rmb} for b in negative_inventory]
            })
        else:
            audit_results.append({
                'type': 'success',
                'message': '所有庫存批次餘額正常'
            })
        
        # 3. 檢查是否有孤立的庫存記錄
        isolated_inventory = db.session.execute(text("""
            SELECT fi.id, fi.remaining_rmb
            FROM fifo_inventory fi
            LEFT JOIN purchase_records pr ON fi.purchase_record_id = pr.id
            WHERE pr.id IS NULL
        """)).fetchall()
        
        if isolated_inventory:
            audit_results.append({
                'type': 'warning',
                'message': f'發現 {len(isolated_inventory)} 個孤立的庫存記錄',
                'details': [{'batch_id': r.id, 'balance': r.remaining_rmb} for r in isolated_inventory]
            })
        else:
            audit_results.append({
                'type': 'success',
                'message': '所有庫存記錄都有對應的買入記錄'
            })
        
        return jsonify({
            'status': 'success',
            'audit_results': audit_results,
            'summary': {
                'total_checks': len(audit_results),
                'success_count': len([r for r in audit_results if r['type'] == 'success']),
                'warning_count': len([r for r in audit_results if r['type'] == 'warning']),
                'error_count': len([r for r in audit_results if r['type'] == 'error'])
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"庫存審計失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'庫存審計失敗: {str(e)}'
        }), 500

# 庫存修復
@inventory_bp.route('/api/inventory/fix', methods=['POST'])
@login_required
def fix_inventory():
    """修復庫存問題"""
    try:
        from app import db, FIFOInventory, CashAccount
        
        data = request.get_json()
        fix_type = data.get('fix_type', 'auto')
        
        fixes_applied = []
        
        if fix_type == 'auto' or fix_type == 'negative_balance':
            # 修復負餘額庫存
            negative_batches = db.session.query(FIFOInventory).filter(
                FIFOInventory.remaining_rmb < 0
            ).all()
            
            for batch in negative_batches:
                old_balance = batch.remaining_rmb
                batch.remaining_rmb = 0
                batch.updated_at = datetime.now()
                
                # 記錄修復日誌
                log_entry = InventoryLog(
                    operation_type='fix',
                    batch_id=batch.id,
                    change_amount=-old_balance,
                    balance_before=old_balance,
                    balance_after=0,
                    note=f'自動修復負餘額庫存',
                    operator_id=current_user.id
                )
                
                db.session.add(log_entry)
                fixes_applied.append(f'修復批次 {batch.id} 的負餘額: {old_balance} → 0')
        
        if fix_type == 'auto' or fix_type == 'sync_accounts':
            # 同步庫存與RMB帳戶餘額
            total_inventory_rmb = db.session.query(func.sum(FIFOInventory.remaining_rmb)).scalar() or 0
            total_rmb_accounts = db.session.query(func.sum(CashAccount.balance)).filter(
                CashAccount.currency == 'RMB'
            ).scalar() or 0
            
            if abs(total_inventory_rmb - total_rmb_accounts) > 0.01:
                # 計算需要調整的差額
                adjustment_needed = total_rmb_accounts - total_inventory_rmb
                
                if adjustment_needed > 0:
                    # 帳戶餘額大於庫存，需要增加庫存
                    # 創建一個調整批次
                    adjustment_batch = FIFOInventory(
                        purchase_record_id=None,  # 特殊調整批次
                        original_rmb=adjustment_needed,
                        remaining_rmb=adjustment_needed,
                        allocated_rmb=0,
                        exchange_rate=4.0,  # 使用預設匯率
                        purchase_date=datetime.now()
                    )
                    
                    db.session.add(adjustment_batch)
                    db.session.flush()
                    
                    # 記錄調整日誌
                    log_entry = InventoryLog(
                        operation_type='fix',
                        batch_id=adjustment_batch.id,
                        change_amount=adjustment_needed,
                        balance_before=0,
                        balance_after=adjustment_needed,
                        note=f'自動同步庫存與帳戶餘額，增加 {adjustment_needed} RMB',
                        operator_id=current_user.id
                    )
                    
                    db.session.add(log_entry)
                    fixes_applied.append(f'同步庫存與帳戶餘額，增加庫存 {adjustment_needed} RMB')
        
        # 提交事務
        db.session.commit()
        
        current_app.logger.info(f"用戶 {current_user.username} 執行庫存修復: {fix_type}")
        
        return jsonify({
            'status': 'success',
            'message': '庫存修復完成',
            'fixes_applied': fixes_applied
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"庫存修復失敗: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'庫存修復失敗: {str(e)}'
        }), 500

# 庫存日誌模型
class InventoryLog(db.Model):
    """庫存操作日誌模型"""
    __tablename__ = "inventory_logs"
    id = db.Column(db.Integer, primary_key=True)
    operation_type = db.Column(db.String(50), nullable=False)  # add, adjust, withdraw, delete, rate_change
    batch_id = db.Column(db.Integer, db.ForeignKey("fifo_inventory.id"), nullable=False)
    change_amount = db.Column(db.Float, nullable=False)  # 正數表示增加，負數表示減少
    balance_before = db.Column(db.Float, nullable=False)
    balance_after = db.Column(db.Float, nullable=False)
    exchange_rate = db.Column(db.Float, nullable=True)  # 操作時的匯率
    source_account_id = db.Column(db.Integer, db.ForeignKey("cash_accounts.id"), nullable=True)
    note = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # 關聯
    batch = db.relationship("FIFOInventory", backref="logs")
    source_account = db.relationship("CashAccount")
    operator = db.relationship("User")
    
    def __repr__(self):
        return f"<InventoryLog(id={self.id}, type={self.operation_type}, batch={self.batch_id})>"

# 註冊藍圖
def init_app(app):
    app.register_blueprint(inventory_bp)

