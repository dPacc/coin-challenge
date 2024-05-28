import cv2
import numpy as np

def manual_circle_mask(image, annotations):
    # Create a mask of zeros with the same size as the image
    mask = np.zeros_like(image)
    for annotation in annotations:
        x, y, width, height = annotation['bbox']
        # Define the center and radius for the circle to be drawn
        center = (x + width // 2, y + height // 2)
        radius = min(width, height) // 2
        # Draw a white circle on the mask
        cv2.circle(mask, center, radius, (255, 255, 255), -1)
    return mask


def hough_circle_detection(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    equalized = cv2.equalizeHist(blur)
    edges = cv2.Canny(equalized, 50, 150)
    circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50, param1=50, param2=30, minRadius=10, maxRadius=100)
    mask = np.zeros_like(gray)  # Create a single-channel mask image
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            cv2.circle(mask, (x, y), r, (255, 255, 255), -1)
    return mask

def threshold_segmentation(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    return mask

def contour_based_segmentation(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(gray)  # Create a single-channel mask image
    for cnt in contours:
        if cv2.contourArea(cnt) > 100:
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            center = (int(x), int(y))
            radius = int(radius)
            cv2.circle(mask, center, radius, (255, 255, 255), -1)
    return mask