from web3 import Web3
import json
import hashlib 
import os
import cv2
import requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEBNINJA_API_KEY")
THRESHOLD = 0.363

SEARCH_IMAGE = "https://i.imgur.com/HBrB8p0.png"
REFERENCE_IMAGE = r"samples\public_test.jpg"


detector = cv2.FaceDetectorYN.create(
    "models/face_detection_yunet_2023mar.onnx",
    "",
    (320, 320)
)

recognizer = cv2.FaceRecognizerSF.create(
    "models/face_recognition_sface_2021dec.onnx",
    ""
)


def get_feature(image):
    detector.setInputSize((image.shape[1], image.shape[0]))

    _, faces = detector.detect(image)

    if faces is None or len(faces) == 0:
        return None

    face = recognizer.alignCrop(image, faces[0])
    return recognizer.feature(face)


def compare(reference, candidate_url):
    try:
        response = requests.get(candidate_url, timeout=15)

        if response.status_code != 200:
            return None

        data = np.frombuffer(response.content, np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)

        if image is None:
            return None

        candidate_feature = get_feature(image)

        if candidate_feature is None:
            return None

        score = recognizer.match(
            reference,
            candidate_feature,
            cv2.FaceRecognizerSF_FR_COSINE
        )

        return float(score)

    except Exception:
        return None


# Load reference face
reference_image = cv2.imread(REFERENCE_IMAGE)
reference_feature = get_feature(reference_image)

if reference_feature is None:
    print("❌ No face detected in reference image.")
    exit()

print("🔎 Searching the web...")

response = requests.get(
    "https://api.openwebninja.com/reverse-image-search/reverse-image-search",
    params={
        "url": SEARCH_IMAGE
    },
    headers={
        "x-api-key": API_KEY
    },
    timeout=30
)

print("API status:", response.status_code)

results = response.json().get("data", [])

print("Candidates found:", len(results))
print()

best_score = -1
best_result = None

for i, result in enumerate(results[:20], start=1):

    image_url = result.get("image")

    if not image_url:
        continue

    score = compare(reference_feature, image_url)

    if score is None:
        print(f"{i}. No usable face")
        continue

    print(f"{i}. Similarity: {score:.4f}")

    if score > best_score:
        best_score = score
        best_result = result


print()
print("================================")

if best_result and best_score >= THRESHOLD:
    print("✅ MATCH FOUND")
    print("Similarity:", round(best_score, 4))

    matched_url = best_result.get("link", "")
    matched_title = best_result.get("title", "")
    matched_image = best_result.get("image", "")

    print("Page:", matched_url)
    print("Title:", matched_title)

    # Create a fingerprint of the discovered result
    matched_data = (
        matched_url
        + "|"
        + matched_title
        + "|"
        + matched_image
    )

    post_hash = hashlib.sha256(
        matched_data.encode("utf-8")
    ).hexdigest()

    print("SHA-256:", post_hash)

    # Connect to blockchain
    w3 = Web3(
        Web3.HTTPProvider("http://127.0.0.1:8545")
    )

    with open(
        "artifacts/contracts/FaceVerification.sol/FaceVerification.json",
        "r"
    ) as f:
        contract_data = json.load(f)

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(
            "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        ),
        abi=contract_data["abi"]
    )

    account = w3.eth.accounts[0]

    # Store fingerprint on blockchain
    tx = contract.functions.registerFace(
        post_hash
    ).transact({
        "from": account
    })

    receipt = w3.eth.wait_for_transaction_receipt(tx)

    print("Transaction:", receipt["transactionHash"].hex())

    # Read it back
    record = contract.functions.verifyFace(
        account
    ).call()

    stored_hash = record[0]
    verified = record[1]

    print("Stored hash:", stored_hash)

    if stored_hash == post_hash and verified:
        print("✅ BLOCKCHAIN VERIFICATION SUCCESS")
    else:
        print("❌ BLOCKCHAIN VERIFICATION FAILED")

else:

    print("❌ NO MATCH FOUND")

    if best_score >= 0:
        print("Best similarity:", round(best_score, 4))