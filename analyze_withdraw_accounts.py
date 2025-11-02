#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析售出扣款 WITHDRAW 記錄：查找何時開始記錄、計算邏輯，並比較三個支付寶帳戶的差異
"""

import sys
import os

# 確保可以找到 app 模組
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from app import app, db, LedgerEntry, CashAccount, SalesRecord
    from sqlalchemy import func
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("請確保在專案根目錄執行此腳本")
    sys.exit(1)

def analyze_withdraw_history():
    """分析 WITHDRAW 記錄的歷史"""
    print("=" * 100)
    print("分析售出扣款 WITHDRAW 記錄的歷史和計算邏輯")
    print("=" * 100)
    
    with app.app_context():
        try:
            # ========== 1. 查找所有售出扣款 WITHDRAW 記錄 ==========
            print("\n【1】查找所有售出扣款 WITHDRAW 記錄")
            print("-" * 100)
            
            withdraw_records = db.session.execute(
                db.select(LedgerEntry)
                .filter(LedgerEntry.entry_type == "WITHDRAW")
                .filter(LedgerEntry.description.like("%售出扣款%"))
                .order_by(LedgerEntry.entry_date.asc())
            ).scalars().all()
            
            if len(withdraw_records) == 0:
                print("❌ 沒有找到任何售出扣款 WITHDRAW 記錄")
                return
            
            print(f"找到 {len(withdraw_records)} 筆售出扣款 WITHDRAW 記錄")
            
            # 查找最早和最晚的記錄
            earliest = withdraw_records[0]
            latest = withdraw_records[-1]
            
            print(f"\n最早記錄：")
            print(f"  ID: {earliest.id}")
            print(f"  時間: {earliest.entry_date}")
            print(f"  帳戶ID: {earliest.account_id}")
            print(f"  金額: {earliest.amount:,.2f} RMB")
            print(f"  描述: {earliest.description}")
            
            print(f"\n最晚記錄：")
            print(f"  ID: {latest.id}")
            print(f"  時間: {latest.entry_date}")
            print(f"  帳戶ID: {latest.account_id}")
            print(f"  金額: {latest.amount:,.2f} RMB")
            print(f"  描述: {latest.description}")
            
            # ========== 2. 按帳戶分析 ==========
            print("\n【2】按帳戶分析售出扣款 WITHDRAW 記錄")
            print("-" * 100)
            
            withdraw_by_account = {}
            for record in withdraw_records:
                account_id = record.account_id
                if account_id not in withdraw_by_account:
                    account = db.session.get(CashAccount, account_id)
                    withdraw_by_account[account_id] = {
                        'account': account,
                        'records': [],
                        'total_amount': 0,
                        'first_record_date': record.entry_date,
                        'last_record_date': record.entry_date
                    }
                
                withdraw_by_account[account_id]['records'].append(record)
                withdraw_by_account[account_id]['total_amount'] += abs(record.amount)
                
                if record.entry_date < withdraw_by_account[account_id]['first_record_date']:
                    withdraw_by_account[account_id]['first_record_date'] = record.entry_date
                if record.entry_date > withdraw_by_account[account_id]['last_record_date']:
                    withdraw_by_account[account_id]['last_record_date'] = record.entry_date
            
            # 找出目標帳戶：0107、7773、6186 支付寶
            # 先查找所有支付寶帳戶，然後匹配
            all_alipay_accounts = db.session.execute(
                db.select(CashAccount)
                .filter(CashAccount.currency == "RMB")
                .filter(CashAccount.name.like("%支付寶%"))
            ).scalars().all()
            
            target_accounts = {}
            account_id_map = {}  # 帳戶ID到帳戶名稱的映射
            
            # 建立帳戶ID映射
            for account in all_alipay_accounts:
                account_id_map[account.id] = account.name
                if '0107' in account.name:
                    target_accounts['0107'] = {'id': account.id, 'name': account.name}
                elif '7773' in account.name:
                    target_accounts['7773'] = {'id': account.id, 'name': account.name}
                elif '6186' in account.name:
                    target_accounts['6186'] = {'id': account.id, 'name': account.name}
            
            # 為目標帳戶添加 WITHDRAW 數據
            for key, info in target_accounts.items():
                account_id = info['id']
                if account_id in withdraw_by_account:
                    info['data'] = withdraw_by_account[account_id]
                else:
                    # 如果沒有 WITHDRAW 記錄，創建空數據結構
                    account = db.session.get(CashAccount, account_id)
                    info['data'] = {
                        'account': account,
                        'records': [],
                        'total_amount': 0,
                        'first_record_date': None,
                        'last_record_date': None
                    }
            
            print(f"\n找到目標帳戶：")
            for key, info in target_accounts.items():
                print(f"  {key}: {info['name']} (ID: {info['id']})")
            
            # ========== 3. 詳細分析三個帳戶 ==========
            print("\n【3】詳細分析三個支付寶帳戶")
            print("-" * 100)
            
            for key in ['0107', '7773', '6186']:
                if key not in target_accounts:
                    print(f"\n⚠️  {key} 支付寶帳戶不在 WITHDRAW 記錄中或不存在")
                    continue
                
                info = target_accounts[key]
                account_id = info['id']
                account_name = info['name']
                data = info['data']
                account = data['account']
                
                print(f"\n{'='*100}")
                print(f"帳戶: {account_name} (ID: {account_id})")
                print(f"{'='*100}")
                
                print(f"\n基本資訊：")
                print(f"  當前餘額: {account.balance:,.2f} RMB")
                print(f"  售出扣款 WITHDRAW 記錄數: {len(data['records'])} 筆")
                print(f"  售出扣款 WITHDRAW 總額: {data['total_amount']:,.2f} RMB")
                print(f"  第一筆記錄時間: {data['first_record_date']}")
                print(f"  最後一筆記錄時間: {data['last_record_date']}")
                print(f"  理論餘額（回補後）: {account.balance + data['total_amount']:,.2f} RMB")
                
                # 統計該帳戶的銷售記錄
                sales_from_account = db.session.execute(
                    db.select(SalesRecord)
                    .filter(SalesRecord.rmb_account_id == account_id)
                    .order_by(SalesRecord.created_at.asc())
                ).scalars().all()
                
                total_sales_rmb_from_account = sum(s.rmb_amount for s in sales_from_account)
                
                print(f"\n銷售記錄統計：")
                print(f"  從此帳戶售出的記錄數: {len(sales_from_account)} 筆")
                print(f"  從此帳戶售出的總額: {total_sales_rmb_from_account:,.2f} RMB")
                
                # 比較
                print(f"\n數據比較：")
                print(f"  WITHDRAW 總額: {data['total_amount']:,.2f} RMB")
                print(f"  銷售總額: {total_sales_rmb_from_account:,.2f} RMB")
                difference = data['total_amount'] - total_sales_rmb_from_account
                print(f"  差異: {difference:,.2f} RMB")
                
                if abs(difference) < 0.01:
                    print(f"  ✅ WITHDRAW 與銷售總額一致")
                else:
                    print(f"  ⚠️  WITHDRAW 與銷售總額不一致")
                    if difference > 0:
                        print(f"     WITHDRAW 多出 {difference:,.2f} RMB（可能有多餘記錄）")
                    else:
                        print(f"     WITHDRAW 缺少 {abs(difference):,.2f} RMB（可能有遺漏記錄）")
                
                # 分析 WITHDRAW 記錄的時間分布
                if len(data['records']) > 0:
                    print(f"\nWITHDRAW 記錄時間分布（前10筆和後10筆）：")
                    records = sorted(data['records'], key=lambda x: x.entry_date)
                    if len(records) > 0:
                        print(f"  前10筆：")
                        for i, record in enumerate(records[:10], 1):
                            print(f"    {i}. {record.entry_date} - {abs(record.amount):,.2f} RMB - {record.description[:50]}")
                        if len(records) > 10:
                            print(f"  後10筆：")
                            for i, record in enumerate(records[-10:], 1):
                                print(f"    {i}. {record.entry_date} - {abs(record.amount):,.2f} RMB - {record.description[:50]}")
                
                # 檢查是否有從其他帳戶扣款但記錄到此帳戶的情況
                # 查找所有與此帳戶相關的 WITHDRAW，但從庫存來源帳戶扣款的記錄
                print(f"\n檢查是否有從其他帳戶扣款的 WITHDRAW 記錄：")
                from app import FIFOSalesAllocation, FIFOInventory, PurchaseRecord
                
                # 查找所有從此帳戶售出的銷售記錄的 FIFO 分配
                allocations_for_sales = []
                for sale in sales_from_account:
                    allocations = db.session.execute(
                        db.select(FIFOSalesAllocation)
                        .filter(FIFOSalesAllocation.sales_record_id == sale.id)
                    ).scalars().all()
                    for alloc in allocations:
                        if alloc.fifo_inventory and alloc.fifo_inventory.purchase_record:
                            source_account = alloc.fifo_inventory.purchase_record.deposit_account
                            if source_account:
                                allocations_for_sales.append({
                                    'sale_id': sale.id,
                                    'source_account_id': source_account.id,
                                    'source_account_name': source_account.name,
                                    'amount': alloc.allocated_rmb
                                })
                
                # 統計從不同帳戶扣款的情況
                source_account_stats = {}
                for alloc in allocations_for_sales:
                    source_id = alloc['source_account_id']
                    if source_id not in source_account_stats:
                        source_account_stats[source_id] = {
                            'name': alloc['source_account_name'],
                            'total': 0,
                            'count': 0
                        }
                    source_account_stats[source_id]['total'] += alloc['amount']
                    source_account_stats[source_id]['count'] += 1
                
                if len(source_account_stats) > 1 or (len(source_account_stats) == 1 and list(source_account_stats.keys())[0] != account_id):
                    print(f"  ⚠️  發現從其他帳戶扣款的 FIFO 分配：")
                    for source_id, stats in source_account_stats.items():
                        if source_id != account_id:
                            print(f"    從 {stats['name']} (ID: {source_id}) 扣款: {stats['total']:,.2f} RMB ({stats['count']} 筆)")
                            print(f"    這可能導致 WITHDRAW 記錄金額與從此帳戶銷售總額不一致")
            
            # ========== 4. 交叉比對三個帳戶 ==========
            print("\n【4】交叉比對三個帳戶的算式")
            print("-" * 100)
            
            if len(target_accounts) >= 3:
                print("\n三個帳戶的比較表：")
                print(f"{'帳戶':<15} {'當前餘額':<15} {'WITHDRAW總額':<18} {'銷售總額':<18} {'理論餘額':<18} {'差異':<15}")
                print("-" * 100)
                
                for key in ['0107', '7773', '6186']:
                    if key not in target_accounts:
                        continue
                    
                    info = target_accounts[key]
                    account = info['data']['account']
                    withdraw_total = info['data']['total_amount']
                    
                    sales_from_account = db.session.execute(
                        db.select(SalesRecord)
                        .filter(SalesRecord.rmb_account_id == info['id'])
                    ).scalars().all()
                    sales_total = sum(s.rmb_amount for s in sales_from_account)
                    
                    theoretical_balance = account.balance + withdraw_total
                    difference = withdraw_total - sales_total
                    
                    print(f"{info['name']:<15} {account.balance:>14,.2f} {withdraw_total:>17,.2f} {sales_total:>17,.2f} {theoretical_balance:>17,.2f} {difference:>14,.2f}")
                
                # 分析 0107 的特殊情況
                if '0107' in target_accounts:
                    info_0107 = target_accounts['0107']
                    data_0107 = info_0107['data']
                    
                    print(f"\n【5】0107 支付寶異常分析")
                    print("-" * 100)
                    
                    # 檢查是否有重複記錄
                    records_0107 = data_0107['records']
                    record_amounts = [abs(r.amount) for r in records_0107]
                    record_descriptions = [r.description for r in records_0107]
                    
                    # 檢查重複的描述
                    from collections import Counter
                    desc_counter = Counter(record_descriptions)
                    duplicates = {desc: count for desc, count in desc_counter.items() if count > 1}
                    
                    if duplicates:
                        print(f"⚠️  發現重複的描述（可能表示重複記錄）：")
                        for desc, count in list(duplicates.items())[:10]:
                            print(f"    '{desc[:60]}' - {count} 次")
                    
                    # 檢查是否有異常大的記錄
                    large_records = [r for r in records_0107 if abs(r.amount) > 100000]
                    if large_records:
                        print(f"\n⚠️  發現異常大的記錄（>100,000 RMB）：")
                        for record in large_records[:5]:
                            print(f"    ID: {record.id}, 時間: {record.entry_date}, 金額: {abs(record.amount):,.2f} RMB")
                            print(f"    描述: {record.description}")
                    
                    # 檢查是否有正數記錄（應該都是負數）
                    positive_records = [r for r in records_0107 if r.amount > 0]
                    if positive_records:
                        print(f"\n⚠️  發現正數金額的記錄（應該是負數）：")
                        for record in positive_records[:5]:
                            print(f"    ID: {record.id}, 金額: {record.amount:,.2f} RMB")
                    
                    # 檢查是否有從其他帳戶扣款但記錄到0107的 WITHDRAW
                    print(f"\n檢查 WITHDRAW 記錄的帳戶ID分佈：")
                    account_ids_in_withdraw = Counter([r.account_id for r in records_0107])
                    for acc_id, count in account_ids_in_withdraw.items():
                        acc = db.session.get(CashAccount, acc_id)
                        acc_name = acc.name if acc else f"ID:{acc_id}"
                        print(f"  帳戶 {acc_name} (ID: {acc_id}): {count} 筆記錄")
                        if acc_id != info_0107['id']:
                            print(f"    ⚠️  警告：此 WITHDRAW 記錄屬於其他帳戶！")
                    
                    # 檢查是否所有的 WITHDRAW 都是從庫存來源帳戶（而不是銷售帳戶）創建的
                    print(f"\n檢查 WITHDRAW 記錄是否從庫存來源帳戶創建：")
                    from app import FIFOSalesAllocation, FIFOInventory, PurchaseRecord
                    
                    # 查找所有包含 0107 相關的 FIFO 分配
                    all_allocations = db.session.execute(
                        db.select(FIFOSalesAllocation)
                    ).scalars().all()
                    
                    withdraw_source_stats = {}
                    for record in records_0107:
                        # 嘗試從描述中提取庫存批次ID
                        import re
                        match = re.search(r'庫存批次\s*(\d+)', record.description)
                        if match:
                            inventory_id = int(match.group(1))
                            inventory = db.session.get(FIFOInventory, inventory_id)
                            if inventory and inventory.purchase_record and inventory.purchase_record.deposit_account:
                                source_account_id = inventory.purchase_record.deposit_account.id
                                source_account_name = inventory.purchase_record.deposit_account.name
                                if source_account_id not in withdraw_source_stats:
                                    withdraw_source_stats[source_account_id] = {
                                        'name': source_account_name,
                                        'total': 0,
                                        'count': 0
                                    }
                                withdraw_source_stats[source_account_id]['total'] += abs(record.amount)
                                withdraw_source_stats[source_account_id]['count'] += 1
                    
                    if withdraw_source_stats:
                        print(f"  WITHDRAW 記錄的來源帳戶分佈：")
                        for source_id, stats in withdraw_source_stats.items():
                            print(f"    從 {stats['name']} (ID: {source_id}) 創建: {stats['total']:,.2f} RMB ({stats['count']} 筆)")
                            if source_id != info_0107['id']:
                                print(f"      ⚠️  這筆 WITHDRAW 是從其他帳戶（{stats['name']}）扣款的！")
                                print(f"      舊邏輯從庫存來源帳戶扣款，而不是從銷售帳戶（0107支付寶）扣款")
                                print(f"      這可能是造成金額不一致的原因！")
            
            # ========== 6. 計算邏輯說明 ==========
            print("\n【6】WITHDRAW 記錄的計算邏輯說明")
            print("-" * 100)
            
            print("""
根據代碼分析，WITHDRAW 記錄的歷史邏輯是：

1. 【舊邏輯】（已停止使用，但歷史記錄仍存在）：
   - 每筆銷售會創建兩個記錄：
     a) SalesRecord（銷售記錄）- rmb_account_id 指向銷售帳戶（如0107支付寶）
     b) WITHDRAW LedgerEntry（售出扣款記錄）- account_id 指向庫存來源帳戶（deposit_account）
   - WITHDRAW 記錄的描述格式為：「售出扣款：分配給客戶（庫存批次 X）」或「售出扣款：客戶...」
   - ⚠️  關鍵問題：WITHDRAW 記錄的 account_id 是庫存來源帳戶，而不是銷售帳戶！
   - 這導致：如果銷售帳戶是 0107，但庫存來自其他帳戶，WITHDRAW 會記錄在其他帳戶上

2. 【新邏輯】（當前使用，從 app.py 第 995 行開始）：
   - 只創建 SalesRecord（銷售記錄）
   - 直接從售出扣款戶（rmb_account）扣款
   - 不再創建 WITHDRAW LedgerEntry（因為售出記錄已包含完整信息）
   - 註釋明確說明：「不創建 WITHDRAW LedgerEntry，因為售出記錄已經會在流水頁面顯示完整的扣款信息」

3. 【理論餘額計算】：
   理論餘額 = 當前餘額 + 售出扣款 WITHDRAW 總額
   這表示：如果將歷史的 WITHDRAW 記錄回補，帳戶餘額應該等於原始狀態

4. 【0107 支付寶金額不對的可能原因】：
   根據舊邏輯，WITHDRAW 記錄的 account_id 是庫存來源帳戶（deposit_account），而不是銷售帳戶（rmb_account）。
   這意味著：
   - 如果從 0107 支付寶售出，但庫存來自其他帳戶（如7773、6186），WITHDRAW 會記錄在其他帳戶
   - 如果從其他帳戶售出，但庫存來自 0107 支付寶，WITHDRAW 會記錄在 0107
   - 因此，0107 的 WITHDRAW 總額可能包含了從其他帳戶售出的扣款
   - 7773 和 6186 正確，可能是因為它們的庫存來源與銷售帳戶一致
            """)
            
            # ========== 7. 詳細分析 0107 的問題 ==========
            if '0107' in target_accounts:
                print("\n【7】0107 支付寶問題診斷")
                print("-" * 100)
                
                info_0107 = target_accounts['0107']
                account_id_0107 = info_0107['id']
                
                # 查找所有包含 0107 庫存的銷售記錄（即使銷售帳戶不是 0107）
                print("查找所有使用 0107 支付寶庫存的銷售記錄：")
                from app import FIFOSalesAllocation, FIFOInventory, PurchaseRecord
                
                all_sales = db.session.execute(db.select(SalesRecord)).scalars().all()
                
                sales_using_0107_inventory = []
                sales_from_0107_account = []
                
                for sale in all_sales:
                    # 檢查銷售帳戶是否為 0107
                    if sale.rmb_account_id == account_id_0107:
                        sales_from_0107_account.append(sale)
                    
                    # 檢查是否有使用 0107 庫存的 FIFO 分配
                    allocations = db.session.execute(
                        db.select(FIFOSalesAllocation)
                        .filter(FIFOSalesAllocation.sales_record_id == sale.id)
                    ).scalars().all()
                    
                    for alloc in allocations:
                        if alloc.fifo_inventory and alloc.fifo_inventory.purchase_record:
                            source_account = alloc.fifo_inventory.purchase_record.deposit_account
                            if source_account and source_account.id == account_id_0107:
                                sales_using_0107_inventory.append({
                                    'sale': sale,
                                    'allocation': alloc,
                                    'amount': alloc.allocated_rmb
                                })
                
                print(f"  從 0107 支付寶售出的記錄: {len(sales_from_0107_account)} 筆")
                total_sales_from_0107 = sum(s.rmb_amount for s in sales_from_0107_account)
                print(f"  從 0107 支付寶售出的總額: {total_sales_from_0107:,.2f} RMB")
                
                print(f"  使用 0107 支付寶庫存的銷售記錄: {len(sales_using_0107_inventory)} 筆")
                total_inventory_from_0107 = sum(item['amount'] for item in sales_using_0107_inventory)
                print(f"  使用 0107 支付寶庫存的總額: {total_inventory_from_0107:,.2f} RMB")
                
                # 這就是關鍵！
                print(f"\n⚠️  關鍵發現：")
                print(f"  - 從 0107 銷售的總額: {total_sales_from_0107:,.2f} RMB")
                print(f"  - 使用 0107 庫存的總額: {total_inventory_from_0107:,.2f} RMB")
                print(f"  - 0107 的 WITHDRAW 總額: {info_0107['data']['total_amount']:,.2f} RMB")
                
                if abs(total_inventory_from_0107 - info_0107['data']['total_amount']) < abs(total_sales_from_0107 - info_0107['data']['total_amount']):
                    print(f"\n✅ 結論：0107 的 WITHDRAW 總額更接近使用 0107 庫存的總額！")
                    print(f"   這證明 WITHDRAW 記錄的 account_id 是庫存來源帳戶，而不是銷售帳戶")
                    print(f"   因此：0107 的 WITHDRAW 包含了從其他帳戶售出但使用 0107 庫存的記錄")
                    print(f"   而 7773 和 6186 正確，可能是因為它們的庫存來源與銷售帳戶基本一致")
            
        except Exception as e:
            print(f"\n❌ 分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == "__main__":
    print("售出扣款 WITHDRAW 記錄分析工具")
    print("此工具會分析 WITHDRAW 記錄的歷史、計算邏輯，並比較三個支付寶帳戶\n")
    
    exit_code = analyze_withdraw_history()
    sys.exit(exit_code)

