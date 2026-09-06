import asyncio, json, os
os.environ["LD_LIBRARY_PATH"] = "/home/user/deps/usr/lib/x86_64-linux-gnu"
os.environ["PATH"] = os.environ.get("PATH", "")
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8080"
errors = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("console", lambda m: errors.append(f"[console.{m.type}] {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"[pageerror] {e}"))

        await page.goto(BASE, wait_until="networkidle")
        title = await page.title()
        h1 = await page.inner_text("#hero-title")
        print("Title:", title)
        print("H1:", h1)

        # wait for results
        await page.wait_for_selector(".hotel-card", timeout=8000)
        n = await page.locator(".hotel-card").count()
        count_text = await page.inner_text("#results-count")
        print("Cards rendered:", n, "|", count_text)

        # screenshot home
        await page.screenshot(path="shot_home.png", full_page=True)

        # search for Jaipur
        await page.fill("#q", "Jaipur")
        await page.click(".btn-search")
        await page.wait_for_timeout(1200)
        n2 = await page.locator(".hotel-card").count()
        print("After search 'Jaipur':", n2, "cards")
        first_name = await page.locator(".hotel-card .card-title").first.inner_text()
        print("First result:", first_name)

        # toggle USD
        await page.click("#cur-usd")
        usd_price = await page.locator(".hotel-card .price").first.inner_text()
        print("USD price sample:", usd_price.strip())
        await page.click("#cur-inr")

        # open first hotel
        await page.locator('[data-view]').first.click()
        await page.wait_for_selector(".detail-hero", timeout=8000)
        dname = await page.inner_text(".detail-info h1")
        print("Opened hotel:", dname)
        # check rooms, menu, accessibility, nearby sections present
        for sel in ["#rooms-section", ".acc-table", ".menu-table", ".nearby-item"]:
            cnt = await page.locator(sel).count()
            print(f"  section {sel!r} present count={cnt}")

        # toggle accessibility filter chips shown? already on detail. go back
        await page.click(".back-link")
        await page.wait_for_timeout(600)

        # click View to open hotel and book
        await page.locator('[data-view]').first.click()
        await page.wait_for_selector(".detail-hero")
        # book the accessible room (first room)
        await page.locator('[data-bookroom]').first.click()
        await page.wait_for_selector("#booking-form", timeout=8000)
        print("Booking modal opened")
        await page.fill("#bk-name", "Test User")
        await page.fill("#bk-email", "test@example.com")
        await page.screenshot(path="shot_booking.png")
        await page.click("#booking-form button[type=submit]")
        await page.wait_for_selector(".confirm", timeout=8000)
        ref = await page.inner_text(".ref-code")
        print("Booking confirmed, ref:", ref)
        bp = await page.locator(".blueprint img").first.get_attribute("src")
        print("Blueprint URL:", bp)
        await page.screenshot(path="shot_confirmation.png")

        # mobile viewport check
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.goto(BASE, wait_until="networkidle")
        await page.wait_for_selector(".hotel-card", timeout=8000)
        menutoggle = await page.locator("#menu-toggle").is_visible()
        print("Mobile menu-toggle visible:", menutoggle)
        await page.click("#menu-toggle")
        mn = await page.locator(".mobile-nav").is_visible()
        print("Mobile nav visible after toggle:", mn)
        await page.screenshot(path="shot_mobile.png", full_page=True)

        await browser.close()

    print("\n=== CONSOLE/PAGE ERRORS ===")
    if errors:
        for e in errors:
            print(e)
    else:
        print("None 🎉")

asyncio.run(main())
