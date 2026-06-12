# =============================================================================
#  FACE DETECTION  —  Webcam demo: find and box the face
# =============================================================================
#  Purpose: demonstrate Haar Cascade face DETECTION (not recognition).
#  It draws a green rectangle around any face the camera sees and shows the
#  cropped 100x100 face. This is the detection building block reused by the
#  rest of the project.
# =============================================================================

import cv2          # OpenCV: camera, image processing, drawing
import numpy as np  # numerical arrays (imported for completeness)

# Open the default webcam.
cap = cv2.VideoCapture(0)

# Load the pre-trained Haar Cascade face detector (an XML model file from OpenCV).
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")

while True:
	# Step 1: read one frame from the camera.
	ret, frame = cap.read()

	# Step 2: convert the color frame to grayscale.
	#         Haar Cascade only needs brightness, and grayscale is faster.
	gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	# If capture failed, skip this loop iteration.
	if ret == False:
		continue

	# Step 3: detect faces.
	#   1.3 = scaleFactor   (how much the image is shrunk at each scale)
	#   5   = minNeighbors  (how many detections needed to confirm a face)
	faces = face_cascade.detectMultiScale(gray_frame, 1.3, 5)

	# If no face is found, skip.
	if len(faces) == 0:
		continue

	# Step 4: take only the first detected face and process it.
	for face in faces[:1]:
		x, y, w, h = face  # bounding box: top-left corner (x,y) + width/height

		# Step 5: crop the face region with a small margin (offset),
		#         then resize it to a fixed 100x100 size.
		offset = 10
		face_offset = frame[y-offset:y+h+offset, x-offset:x+w+offset]
		face_selection = cv2.resize(face_offset, (100, 100))

		# Show the cropped face in its own window.
		cv2.imshow("Face", face_selection)

		# Draw a green rectangle on the original frame around the face.
		cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

	# Step 6: show the full frame with the rectangle drawn.
	cv2.imshow("faces", frame)

	# Exit when 'q' is pressed.
	key_pressed = cv2.waitKey(1) & 0xFF
	if key_pressed == ord('q'):
		break

# Clean up: release camera and close windows.
cap.release()
cv2.destroyAllWindows()