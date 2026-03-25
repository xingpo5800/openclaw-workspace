#!/usr/bin/env python3
"""PixVerse 登录 - v8"""
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
        await asyncio.sleep(3)

        # 用JS找到并点击modal的关闭按钮
        await page.evaluate("""() => {
            // 找modal中的关闭按钮
            const modals = document.querySelectorAll('[data-state="open"]');
            modals.forEach(modal => {
                // 找modal里的X关闭按钮
                const closeBtn = modal.querySelector('button, [role="button"]');
                if (closeBtn) closeBtn.click();
                // 或者找SVG close图标
                const svgs = modal.querySelectorAll('svg');
                svgs.forEach(svg => {
                    const parent = svg.parentElement;
                    if (parent) parent.click();
                });
            });
        }""")
        print("尝试用JS关闭modal")
        await asyncio.sleep(2)

        # 再次尝试按ESC
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)

        await page.screenshot(path="/home/kevin/v8_s1.png")

        # 点登录
        login = page.locator('button:has-text("Login")').first
        await login.click(timeout=8000, force=True)
        print("点击Login成功")
        await asyncio.sleep(5)

        await page.screenshot(path="/home/kevin/v8_s2.png")
        print(f"URL: {page.url}")

        # 如果URL没变，试试其他按钮
        if page.url == "https://app.pixverse.ai/onboard":
            print("URL没变，尝试其他登录方式...")
            # 看看页面上有没有登录相关的链接
            try:
                signin = page.locator('a:has-text("Sign in"), button:has-text("Sign in")').first
                await signin.click(timeout=5000)
                print("点击Sign in")
                await asyncio.sleep(3)
            except:
                pass

        await page.screenshot(path="/home/kevin/v8_s3.png")
        print(f"最终URL: {page.url}")

        # 如果到了Google登录页
        if "accounts.google" in page.url:
            print("Google登录页...")
            await page.locator('input[type="email"], input[name="identifier"]').first.fill(EMAIL)
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)
            await page.locator('input[type="password"]').first.fill(PASSWORD)
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)

        await page.screenshot(path="/home/kevin/v8_s4.png")
        await context.storage_state(path="/home/kevin/pixverse_state.json")
        print("登录状态已保存!")
        await browser.close()
        print("完成!")

asyncio.run(main())
