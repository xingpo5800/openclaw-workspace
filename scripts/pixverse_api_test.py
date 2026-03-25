#!/usr/bin/env python3
import urllib.request
import json

API_BASE = "https://app-api.pixverse.ai"

endpoints = [
    "/creative_platform/auth/google",
    "/creative_platform/user/login",
    "/creative_platform/auth/login",
    "/creative_platform/login",
    "/auth/login",
    "/user/login",
]

for ep in endpoints:
    url = API_BASE + ep
    try:
        data = json.dumps({"email": "zhengyi5800@gmail.com", "password": "Xingpo888***"}).encode()
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Origin": "https://app.pixverse.ai",
            "Referer": "https://app.pixverse.ai/"
        })
        try:
            resp = urllib.request.urlopen(req, timeout=8)
            body = resp.read().decode()
            print(f"OK {ep}: {resp.status}")
            print(f"   {body[:300]}")
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            print(f"ERR {ep}: {e.code} {e.reason}")
            print(f"   {body}")
        except Exception as e:
            print(f"ERR {ep}: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"FAIL {ep}: {e}")
