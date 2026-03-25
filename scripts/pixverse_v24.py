#!/usr/bin/env python3
"""PixVerse 登录 - v24 直接去Google登录"""
import asyncio
from playwright.async_api import async_playwright

EMAIL = "zhengyi5800@gmail.com"
PASSWORD = "Xingpo888***"

# PixVerse的OAuth配置
CLIENT_ID = "542002026763-i3nrvvli4nkk37m8kmrh1fefgumtq62e.apps.googleusercontent.com"
REDIRECT_URI = "https://app.pixverse.ai/login"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        page.set_default_timeout(15000)

        # Step 1: 直接打开Google OAuth授权页
        print("1. 打开Google授权页...")
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=openid%20email%20profile"
            f"&access_type=offline"
            f"&prompt=consent"
        )
        await page.goto(auth_url, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"   URL: {page.url}")
        await page.screenshot(path="/home/kevin/v24_s1.png")

        # Step 2: 在Google页登录
        if "accounts.google.com" in page.url:
            print("2. 在Google页输入邮箱...")
            await page.locator('input[type="email"], input[name="identifier"]').first.fill(EMAIL)
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)

            print("3. 输入密码...")
            await page.screenshot(path="/home/kevin/v24_s2.png")
            await page.locator('input[type="password"], input[name="password"]').first.fill(PASSWORD)
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)

            print(f"4. 登录后URL: {page.url}")
            await page.screenshot(path="/home/kevin/v24_s3.png")

        # Step 3: Google会重定向回PixVerse
        if "pixverse" in page.url or "code=" in page.url:
            print(f"5. 授权完成! URL: {page.url}")
            # 提取code
            code = await page.evaluate('() => new URL(window.location.href).searchParams.get("code")')
            print(f"   Auth Code: {code[:50] if code else None}...")
        else:
            print(f"5. 当前URL: {page.url}")

        await browser.close()
        print("完成!")

asyncio.run(main())
