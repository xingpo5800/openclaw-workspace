#!/usr/bin/env python3
"""PixVerse 登录 - v29 启用FedCM"""
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth

EMAIL = "zhengyi5800@gmail.com"
PASSWORD = "Xingpo888***"

async def main():
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--enable-features=FedCm,FedCmMaxAge,FedCmButton,OneEaFedCm",
                "--disable-features=IpProtection",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            # 接受第三方cookie以便Google OAuth
            accept_downloads=True,
        )
        page = await context.new_page()
        page.set_default_timeout(20000)

        print("1. 打开登录页 (FedCM模式)...")
        await page.goto("https://app.pixverse.ai/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"   URL: {page.url}")
        await page.screenshot(path="/home/kevin/v29_s1.png")

        client_id = await page.evaluate("""() => {
            const iframe = document.querySelector('iframe[src*="google.com"]');
            if (!iframe) return null;
            const match = iframe.src.match(/client_id=([^&]+)/);
            return match ? match[1] : null;
        }""")
        print(f"2. Client ID: {client_id}")

        if client_id:
            # 初始化GIS并尝试FedCM
            print("3. 调用GIS FedCM...")
            await page.evaluate(f"""() => {{
                google.accounts.id.initialize({{
                    client_id: '{client_id}',
                    auto_select: false,
                    callback: (resp) => {{
                        window._gis_cb = resp;
                        console.log('GIS callback:', JSON.stringify(resp).slice(0,100));
                    }}
                }});

                // 尝试FedCM方式
                if (navigator.credentials && navigator.credentials.get) {{
                    console.log('FedCM可用');
                }}

                // render按钮
                const container = document.createElement('div');
                container.id = 'gis-btn';
                document.body.appendChild(container);
                google.accounts.id.renderButton(
                    document.getElementById('gis-btn'),
                    {{ theme: 'outline', size: 'large' }}
                );
            }}""")

            await asyncio.sleep(3)
            await page.screenshot(path="/home/kevin/v29_s2.png")

            # 点击GIS iframe
            print("4. 点击GIS iframe...")
            await page.evaluate("""() => {
                // 找到原始的Google iframe并点击
                const iframes = document.querySelectorAll('iframe');
                for (const iframe of iframes) {
                    const src = iframe.src || '';
                    if (src.includes('google.com') && src.includes('gsi/button')) {
                        console.log('点击Google iframe:', iframe.className || iframe.id);
                        // 尝试多种点击方式
                        iframe.click();
                        // 尝试直接调用contentWindow
                        try {
                            const cw = iframe.contentWindow;
                            if (cw) {
                                const btn = cw.document.querySelector('button');
                                if (btn) {
                                    btn.click();
                                    console.log('通过contentWindow点击了按钮');
                                }
                            }
                        } catch(e) {{
                            console.log('contentWindow错误:', e.message);
                        }}
                        break;
                    }
                }
            }""")

            await asyncio.sleep(8)
            await page.screenshot(path="/home/kevin/v29_s3.png")

            gis_cb = await page.evaluate("window._gis_cb || null")
            if gis_cb:
                print(f"5. GIS回调: {str(gis_cb)[:100]}")
            else:
                print("5. 无GIS回调")

        print(f"6. 最终URL: {page.url}")
        print(f"   页面数: {len(context.pages)}")
        for i, pg in enumerate(context.pages):
            print(f"   [{i}] {pg.url[:80]}")

        await context.storage_state(path="/home/kevin/pixverse_state.json")
        print("状态已保存")
        await browser.close()
        print("完成!")

asyncio.run(main())
