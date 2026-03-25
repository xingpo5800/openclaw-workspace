#!/usr/bin/env python3
"""PixVerse 登录 - v21 用Google Identity Services API"""
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

        await page.screenshot(path="/home/kevin/v21_s1.png")

        # 从iframe URL中提取client_id
        client_id = await page.evaluate('''() => {
            const iframe = document.querySelector('iframe[src*="google.com"]');
            if (iframe) {
                const src = iframe.src;
                const match = src.match(/client_id=([^&]+)/);
                return match ? match[1] : null;
            }
            return null;
        }''')
        print(f"2. Client ID: {client_id}")

        # 用GIS API触发登录
        print("3. 调用Google Identity Services...")
        await page.evaluate('''() => {
            const iframe = document.querySelector('iframe[src*="google.com"]');
            const src = iframe.src;
            const clientIdMatch = src.match(/client_id=([^&]+)/);
            const clientId = clientIdMatch ? clientIdMatch[1] : '';
            
            // 初始化GIS
            google.accounts.id.initialize({
                client_id: clientId,
                callback: (response) => {
                    console.log('GIS callback:', JSON.stringify(response));
                    window._gis_response = response;
                }
            });
            
            // 尝试render按钮并点击
            const container = document.createElement('div');
            container.id = 'gis-button-container';
            document.body.appendChild(container);
            
            google.accounts.id.renderButton(
                document.getElementById('gis-button-container'),
                { theme: 'outline', size: 'large', shape: 'square' }
            );
            
            // 自动点击render出来的按钮
            setTimeout(() => {
                const btn = document.querySelector('#gis-button-container button');
                if (btn) {
                    console.log('点击GIS按钮');
                    btn.click();
                } else {
                    console.log('未找到GIS按钮');
                }
            }, 1000);
        }''')

        print("   API调用完成")
        await asyncio.sleep(5)
        await page.screenshot(path="/home/kevin/v21_s2.png")
        print(f"4. 当前URL: {page.url}")

        # 检查GIS回调结果
        gis_resp = await page.evaluate('window._gis_response || null')
        if gis_resp:
            print(f"5. GIS响应: {str(gis_resp)[:100]}")
        else:
            print("5. 无GIS响应")

        # 检查是否有弹窗
        if len(context.pages) > 1:
            print(f"6. 弹窗数量: {len(context.pages)-1}")
            for i, pop in enumerate(context.pages[1:], 1):
                print(f"   弹窗{i}: {pop.url}")

        print(f"7. 最终URL: {page.url}")
        await page.screenshot(path="/home/kevin/v21_s3.png")

        await browser.close()
        print("完成!")

asyncio.run(main())
