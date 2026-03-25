#!/usr/bin/env python3
"""PixVerse 登录 - v6 最终版"""
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

        # 关弹窗 - 直接用JS关掉modal
        try:
            await page.evaluate("""() => {
                // 关掉所有open状态的弹窗
                document.querySelectorAll('[data-state="open"]').forEach(el => {
                    el.remove();
                });
                // 或者设置关闭属性
                document.querySelectorAll('.fixed.inset-0.bg-black').forEach(el => el.remove());
            }""")
            print("用JS删除了弹窗")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"JS弹窗处理: {e}")

        print(f"URL: {page.url}")
        await page.screenshot(path="/home/kevin/v6_s1.png")

        # 点登录 - 用force=True跳过overlay检查
        try:
            login = page.locator('button:has-text("Login")').first
            await login.click(timeout=8000, force=True)
            print("点击Login成功")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"Login: {e}")

        print(f"登录页URL: {page.url}")
        await page.screenshot(path="/home/kevin/v6_s2.png")

        # 找Google登录
        try:
            google = page.locator('[aria-label*="google" i], [title*="google" i], button:has-text("Google")').first
            await google.click(timeout=8000, force=True)
            print("点击Google成功")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"Google: {e}")

        print(f"Google页URL: {page.url}")
        await page.screenshot(path="/home/kevin/v6_s3.png")

        # Google登录流程
        if "accounts.google" in page.url:
            print("在Google登录页...")
            try:
                await page.locator('input[type="email"], input[name="identifier"]').first.fill(EMAIL)
                await asyncio.sleep(1)
                await page.keyboard.press("Enter")
                await asyncio.sleep(3)
                
                await page.locator('input[type="password"]').first.fill(PASSWORD)
                await asyncio.sleep(1)
                await page.keyboard.press("Enter")
                await asyncio.sleep(5)
                
                print("登录完成!")
            except Exception as e:
                print(f"Google输入: {e}")

        print(f"最终URL: {page.url}")
        await page.screenshot(path="/home/kevin/v6_s4.png")
        
        # 保存登录状态
        await context.storage_state(path="/home/kevin/pixverse_state.json")
        print("登录状态已保存!")
        
        await browser.close()
        print("完成!")

asyncio.run(main())
