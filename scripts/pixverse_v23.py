#!/usr/bin/env python3
"""PixVerse 登录 - v23 绕过自动化检测"""
import asyncio
from playwright.async_api import async_playwright

EMAIL = "zhengyi5800@gmail.com"
PASSWORD = "Xingpo888***"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--exclude-switches=enable-automation",
                "--disable-infobars",
                "--no-first-run",
                "--no-zygote",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            # 模拟真实浏览器
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(15000)

        # 隐藏 webdriver
        await page.add_init_script("""() => {
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            navigator.chrome = { runtime: {} };
            window.navigator.chrome = { runtime: {} };
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        }""")

        print("1. 打开登录页 (反检测模式)...")
        await page.goto("https://app.pixverse.ai/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"   URL: {page.url}")
        await page.screenshot(path="/home/kevin/v23_s1.png")

        # GIS prompt
        print("2. GIS prompt...")
        await page.evaluate('''() => {
            const iframe = document.querySelector('iframe[src*="google.com"]');
            const src = iframe ? iframe.src : '';
            const match = src.match(/client_id=([^&]+)/);
            const clientId = match ? match[1] : '';
            
            google.accounts.id.initialize({
                client_id: clientId,
                auto_select: false,
                callback: (response) => {
                    window._gis_resp = response;
                }
            });
            
            // 等一下再prompt
            setTimeout(() => {
                google.accounts.id.prompt();
            }, 2000);
        }''')

        await asyncio.sleep(8)
        await page.screenshot(path="/home/kevin/v23_s2.png")
        print(f"3. 当前URL: {page.url}")

        # 如果URL没变，尝试点击iframe父容器
        if "pixverse" in page.url:
            print("4. 点击iframe父容器...")
            await page.evaluate('''() => {
                const iframe = document.querySelector('iframe[src*="google.com"]');
                const parent = iframe?.parentElement;
                if (parent) {
                    const event = new MouseEvent('click', {
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: 100,
                        clientY: 50
                    });
                    parent.dispatchEvent(event);
                    console.log('dispatched click event on:', parent.className);
                }
            }''')
            await asyncio.sleep(5)
            await page.screenshot(path="/home/kevin/v23_s3.png")
            print(f"5. 点击后URL: {page.url}")

        # 检查所有页面
        pages = context.pages
        print(f"6. 页面数: {len(pages)}")
        for i, pg in enumerate(pages):
            print(f"   [{i}] {pg.url[:80]}")

        # GIS响应
        gis_resp = await page.evaluate('window._gis_resp || null')
        if gis_resp:
            print(f"7. GIS响应: {str(gis_resp)[:100]}")
            # 用token登录PixVerse
            import json
            resp = json.loads(gis_resp)
            if 'credential' in resp:
                print("8. 获取到credential，尝试用token登录...")
                # PixVerse API用credential登录
                pass

        await browser.close()
        print("完成!")

asyncio.run(main())
