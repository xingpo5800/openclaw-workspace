#!/usr/bin/env python3
"""PixVerse 登录 - v16 等待页面稳定"""
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
        await asyncio.sleep(3)

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
        
        # 等待页面稳定
        await asyncio.sleep(5)
        
        # 截图
        await page.screenshot(path="/home/kevin/v16_s1.png")
        print("3. 截图已保存")

        # 关闭语言下拉框
        try:
            await page.locator('button:has-text("English")').first.click(timeout=3000)
            print("4. 关闭语言下拉框")
            await asyncio.sleep(1)
        except:
            pass

        # 等待一下
        await asyncio.sleep(2)

        # 再次截图
        await page.screenshot(path="/home/kevin/v16_s2.png")
        print("5. 关闭下拉框后截图")

        # 用JS精确查找并点击Google按钮
        result = await page.evaluate("""() => {
            const buttons = document.querySelectorAll('button');
            for (let i = 0; i < buttons.length; i++) {
                const btn = buttons[i];
                const text = btn.innerText?.trim();
                if (text === 'Sign in with Google') {
                    console.log('找到Google按钮, 位置:', i);
                    console.log('按钮位置:', btn.getBoundingClientRect());
                    console.log('按钮是否可见:', btn.offsetParent !== null);
                    btn.click();
                    return true;
                }
            }
            console.log('没找到Google按钮');
            return false;
        }""")
        print(f"6. JS点击结果: {result}")
        await asyncio.sleep(5)

        await page.screenshot(path="/home/kevin/v16_s3.png")
        print(f"7. 点击后URL: {page.url}")

        # 如果是Google登录页
        if "accounts.google" in page.url:
            print("8. 在Google登录页，输入邮箱...")
            await page.locator('input[type="email"], input[name="identifier"]').first.fill(EMAIL)
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)

            print("9. 输入密码...")
            await page.locator('input[type="password"], input[name="password"]').first.fill(PASSWORD)
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)

            print(f"10. 登录后URL: {page.url}")
            await page.screenshot(path="/home/kevin/v16_s4.png")

        # 保存登录状态
        await context.storage_state(path="/home/kevin/pixverse_state.json")
        print(f"✅ 登录状态已保存! 最终URL: {page.url}")

        await browser.close()
        print("完成!")

asyncio.run(main())