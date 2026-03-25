#!/usr/bin/env python3
"""
PixVerse 视频生成自动化脚本
运行在 VPS 上，登录账号并生成视频
"""
import asyncio
import os
import sys
from playwright.async_api import async_playwright

EMAIL = os.environ.get("PIXVERSE_EMAIL", "")
PASSWORD = os.environ.get("PIXVERSE_PASSWORD", "")
PROMPT = sys.argv[1] if len(sys.argv) > 1 else "A cat playing guitar in a cyberpunk city"
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/home/kevin/videos")
TIMEOUT = 60000  # 60s

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"🎬 启动 PixVerse 自动化")
    print(f"  账号: {EMAIL}")
    print(f"  提示词: {PROMPT}")

    async with async_playwright() as p:
        # 启动无头浏览器
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        )

        page = await context.new_page()
        page.set_default_timeout(TIMEOUT)

        try:
            # 1. 打开 PixVerse
            print("🌐 打开 PixVerse...")
            await page.goto("https://app.pixverse.ai", wait_until="networkidle")
            await asyncio.sleep(2)

            # 2. 检查是否已登录
            current_url = page.url
            print(f"当前URL: {current_url}")

            if "login" in current_url.lower() or "sign" in current_url.lower():
                print("需要登录...")
                # 点击登录按钮
                login_btn = page.locator('button:has-text("Log in"), button:has-text("Sign in"), a:has-text("Log in")').first
                await login_btn.click()
                await asyncio.sleep(2)

                # 输入邮箱
                email_input = page.locator('input[type="email"], input[placeholder*="email"], input[placeholder*="Email"]').first
                await email_input.fill(EMAIL)
                await asyncio.sleep(1)

                # 输入密码
                pw_input = page.locator('input[type="password"]').first
                await pw_input.fill(PASSWORD)
                await asyncio.sleep(1)

                # 点击登录
                submit_btn = page.locator('button[type="submit"], button:has-text("Log in"), button:has-text("Sign in")').first
                await submit_btn.click()
                await asyncio.sleep(5)

                print(f"登录后URL: {page.url}")
            else:
                print("已登录")

            # 3. 找到 "Create" 按钮并点击
            print("📝 进入创建页面...")
            create_btn = page.locator('a:has-text("Create"), button:has-text("Create"), a:has-text("创建")').first
            await create_btn.click()
            await asyncio.sleep(3)

            # 4. 找到文本输入框
            print("✍️ 输入提示词...")
            prompt_input = page.locator(
                'textarea[placeholder*="prompt"], textarea[placeholder*="Prompt"], '
                'input[placeholder*="prompt"], input[placeholder*="Prompt"], '
                '[contenteditable="true"]'
            ).first
            await prompt_input.fill(PROMPT)
            await asyncio.sleep(1)

            # 5. 点击生成按钮
            print("🚀 点击生成...")
            generate_btn = page.locator(
                'button:has-text("Generate"), button:has-text("Create Video"), '
                'button:has-text("生成"), button:has-text("Create")'
            ).first
            await generate_btn.click()

            # 6. 等待视频生成完成（轮询状态）
            print("⏳ 等待视频生成...")
            for i in range(60):  # 最多等10分钟
                await asyncio.sleep(10)
                
                # 检查是否有进度条或完成提示
                try:
                    status_text = await page.locator("text=Processing,text=Generating,text=Complete,text=Ready").first.text_content(timeout=3000)
                    print(f"  状态 [{i*10}s]: {status_text}")
                except:
                    print(f"  等待中... [{i*10}s]")
                
                # 检查是否有下载链接
                try:
                    video_preview = await page.locator("video").first
                    if video_preview:
                        print("✅ 视频生成完成!")
                        break
                except:
                    pass

            # 7. 保存页面截图
            screenshot_path = os.path.join(OUTPUT_DIR, "result.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 截图已保存: {screenshot_path}")

        except Exception as e:
            print(f"❌ 错误: {e}")
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "error.png"), full_page=True)
            raise

        finally:
            await browser.close()

    print("✅ 完成!")
    return True

if __name__ == "__main__":
    asyncio.run(main())
