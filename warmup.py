# =============================================================================
#  WARMUP  —  Pre-load the DeepFace AI models into memory
# =============================================================================
#  Purpose: the FIRST time DeepFace runs, it has to download and load the model
#  weights, which takes several seconds. Running this script once at startup
#  "warms up" (caches) the models so the FIRST real user doesn't experience a
#  long delay.
# =============================================================================

from deepface import DeepFace
import numpy as np

# Create a tiny blank black image (100x100, 3 color channels).
# We don't care about the content — we only want to trigger model loading.
img = np.zeros((100, 100, 3), dtype=np.uint8)

try:
    # Run the anti-spoofing model once. This forces DeepFace to download and
    # load the MiniFASNet weights into memory.
    # enforce_detection=False -> don't error out even though there's no real face.
    DeepFace.extract_faces(img_path=img, anti_spoofing=True, enforce_detection=False)
except Exception as e:
    # A "no face found" error here is EXPECTED (the image is blank).
    # The important side effect — loading the models — already happened.
    print("Warmup error (expected):", e)

print("Models cached.")
