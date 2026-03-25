#!/usr/bin/env python3
"""PixVerse 登录 - v10"""
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

        print("1. 打开PixVerse...")
        await page.goto("https://app.pixverse.ai", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # 用JS关闭modal
        await page.evaluate("""() => {
            const modals = document.querySelectorAll('[data-state="open"]');
            modals.forEach(modal => {
                const closeBtn = modal.querySelector('button, [role="button"]');
                if (closeBtn) closeBtn.click();
            });
        }""")
        await asyncio.sleep(1)
        print("2. 关闭弹窗")

        # 点登录
        await page.locator('button:has-text("Login")').first.click(timeout=8000, force=True)
        await asyncio.sleep(3)
        print(f"3. 点击Login, URL: {page.url}")

        # 等待login页面加载
        await page.wait_for_url("**/login**", timeout=10000)
        print(f"4. 到达登录页: {page.url}")
        await page.screenshot(path="/home/kevin/v10_s1.png")

        # 点Google登录 - 搜索"Sign in with Google"
        try:
            google_btn = page.locator('button:has-text("Sign in with Google")').first
            await google_btn.click(timeout=8000, force=True)
            print("5. 点击Google登录成功")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Google按钮失败: {e}")
            # 试试找包含Google的按钮
            try:
                google_btn = page.locator('button:has-text("Google")').first
                await google_btn.click(timeout=8000, force=True)
                print("6. 点击Google按钮成功")
                await asyncio.sleep(5)
            except:
                print("无法点击Google按钮")

        await page.screenshot(path="/home/kevin/v10_s2.png")
        print(f"6. 当前URL: {page.url}")

        # 如果是Google登录页
        if "accounts.google" in page.url:
            print("7. 在Google登录页，输入邮箱...")
            await page.locator('input[type="email"], input[name="identifier"]').first.fill(EMAIL)
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)

            print("8. 输入密码...")
            await page.locator('input[type="password"], input[name="password"]').first.fill(PASSWORD)
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)

            print(f"9. 登录后URL: {page.url}")
            await page.screenshot(path="/home/kevin/v10_s3.png")

        # 保存登录状态
        await context.storage_state(path="/home/kevin/pixverse_state.json")
        print(f"✅ 登录状态已保存! 最终URL: {page.url}")

        await browser.close()
        print("完成!")

asyncio.run(main())
