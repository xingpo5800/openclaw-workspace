#!/usr/bin/env python3
"""PixVerse 登录 - v27 GIS renderButton并点击"""
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

        print("1. 打开登录页...")
        await page.goto("https://app.pixverse.ai/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"   URL: {page.url}")

        await page.screenshot(path="/home/kevin/v27_s1.png")

        # 获取client_id
        client_id = await page.evaluate("""() => {
            const iframe = document.querySelector('iframe[src*="google.com"]');
            if (!iframe) return null;
            const match = iframe.src.match(/client_id=([^&]+)/);
            return match ? match[1] : null;
        }""")
        print(f"2. Client ID: {client_id}")

        if client_id:
            # 用GIS renderButton在页面中创建一个按钮
            print("3. 用GIS renderButton...")
            await page.evaluate(f"""() => {{
                // 创建容器
                const container = document.createElement('div');
                container.id = 'gis-override';
                container.style.position = 'fixed';
                container.style.top = '0';
                container.style.left = '0';
                container.style.zIndex = '99999';
                document.body.appendChild(container);

                // 初始化GIS
                google.accounts.id.initialize({{
                    client_id: '{client_id}',
                    auto_select: false,
                    callback: (resp) => {{
                        window._gis_cb = resp;
                        console.log('GIS callback!', JSON.stringify(resp).slice(0, 100));
                    }}
                }});

                // render一个按钮
                google.accounts.id.renderButton(
                    document.getElementById('gis-override'),
                    {{
                        theme: 'outline',
                        size: 'large',
                        shape: 'rectangular',
                        text: 'signin_with',
                        width: 300
                    }}
                );
                console.log('renderButton完成');
            }}""")
            await asyncio.sleep(2)

            # 截图看render出来的按钮
            await page.screenshot(path="/home/kevin/v27_s2.png")
            print("4. 按钮已渲染，尝试点击...")

            # 点击render出来的按钮
            clicked = await page.evaluate("""() => {
                const btn = document.querySelector('#gis-override button');
                if (btn) {
                    console.log('找到GIS按钮，准备点击');
                    btn.click();
                    return 'clicked';
                }
                // 尝试任意#gis-override内的可点击元素
                const anyBtn = document.querySelector('#gis-override [role="button"], #gis-override a, #gis-override iframe');
                if (anyBtn) {
                    console.log('找到元素:', anyBtn.tagName, anyBtn.className);
                    anyBtn.click();
                    return 'clicked alt: ' + anyBtn.tagName;
                }
                return 'not found';
            }""")
            print(f"   {clicked}")

            await asyncio.sleep(5)
            await page.screenshot(path="/home/kevin/v27_s3.png")

            # 检查GIS回调
            gis_cb = await page.evaluate("window._gis_cb || null")
            if gis_cb:
                print(f"5. GIS回调成功!: {str(gis_cb)[:100]}")
            else:
                print("5. 无GIS回调")

            # 检查是否有新页面/弹窗
            print(f"6. 页面数: {len(context.pages)}")
            for i, pg in enumerate(context.pages):
                print(f"   [{i}] {pg.url[:80]}")

        print(f"7. 最终URL: {page.url}")
        await browser.close()
        print("完成!")

asyncio.run(main())
