#!/usr/bin/env python3
"""PixVerse 登录 - v15 多种方法点击"""
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
        await asyncio.sleep(5)

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
        await page.screenshot(path="/home/kevin/v15_s1.png")

        # 方法1: 直接用文本查找
        try:
            print("3. 方法1: 用文本查找...")
            await page.get_by_text("Sign in with Google").click(timeout=5000, force=True)
            print("   点击成功!")
        except Exception as e:
            print(f"   失败: {e}")

        await asyncio.sleep(2)

        # 方法2: 用locator
        try:
            print("4. 方法2: 用locator...")
            await page.locator('button:has-text("Sign in with Google")').first.click(timeout=5000, force=True)
            print("   点击成功!")
        except Exception as e:
            print(f"   失败: {e}")

        await asyncio.sleep(2)

        # 方法3: 用JS查找并点击
        try:
            print("5. 方法3: 用JS...")
            await page.evaluate("""() => {
                const buttons = document.querySelectorAll('button');
                for (let btn of buttons) {
                    const text = btn.innerText?.trim();
                    if (text === 'Sign in with Google') {
                        console.log('找到按钮:', text);
                        btn.click();
                        return true;
                    }
                }
                return false;
            }""")
            print("   JS点击成功!")
        except Exception as e:
            print(f"   失败: {e}")

        await asyncio.sleep(5)

        await page.screenshot(path="/home/kevin/v15_s2.png")
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
            await page.screenshot(path="/home/kevin/v15_s3.png")

        # 保存登录状态
        await context.storage_state(path="/home/kevin/pixverse_state.json")
        print(f"✅ 登录状态已保存! 最终URL: {page.url}")

        await browser.close()
        print("完成!")

asyncio.run(main())