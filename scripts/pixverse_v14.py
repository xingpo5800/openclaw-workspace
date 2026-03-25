#!/usr/bin/env python3
"""PixVerse 登录 - v14 用load等待"""
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
        await page.goto("https://app.pixverse.ai", wait_until="load")
        await asyncio.sleep(8)  # 等待动态内容

        # 关弹窗
        await page.evaluate("""() => {
            const modals = document.querySelectorAll('[data-state="open"]');
            modals.forEach(modal => {
                const closeBtn = modal.querySelector('button, [role="button"]');
                if (closeBtn) closeBtn.click();
            });
        }""")
        await asyncio.sleep(1)

        # 点登录
        await page.locator('button:has-text("Login")').first.click(timeout=8000, force=True)
        await asyncio.sleep(3)

        # 等待登录页
        await page.wait_for_url("**/login**", timeout=10000)
        print(f"2. 到达登录页: {page.url}")
        await asyncio.sleep(5)

        # 截图
        await page.screenshot(path="/home/kevin/v14_s1.png")

        # 用JS查找并点击Google按钮
        await page.evaluate("""() => {
            const buttons = document.querySelectorAll('button, a');
            for (let btn of buttons) {
                const text = btn.innerText?.trim() || '';
                const aria = btn.getAttribute('aria-label') || '';
                const title = btn.getAttribute('title') || '';
                const href = btn.getAttribute('href') || '';
                if (text.toLowerCase().includes('google') || aria.toLowerCase().includes('google') || title.toLowerCase().includes('google') || href.includes('google')) {
                    console.log('找到Google按钮:', text, aria, href);
                    btn.click();
                    break;
                }
            }
        }""")
        print("3. 用JS点击Google按钮")
        await asyncio.sleep(8)

        await page.screenshot(path="/home/kevin/v14_s2.png")
        print(f"4. 当前URL: {page.url}")

        # 如果是Google登录页
        if "accounts.google" in page.url:
            print("5. 在Google登录页，输入邮箱...")
            await page.locator('input[type="email"], input[name="identifier"]').first.fill(EMAIL)
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)

            print("6. 输入密码...")
            await page.locator('input[type="password"], input[name="password"]').first.fill(PASSWORD)
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)

            print(f"7. 登录后URL: {page.url}")
            await page.screenshot(path="/home/kevin/v14_s3.png")

        # 保存登录状态
        await context.storage_state(path="/home/kevin/pixverse_state.json")
        print(f"✅ 登录状态已保存! 最终URL: {page.url}")

        await browser.close()
        print("完成!")

asyncio.run(main())
