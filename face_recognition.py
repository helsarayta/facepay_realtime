import numpy as np
import cv2
import os
from deepface import DeepFace

########## KNN CODE ############
def calc_distance(v1, v2):
    return np.sqrt(((v1-v2)**2).sum())

def knn(train, test, k=5):
    dist = []
    for i in range(train.shape[0]):
        ix = train[i, :-1]
        iy = train[i, -1]
        d = calc_distance(test, ix)
        dist.append([d, iy])
    dk = sorted(dist, key=lambda x: x[0])[:k]
    labels = np.array(dk)[:, -1]
    output = np.unique(labels, return_counts=True)
    index = np.argmax(output[1])
    return output[0][index]
################################

########## LIVENESS (DEEPFACE ANTI-SPOOFING) ############
# Runs every N frames to keep real-time performance
ANTISPOOF_INTERVAL = 15
#########################################################

cap = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")

dataset_path = "./face_dataset/"
face_data = []
labels = []
class_id = 0
names = {}

for fx in os.listdir(dataset_path):
    if fx.endswith('.npy'):
        names[class_id] = fx[:-4]
        data_item = np.load(dataset_path + fx)
        face_data.append(data_item)
        target = class_id * np.ones((data_item.shape[0],))
        class_id += 1
        labels.append(target)

face_dataset = np.concatenate(face_data, axis=0)
face_labels  = np.concatenate(labels, axis=0).reshape((-1, 1))
trainset     = np.concatenate((face_dataset, face_labels), axis=1)

# Liveness state
is_live       = False
spoof_score   = 0.0
frame_count   = 0

font = cv2.FONT_HERSHEY_SIMPLEX

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    # Reset liveness when no face present
    if len(faces) == 0:
        is_live     = False
        spoof_score = 0.0
        frame_count = 0

    frame_count += 1

    for face in faces:
        x, y, w, h = face

        # --- Liveness check every N frames (DeepFace anti-spoofing) ---
        if frame_count % ANTISPOOF_INTERVAL == 0:
            try:
                result = DeepFace.extract_faces(
                    img_path=frame,
                    anti_spoofing=True,
                    enforce_detection=False
                )
                if result:
                    is_live     = result[0]["is_real"]
                    spoof_score = result[0]["antispoof_score"]
            except Exception as e:
                print(f"[antispoof error] {e}")
                is_live     = False
                spoof_score = 0.0

        # --- Face recognition: only runs when liveness confirmed ---
        offset = 5
        face_section = frame[max(0,y-offset):y+h+offset, max(0,x-offset):x+w+offset]
        face_section = cv2.resize(face_section, (100, 100))

        if is_live:
            out  = knn(trainset, face_section.flatten())
            name = names[int(out)]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, name,  (x, y-35), font, 0.9,  (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"LIVE  {spoof_score:.2f}", (x, y-10), font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
        else:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(frame, "FAKE / Verifying...", (x, y-10), font, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

    cv2.imshow("Face Recognition", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
