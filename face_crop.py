import cv2
import sys
import os

# =========================
# CHECK INPUT
# =========================

if len(sys.argv) < 2:
    print("Usage: python face_crop.py <image_path>")
    sys.exit()

image_path = sys.argv[1]

if not os.path.exists(image_path):
    print("❌ Image not found:", image_path)
    sys.exit()


# =========================
# LOAD IMAGE
# =========================

image = cv2.imread(image_path)

if image is None:
    print("❌ Could not read image")
    sys.exit()

print("✅ Image loaded")


# =========================
# LOAD FACE DETECTOR
# =========================

detector = cv2.FaceDetectorYN.create(
    "models/face_detection_yunet_2023mar.onnx",
    "",
    (320, 320)
)

detector.setInputSize(
    (image.shape[1], image.shape[0])
)


# =========================
# DETECT FACE
# =========================

_, faces = detector.detect(image)

if faces is None or len(faces) == 0:
    print("❌ No face detected")
    sys.exit()

print("✅ Face detected")
print("Number of faces:", len(faces))


# =========================
# GET FIRST FACE
# =========================

face = faces[0]

x = int(face[0])
y = int(face[1])
w = int(face[2])
h = int(face[3])

# Keep coordinates inside image
x = max(0, x)
y = max(0, y)

x2 = min(image.shape[1], x + w)
y2 = min(image.shape[0], y + h)

face_crop = image[y:y2, x:x2]


# =========================
# SAVE FACE
# =========================

os.makedirs("search_images", exist_ok=True)

output_path = "search_images/face_search.jpg"

cv2.imwrite(output_path, face_crop)

print("✅ Face crop saved:")
print(output_path)