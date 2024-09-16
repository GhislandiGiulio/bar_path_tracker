import cv2 as cv
import numpy as np

# Open the video capture
cap = cv.VideoCapture('sample_data/squat.mov')

# Read the first frame of the video
ret, frame = cap.read()

# Allow the user to select the ROI
roi_box = cv.selectROI("Select ROI", frame, fromCenter=False, showCrosshair=True)

# Extract the coordinates of the ROI
x, y, w, h = map(int, roi_box)
roi = frame[y:y+h, x:x+w]

# Convert the ROI to HSV color space
hsv_roi = cv.cvtColor(roi, cv.COLOR_BGR2HSV)

# Create a mask to filter out low light (this removes dark pixels from the histogram calculation)
mask = cv.inRange(hsv_roi, np.array((0., 60., 32.)), np.array((180., 255., 255.)))

# Compute the histogram of the ROI in the HSV color space (using only the hue channel)
roi_hist = cv.calcHist([hsv_roi], [0], mask, [180], [0, 180])

# Normalize the histogram
cv.normalize(roi_hist, roi_hist, 0, 255, cv.NORM_MINMAX)

# Define the termination criteria: either 50 iterations or moving by at least 1.5 pt
term_crit = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 1)

# Create the initial window for tracking
track_window = (x, y, w, h)

while True:
    # Capture a new frame
    ret, frame = cap.read()

    if ret:
        # Convert the frame to HSV color space
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

        # Back-project the histogram of the ROI onto the new frame (using the hue channel)
        dst = cv.calcBackProject([hsv], [0], roi_hist, [0, 180], 1)

        # Apply the mean shift to get the new location
        ret, track_window = cv.meanShift(dst, track_window, term_crit)

        # Draw the new tracking window on the frame
        x, y, w, h = track_window
        cv.rectangle(frame, (x, y), (x+w, y+h), 255, 2)

        # Display the result
        cv.imshow('CamShift Tracking', frame)

        # Exit when the user presses the Esc key
        if cv.waitKey(1) & 0xFF == 27:  # Reduce wait time for faster processing
            break
    else:
        break

# Release the capture and close windows
cap.release()
cv.destroyAllWindows()
