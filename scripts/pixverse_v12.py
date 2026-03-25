#!/usr/bin/env python3
"""PixVerse 登录 - v12 调试版"""
import asyncio
import json
from playwright.async_api import async_playwright

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
        await asyncio.sleep(2)

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

        # 用JS列出所有可点击元素
        result = await page.evaluate("""() => {
            const items = [];
            // button
            document.querySelectorAll('button').forEach(el => {
                const text = el.innerText?.trim() || '';
                const aria = el.getAttribute('aria-label') || '';
                const title = el.getAttribute('title') || '';
                const classList = el.className || '';
                if (text || aria || title) {
                    items.push({tag: 'button', text: text.slice(0,50), aria: aria.slice(0,50), title: title.slice(0,50), class: classList.slice(0,50)});
                }
            });
            // a标签
            document.querySelectorAll('a').forEach(el => {
                const text = el.innerText?.trim() || '';
                const aria = el.getAttribute('aria-label') || '';
                const title = el.getAttribute('title') || '';
                const href = el.getAttribute('href') || '';
                if (text || aria || title) {
                    items.push({tag: 'a', text: text.slice(0,50), aria: aria.slice(0,50), title: title.slice(0,50), href: href.slice(0,50)});
                }
            });
            return JSON.stringify(items.slice(0, 100));
        }""")

        print("页面元素:")
        items = json.loads(result)
        for item in items:
            if item['text'] or item['aria'] or item['title']:
                print(f"  [{item['tag']}] text={item['text']}, aria={item['aria']}, title={item['title']}")

        await page.screenshot(path="/home/kevin/v12_s1.png")

        await browser.close()
        print("完成!")

asyncio.run(main())
