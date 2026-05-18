import numpy as np
import cv2
import os
from deepface import DeepFace
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Face Payment Service")

DATASET_PATH   = "./face_dataset/"
ENROLL_SAMPLES = 100       # face frames to collect during enrollment
ENROLL_SKIP    = 10        # capture every Nth frame
VERIFY_TIMEOUT = 200       # max frames to try before giving up (~6s at 30fps)
CASCADE_PATH   = "haarcascade_frontalface_alt.xml"

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

# ── Request models ────────────────────────────────────────────────
class EnrollRequest(BaseModel):
    user_id: int

class VerifyRequest(BaseModel):
    user_id: int

# ── KNN ───────────────────────────────────────────────────────────
def calc_distance(v1, v2):
    return np.sqrt(((v1 - v2) ** 2).sum())

def knn(train, test, k=5):
    dist = []
    for i in range(train.shape[0]):
        ix = train[i, :-1]
        iy = train[i, -1]
        dist.append([calc_distance(test, ix), iy])
    dk = sorted(dist, key=lambda x: x[0])[:k]
    labels = np.array(dk)[:, -1]
    output = np.unique(labels, return_counts=True)
    return output[0][np.argmax(output[1])]

# ── Load trainset from face_dataset/ (excluding one user) ─────────
def load_trainset(exclude_user_id=None):
    face_data, label_list = [], []
    class_id = 0
    id_to_name = {}

    for fx in sorted(os.listdir(DATASET_PATH)):
        if not fx.endswith(".npy"):
            continue
        name = fx[:-4]
        # skip the user being verified (their own file is the reference)
        if exclude_user_id and name == str(exclude_user_id):
            continue
        data_item = np.load(DATASET_PATH + fx)
        face_data.append(data_item)
        label_list.append(class_id * np.ones((data_item.shape[0],)))
        id_to_name[class_id] = name
        class_id += 1

    if not face_data:
        return None, {}

    dataset  = np.concatenate(face_data, axis=0)
    labels   = np.concatenate(label_list, axis=0).reshape((-1, 1))
    trainset = np.concatenate((dataset, labels), axis=1)
    return trainset, id_to_name

# ── Detect largest face in frame ──────────────────────────────────
def detect_face(frame):
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) == 0:
        return None
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]
    offset = 5
    crop = frame[max(0, y-offset):y+h+offset, max(0, x-offset):x+w+offset]
    return cv2.resize(crop, (100, 100))

# ── Endpoints ─────────────────────────────────────────────────────

@app.post("/enroll")
def enroll(req: EnrollRequest):
    """
    Open camera, collect ENROLL_SAMPLES face frames,
    save as face_dataset/{user_id}.npy
    """
    os.makedirs(DATASET_PATH, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Camera not available")

    collected = []
    skip = 0

    print(f"[enroll] Starting face enrollment for user {req.user_id} ...")

    try:
        while len(collected) < ENROLL_SAMPLES:
            ret, frame = cap.read()
            if not ret:
                continue

            skip += 1
            face = detect_face(frame)

            if face is not None and skip % ENROLL_SKIP == 0:
                collected.append(face)
                print(f"[enroll] Collected {len(collected)}/{ENROLL_SAMPLES}")

            # Show progress window
            cv2.putText(frame,
                        f"Enrolling: {len(collected)}/{ENROLL_SAMPLES} — look at camera",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
            cv2.imshow("Face Enrollment", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    if len(collected) < ENROLL_SAMPLES:
        raise HTTPException(status_code=500, detail="Not enough face samples collected")

    face_array = np.array(collected).reshape((len(collected), -1))
    save_path  = os.path.join(DATASET_PATH, f"{req.user_id}.npy")
    np.save(save_path, face_array)
    print(f"[enroll] Saved {save_path}")

    return {"success": True, "user_id": req.user_id, "samples": len(collected)}


@app.post("/verify")
def verify(req: VerifyRequest):
    """
    Load user's face data, open camera, run anti-spoof + KNN match.
    Returns match=True only when face is live AND matches stored data.
    """
    npy_path = os.path.join(DATASET_PATH, f"{req.user_id}.npy")
    if not os.path.exists(npy_path):
        raise HTTPException(status_code=404, detail=f"No face data for user {req.user_id}")

    # Build trainset containing only this user (1 class)
    user_data   = np.load(npy_path)
    user_labels = np.zeros((user_data.shape[0], 1))   # class 0 = this user
    trainset    = np.concatenate((user_data, user_labels), axis=1)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Camera not available")

    is_live     = False
    spoof_score = 0.0
    frame_count = 0
    knn_distances = []

    print(f"[verify] Starting face verification for user {req.user_id} ...")

    try:
        while frame_count < VERIFY_TIMEOUT:
            ret, frame = cap.read()
            if not ret:
                continue

            frame_count += 1

            # Anti-spoof check every 15 frames
            if frame_count % 15 == 0:
                try:
                    result = DeepFace.extract_faces(
                        img_path=frame,
                        anti_spoofing=True,
                        enforce_detection=False
                    )
                    if result:
                        is_live     = result[0]["is_real"]
                        spoof_score = result[0]["antispoof_score"]
                        print(f"[verify] Anti-spoof: live={is_live}, score={spoof_score:.2f}")
                except Exception as e:
                    print(f"[verify] Anti-spoof error: {e}")
                    is_live = False

            # KNN match only when face is live
            if is_live:
                face = detect_face(frame)
                if face is not None:
                    dist_scores = []
                    for i in range(trainset.shape[0]):
                        d = calc_distance(face.flatten(), trainset[i, :-1])
                        dist_scores.append(d)
                    avg_dist = np.mean(sorted(dist_scores)[:5])
                    knn_distances.append(avg_dist)
                    print(f"[verify] KNN avg dist: {avg_dist:.2f}")

                    # Confident match — distance below threshold
                    if avg_dist < 6000 and len(knn_distances) >= 3:
                        cv2.putText(frame, "VERIFIED", (10, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                        cv2.imshow("Face Verify", frame)
                        cv2.waitKey(800)
                        return {
                            "match": True,
                            "user_id": req.user_id,
                            "score": round(spoof_score, 4)
                        }

            # Show status on screen
            label = f"LIVE {spoof_score:.2f} — Verifying..." if is_live else "Show your face..."
            color = (0, 255, 0) if is_live else (0, 0, 255)
            cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.imshow("Face Verify", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print(f"[verify] Verification failed for user {req.user_id}")
    return {"match": False, "user_id": req.user_id, "score": round(spoof_score, 4)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
