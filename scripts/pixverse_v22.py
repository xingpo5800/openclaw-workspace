#!/usr/bin/env python3
"""PixVerse 登录 - v22 点击iframe父容器+GIS prompt"""
import asyncio
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

        print("1. 打开登录页...")
        await page.goto("https://app.pixverse.ai/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"   URL: {page.url}")
        await page.screenshot(path="/home/kevin/v22_s1.png")

        # 方法A: 点击iframe父容器
        print("2. 方法A: 点击iframe父容器...")
        clicked = await page.evaluate('''() => {
            const iframe = document.querySelector('iframe[src*="google.com"]');
            if (!iframe) return 'no iframe';
            // 找到iframe的父容器
            let parent = iframe.parentElement;
            while (parent && parent.tagName !== 'BODY') {
                // 尝试点击父容器中的任意位置
                const rect = parent.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    parent.click();
                    return 'clicked parent: ' + parent.tagName + ' class=' + parent.className.slice(0,50);
                }
                parent = parent.parentElement;
            }
            // 直接点击iframe的某个邻居按钮
            const siblings = iframe.parentElement?.querySelectorAll('button, a, div[role="button"]');
            if (siblings && siblings.length > 0) {
                siblings[0].click();
                return 'clicked sibling: ' + siblings[0].tagName;
            }
            return 'failed';
        }''')
        print(f"   {clicked}")

        await asyncio.sleep(5)
        await page.screenshot(path="/home/kevin/v22_s2.png")
        print(f"3. 当前URL: {page.url}")

        # 方法B: GIS prompt
        if "pixverse" in page.url:
            print("4. 方法B: GIS prompt...")
            await page.evaluate('''() => {
                if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
                    // 用iframe的client_id
                    const iframe = document.querySelector('iframe[src*="google.com"]');
                    const src = iframe ? iframe.src : '';
                    const match = src.match(/client_id=([^&]+)/);
                    const clientId = match ? match[1] : '';
                    
                    google.accounts.id.initialize({
                        client_id: clientId,
                        auto_select: true,
                        callback: (response) => {
                            window._gis_resp = response;
                            console.log('GIS callback fired');
                        }
                    });
                    
                    // 调用prompt显示One Tap
                    google.accounts.id.prompt();
                    console.log('prompt() called');
                }
            }''')
            print("   prompt已调用")
            await asyncio.sleep(5)
            await page.screenshot(path="/home/kevin/v22_s3.png")
            print(f"5. prompt后URL: {page.url}")

        # 检查弹窗
        pages = context.pages
        print(f"6. 页面数: {len(pages)}")
        for i, pg in enumerate(pages):
            print(f"   [{i}] {pg.url[:80]}")

        # GIS响应
        gis_resp = await page.evaluate('window._gis_resp || null')
        if gis_resp:
            print(f"7. GIS响应: {str(gis_resp)[:100]}")

        await browser.close()
        print("完成!")

asyncio.run(main())
