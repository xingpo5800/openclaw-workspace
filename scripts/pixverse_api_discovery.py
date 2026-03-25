#!/usr/bin/env python3
"""PixVerse API发现"""
from playwright.async_api import async_playwright
import asyncio

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
        page = await browser.new_page()
        
        requests = []
        def on_request(req):
            url = req.url
            if any(x in url for x in ["api", "auth", "user", "profile", "v1", "graphql", "PixVerse", "pixverse"]):
                requests.append(url)
        
        page.on("request", on_request)
        
        await page.goto("https://app.pixverse.ai", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        print("PixVerse相关请求:")
        seen = set()
        for url in requests:
            if url not in seen:
                seen.add(url)
                print(f"  {url[:120]}")
        
        await browser.close()

asyncio.run(main())
