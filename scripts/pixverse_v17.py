#!/usr/bin/env python3
"""PixVerse 登录 - v17 调查按钮结构"""
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
        await asyncio.sleep(3)

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
        
        # 等待页面稳定
        await asyncio.sleep(5)
        
        # 截图
        await page.screenshot(path="/home/kevin/v17_s1.png")

        # 调查所有包含Google的元素
        result = await page.evaluate("""() => {
            const allElements = [];
            
            // 查找所有可能包含Google的元素
            const selectors = ['button', 'a', 'div', 'span', 'input'];
            selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    const text = el.innerText?.trim() || '';
                    const aria = el.getAttribute('aria-label') || '';
                    const title = el.getAttribute('title') || '';
                    const className = el.className || '';
                    const role = el.getAttribute('role') || '';
                    const href = el.getAttribute('href') || '';
                    
                    if (text.toLowerCase().includes('google') || aria.toLowerCase().includes('google') || title.toLowerCase().includes('google')) {
                        allElements.push({
                            tag: selector,
                            text: text,
                            aria: aria,
                            title: title,
                            class: className,
                            role: role,
                            href: href,
                            tagName: el.tagName,
                            outerHTML: el.outerHTML.slice(0, 200)
                        });
                    }
                });
            });
            
            return JSON.stringify(allElements);
        }""")

        print("3. Google相关元素:")
        elements = json.loads(result)
        for i, el in enumerate(elements):
            print(f"  元素 {i+1}:")
            print(f"    标签: {el['tag']}")
            print(f"    标签名: {el['tagName']}")
            print(f"    文本: '{el['text']}'")
            print(f"    aria: '{el['aria']}'")
            print(f"    class: '{el['class']}'")
            print(f"    role: '{el['role']}'")
            print(f"    href: '{el['href']}'")

        # 如果找到了Google元素，尝试点击
        if elements:
            print(f"4. 找到 {len(elements)} 个Google相关元素，尝试点击第一个...")
            await page.evaluate("""() => {
                const selectors = ['button', 'a', 'div', 'span'];
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        const text = el.innerText?.trim() || '';
                        if (text.toLowerCase().includes('google')) {
                            el.click();
                            return;
                        }
                    });
                });
            }""")
            print("   点击完成")
        else:
            print("4. 没找到Google元素")

        await asyncio.sleep(5)

        await page.screenshot(path="/home/kevin/v17_s2.png")
        print(f"5. 点击后URL: {page.url}")

        await browser.close()
        print("完成!")

asyncio.run(main())