from flask import Flask, request, render_template_string
import os
import cv2
import requests
import numpy as np
import hashlib
import json
from dotenv import load_dotenv
from web3 import Web3

# ============================================================
# CONFIG
# ============================================================

load_dotenv()

app = Flask(__name__)

OPENWEBNINJA_API_KEY = os.getenv("OPENWEBNINJA_API_KEY")
DEMO_SEARCH_URL = ""

THRESHOLD = 0.363

# Public image URL already tested successfully with OpenWebNinja.
# This is ONLY the demo search source.


BLOCKCHAIN_RPC = "http://127.0.0.1:8545"

CONTRACT_ADDRESS = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"

# ============================================================
# LOAD FACE MODELS
# ============================================================

detector = cv2.FaceDetectorYN.create(
    "models/face_detection_yunet_2023mar.onnx",
    "",
    (320, 320)
)

recognizer = cv2.FaceRecognizerSF.create(
    "models/face_recognition_sface_2021dec.onnx",
    ""
)

# ============================================================
# BLOCKCHAIN SETUP
# ============================================================

w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_RPC))

contract = None

if w3.is_connected():
    try:
        with open(
            "artifacts/contracts/FaceVerification.sol/FaceVerification.json",
            "r"
        ) as f:
            contract_data = json.load(f)

        contract = w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=contract_data["abi"]
        )

        print("⛓️ Blockchain connected")
        print("📜 Contract:", CONTRACT_ADDRESS)

    except Exception as e:
        print("⚠️ Blockchain contract loading failed:", e)

else:
    print("⚠️ Blockchain not connected")


# ============================================================
# FACE FUNCTIONS
# ============================================================

def get_face_feature(image):
    """
    Detect the first face and create an SFace feature.
    """

    if image is None:
        return None

    detector.setInputSize(
        (image.shape[1], image.shape[0])
    )

    _, faces = detector.detect(image)

    if faces is None or len(faces) == 0:
        return None

    face = recognizer.alignCrop(
        image,
        faces[0]
    )

    feature = recognizer.feature(face)

    return feature


def compare_features(reference_feature, candidate_image):
    """
    Compare reference face with candidate image.
    """

    candidate_feature = get_face_feature(candidate_image)

    if candidate_feature is None:
        return None

    score = recognizer.match(
        reference_feature,
        candidate_feature,
        cv2.FaceRecognizerSF_FR_COSINE
    )

    return float(score)


# ============================================================
# DOWNLOAD IMAGE
# ============================================================

def download_image(url):
    """
    Download an image from a public URL.
    """

    try:
        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        if response.status_code != 200:
            return None

        data = np.frombuffer(
            response.content,
            np.uint8
        )

        image = cv2.imdecode(
            data,
            cv2.IMREAD_COLOR
        )

        return image

    except Exception as e:
        print("⚠️ Image download error:", e)
        return None
def upload_to_img402(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            "https://img402.dev/api/free",
            files={"file": f},
            timeout=30
        )

    response.raise_for_status()

    return response.json()["url"]


# ============================================================
# REVERSE IMAGE SEARCH
# ============================================================

def reverse_image_search(image_url):
    """
    Search the public image URL using OpenWebNinja.
    """

    if not OPENWEBNINJA_API_KEY:
        print("❌ OPENWEBNINJA_API_KEY missing")
        return []

    try:

        response = requests.get(
            "https://api.openwebninja.com/reverse-image-search/reverse-image-search",
            params={
                "url": image_url
            },
            headers={
                "x-api-key": OPENWEBNINJA_API_KEY
            },
            timeout=40
        )

        print("🔎 OpenWebNinja status:", response.status_code)

        if response.status_code != 200:
            print("❌ Reverse search failed:")
            print(response.text[:500])
            return []

        data = response.json()
        print("🔎 API response type:", type(data))
        print("🔎 API response keys:", data.keys() if isinstance(data, dict) else "NOT DICT")
        print("🔎 DATA TYPE:", type(data.get("data")) if isinstance(data, dict) else "N/A")
        results = data.get("data", [])

        print("🔎 Reverse search results:", len(results))

        return results

    except Exception as e:

        print("❌ Reverse search error:", e)

        return []


# ============================================================
# HTML
# ============================================================

HTML = """

<!DOCTYPE html>

<html>

<head>

    <title>Face ID + Blockchain</title>

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <style>

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f6f8;
        }

        .container {
            width: 760px;
            max-width: 90%;
            margin: 60px auto;
            background: white;
            padding: 38px;
            border-radius: 18px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }

        h1 {
            text-align: center;
            margin-bottom: 8px;
        }

        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 35px;
        }

        label {
            display: block;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 8px;
        }

        input[type="file"],
        input[type="text"] {
            width: 100%;
            box-sizing: border-box;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 8px;
        }

        button {
            width: 100%;
            margin-top: 28px;
            padding: 16px;
            border: none;
            border-radius: 9px;
            background: #222;
            color: white;
            font-size: 17px;
            cursor: pointer;
        }

        button:hover {
            background: #444;
        }

        .result {
            margin-top: 30px;
            padding: 25px;
            border-radius: 12px;
            background: #f1f1f1;
        }

        .success {
            background: #e9f8ee;
        }

        .error {
            background: #fff0f0;
        }

        .info {
            background: #eef5ff;
        }

        code {
            word-break: break-all;
            font-size: 12px;
        }

        a {
            color: #1264a3;
        }

        .step {
            padding: 10px 0;
        }

    </style>

</head>

<body>

<div class="container">

    <h1>🔐 Face ID + Blockchain</h1>

    <div class="subtitle">
        Face identification, reverse-image search and blockchain verification
    </div>

    <form action="/verify"
          method="POST"
          enctype="multipart/form-data">

        <label>
            1️⃣ Upload Person's Photo
        </label>

        <input
            type="file"
            name="image1"
            accept="image/*"
            required
        >

       
        <button type="submit">
            🔎 Find Social Media & Verify
        </button>

    </form>


    {% if result %}

        <div class="result
            {% if result.success %}
                success
            {% else %}
                error
            {% endif %}
        ">

            <h2>{{ result.status }}</h2>

            {% if result.message %}
                <p>{{ result.message }}</p>
            {% endif %}


            {% if result.score is not none %}

                <div class="step">
                    <strong>👤 Face Similarity:</strong>
                    {{ result.score }}
                </div>

                <div class="step">
                    <strong>Threshold:</strong>
                    {{ result.threshold }}
                </div>

            {% endif %}


            {% if result.matched_title %}

                <div class="step">

                    <strong>🌐 Matched Web Result:</strong>

                    <br>

                    {{ result.matched_title }}

                </div>

            {% endif %}


            {% if result.matched_url %}

                <div class="step">

                    <strong>🔗 Source:</strong>

                    <br>

                    <a href="{{ result.matched_url }}"
                       target="_blank">

                        Open matched page

                    </a>

                </div>

            {% endif %}


            {% if result.face_hash %}

                <div class="step">

                    <strong>🔐 SHA-256 Fingerprint:</strong>

                    <br>

                    <code>
                        {{ result.face_hash }}
                    </code>

                </div>

            {% endif %}


            {% if result.transaction %}

                <div class="step">

                    <strong>⛓️ Blockchain Transaction:</strong>

                    <br>

                    <code>
                        {{ result.transaction }}
                    </code>

                </div>

            {% endif %}


            {% if result.blockchain %}

                <hr>

                <h3>
                    ✅ Blockchain Verification Successful
                </h3>

                <p>
                    The fingerprint stored on blockchain
                    matches the fingerprint generated
                    from the discovered result.
                </p>

                {% if result.timestamp %}

                    <p>
                        <strong>Blockchain Timestamp:</strong>
                        {{ result.timestamp }}
                    </p>

                {% endif %}

            {% endif %}

        </div>

    {% endif %}

</div>

</body>

</html>

"""


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template_string(
        HTML,
        result=None,
        demo_url=""
    )


# ============================================================
# VERIFY
# ============================================================

@app.route("/verify", methods=["POST"])
def verify():

    result = {
        "success": False,
        "status": "❌ Verification Failed",
        "message": "",
        "score": None,
        "threshold": THRESHOLD,
        "matched_title": None,
        "matched_url": None,
        "face_hash": None,
        "transaction": None,
        "blockchain": False,
        "timestamp": None
    }

   
 # --------------------------------------------------------
    # 1. GET UPLOADED PHOTO
    # --------------------------------------------------------

    uploaded = request.files.get("image1")

    if not uploaded:

        result["message"] = "Please upload a photo."

        return render_template_string(
            HTML,
            result=result,
            demo_url=""
        )

    # --------------------------------------------------------
    # 2. READ PHOTO
    # --------------------------------------------------------

    image_bytes = uploaded.read()

    image_array = np.frombuffer(
        image_bytes,
        np.uint8
    )

    reference_image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )

    if reference_image is None:

        result["message"] = "Could not read the uploaded image."

        return render_template_string(
            HTML,
            result=result,
            demo_url=""
        )


    # --------------------------------------------------------
    # 3. FACE DETECTION
    # --------------------------------------------------------

    reference_feature = get_face_feature(
        reference_image
    )

    if reference_feature is None:

        result["message"] = (
            "No face detected in the uploaded image."
        )

        return render_template_string(
            HTML,
            result=result,
            demo_url=""
        )

    print("✅ Face detected")

# --------------------------------------------------------
    # 4. UPLOAD IMAGE FOR REVERSE SEARCH
    # --------------------------------------------------------

    try:
        temp_path = "uploaded_search_image.jpg"

        with open(temp_path, "wb") as f:
            f.write(image_bytes)

        search_url = upload_to_img402(temp_path)

        print("🔎 Searching uploaded image:", search_url)

    except Exception as e:

        result["message"] = (
            "Could not upload the image for reverse search."
        )

        print("❌ Reverse search upload error:", e)

        return render_template_string(
            HTML,
            result=result,
            demo_url=""
        )



    # --------------------------------------------------------
    # 5. REVERSE IMAGE SEARCH
    # --------------------------------------------------------

    search_results = reverse_image_search(
        search_url
    )

    if not search_results:

        result["status"] = "❌ No public search results found"

        result["message"] = (
            "The reverse-image API returned no indexed results "
            "for this public image URL."
        )

        return render_template_string(
            HTML,
            result=result,
            demo_url=""
        )


    # --------------------------------------------------------
    # 6. COMPARE FACES
    # --------------------------------------------------------

    best_score = -1
    best_result = None

    print()
    print("👤 Comparing candidate faces...")

    for item in search_results[:50]:

        candidate_url = item.get("image")

        if not candidate_url:
            continue

        candidate_image = download_image(
            candidate_url
        )

        if candidate_image is None:
            continue

        score = compare_features(
            reference_feature,
            candidate_image
        )

        if score is None:
            continue

        print(
            "Similarity:",
            round(score, 4)
        )

        if score > best_score:

            best_score = score
            best_result = item


    # --------------------------------------------------------
    # 7. CHECK FACE MATCH
    # --------------------------------------------------------

    if (
        best_result is None
        or best_score < THRESHOLD
    ):

        result["status"] = "❌ No matching public post found"

        if best_score >= 0:

            result["message"] = (
                "Search results were found, but none passed "
                "the face similarity threshold."
            )

            result["score"] = round(
                best_score,
                4
            )

        else:

            result["message"] = (
                "Search results were found, but no candidate "
                "contained a usable face."
            )

        return render_template_string(
            HTML,
            result=result,
            demo_url=""
        )


    # --------------------------------------------------------
    # 8. MATCH FOUND
    # --------------------------------------------------------

    matched_title = best_result.get(
        "title",
        "Untitled result"
    )

    matched_url = best_result.get(
        "link",
        ""
    )

    matched_image = best_result.get(
        "image",
        ""
    )

    print()
    print("================================")
    print("✅ MATCH FOUND")
    print("Similarity:", best_score)
    print("Title:", matched_title)
    print("Page:", matched_url)
    print("================================")


    result["success"] = True

    result["status"] = "✅ Face Match Found"

    result["message"] = (
        "A public web result was found whose candidate "
        "face passed the configured similarity threshold."
    )

    result["score"] = round(
        best_score,
        4
    )

    result["matched_title"] = matched_title
    result["matched_url"] = matched_url


    # --------------------------------------------------------
    # 9. CREATE SHA-256 FINGERPRINT
    # --------------------------------------------------------

    fingerprint_data = (
        matched_url
        + "|"
        + matched_title
        + "|"
        + matched_image
    )

    post_hash = hashlib.sha256(
        fingerprint_data.encode("utf-8")
    ).hexdigest()

    result["face_hash"] = post_hash

    print("🔐 SHA-256:", post_hash)


    # --------------------------------------------------------
    # 10. BLOCKCHAIN
    # --------------------------------------------------------

    if contract is None:

        result["message"] += (
            " Blockchain is not connected."
        )

        return render_template_string(
            HTML,
            result=result,
            demo_url=""
        )


    try:

        account = w3.eth.accounts[0]

        print("⛓️ Blockchain account:", account)

        # Store fingerprint
        tx = contract.functions.registerFace(
            post_hash
        ).transact({
            "from": account
        })

        receipt = w3.eth.wait_for_transaction_receipt(
            tx
        )

        tx_hash = receipt["transactionHash"].hex()

        result["transaction"] = tx_hash

        print("⛓️ Transaction:", tx_hash)


        # ----------------------------------------------------
        # 11. RE-VERIFY FROM BLOCKCHAIN
        # ----------------------------------------------------

        record = contract.functions.verifyFace(
            account
        ).call()

        stored_hash = record[0]
        verified = record[1]
        timestamp = record[2]

        print("Stored hash:", stored_hash)
        print("Verified:", verified)
        print("Timestamp:", timestamp)


        if (
            stored_hash == post_hash
            and verified
        ):

            result["blockchain"] = True

            result["timestamp"] = timestamp

            result["status"] = (
                "🎉 Face Match + Blockchain Verified"
            )

            result["message"] = (
                "The matched public result was fingerprinted "
                "with SHA-256, stored on blockchain, and "
                "successfully re-verified."
            )

            print(
                "✅ BLOCKCHAIN VERIFICATION SUCCESS"
            )

        else:

            result["blockchain"] = False

            result["message"] = (
                "The blockchain record did not match "
                "the generated fingerprint."
            )

    except Exception as e:

        print(
            "❌ Blockchain error:",
            e
        )

        result["message"] += (
            " Blockchain transaction failed."
        )


    # --------------------------------------------------------
    # 12. SHOW RESULT
    # --------------------------------------------------------

    return render_template_string(
        HTML,
        result=result,
        demo_url=""
    )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("🚀 Face ID + Blockchain server starting...")
    print("🌐 Open http://127.0.0.1:5000 in your browser")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )