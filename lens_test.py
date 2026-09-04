from playwright.sync_api import sync_playwright

IMAGE_PATH = r"search_images\face_search.jpg"

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False,
        channel="chrome"
    )

    page = browser.new_page()

    print("🌐 Opening Google Lens...")
    page.goto("https://lens.google.com/", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    print("📤 Looking for upload button...")

    # Click the visible "upload a file" control
    upload_text = page.get_by_text("upload a file", exact=False)

    print("Upload controls found:", upload_text.count())

    if upload_text.count() == 0:
        print("❌ Upload button not found.")
        input("Press ENTER to close...")
        browser.close()
        raise SystemExit

    with page.expect_file_chooser(timeout=15000) as chooser_info:
        upload_text.first.click()

    chooser = chooser_info.value
    chooser.set_files(IMAGE_PATH)

    print("✅ Original image uploaded")
    print("⏳ Waiting for Lens results...")

    page.wait_for_timeout(15000)

    print("\n========== RESULT ==========")
    print("URL:", page.url)
    print("TITLE:", page.title())

    print("\nImages:", page.locator("img").count())
    print("Links:", page.locator("a").count())

    print("\nPage text:")
    print(page.locator("body").inner_text()[:5000])

    input("\nPress ENTER to close...")
    browser.close()