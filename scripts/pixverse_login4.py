#!/usr/bin/env python3
"""PixVerse 登录 - v4"""
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
        await page.goto("https://app.pixverse.ai/auth/login", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        print(f"URL: {page.url}")
        await page.screenshot(path="/home/kevin/v4_s1.png")

        # 直接在登录页找Google登录
        try:
            # 找所有按钮和链接
            buttons = await page.locator('button, a, [role="button"]').all()
            for b in buttons:
                try:
                    txt = await b.inner_text()
                    if txt and 'google' in txt.lower():
                        print(f"找到Google按钮: {txt}")
                        await b.click(timeout=5000)
                        await asyncio.sleep(3)
                        break
                except:
                    pass
        except Exception as e:
            print(f"找按钮: {e}")

        print(f"点击后URL: {page.url}")
        await page.screenshot(path="/home/kevin/v4_s2.png")

        # 如果是Google登录页
        if "accounts.google" in page.url:
            print("在Google登录页...")
            try:
                await page.locator('input[type="email"], input[name="identifier"], input[aria-label*="email" i]').first.fill(EMAIL)
                await asyncio.sleep(1)
                await page.keyboard.press("Enter")
                await asyncio.sleep(3)
                
                await page.locator('input[type="password"], input[name="password"], input[aria-label*="password" i]').first.fill(PASSWORD)
                await asyncio.sleep(1)
                await page.keyboard.press("Enter")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"输入: {e}")

        print(f"最终URL: {page.url}")
        await page.screenshot(path="/home/kevin/v4_s3.png")
        
        # 保存登录状态
        await context.storage_state(path="/home/kevin/pixverse_state.json")
        print("登录状态已保存!")
        
        await browser.close()
        print("完成!")

asyncio.run(main())
