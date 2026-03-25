#!/usr/bin/env python3
"""PixVerse 登录 - v19 用frame()切入iframe"""
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

        await page.screenshot(path="/home/kevin/v19_s1.png")

        # 用frame()按URL获取iframe
        frame = page.frame(url=lambda u: "accounts.google.com" in u)
        if frame:
            print(f"2. 已切换到Google iframe: {frame.url}")
            
            # 截图iframe内容
            await frame.screenshot(path="/home/kevin/v19_iframe.png")
            
            # 点击Google按钮 - 尝试多种方式
            try:
                await frame.locator('[aria-label="Sign in with Google"]').click(timeout=5000)
                print("3. 点击aria-label成功!")
            except Exception as e:
                print(f"3. aria-label: {e}")
                try:
                    await frame.locator('button.nsm7Bb-HzV7m-LgbsSe').click(timeout=5000)
                    print("3. 点击.nsm7Bb成功!")
                except Exception as e2:
                    print(f"3. nsm7Bb: {e2}")
                    try:
                        await frame.locator('button').click(timeout=5000)
                        print("3. 点击button成功!")
                    except Exception as e3:
                        print(f"3. button: {e3}")
                        # 最后用JS
                        await frame.evaluate('() => { const btn = document.querySelector("button"); if(btn) btn.click(); }')
                        print("3. JS点击完成")
        else:
            print("2. 找不到Google iframe")
            # 列出所有frame
            frames = page.frames
            print(f"   所有frame数: {len(frames)}")
            for f in frames:
                print(f"   frame: {f.url[:80]}")

        await asyncio.sleep(5)
        await page.screenshot(path="/home/kevin/v19_s2.png")
        print(f"4. 当前URL: {page.url}")

        # Google OAuth 弹窗
        try:
            # 等待新窗口/弹窗
            popup = await context.wait_for_event("page", timeout=10000)
            print(f"5. 弹窗: {popup.url}")
            await asyncio.sleep(3)
        except:
            print("5. 无新弹窗")

        print(f"6. 最终URL: {page.url}")
        await page.screenshot(path="/home/kevin/v19_s3.png")

        await context.storage_state(path="/home/kevin/pixverse_state.json")
        print("✅ 登录状态已保存!")
        await browser.close()
        print("完成!")

asyncio.run(main())
