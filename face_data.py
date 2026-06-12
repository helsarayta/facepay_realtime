# =============================================================================
#  FACE DATA COLLECTION  —  Standalone enrollment script (OFFLINE / LOCAL DEMO)
# =============================================================================
#  Purpose: collect a person's face images from the webcam and save them as a
#  .npy dataset file. This is the LOCAL/DESKTOP version of enrollment.
#
#  NOTE: This script stores RAW PIXELS (the original approach). The deployed
#  web service (face_service.py) instead stores FaceNet EMBEDDINGS, which are
#  far more accurate. Keep this file for demonstrating the original method.
# =============================================================================

import cv2
import numpy as np

# Open the default webcam.
cap = cv2.VideoCapture(0)

# Load the Haar Cascade face detector.
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")

skip = 0                       # frame counter (used to sample every 10th frame)
face_data = []                 # list that will hold the captured face images
dataset_path = "./face_dataset/"

# Ask the user to type the person's name (used as the saved file name).
file_name = input("Enter the name of person : ")


while True:
	# Step 1: read one frame from the camera.
	ret, frame = cap.read()

	# Step 2: convert to grayscale for detection.
	gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	if ret == False:
		continue

	# Step 3: detect faces; skip the frame if none found.
	faces = face_cascade.detectMultiScale(gray_frame, 1.3, 5)
	if len(faces) == 0:
		continue

	k = 1

	# Step 4: sort faces by area (w*h) so the LARGEST (closest) face is first.
	faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)

	skip += 1

	# Step 5: process only the single largest face.
	for face in faces[:1]:
		x, y, w, h = face

		# Crop the face with a small margin and resize to 100x100.
		offset = 5
		face_offset = frame[y-offset:y+h+offset, x-offset:x+w+offset]
		face_selection = cv2.resize(face_offset, (100, 100))

		# Step 6: save this face only every 10th frame (to get varied samples,
		#         not 30 near-identical frames in a row).
		if skip % 10 == 0:
			face_data.append(face_selection)
			print(len(face_data))   # print how many samples collected so far

		# Show the cropped face and draw a box on the live frame.
		cv2.imshow(str(k), face_selection)
		k += 1
		cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

	# Show the full frame.
	cv2.imshow("faces", frame)

	# Press 'q' to stop collecting.
	key_pressed = cv2.waitKey(1) & 0xFF
	if key_pressed == ord('q'):
		break

# Step 7: convert the list of images into a NumPy array.
face_data = np.array(face_data)

# Step 8: flatten each 100x100x3 image into a single row vector (30,000 numbers).
#         Final shape = (number_of_samples, 30000).
face_data = face_data.reshape((face_data.shape[0], -1))
print(face_data.shape)

# Step 9: save the dataset to disk as <name>.npy.
np.save(dataset_path + file_name, face_data)
print("Dataset saved at : {}".format(dataset_path + file_name + '.npy'))

# Clean up.
cap.release()
cv2.destroyAllWindows()