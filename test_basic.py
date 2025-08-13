import urllib.request
import urllib.parse
import json

def test_basic():
    print("=== 基本渠道功能測試 ===")
    
    try:
        # 測試公開渠道API
        print("\n1. 測試獲取渠道列表...")
        url = "http://127.0.0.1:5000/api/channels/public"
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = response.read()
            channels = json.loads(data.decode('utf-8'))
            print(f"✓ 成功獲取渠道列表: {len(channels)} 個渠道")
            for channel in channels:
                print(f"  - {channel['name']} (ID: {channel['id']})")
                
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP錯誤: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        print(f"✗ 連接錯誤: {e.reason}")
    except Exception as e:
        print(f"✗ 其他錯誤: {e}")
    
    print("\n=== 測試完成 ===")

if __name__ == "__main__":
    test_basic()
