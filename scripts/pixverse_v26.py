#!/usr/bin/env python3
"""PixVerse 登录 - v26 stealth正确用法"""
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth

EMAIL = "zhengyi5800@gmail.com"
PASSWORD = "Xingpo888***"

async def main():
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        page.set_default_timeout(15000)

        print("1. Stealth模式已启用")
        await page.goto("https://app.pixverse.ai/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"   URL: {page.url}")

        is_webdriver = await page.evaluate("navigator.webdriver")
        print(f"2. navigator.webdriver = {is_webdriver}")
        await page.screenshot(path="/home/kevin/v26_s1.png")

        # GIS prompt
        client_id = await page.evaluate("""() => {
            const iframe = document.querySelector('iframe[src*="google.com"]');
            if (!iframe) return null;
            const match = iframe.src.match(/client_id=([^&]+)/);
            return match ? match[1] : null;
        }""")
        print(f"3. Client ID: {client_id}")

        if client_id:
            await page.evaluate(f"""() => {{
                google.accounts.id.initialize({{
                    client_id: '{client_id}',
                    auto_select: false,
                    callback: (resp) => {{
                        window._gis_cb = resp;
                    }}
                }});
                setTimeout(() => {{
                    google.accounts.id.prompt(notification => {{
                        console.log('prompt:', notification);
                    }});
                }}, 2000);
            }}""")
            print("4. GIS prompt已调用")
            await asyncio.sleep(5)
            await page.screenshot(path="/home/kevin/v26_s2.png")

            gis_cb = await page.evaluate("window._gis_cb || null")
            if gis_cb:
                print(f"5. GIS回调: {str(gis_cb)[:100]}")
            else:
                print("5. 无GIS回调")

        print(f"6. 最终URL: {page.url}")
        print(f"   页面数: {len(context.pages)}")

        await browser.close()
        print("完成!")

asyncio.run(main())
