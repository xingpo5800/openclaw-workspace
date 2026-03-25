#!/usr/bin/env python3
"""PixVerse 登录 - v20 在iframe中点击Google按钮"""
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
            # 允许弹窗
        )
        page = await context.new_page()
        page.set_default_timeout(15000)

        print("1. 打开登录页...")
        await page.goto("https://app.pixverse.ai/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"   URL: {page.url}")

        await page.screenshot(path="/home/kevin/v20_s1.png")

        # 获取Google iframe
        frame = page.frame(url=lambda u: "accounts.google.com" in u and "gsi/button" in u)
        assert frame, "找不到Google iframe"
        print(f"2. 已切入Google iframe")

        # 在iframe中点击Google按钮
        print("3. 点击Google按钮...")
        try:
            await frame.locator('[aria-label="Sign in with Google"]').click(timeout=5000)
            print("   aria-label点击成功!")
        except Exception as e:
            print(f"   aria-label: {e}")
            try:
                await frame.locator('button').click(timeout=5000)
                print("   button点击成功!")
            except Exception as e2:
                print(f"   button: {e2}")
                await frame.evaluate('() => { document.querySelector("button")?.click() }')
                print("   JS点击完成")

        await asyncio.sleep(5)
        await page.screenshot(path="/home/kevin/v20_s2.png")
        print(f"4. 当前URL: {page.url}")

        # 检查是否有新窗口（OAuth弹窗）
        for _ in range(10):
            await asyncio.sleep(1)
            pages = context.pages
            if len(pages) > 1:
                print(f"5. 检测到弹窗! 共{len(pages)}个页面")
                oauth_page = pages[-1]
                print(f"   弹窗URL: {oauth_page.url}")
                break
        else:
            print("5. 无弹窗，URL:", page.url)

        # 如果还在主页面但有弹窗，点击Google按钮后再等待
        if "pixverse" in page.url and len(context.pages) == 1:
            # 也许OAuth是在当前页跳转的
            # 尝试等待URL变化
            try:
                await page.wait_for_url("**accounts.google.com**", timeout=8000)
                print("5. 页面跳转到Google")
            except:
                print("5. 未检测到Google跳转")

        print(f"6. 最终URL: {page.url}")
        await page.screenshot(path="/home/kevin/v20_s3.png")

        # 尝试Google登录
        if "accounts.google" in page.url:
            print("7. 在Google页，输入邮箱...")
            await page.locator('input[type="email"], input[name="identifier"]').first.fill(EMAIL)
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)
            await page.locator('input[type="password"], input[name="password"]').first.fill(PASSWORD)
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)
            print(f"   登录后URL: {page.url}")
            await page.screenshot(path="/home/kevin/v20_s4.png")

        await context.storage_state(path="/home/kevin/pixverse_state.json")
        print("✅ 登录状态已保存!")
        await browser.close()
        print("完成!")

asyncio.run(main())
