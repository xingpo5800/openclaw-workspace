const { chromium, Stealth } = require('playwright');

(async () => {
    const EMAIL = "zhengyi5800@gmail.com";
    const PASSWORD = "Xingpo888***";

    console.log("1. 启动Chromium (非headless模式)...");
    const browser = await chromium.launch({
        headless: false,  // 真实浏览器!
        args: ["--no-sandbox"]
    });

    const context = await browser.newContext({
        viewport: { width: 1280, height: 800 },
        userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    });
    const page = await context.newPage();
    page.setDefaultTimeout(20000);

    console.log("2. 打开PixVerse登录页...");
    await page.goto("https://app.pixverse.ai/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(5000);
    console.log("   URL:", page.url());
    await page.screenshot({ path: "/tmp/pix_mac1.png", fullPage: false });

    // 获取client_id
    const clientId = await page.evaluate(() => {
        const iframe = document.querySelector('iframe[src*="google.com"]');
        if (!iframe) return null;
        const match = iframe.src.match(/client_id=([^&]+)/);
        return match ? match[1] : null;
    });
    console.log("3. Client ID:", clientId);

    if (clientId) {
        // GIS prompt
        await page.evaluate((cid) => {
            google.accounts.id.initialize({
                client_id: cid,
                auto_select: false,
                callback: (resp) => {
                    window._gis_cb = resp;
                    console.log("GIS callback!", JSON.stringify(resp).slice(0, 100));
                }
            });
            // 尝试prompt
            google.accounts.id.prompt(notification => {
                console.log("prompt通知:", notification);
            });
            // render按钮
            const container = document.createElement("div");
            container.id = "gis-btn";
            container.style.position = "fixed";
            container.style.top = "200px";
            container.style.left = "100px";
            container.style.zIndex = "99999";
            document.body.appendChild(container);
            google.accounts.id.renderButton(
                document.getElementById("gis-btn"),
                { theme: "outline", size: "large" }
            );
        }, clientId);

        await page.waitForTimeout(3000);
        await page.screenshot({ path: "/tmp/pix_mac2.png", fullPage: false });
        console.log("4. 等待用户操作...");

        // 等待登录完成或弹窗
        try {
            await page.waitForFunction(
                () => window._gis_cb || (window.location.href && !window.location.href.includes("login")),
                { timeout: 60000 }
            );
            console.log("5. 登录触发!");
        } catch (e) {
            console.log("5. 等待超时，URL:", page.url());
        }

        await page.screenshot({ path: "/tmp/pix_mac3.png", fullPage: false });

        const gisCb = await page.evaluate("window._gis_cb || null");
        if (gisCb) {
            console.log("6. GIS回调:", gisCb);
        }

        // 保存状态
        await context.storageState({ path: "/tmp/pixverse_state.json" });
        console.log("7. 状态已保存到 /tmp/pixverse_state.json");
    }

    console.log("最终URL:", page.url());
    console.log("页面数:", (await context.pages()).length);

    await browser.close();
    console.log("完成!");
})();
