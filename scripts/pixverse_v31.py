#!/usr/bin/env python3
"""PixVerse 登录 - v31 监听OAuth弹窗"""
import asyncio
from playwright.async_api import async_playwright

EMAIL = "zhengyi5800@gmail.com"
PASSWORD = "Xingpo888***"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--enable-features=FedCm,FedCmMixedApi,WebIdentityDigitalCredentials",
            ]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        page.set_default_timeout(15000)

        # 监听弹窗
        popup_info = {}
        async def handle_popup(popup):
            popup_info["opened"] = True
            popup_info["url"] = popup.url
            popup_info["page"] = popup
            print(f"   弹窗打开: {popup.url[:80]}")

            # 在弹窗中等待Google登录表单
            try:
                await popup.wait_for_load_state("domcontentloaded", timeout=10000)
                await asyncio.sleep(3)

                if "accounts.google.com" in popup.url:
                    print("   在Google登录页...")
                    await popup.screenshot(path="/home/kevin/popup_google.png")

                    # 输入邮箱
                    try:
                        await popup.locator('input[type="email"], input[name="identifier"]').first.fill(EMAIL)
                        await popup.keyboard.press("Enter")
                        print("   邮箱已输入")
                        await asyncio.sleep(3)
                    except Exception as e:
                        print(f"   邮箱输入失败: {e}")

                    # 输入密码
                    try:
                        await popup.locator('input[type="password"], input[name="password"]').first.fill(PASSWORD)
                        await popup.keyboard.press("Enter")
                        print("   密码已输入")
                        await asyncio.sleep(5)
                    except Exception as e:
                        print(f"   密码输入失败: {e}")

                    print(f"   最终弹窗URL: {popup.url}")
                    await popup.screenshot(path="/home/kevin/popup_final.png")
            except Exception as e:
                print(f"   弹窗处理错误: {e}")

        context.on("page", handle_popup)

        print("1. 打开登录页...")
        await page.goto("https://app.pixverse.ai/login", wait_until="domcontentloaded")
        await asyncio.sleep(8)
        print(f"   URL: {page.url}")
        await page.screenshot(path="/home/kevin/v31_s1.png")

        # 等FedCM失败（NetworkError）后再尝试按钮点击
        await asyncio.sleep(5)

        print("2. 点击Google iframe...")
        # 点击iframe元素（让事件传播到Google按钮）
        clicked = await page.evaluate("""() => {
            const iframe = document.querySelector('iframe[src*="google.com"]');
            if (!iframe) return 'no iframe';
            const parent = iframe.parentElement;
            if (!parent) return 'no parent';

            // 尝试多个父容器
            let el = parent;
            for (let i = 0; i < 5; i++) {
                if (!el || el === document.body) break;
                // 点击元素中心
                const rect = el.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;

                const event = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: x,
                    clientY: y
                });
                el.dispatchEvent(event);
                el = el.parentElement;
            }
            return 'clicked: ' + parent.className;
        }""")
        print(f"   {clicked}")

        # 等待弹窗
        print("3. 等待弹窗...")
        await asyncio.sleep(10)

        await page.screenshot(path="/home/kevin/v31_s2.png")
        print(f"4. 最终URL: {page.url}")
        print(f"5. 弹窗状态: {popup_info.get('opened', False)}")

        # 检查所有页面
        pages = context.pages
        print(f"6. 页面数: {len(pages)}")
        for i, pg in enumerate(pages):
            print(f"   [{i}] {pg.url[:80]}")

        await browser.close()
        print("完成!")

asyncio.run(main())
