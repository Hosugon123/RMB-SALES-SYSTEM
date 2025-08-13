import requests

def test_simple():
    print("測試開始")
    
    try:
        # 測試公開渠道API
        response = requests.get("http://127.0.0.1:5000/api/channels/public")
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.text}")
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    test_simple()
