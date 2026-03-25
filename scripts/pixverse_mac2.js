const { chromium } = require('playwright');

(async () => {
    const EMAIL = "zhengyi5800@gmail.com";
    const PASSWORD = "Xingpo888***";

    console.log("1. 启动Chromium...");
    const browser = await chromium.launch({
        headless: false,
        args: ["--no-sandbox"]
    });

    const context = await browser.newContext({
        viewport: { width: 1280, height: 800 }
    });
    const page = await context.newPage();
    page.setDefaultTimeout(20000);

    console.log("2. 打开PixVerse登录页...");
    await page.goto("https://app.pixverse.ai/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    console.log("   URL:", page.url());
    await page.screenshot({ path: "/tmp/pix_m2_1.png" });

    // 方法1: 尝试点One Tap (FedCM)按钮
    console.log("3. 尝试点One Tap FedCM按钮...");
    try {
        // 找中文的Google登录按钮
        const oneTap = page.locator('text=使用 Google 账号登录').first();
        if (await oneTap.count() > 0) {
            await oneTap.click({ timeout: 3000 });
            console.log("   点击One Tap成功!");
        } else {
            console.log("   未找到One Tap按钮，尝试其他...");
        }
    } catch(e) {
        console.log("   One Tap点击失败:", e.message.slice(0, 100));
    }

    await page.waitForTimeout(5000);
    await page.screenshot({ path: "/tmp/pix_m2_2.png" });
    console.log("4. URL:", page.url());

    // 方法2: 点"Sign in with Google"大按钮
    if (page.url().includes("login")) {
        console.log("5. 尝试点Sign in with Google...");
        try {
            await page.locator('button:has-text("Sign in with Google")').first().click({ timeout: 5000 });
            console.log("   点击成功!");
        } catch(e) {
            console.log("   点击失败:", e.message.slice(0, 100));
        }
        await page.waitForTimeout(8000);
        await page.screenshot({ path: "/tmp/pix_m2_3.png" });
        console.log("6. URL:", page.url());
    }

    // 检查是否跳转到Google
    if (page.url().includes("google") || page.url().includes("accounts.google")) {
        console.log("7. 在Google页，输入邮箱...");
        await page.locator('input[type="email"], input[name="identifier"]').first().fill(EMAIL);
        await page.keyboard.press("Enter");
        await page.waitForTimeout(3000);
        await page.locator('input[type="password"], input[name="password"]').first().fill(PASSWORD);
        await page.keyboard.press("Enter");
        await page.waitForTimeout(5000);
        console.log("   登录后URL:", page.url());
    }

    // 检查页面数
    const pages = context.pages();
    console.log("8. 页面数:", pages.length);
    for (let i = 0; i < pages.length; i++) {
        console.log("   [" + i + "]", pages[i].url().slice(0, 80));
    }

    await page.screenshot({ path: "/tmp/pix_m2_4.png" });

    // 保存状态
    await context.storageState({ path: "/tmp/pixverse_auth.json" });
    console.log("9. 状态已保存!");

    console.log("最终URL:", page.url());

    // 等待用户按回车
    console.log("\n按回车键关闭浏览器...");
    await new Promise(r => process.stdin.once('data', r));

    await browser.close();
    console.log("完成!");
})();
