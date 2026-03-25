#!/usr/bin/env python3
import urllib.request
import json

API_BASE = "https://app-api.pixverse.ai"

# 尝试 /creative_platform/login with Username field
url = API_BASE + "/creative_platform/login"
data = json.dumps({"Username": "zhengyi5800@gmail.com", "Password": "Xingpo888***"}).encode()
req = urllib.request.Request(url, data=data, headers={
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Origin": "https://app.pixverse.ai",
    "Referer": "https://app.pixverse.ai/"
})
try:
    resp = urllib.request.urlopen(req, timeout=8)
    body = resp.read().decode()
    print(f"OK: {resp.status}")
    print(f"Headers: {dict(resp.headers)}")
    print(f"Body: {body[:500]}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {e.reason}")
    print(f"Body: {body[:500]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# Also check what the login page JS says about the auth endpoint
print("\n--- 检查其他可能端点 ---")
other_endpoints = [
    "/creative_platform/user/register",
    "/creative_platform/auth/register",
    "/creative_platform/register",
    "/creative_platform/guest/login",
    "/creative_platform/guest/register",
]
for ep in other_endpoints:
    url2 = API_BASE + ep
    data2 = json.dumps({}).encode()
    req2 = urllib.request.Request(url2, data=data2, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://app.pixverse.ai",
        "Referer": "https://app.pixverse.ai/"
    })
    try:
        resp2 = urllib.request.urlopen(req2, timeout=5)
        print(f"OK {ep}: {resp2.status}")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"ERR {ep}: {e.code}")
        else:
            pass  # skip 404s
    except:
        pass
