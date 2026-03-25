#!/usr/bin/env python3
"""PixVerse 登录 - v28 监听OAuth请求"""
import asyncio
import json
from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth

async def main():
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        page.set_default_timeout(15000)

        oauth_requests = []
        popup_opened = None

        # 监听所有请求，找OAuth相关
        async def on_request(request):
            url = request.url
            if any(k in url.lower() for k in ['oauth', 'googleapis', 'accounts.google', 'consent', 'signin']):
                oauth_requests.append({
                    'url': url[:200],
                    'method': request.method,
                    'post_data': str(request.post_data)[:200] if request.post_data else None
                })

        page.on("request", on_request)

        async def on_response(response):
            url = response.url
            if any(k in url.lower() for k in ['oauth', 'googleapis', 'accounts.google', 'consent', 'signin']):
                try:
                    body = await response.text()
                except:
                    body = ""
                oauth_requests.append({
                    'response': url[:200],
                    'status': response.status
                })

        page.on("response", on_response)

        print("1. 打开登录页...")
        await page.goto("https://app.pixverse.ai/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)

        client_id = await page.evaluate("""() => {
            const iframe = document.querySelector('iframe[src*="google.com"]');
            if (!iframe) return null;
            const match = iframe.src.match(/client_id=([^&]+)/);
            return match ? match[1] : null;
        }""")
        print(f"2. Client ID: {client_id}")

        if client_id:
            await page.evaluate(f"""() => {{
                const container = document.createElement('div');
                container.id = 'gis-override';
                document.body.appendChild(container);
                google.accounts.id.initialize({{
                    client_id: '{client_id}',
                    callback: (resp) => {{ window._gis_cb = resp; }}
                }});
                google.accounts.id.renderButton(
                    document.getElementById('gis-override'),
                    {{ theme: 'outline', size: 'large', text: 'signin_with' }}
                );
            }}""")
            await asyncio.sleep(2)
            print("3. GIS按钮已渲染")

            # 点击
            await page.evaluate("""() => {
                const iframe = document.querySelector('#gis-override iframe');
                if (iframe) {
                    console.log('点击GIS iframe');
                    iframe.contentWindow?.postMessage('click', '*');
                    iframe.click();
                }
            }""")
            print("4. 点击iframe")
            await asyncio.sleep(8)

            await page.screenshot(path="/home/kevin/v28_s1.png")

        print(f"5. OAuth相关请求数: {len(oauth_requests)}")
        for i, req in enumerate(oauth_requests[:20]):
            print(f"   [{i}] {json.dumps(req)[:200]}")

        print(f"6. 最终URL: {page.url}")
        print(f"   页面数: {len(context.pages)}")

        await browser.close()
        print("完成!")

asyncio.run(main())
