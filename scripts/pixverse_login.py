#!/usr/bin/env python3
from playwright.async_api import async_playwright
import asyncio

EMAIL = "zhengyi5800@gmail.com"
PASSWORD = "Xingpo888***"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        await page.goto("https://app.pixverse.ai", timeout=30000)
        await asyncio.sleep(2)

        # 关弹窗
        try:
            close_btn = page.locator('[aria-label="Close"]').first
            await close_btn.click()
            await asyncio.sleep(1)
        except:
            pass

        print(f"URL: {page.url}")

        # 点登录
        try:
            login_btn = page.locator('button:has-text("Login"), a:has-text("Login")').first
            await login_btn.click()
            await asyncio.sleep(3)
            print(f"登录页URL: {page.url}")
        except Exception as e:
            print(f"点登录失败: {e}")

        await page.screenshot(path="/home/kevin/login_screen.png", full_page=True)
        print("截图已保存到 /home/kevin/login_screen.png")

        # 找Google登录
        try:
            google_btn = page.locator('[aria-label*="Google"], [title*="Google"], button:has-text("Google")').first
            await google_btn.click()
            await asyncio.sleep(3)
            print(f"Google登录页URL: {page.url}")
        except Exception as e:
            print(f"找Google按钮: {e}")

        await page.screenshot(path="/home/kevin/after_login.png", full_page=True)

        # 尝试输入Google账号
        try:
            email_input = page.locator('input[type="email"], input[aria-label*="email"], input[name="email"]').first
            await email_input.fill(EMAIL)
            await asyncio.sleep(1)
            next_btn = page.locator('button:has-text("Next"), button:has-text("继续"), button:has-text("下一步")').first
            await next_btn.click()
            await asyncio.sleep(2)
            pw_input = page.locator('input[type="password"], input[name="password"]').first
            await pw_input.fill(PASSWORD)
            await asyncio.sleep(1)
            submit_btn = page.locator('button:has-text("Next"), button:has-text("Sign in"), button:has-text("登录")').first
            await submit_btn.click()
            await asyncio.sleep(5)
            print(f"登录后URL: {page.url}")
        except Exception as e:
            print(f"Google登录流程: {e}")

        await page.screenshot(path="/home/kevin/final.png", full_page=True)
        await browser.close()
        print("完成")

asyncio.run(main())
