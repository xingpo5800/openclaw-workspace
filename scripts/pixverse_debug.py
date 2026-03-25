#!/usr/bin/env python3
"""PixVerse 登录 - v5 调试版"""
import asyncio
import json
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

        # 关弹窗 - 按ESC或点空白处
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)
        
        # 找所有可点击文本
        texts = await page.evaluate("""() => {
            const els = document.querySelectorAll('button, a, [role="button"], [tabindex]');
            const found = [];
            els.forEach(el => {
                const txt = el.innerText?.trim().slice(0, 50);
                const aria = el.getAttribute('aria-label') || '';
                const href = el.href || '';
                if (txt || aria) {
                    found.push({tag: el.tagName, text: txt, aria: aria.slice(0,50), href: href.slice(0,50)});
                }
            });
            return JSON.stringify(found.slice(0, 50));
        }""")
        
        print("页面元素:")
        items = json.loads(texts)
        for item in items:
            if item['text'] or item['aria']:
                print(f"  {item['tag']}: {item['text'] or item['aria']}")
        
        await page.screenshot(path="/home/kevin/v5_s1.png")
        
        # 点登录按钮
        try:
            login = page.get_by_text("Login", exact=True).first
            await login.click(timeout=5000)
            print("点击Login")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"Login: {e}")
            # 尝试其他方式
            try:
                login = page.locator('[href*="login" i], [href*="sign" i]').first
                await login.click(timeout=5000)
                print("点击登录链接")
                await asyncio.sleep(3)
            except:
                pass

        await page.screenshot(path="/home/kevin/v5_s2.png")
        print(f"URL: {page.url}")
        
        # 再次列出元素
        texts2 = await page.evaluate("""() => {
            const els = document.querySelectorAll('button, a, [role="button"]');
            const found = [];
            els.forEach(el => {
                const txt = el.innerText?.trim().slice(0, 50);
                const aria = el.getAttribute('aria-label') || '';
                if (txt || aria) {
                    found.push({tag: el.tagName, text: txt, aria: aria.slice(0,50)});
                }
            });
            return JSON.stringify(found.slice(0, 50));
        }""")
        
        print("登录后元素:")
        items2 = json.loads(texts2)
        for item in items2:
            if item['text'] or item['aria']:
                print(f"  {item['tag']}: {item['text'] or item['aria']}")
        
        await browser.close()

asyncio.run(main())
