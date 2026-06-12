# =============================================================================
#  FACE RECOGNITION  —  Standalone real-time demo (OFFLINE / LOCAL DEMO)
# =============================================================================
#  Purpose: run live face recognition on the webcam. It detects a face,
#  checks liveness (anti-spoofing), and identifies WHO it is using KNN.
#
#  NOTE: This local demo uses the ORIGINAL approach — raw pixels + Euclidean
#  distance KNN. The deployed web service (face_service.py) uses the improved
#  FaceNet embeddings + cosine distance. Keep this file to demonstrate the
#  original classical method.
# =============================================================================

import numpy as np
import cv2
import os
from deepface import DeepFace


# =============================================================================
#  KNN — classify a face by comparing it to all stored faces
# =============================================================================
def calc_distance(v1, v2):
    """Euclidean distance between two vectors: sqrt(sum of squared differences)."""
    return np.sqrt(((v1 - v2) ** 2).sum())


def knn(train, test, k=5):
    """
    K-Nearest Neighbors classifier.
      train = stored faces, each row = [pixel features..., label]
      test  = the new face to identify (pixel features only)
      k     = how many nearest neighbors to vote with
    Returns the predicted label (which person).
    """
    dist = []

    # Step 1: compute distance from the test face to EVERY stored face.
    for i in range(train.shape[0]):
        ix = train[i, :-1]   # all columns except last = the face features
        iy = train[i, -1]    # last column = the label (person id)
        d = calc_distance(test, ix)
        dist.append([d, iy])

    # Step 2: sort by distance (ascending) and keep the k closest.
    dk = sorted(dist, key=lambda x: x[0])[:k]

    # Step 3: take the labels of those k neighbors.
    labels = np.array(dk)[:, -1]

    # Step 4: count how often each label appears among the neighbors.
    output = np.unique(labels, return_counts=True)

    # Step 5: return the label that appears most often (majority vote).
    index = np.argmax(output[1])
    return output[0][index]


# =============================================================================
#  LIVENESS (anti-spoofing) configuration
# =============================================================================
# Running the deep anti-spoof model on every frame is slow, so we only run it
# once every N frames to keep the video smooth (real-time).
ANTISPOOF_INTERVAL = 15


# ---- Camera + detector setup ------------------------------------------------
cap = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")

dataset_path = "./face_dataset/"
face_data = []   # list of all stored face arrays
labels = []      # list of label arrays (which person each sample belongs to)
class_id = 0     # numeric id assigned to each person
names = {}       # maps numeric id -> person's name


# =============================================================================
#  LOAD the enrolled dataset from disk (all .npy files)
# =============================================================================
for fx in os.listdir(dataset_path):
    if fx.endswith('.npy'):
        # The file name (without ".npy") is the person's name.
        names[class_id] = fx[:-4]

        # Load this person's stored face samples.
        data_item = np.load(dataset_path + fx)
        face_data.append(data_item)

        # Create a label array (all the same class_id) for these samples.
        target = class_id * np.ones((data_item.shape[0],))
        class_id += 1
        labels.append(target)

# Combine everyone's faces into one big training matrix.
face_dataset = np.concatenate(face_data, axis=0)
face_labels  = np.concatenate(labels, axis=0).reshape((-1, 1))

# Join features + labels side by side -> each row = [features..., label].
trainset = np.concatenate((face_dataset, face_labels), axis=1)


# ---- Liveness state variables -----------------------------------------------
is_live     = False   # is the current face a real live person?
spoof_score = 0.0     # confidence score from the anti-spoof model
frame_count = 0       # counts frames so we know when to re-check liveness

font = cv2.FONT_HERSHEY_SIMPLEX   # font for drawing text on screen


# =============================================================================
#  MAIN LOOP — process the webcam frame by frame
# =============================================================================
while True:
    # Step 1: grab a frame.
    ret, frame = cap.read()
    if not ret:
        continue

    # Step 2: detect faces in grayscale.
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    # Step 3: if no face is visible, reset the liveness state.
    if len(faces) == 0:
        is_live     = False
        spoof_score = 0.0
        frame_count = 0

    frame_count += 1

    # Step 4: handle each detected face.
    for face in faces:
        x, y, w, h = face

        # --- Liveness check: only every N frames to stay real-time ---
        if frame_count % ANTISPOOF_INTERVAL == 0:
            try:
                result = DeepFace.extract_faces(
                    img_path=frame,
                    anti_spoofing=True,
                    enforce_detection=False
                )
                if result:
                    is_live     = result[0]["is_real"]        # True = real face
                    spoof_score = result[0]["antispoof_score"]
            except Exception as e:
                print(f"[antispoof error] {e}")
                is_live     = False
                spoof_score = 0.0

        # --- Crop + resize the face to 100x100 (same format as training) ---
        offset = 5
        face_section = frame[max(0, y-offset):y+h+offset, max(0, x-offset):x+w+offset]
        face_section = cv2.resize(face_section, (100, 100))

        # --- Recognition only runs if the face passed the liveness check ---
        if is_live:
            # Flatten the face to a vector and classify it with KNN.
            out  = knn(trainset, face_section.flatten())
            name = names[int(out)]
            # Draw a GREEN box + the person's name + liveness score.
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, name,  (x, y-35), font, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"LIVE  {spoof_score:.2f}", (x, y-10), font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
        else:
            # Draw a RED box: face is fake or still being verified.
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(frame, "FAKE / Verifying...", (x, y-10), font, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

    # Step 5: show the annotated frame.
    cv2.imshow("Face Recognition", frame)

    # Press 'q' to quit.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up.
cap.release()
cv2.destroyAllWindows()
