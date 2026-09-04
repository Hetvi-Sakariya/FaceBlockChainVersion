from playwright.sync_api import sync_playwright
import cv2
import requests
import os
import hashlib
from urllib.parse import urlparse

# ==========================================
# SETTINGS
# ==========================================

INPUT_IMAGE = r"samples\test.jpg.jpg"
THRESHOLD = 0.363

os.makedirs("web_candidates", exist_ok=True)


# ==========================================
# LOAD FACE MODELS
# ==========================================

detector = cv2.FaceDetectorYN.create(
    "models/face_detection_yunet_2023mar.onnx",
    "",
    (320, 320)
)

recognizer = cv2.FaceRecognizerSF.create(
    "models/face_recognition_sface_2021dec.onnx",
    ""
)


# ==========================================
# GET FACE FEATURE FROM IMAGE
# ==========================================

def get_face_feature(image):

    if image is None:
        return None

    detector.setInputSize(
        (image.shape[1], image.shape[0])
    )

    _, faces = detector.detect(image)

    if faces is None or len(faces) == 0:
        return None

    # Use the largest detected face
    face = max(
        faces,
        key=lambda f: f[2] * f[3]
    )

    aligned = recognizer.alignCrop(
        image,
        face
    )

    feature = recognizer.feature(aligned)

    return feature


# ==========================================
# LOAD ORIGINAL IMAGE
# ==========================================

print("📷 Loading original image...")

original = cv2.imread(INPUT_IMAGE)

if original is None:
    print("❌ Could not load input image")
    exit()

original_feature = get_face_feature(original)

if original_feature is None:
    print("❌ No face detected in input image")
    exit()

print("✅ Face detected in input image")


# ==========================================
# GOOGLE LENS SEARCH
# ==========================================

print("\n🌐 Opening Google Lens...")

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    page.goto("https://lens.google.com/")
    page.wait_for_timeout(3000)

    uploader = page.locator(
        'input[name="encoded_image"]'
    )

    print("📤 Uploading ORIGINAL image...")

    uploader.set_input_files(
        INPUT_IMAGE
    )

    print("⏳ Waiting for search results...")

    page.wait_for_timeout(12000)

    print("✅ Lens search completed")
    print("Search URL:")
    print(page.url)

    # ======================================
    # COLLECT IMAGE URLs
    # ======================================

    image_urls = []

    images = page.locator("img")

    print("\n🔎 Collecting candidate images...")

    for i in range(images.count()):

        try:

            img = images.nth(i)

            src = img.get_attribute("src")

            if src and src.startswith("http"):

                if src not in image_urls:
                    image_urls.append(src)

        except:
            pass

    print(
        "Candidate images found:",
        len(image_urls)
    )

    # ======================================
    # COLLECT PAGE LINKS
    # ======================================

    links = []

    anchors = page.locator("a")

    for i in range(anchors.count()):

        try:

            a = anchors.nth(i)

            href = a.get_attribute("href")

            if href and href.startswith("http"):

                if href not in links:
                    links.append(href)

        except:
            pass

    print(
        "Candidate webpages found:",
        len(links)
    )

    input(
        "\nPress ENTER after you have seen the Lens results..."
    )

    browser.close()


# ==========================================
# DOWNLOAD CANDIDATE IMAGES
# ==========================================

print("\n⬇️ Downloading candidate images...")

downloaded = []

for number, url in enumerate(
    image_urls[:30],
    1
):

    try:

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        if response.status_code != 200:
            continue

        filename = (
            f"web_candidates/"
            f"candidate_{number}.jpg"
        )

        with open(filename, "wb") as f:
            f.write(response.content)

        downloaded.append(
            (filename, url)
        )

    except Exception:
        continue


print(
    "Downloaded:",
    len(downloaded)
)


# ==========================================
# FACE VERIFICATION
# ==========================================

print("\n🧠 Verifying candidate faces...")
print("=" * 60)

matches = []

for filename, source_url in downloaded:

    candidate = cv2.imread(filename)

    if candidate is None:
        continue

    candidate_feature = get_face_feature(
        candidate
    )

    if candidate_feature is None:
        continue

    score = recognizer.match(
        original_feature,
        candidate_feature,
        cv2.FaceRecognizerSF_FR_COSINE
    )

    print(
        f"{filename} → similarity: "
        f"{score:.4f}"
    )

    if score >= THRESHOLD:

        print("   ✅ FACE MATCH")

        matches.append({
            "image": filename,
            "source": source_url,
            "score": float(score)
        })

    else:

        print("   ❌ Not the same face")


# ==========================================
# FINAL RESULT
# ==========================================

print("\n")
print("=" * 60)

if matches:

    print("🎯 VERIFIED WEB FACE MATCHES")
    print("=" * 60)

    for match in matches:

        print("\nImage:")
        print(match["image"])

        print("Source:")
        print(match["source"])

        print(
            "Similarity:",
            round(match["score"], 4)
        )

else:

    print(
        "❌ NO VERIFIED PUBLIC WEB MATCH FOUND"
    )

print("=" * 60)