# =============================================================================
#  VIDEO READ  —  Most basic webcam demo
# =============================================================================
#  Purpose: prove the webcam works by showing the live video feed.
#  This is the simplest possible OpenCV program — no AI, just camera display.
# =============================================================================

import cv2  # OpenCV library for camera access and image display

# Open the default camera (device index 0 = built-in/first webcam).
cap = cv2.VideoCapture(0)

# Loop forever, grabbing and showing frames one by one.
while True:
    # Read one frame from the camera.
    #   ret   = True if a frame was successfully captured
    #   frame = the actual image (a NumPy array)
    ret, frame = cap.read()

    # If the camera failed to give a frame, skip and try again.
    if ret == False:
        continue

    # Display the frame in a window titled "video frame".
    cv2.imshow("video frame", frame)

    # Wait 1 ms for a key press. The & 0xFF keeps only the relevant bits.
    key_pressed = cv2.waitKey(1) & 0xFF

    # If the user presses the 'q' key, exit the loop.
    if key_pressed == ord('q'):
        break

# Release the camera so other programs can use it, then close all windows.
cap.release()
cv2.destroyAllWindows()