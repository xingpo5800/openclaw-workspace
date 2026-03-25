#!/usr/bin/env python3
"""PixVerse 登录 - 简单版"""
import asyncio
from playwright.async_api import async_playwright

EMAIL = "zhengyi5800@gmail.com"
PASSWORD = "Xingpo888***"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            java_script_enabled=True
        )
        page = await context.new_page()
        page.set_default_timeout(15000)

        print("打开PixVerse...")
        await page.goto("https://app.pixverse.ai", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # 关弹窗
        try:
            close = page.locator('[aria-label="Close"], [aria-label="close"]').first
            await close.click(timeout=3000)
            print("关掉弹窗")
        except:
            pass

        print(f"当前URL: {page.url}")
        await page.screenshot(path="/home/kevin/s1.png")

        # 点登录
        try:
            login = page.locator('button:has-text("Login")').first
            await login.click(timeout=5000)
            print("点击登录")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"找登录按钮: {e}")

        print(f"登录页URL: {page.url}")
        await page.screenshot(path="/home/kevin/s2.png")

        # 找Google登录
        try:
            google = page.locator('[aria-label*="Google" i], [title*="Google" i]').first
            await google.click(timeout=5000)
            print("点击Google登录")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"找Google按钮: {e}")

        print(f"Google页URL: {page.url}")
        await page.screenshot(path="/home/kevin/s3.png")

        # 如果是Google登录页，输入邮箱
        if "accounts.google" in page.url:
            print("在Google登录页，输入邮箱...")
            await page.locator('input[type="email"], input[name="identifier"]').first.fill(EMAIL)
            await asyncio.sleep(1)
            await page.locator('button:has-text("Next"), button:has-text("继续")').first.click()
            await asyncio.sleep(2)
            
            print("输入密码...")
            await page.locator('input[type="password"], input[name="password"]').first.fill(PASSWORD)
            await asyncio.sleep(1)
            await page.locator('button:has-text("Next"), button:has-text("继续")').first.click()
            await asyncio.sleep(5)

        print(f"最终URL: {page.url}")
        await page.screenshot(path="/home/kevin/s4.png")
        await browser.close()
        print("完成!")

asyncio.run(main())
