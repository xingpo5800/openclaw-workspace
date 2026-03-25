#!/usr/bin/env python3
"""PixVerse 登录 - v7"""
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
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        page.set_default_timeout(15000)

        print("打开PixVerse...")
        await page.goto("https://app.pixverse.ai", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        # 尝试按ESC关弹窗
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)

        # 找close按钮并点击
        try:
            close = page.get_by_text("close", exact=True).first
            await close.click(timeout=3000, force=True)
            print("点击了close")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"close: {e}")

        await page.screenshot(path="/home/kevin/v7_s1.png")
        
        # 点登录
        try:
            login = page.locator('button:has-text("Login")').first
            await login.click(timeout=8000, force=True)
            print("点击Login成功")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Login: {e}")

        await page.screenshot(path="/home/kevin/v7_s2.png")
        print(f"URL: {page.url}")

        # 列出所有按钮
        btns = await page.locator('button, a').all()
        for b in btns:
            try:
                t = await b.inner_text()
                t = t.strip()[:30]
                if t:
                    print(f"  btn: {t}")
            except:
                pass

        await browser.close()
        print("完成!")

asyncio.run(main())
