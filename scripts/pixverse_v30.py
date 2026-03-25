#!/usr/bin/env python3
"""PixVerse 登录 - v30 拦截OAuth URL"""
import asyncio
import json
from urllib.parse import parse_qs, urlparse
from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth

EMAIL = "zhengyi5800@gmail.com"
PASSWORD = "Xingpo888***"

async def main():
    captured_urls = []
    oauth_url = None

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        page.set_default_timeout(15000)

        async def on_request(request):
            url = request.url
            # 捕获Google OAuth相关请求
            if any(k in url for k in [
                'accounts.google.com/v2/signin',
                'accounts.google.com/o/oauth2',
                'accounts.google.com/ServiceLogin',
                'accounts.google.com/fedservlet',
                'oauth2/authentication',
                'oauth2/v4',
            ]):
                captured_urls.append(url)
                print(f"  [OAuth请求] {url[:150]}")

            # FedCM
            if 'fedcm' in url and 'accounts.google' in url:
                captured_urls.append(url)
                print(f"  [FedCM请求] {url[:150]}")

        page.on("request", on_request)

        # 同时监听iframe的src变化
        async def on_navigation(frame):
            if frame:
                url = frame.url
                if 'google' in url or 'oauth' in url or 'signin' in url:
                    print(f"  [Frame导航] {url[:150]}")

        page.on("frame", on_navigation)

        print("1. 打开登录页...")
        await page.goto("https://app.pixverse.ai/login", wait_until="domcontentloaded")
        await asyncio.sleep(5)

        # 检查原始iframe的src
        iframe_src = await page.evaluate("""() => {
            const iframe = document.querySelector('iframe[src*="google.com"]');
            return iframe ? iframe.src : null;
        }""")
        print(f"2. Google iframe src: {iframe_src[:100] if iframe_src else None}")

        # 尝试用JS模拟完整的GIS点击流程
        print("3. 尝试触发GIS点击...")
        result = await page.evaluate("""() => {
            const result = { clicked: false, error: null };

            // 找到原始GIS iframe
            const iframe = document.querySelector('iframe[src*="gsi/button"]');
            if (!iframe) {
                result.error = 'no iframe';
                return result;
            }

            // 创建并发送点击事件到iframe
            try {
                // 方法1: dispatchEvent on iframe
                const event = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: iframe.getBoundingClientRect().left + 150,
                    clientY: iframe.getBoundingClientRect().top + 30
                });
                iframe.dispatchEvent(event);
                result.clicked = true;
                result.method = 'dispatchEvent';
            } catch(e) {
                result.error = e.message;
            }

            // 方法2: 使用navigator.credentials (FedCM)
            try {
                if (navigator.credentials && navigator.credentials.get) {
                    // 触发FedCM
                    const fedcmPromise = navigator.credentials.get({
                        identity: {
                            context: 'signin',
                            providers: [{
                                configURL: 'https://accounts.google.com/fedcm',
                                clientId: '542002026763-i3nrvvli4nkk37m8kmrh1fefgumtq62e.apps.googleusercontent.com',
                                mode: 'active',
                                nonce: Math.random().toString(36)
                            }]
                        }
                    });
                    result.fedcm = 'triggered';
                }
            } catch(e) {
                result.fedcm_error = e.message;
            }

            return result;
        }""")
        print(f"4. 点击结果: {json.dumps(result)}")

        await asyncio.sleep(10)
        await page.screenshot(path="/home/kevin/v30_s1.png")

        print(f"5. 捕获的URL数: {len(captured_urls)}")
        for i, url in enumerate(captured_urls[:10]):
            print(f"   [{i}] {url[:120]}")

        # 尝试从iframe URL中提取OAuth参数并手动构建URL
        if iframe_src:
            parsed = urlparse(iframe_src)
            params = parse_qs(parsed.query)
            print(f"6. iframe参数: {json.dumps({k:v[0] if len(v)==1 else v for k,v in params.items()})}")

        print(f"7. 最终URL: {page.url}, 页面数: {len(context.pages)}")

        await browser.close()
        print("完成!")

asyncio.run(main())
