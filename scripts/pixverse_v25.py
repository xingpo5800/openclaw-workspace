#!/usr/bin/env python3
"""PixVerse 登录 - v25 模拟真实浏览器"""
import asyncio
from playwright.async_api import async_playwright

EMAIL = "zhengyi5800@gmail.com"
PASSWORD = "Xingpo888***"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 非headless模式
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        # 注入脚本隐藏webdriver
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
        """)

        page = await context.new_page()
        page.set_default_timeout(30000)

        print("1. 打开PixVerse登录页...")
        await page.goto("https://app.pixverse.ai/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"   URL: {page.url}")

        await page.screenshot(path="/home/kevin/v25_s1.png")

        # 等待页面完全加载
        await page.wait_for_load_state("networkidle", timeout=20000)
        await asyncio.sleep(3)

        # 检查Google iframe
        iframe_el = page.locator("iframe[src*='google.com']").first
        if await iframe_el.count() > 0:
            print("2. 找到Google iframe，尝试点击...")

            # 获取iframe的frame对象
            frame = page.frame(url=lambda u: "google.com" in u)
            if frame:
                print(f"   frame URL: {frame.url[:60]}")
                # 在frame里找按钮
                btn_count = await frame.locator("button").count()
                print(f"   frame内button数: {btn_count}")
                
                if btn_count > 0:
                    # 点击frame内的按钮
                    await frame.locator("button").first.click()
                    print("3. 点击frame内按钮成功!")
                else:
                    # 尝试JS点击
                    clicked = await frame.evaluate("""() => {
                        const btn = document.querySelector('button, [role="button"], div');
                        if (btn) { btn.click(); return btn.className; }
                        return 'not found';
                    }""")
                    print(f"3. JS点击: {clicked}")
            else:
                # 不用frame，直接在主页面点击iframe父元素
                await iframe_el.click(timeout=5000)
                print("2. 直接点击iframe元素")
        else:
            print("2. 未找到Google iframe")

        await asyncio.sleep(5)
        await page.screenshot(path="/home/kevin/v25_s2.png")
        print(f"4. 当前URL: {page.url}")

        # 检查弹窗
        pages = context.pages
        print(f"5. 页面数: {len(pages)}")
        for i, pg in enumerate(pages):
            print(f"   [{i}] {pg.url[:80]}")

        await browser.close()
        print("完成!")

asyncio.run(main())
