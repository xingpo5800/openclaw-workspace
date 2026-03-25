#!/usr/bin/env python3
"""PixVerse 登录 - v18 切换iframe点击Google按钮"""
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

        print("1. 打开登录页...")
        await page.goto("https://app.pixverse.ai/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"   URL: {page.url}")

        await page.screenshot(path="/home/kevin/v18_s1.png")

        # 找iframe
        iframe_el = page.locator("iframe").first
        print("2. 找到Google iframe")

        # 切换到iframe
        frame = await iframe_el.content_frame()
        if frame:
            print("3. 已切换到iframe")
            
            # 在iframe中查找Google按钮
            await frame.screenshot(path="/home/kevin/v18_iframe.png")
            
            # 直接点击Google按钮容器
            google_btn = frame.locator('[aria-label="Sign in with Google"], #container button').first
            try:
                await google_btn.click(timeout=5000)
                print("4. 点击Google按钮成功!")
            except Exception as e:
                print(f"4. 点击失败: {e}")
                # 尝试JS点击
                await frame.evaluate('''() => {
                    const btn = document.querySelector('[aria-label="Sign in with Google"] button, #container button, .nsm7Bb-HzV7m-LgbsSe');
                    if (btn) btn.click();
                }''')
                print("   JS点击完成")
        else:
            print("3. 无法获取iframe")

        await asyncio.sleep(5)
        await page.screenshot(path="/home/kevin/v18_s2.png")
        print(f"5. 当前URL: {page.url}")

        # 如果跳转到Google
        if "accounts.google" in page.url or "googleapis" in page.url:
            print("6. 在Google登录页...")
            await page.locator('input[type="email"], input[name="identifier"]').first.fill(EMAIL)
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)
            await page.locator('input[type="password"], input[name="password"]').first.fill(PASSWORD)
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)

        await page.screenshot(path="/home/kevin/v18_s3.png")
        print(f"7. 最终URL: {page.url}")

        await context.storage_state(path="/home/kevin/pixverse_state.json")
        print("✅ 登录状态已保存!")
        await browser.close()
        print("完成!")

asyncio.run(main())
