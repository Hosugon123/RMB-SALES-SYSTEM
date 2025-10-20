#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests
import json
from datetime import datetime

def test_api_performance():
    """測試API性能"""
    print("=== API性能測試 ===")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    base_url = "http://localhost:5000"
    
    # 測試的API端點
    apis = [
        {
            "name": "完整API",
            "url": f"{base_url}/api/cash_management/transactions?page=1&per_page=10",
            "timeout": 30
        },
        {
            "name": "簡化API", 
            "url": f"{base_url}/api/cash_management/transactions_simple?page=1&per_page=10",
            "timeout": 10
        },
        {
            "name": "總利潤API",
            "url": f"{base_url}/api/total-profit",
            "timeout": 10
        }
    ]
    
    results = []
    
    for api in apis:
        print(f"測試 {api['name']}:")
        print(f"  URL: {api['url']}")
        
        start_time = time.time()
        
        try:
            response = requests.get(api['url'], timeout=api['timeout'])
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'success':
                        print(f"  ✅ 成功 - 響應時間: {response_time:.2f}秒")
                        
                        # 檢查數據量
                        if 'data' in data:
                            if 'transactions' in data['data']:
                                record_count = len(data['data']['transactions'])
                                print(f"  📊 記錄數量: {record_count}")
                            elif 'records' in data['data']:
                                record_count = len(data['data']['records'])
                                print(f"  📊 記錄數量: {record_count}")
                        
                        results.append({
                            'name': api['name'],
                            'success': True,
                            'response_time': response_time,
                            'status_code': response.status_code
                        })
                    else:
                        print(f"  ❌ API返回錯誤: {data.get('message', 'Unknown error')}")
                        results.append({
                            'name': api['name'],
                            'success': False,
                            'error': data.get('message', 'Unknown error')
                        })
                except json.JSONDecodeError:
                    print(f"  ❌ JSON解析失敗")
                    results.append({
                        'name': api['name'],
                        'success': False,
                        'error': 'JSON parse error'
                    })
            else:
                print(f"  ❌ HTTP錯誤: {response.status_code}")
                results.append({
                    'name': api['name'],
                    'success': False,
                    'error': f'HTTP {response.status_code}'
                })
                
        except requests.exceptions.Timeout:
            print(f"  ⏰ 超時 ({api['timeout']}秒)")
            results.append({
                'name': api['name'],
                'success': False,
                'error': 'Timeout'
            })
        except requests.exceptions.ConnectionError:
            print(f"  🔌 連接失敗")
            results.append({
                'name': api['name'],
                'success': False,
                'error': 'Connection error'
            })
        except Exception as e:
            print(f"  ❌ 其他錯誤: {e}")
            results.append({
                'name': api['name'],
                'success': False,
                'error': str(e)
            })
        
        print()
    
    # 總結
    print("=== 測試總結 ===")
    successful_apis = [r for r in results if r['success']]
    failed_apis = [r for r in results if not r['success']]
    
    print(f"成功: {len(successful_apis)}/{len(results)}")
    print(f"失敗: {len(failed_apis)}/{len(results)}")
    
    if successful_apis:
        print("\n成功的API:")
        for result in successful_apis:
            print(f"  ✅ {result['name']}: {result['response_time']:.2f}秒")
    
    if failed_apis:
        print("\n失敗的API:")
        for result in failed_apis:
            print(f"  ❌ {result['name']}: {result['error']}")
    
    print()
    
    # 建議
    print("=== 建議 ===")
    if any(r['name'] == '完整API' and r['success'] and r['response_time'] > 10 for r in results):
        print("⚠️ 完整API響應時間過長，建議:")
        print("  1. 使用簡化API作為備用")
        print("  2. 減少每頁記錄數量")
        print("  3. 優化FIFO計算邏輯")
    
    if any(r['name'] == '簡化API' and r['success'] for r in results):
        print("✅ 簡化API可用，建議在前端實現自動降級")
    
    print("\n=== 測試完成 ===")

if __name__ == "__main__":
    test_api_performance()
