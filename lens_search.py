from playwright.sync_api import sync_playwright

IMAGE_PATH = "search_images/face_search.jpg"

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    print("🌐 Opening Google Lens...")
    page.goto("https://lens.google.com/")
    page.wait_for_timeout(3000)

    inputs = page.locator('input[type="file"]')

    print("📤 Uploading face crop...")
    inputs.nth(0).set_input_files(IMAGE_PATH)

    page.wait_for_timeout(10000)

    print("✅ Search completed")
    print("URL:")
    print(page.url)

    # Get links from the results page
    links = page.locator("a").all()

    print("\n🔎 Search results:\n")

    count = 0

    for link in links:
        try:
            text = link.inner_text().strip()
            href = link.get_attribute("href")

            if text and href and href.startswith("http"):
                print(f"{count + 1}. {text[:100]}")
                print(f"   {href}\n")
                count += 1

            if count >= 10:
                break

        except:
            pass

    input("Press Enter to close the browser...")

    browser.close()