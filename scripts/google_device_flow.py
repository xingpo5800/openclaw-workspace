#!/usr/bin/env python3
"""测试Google OAuth Device Code Flow"""
import urllib.request
import json

# Google OAuth Device Code Flow
# https://developers.google.com/identity/protocols/oauth2/for-devices
DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"

CLIENT_ID = "542002026763-i3nrvvli4nkk37m8kmrh1fefgumtq62e.apps.googleusercontent.com"

print("1. 请求Device Code...")
data = json.dumps({
    "client_id": CLIENT_ID,
    "scope": "openid email profile"
}).encode()

req = urllib.request.Request(DEVICE_CODE_URL, data=data, headers={
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
})

try:
    resp = urllib.request.urlopen(req, timeout=10)
    result = json.loads(resp.read().decode())
    device_code = result.get("device_code", "")
    user_code = result.get("user_code", "")
    verification_url = result.get("verification_url", "")
    interval = result.get("interval", 5)
    
    print(f"   device_code: {device_code}")
    print(f"   user_code: {user_code}")
    print(f"   verification_url: {verification_url}")
    print(f"   interval: {interval}")
    
    if device_code and user_code:
        print(f"\n2. User Code: {user_code}")
        print(f"   请手动访问: {verification_url}")
        print(f"   然后输入 user_code 登录Google")
        print(f"   (但这需要手动操作...)")
        
        # 自动轮询token
        print(f"\n3. 等待用户登录...")
        import time
        for i in range(20):
            time.sleep(interval)
            
            # 请求token
            token_data = json.dumps({
                "client_id": CLIENT_ID,
                "device_code": device_code,
                "grant_type": "http://oauth.net/grant_type/device/1.0"
            }).encode()
            
            token_req = urllib.request.Request(TOKEN_URL, data=token_data, headers={
                "Content-Type": "application/json"
            })
            
            try:
                token_resp = urllib.request.urlopen(token_req, timeout=10)
                token_result = json.loads(token_resp.read().decode())
                print(f"\n4. 成功! Token:")
                print(f"   id_token: {token_result.get('id_token', '')[:50]}...")
                print(f"   access_token: {token_result.get('access_token', '')[:30]}...")
                break
            except urllib.error.HTTPError as e:
                error = json.loads(e.read().decode())
                error_code = error.get("error", "")
                print(f"   轮询 {i+1}/20: {error_code}")
                if error_code in ["invalid_grant", "invalid_request"]:
                    print(f"   登录失败: {error}")
                    break
        else:
            print("\n   轮询超时")
            
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:300]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
