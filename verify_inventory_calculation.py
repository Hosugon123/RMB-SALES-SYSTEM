#!/usr/bin/env python3
"""
驗證FIFO庫存計算是否正確
通過檢查歷史買入和售出數據來驗算
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.')

from app import app, db
from sqlalchemy import func
from app import (
    PurchaseRecord, SalesRecord, FIFOInventory, FIFOSalesAllocation
)

def verify_inventory():
    """驗證FIFO庫存計算"""
    with app.app_context():
        print("=" * 80)
        print("驗證FIFO庫存計算是否正確")
        print("=" * 80)
        
        # 1. 檢查所有買入記錄
        print("\n【1】檢查所有買入記錄")
        print("-" * 80)
        
        all_purchases = PurchaseRecord.query.all()
        total_purchase_rmb = sum(p.rmb_amount for p in all_purchases)
        
        print(f"買入記錄總數: {len(all_purchases)}")
        print(f"買入RMB總和: {total_purchase_rmb:,.2f} RMB")
        
        # 檢查每個買入記錄是否都有對應的FIFO庫存
        purchase_without_inventory = []
        for purchase in all_purchases:
            inventory = FIFOInventory.query.filter_by(purchase_record_id=purchase.id).first()
            if not inventory:
                purchase_without_inventory.append(purchase)
        
        if purchase_without_inventory:
            print(f"\n[警告] 發現 {len(purchase_without_inventory)} 筆買入記錄沒有對應的FIFO庫存：")
            for p in purchase_without_inventory:
                print(f"  買入記錄 ID {p.id}: {p.rmb_amount:,.2f} RMB, 日期: {p.purchase_date}")
        else:
            print("  [正常] 所有買入記錄都有對應的FIFO庫存")
        
        # 2. 檢查所有售出記錄
        print("\n【2】檢查所有售出記錄")
        print("-" * 80)
        
        all_sales = SalesRecord.query.all()
        total_sales_rmb = sum(s.rmb_amount for s in all_sales)
        
        print(f"售出記錄總數: {len(all_sales)}")
        print(f"售出RMB總和: {total_sales_rmb:,.2f} RMB")
        
        # 檢查每個售出記錄是否都有對應的FIFO分配
        sales_without_allocation = []
        sales_allocation_sum = {}
        for sale in all_sales:
            allocations = FIFOSalesAllocation.query.filter_by(sales_record_id=sale.id).all()
            if not allocations:
                sales_without_allocation.append(sale)
            else:
                allocated_sum = sum(a.allocated_rmb for a in allocations)
                if abs(allocated_sum - sale.rmb_amount) > 0.01:
                    sales_allocation_sum[sale.id] = {
                        'sale_rmb': sale.rmb_amount,
                        'allocated_rmb': allocated_sum,
                        'difference': sale.rmb_amount - allocated_sum
                    }
        
        if sales_without_allocation:
            print(f"\n[警告] 發現 {len(sales_without_allocation)} 筆售出記錄沒有對應的FIFO分配：")
            for s in sales_without_allocation:
                print(f"  售出記錄 ID {s.id}: {s.rmb_amount:,.2f} RMB, 日期: {s.created_at}")
        else:
            print("  [正常] 所有售出記錄都有對應的FIFO分配")
        
        if sales_allocation_sum:
            print(f"\n[警告] 發現 {len(sales_allocation_sum)} 筆售出記錄的分配金額不匹配：")
            for sale_id, info in sales_allocation_sum.items():
                print(f"  售出記錄 ID {sale_id}: 售出 {info['sale_rmb']:,.2f} RMB, 分配 {info['allocated_rmb']:,.2f} RMB, 差異 {info['difference']:,.2f} RMB")
        else:
            print("  [正常] 所有售出記錄的分配金額都匹配")
        
        # 3. 計算理論FIFO庫存
        print("\n【3】計算理論FIFO庫存")
        print("-" * 80)
        
        theoretical_fifo = total_purchase_rmb - total_sales_rmb
        print(f"理論FIFO庫存 = 買入總和 {total_purchase_rmb:,.2f} - 售出總和 {total_sales_rmb:,.2f} = {theoretical_fifo:,.2f} RMB")
        
        # 4. 檢查實際FIFO庫存
        print("\n【4】檢查實際FIFO庫存")
        print("-" * 80)
        
        all_inventories = FIFOInventory.query.all()
        total_actual_fifo = sum(inv.remaining_rmb for inv in all_inventories)
        total_original_fifo = sum(inv.rmb_amount for inv in all_inventories)
        
        print(f"FIFO庫存批次總數: {len(all_inventories)}")
        print(f"FIFO庫存原始總和: {total_original_fifo:,.2f} RMB")
        print(f"FIFO庫存剩餘總和: {total_actual_fifo:,.2f} RMB")
        
        # 檢查原始總和是否等於買入總和
        if abs(total_original_fifo - total_purchase_rmb) > 0.01:
            print(f"\n[問題] FIFO庫存原始總和 ({total_original_fifo:,.2f}) ≠ 買入總和 ({total_purchase_rmb:,.2f})")
            print(f"  差異: {total_original_fifo - total_purchase_rmb:,.2f} RMB")
        else:
            print("  [正常] FIFO庫存原始總和 = 買入總和")
        
        # 檢查剩餘總和是否等於理論值
        if abs(total_actual_fifo - theoretical_fifo) > 0.01:
            print(f"\n[問題] FIFO庫存剩餘總和 ({total_actual_fifo:,.2f}) ≠ 理論值 ({theoretical_fifo:,.2f})")
            print(f"  差異: {total_actual_fifo - theoretical_fifo:,.2f} RMB")
        else:
            print("  [正常] FIFO庫存剩餘總和 = 理論值")
        
        # 5. 檢查FIFOSalesAllocation總和
        print("\n【5】檢查FIFOSalesAllocation總和")
        print("-" * 80)
        
        all_allocations = FIFOSalesAllocation.query.all()
        total_allocated_rmb = sum(a.allocated_rmb for a in all_allocations)
        
        print(f"FIFO分配記錄總數: {len(all_allocations)}")
        print(f"FIFO分配RMB總和: {total_allocated_rmb:,.2f} RMB")
        
        # 檢查分配總和是否等於售出總和
        if abs(total_allocated_rmb - total_sales_rmb) > 0.01:
            print(f"\n[問題] FIFO分配總和 ({total_allocated_rmb:,.2f}) ≠ 售出總和 ({total_sales_rmb:,.2f})")
            print(f"  差異: {total_allocated_rmb - total_sales_rmb:,.2f} RMB")
        else:
            print("  [正常] FIFO分配總和 = 售出總和")
        
        # 6. 驗證公式：原始 - 分配 = 剩餘
        print("\n【6】驗證公式：原始 - 分配 = 剩餘")
        print("-" * 80)
        
        calculated_remaining = total_original_fifo - total_allocated_rmb
        print(f"計算的剩餘 = 原始 {total_original_fifo:,.2f} - 分配 {total_allocated_rmb:,.2f} = {calculated_remaining:,.2f} RMB")
        print(f"實際的剩餘: {total_actual_fifo:,.2f} RMB")
        
        if abs(calculated_remaining - total_actual_fifo) > 0.01:
            print(f"\n[問題] 計算的剩餘 ({calculated_remaining:,.2f}) ≠ 實際的剩餘 ({total_actual_fifo:,.2f})")
            print(f"  差異: {calculated_remaining - total_actual_fifo:,.2f} RMB")
            print("  這表示FIFO庫存的remaining_rmb字段可能不正確！")
        else:
            print("  [正常] 計算的剩餘 = 實際的剩餘")
        
        # 7. 檢查每個FIFO庫存批次的計算
        print("\n【7】檢查每個FIFO庫存批次的計算")
        print("-" * 80)
        
        inventory_issues = []
        for inv in all_inventories:
            # 計算該批次的實際分配總和
            allocated_for_this_batch = sum(
                a.allocated_rmb for a in FIFOSalesAllocation.query.filter_by(fifo_inventory_id=inv.id).all()
            )
            
            # 計算應該的剩餘
            should_remaining = inv.rmb_amount - allocated_for_this_batch
            
            # 檢查實際剩餘是否正確
            if abs(inv.remaining_rmb - should_remaining) > 0.01:
                inventory_issues.append({
                    'inventory_id': inv.id,
                    'original': inv.rmb_amount,
                    'allocated': allocated_for_this_batch,
                    'should_remaining': should_remaining,
                    'actual_remaining': inv.remaining_rmb,
                    'difference': inv.remaining_rmb - should_remaining
                })
        
        if inventory_issues:
            print(f"[問題] 發現 {len(inventory_issues)} 個FIFO庫存批次的剩餘數量不正確：")
            for issue in inventory_issues[:10]:  # 只顯示前10個
                print(f"  批次 ID {issue['inventory_id']}:")
                print(f"    原始: {issue['original']:,.2f} RMB")
                print(f"    已分配: {issue['allocated']:,.2f} RMB")
                print(f"    應該剩餘: {issue['should_remaining']:,.2f} RMB")
                print(f"    實際剩餘: {issue['actual_remaining']:,.2f} RMB")
                print(f"    差異: {issue['difference']:,.2f} RMB")
            if len(inventory_issues) > 10:
                print(f"  ... 還有 {len(inventory_issues) - 10} 個批次有問題")
        else:
            print("  [正常] 所有FIFO庫存批次的剩餘數量都正確")
        
        # 8. 總結
        print("\n" + "=" * 80)
        print("【總結】")
        print("=" * 80)
        
        issues_found = []
        if purchase_without_inventory:
            issues_found.append(f"{len(purchase_without_inventory)} 筆買入記錄沒有FIFO庫存")
        if sales_without_allocation:
            issues_found.append(f"{len(sales_without_allocation)} 筆售出記錄沒有FIFO分配")
        if sales_allocation_sum:
            issues_found.append(f"{len(sales_allocation_sum)} 筆售出記錄分配金額不匹配")
        if abs(total_original_fifo - total_purchase_rmb) > 0.01:
            issues_found.append("FIFO庫存原始總和 ≠ 買入總和")
        if abs(total_actual_fifo - theoretical_fifo) > 0.01:
            issues_found.append("FIFO庫存剩餘總和 ≠ 理論值")
        if abs(total_allocated_rmb - total_sales_rmb) > 0.01:
            issues_found.append("FIFO分配總和 ≠ 售出總和")
        if abs(calculated_remaining - total_actual_fifo) > 0.01:
            issues_found.append("計算的剩餘 ≠ 實際的剩餘")
        if inventory_issues:
            issues_found.append(f"{len(inventory_issues)} 個FIFO庫存批次剩餘數量不正確")
        
        if issues_found:
            print("[問題] 發現以下問題：")
            for issue in issues_found:
                print(f"  - {issue}")
        else:
            print("[成功] 所有驗證都通過！FIFO庫存計算完全正確。")
        
        print("=" * 80)

if __name__ == "__main__":
    verify_inventory()

