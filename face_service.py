# =============================================================================
#  FACE PAYMENT SERVICE  —  Python AI Engine
# =============================================================================
#  This service is the "brain" of the face-payment system. It exposes two
#  REST API endpoints that the Spring Boot backend calls:
#
#     POST /enroll   -> register a user's face (runs once per user)
#     POST /verify   -> check a face during payment (anti-spoof + identity)
#
#  AI pipeline used:
#     1. Haar Cascade        -> detect WHERE the face is in the image
#     2. FaceNet (deep CNN)  -> turn the face into a 128-number "fingerprint"
#                               (called an embedding)
#     3. MiniFASNet          -> anti-spoofing: is it a real live face or a photo?
#     4. KNN + Cosine        -> compare fingerprints to decide identity
# =============================================================================

# ---- Library imports --------------------------------------------------------
import numpy as np                       # numerical arrays + math (vectors, distances)
import cv2                               # OpenCV: image decoding & processing
import os                                # file system: build paths, check files exist
from deepface import DeepFace            # deep-learning face library (FaceNet + MiniFASNet)
from fastapi import FastAPI, File, UploadFile, Form, HTTPException  # web API framework
from fastapi.middleware.cors import CORSMiddleware                  # allow cross-origin calls
from typing import List                  # type hint for "list of files"


# ---- Create the web application ---------------------------------------------
app = FastAPI(title="Face Payment Service")

# CORS = Cross-Origin Resource Sharing.
# This lets the Spring Boot backend (running on a different port/host)
# call this Python service without the browser blocking the request.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # accept requests from any origin
    allow_methods=["*"],   # accept any HTTP method (GET, POST, ...)
    allow_headers=["*"],   # accept any request header
)


# ---- Global configuration constants -----------------------------------------
DATASET_PATH = "./face_dataset/"   # folder where each user's face data is stored
MODEL_NAME = "Facenet"             # the deep-learning model that produces the embedding
COSINE_THRESHOLD = 0.40            # decision boundary: distance below this = same person
                                   # (0.40 is DeepFace's recommended value for FaceNet)
EMBEDDING_DIM = 128                # FaceNet outputs a 128-dimensional vector per face


# =============================================================================
#  HELPER FUNCTION 1 — Decode raw bytes into an image
# =============================================================================
def decode_image(img_bytes: bytes):
    """Convert the raw bytes received from the network into an OpenCV image."""
    # Step 1: interpret the raw bytes as a 1-D array of unsigned 8-bit numbers.
    arr = np.frombuffer(img_bytes, np.uint8)
    # Step 2: decode that byte array into a real color image (BGR matrix).
    #         IMREAD_COLOR forces a 3-channel (Blue, Green, Red) image.
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


# =============================================================================
#  HELPER FUNCTION 2 — Turn a face image into a 128-number embedding
# =============================================================================
def get_embedding(frame):
    """
    Take an image, find the face, and return its 128-dimensional FaceNet
    embedding (a numeric 'fingerprint' of the face). Returns None if no
    face is found.
    """
    try:
        # DeepFace.represent does THREE things internally in one call:
        #   (a) detects the face using the 'opencv' (Haar Cascade) detector
        #   (b) aligns the face (straightens eyes horizontally) for accuracy
        #   (c) runs the FaceNet CNN to produce the 128-d embedding
        result = DeepFace.represent(
            img_path=frame,
            model_name=MODEL_NAME,       # use FaceNet
            enforce_detection=True,      # error out if no face is found (don't guess)
            detector_backend='opencv',   # use OpenCV Haar Cascade for detection
            align=True,                  # align the face before embedding
        )

        # 'result' is a list (one entry per detected face). We expect at least one.
        if result and len(result) > 0:
            # Convert the embedding (a Python list) into a NumPy float32 array.
            emb = np.array(result[0]['embedding'], dtype=np.float32)
            # facial_area = where the face was found (x, y, width, height) — for logging.
            facial_area = result[0].get('facial_area', {})
            print(f"[embed] face found at {facial_area}, embedding shape={emb.shape}")
            return emb

    except Exception as e:
        # If no face is detected (or any other error), log it and return None.
        print(f"[embed] no face: {e}")

    return None


# =============================================================================
#  HELPER FUNCTION 3 — Measure how different two face fingerprints are
# =============================================================================
def cosine_distance(a, b):
    """
    Cosine distance measures the ANGLE between two vectors.
      result close to 0  -> vectors point the same way  -> same person
      result close to 1  -> vectors point different ways -> different person

    We use cosine (not Euclidean) because FaceNet embeddings carry identity
    in their DIRECTION, not their length.
    """
    # Step 1: normalize each vector to unit length (length = 1).
    #         This isolates direction and removes magnitude differences.
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    # Step 2: dot product of two unit vectors = cosine of the angle between them.
    #         1 - cosine gives a "distance" (0 = identical direction).
    return 1.0 - float(np.dot(a, b))


# =============================================================================
#  ENDPOINT 1 — /enroll  (register a new face for a user)
# =============================================================================
@app.post("/enroll")
async def enroll(
    user_id: int = Form(...),                 # which user is enrolling (form field)
    files: List[UploadFile] = File(...)       # the ~30 captured face images
):
    """Register a user's face by storing many FaceNet embeddings of them."""

    # Step 1: make sure the storage folder exists (create it if it doesn't).
    os.makedirs(DATASET_PATH, exist_ok=True)

    # This list will collect one 128-d embedding per valid face image.
    embeddings = []

    # Step 2: loop over every uploaded image frame.
    for file in files:
        img_bytes = await file.read()          # read the raw bytes of this image
        frame = decode_image(img_bytes)        # decode bytes -> OpenCV image
        if frame is None:                      # skip if the image was corrupted
            continue
        emb = get_embedding(frame)             # detect face + extract embedding
        if emb is not None:                    # only keep frames where a face was found
            embeddings.append(emb)

    # Step 3: quality gate — we need at least 3 good face samples to enroll.
    #         (FaceNet is very discriminative, so 3 is enough.)
    if len(embeddings) < 3:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough face frames detected ({len(embeddings)}/3 minimum). "
                   f"Ensure good lighting and face the camera directly."
        )

    # Step 4: stack all embeddings into one matrix of shape (N, 128)
    #         and save it to disk as <user_id>.npy.
    #         Re-enrolling overwrites the old file automatically.
    arr = np.array(embeddings, dtype=np.float32)
    np.save(os.path.join(DATASET_PATH, f"{user_id}.npy"), arr)

    print(f"[enroll] user {user_id}: saved {len(embeddings)} embeddings (shape={arr.shape})")

    # Step 5: tell the backend enrollment succeeded.
    return {"success": True, "user_id": user_id, "samples": len(embeddings)}


# =============================================================================
#  ENDPOINT 2 — /verify  (check a face during payment)
# =============================================================================
@app.post("/verify")
async def verify(
    user_id: int = Form(...),     # which account is claimed (form field)
    file: UploadFile = File(...)  # a single live face image from checkout
):
    """
    Verify a face in two security stages:
      Stage 1 — Anti-spoofing: is this a REAL live face (not a photo/screen)?
      Stage 2 — Identity match: does this face belong to the claimed user?
    Both stages must pass for the payment to be approved.
    """

    # Step 0: locate this user's stored face data. If it doesn't exist, they
    #         never enrolled, so verification is impossible.
    npy_path = os.path.join(DATASET_PATH, f"{user_id}.npy")
    if not os.path.exists(npy_path):
        raise HTTPException(status_code=404, detail=f"No face data for user {user_id}")

    # Step 1: read and decode the incoming live image.
    img_bytes = await file.read()
    frame = decode_image(img_bytes)
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image data")

    # -------------------------------------------------------------------------
    # STAGE 1 — Anti-spoofing / liveness detection (MiniFASNet)
    # -------------------------------------------------------------------------
    # Goal: block attacks where someone holds up a PHOTO or plays a VIDEO of
    #       the real user. A printed photo can fool identity matching but not
    #       a liveness model.
    is_live = False        # default: assume NOT live until proven otherwise
    spoof_score = 0.0      # confidence score from the model (0.0 - 1.0)
    try:
        # MiniFASNet (via DeepFace) analyzes texture/reflection to judge realness.
        result = DeepFace.extract_faces(
            img_path=frame,
            anti_spoofing=True,        # turn on the liveness model
            enforce_detection=False    # don't crash if face is hard to detect
        )
        if result:
            is_live = result[0].get("is_real", False)            # True = real person
            spoof_score = float(result[0].get("antispoof_score", 0.0))
    except Exception as e:
        print(f"[verify] anti-spoof error: {e}")

    # If the face is judged fake (photo/screen/mask), reject immediately.
    # We never even check the identity — security first.
    if not is_live:
        print(f"[verify] user {user_id}: liveness FAILED (score={spoof_score:.4f})")
        return {"match": False, "user_id": user_id,
                "score": round(spoof_score, 4), "reason": "liveness_failed"}

    # -------------------------------------------------------------------------
    # STAGE 2 — Extract the embedding of the live face (the "probe")
    # -------------------------------------------------------------------------
    # Turn the verified live face into its 128-d FaceNet fingerprint.
    probe = get_embedding(frame)
    if probe is None:                  # safety: face passed liveness but not detectable here
        return {"match": False, "user_id": user_id,
                "score": round(spoof_score, 4), "reason": "no_face_detected"}

    # -------------------------------------------------------------------------
    # STAGE 3 — Load the user's enrolled fingerprints + validate format
    # -------------------------------------------------------------------------
    enrolled = np.load(npy_path)       # shape (N, 128): N stored embeddings
    if enrolled.ndim == 1:             # safety: if only 1 sample, reshape to 2-D
        enrolled = enrolled.reshape(1, -1)
    # Guard against old-format data (e.g. raw-pixel files from a previous version).
    if enrolled.shape[1] != EMBEDDING_DIM:
        print(f"[verify] user {user_id}: OUTDATED enrollment "
              f"(shape={enrolled.shape}, expected {EMBEDDING_DIM}-d)")
        return {"match": False, "user_id": user_id,
                "score": round(spoof_score, 4), "reason": "outdated_enrollment"}

    # -------------------------------------------------------------------------
    # STAGE 4 — KNN matching using cosine distance
    # -------------------------------------------------------------------------
    # Step 4a: compute the cosine distance from the live probe to EVERY
    #          enrolled fingerprint of this user.
    distances = [cosine_distance(probe, enrolled[i]) for i in range(enrolled.shape[0])]

    # Step 4b: KNN with k=5 — look at the 5 CLOSEST stored faces.
    #          (If fewer than 5 are enrolled, use however many exist.)
    k = min(5, len(distances))

    # Step 4c: average those 5 smallest distances into one similarity score.
    #          Averaging makes the decision robust to one odd frame.
    avg_dist = float(np.mean(sorted(distances)[:k]))

    # Step 4d: final decision. Below the threshold = same person = match.
    matched = avg_dist < COSINE_THRESHOLD

    print(f"[verify] user {user_id}: live=True, cosine_dist={avg_dist:.4f} "
          f"(threshold={COSINE_THRESHOLD}), match={matched}")

    # Step 5: return the verdict to the backend, which then approves/denies payment.
    return {"match": matched, "user_id": user_id,
            "score": round(spoof_score, 4), "avg_dist": round(avg_dist, 4)}


# =============================================================================
#  ENTRY POINT — start the web server when this file is run directly
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    # uvicorn is the server that runs our FastAPI app.
    # host="0.0.0.0" -> listen on all network interfaces
    # port=8000      -> the Spring Boot backend calls this port
    uvicorn.run(app, host="0.0.0.0", port=8000)