import os
import cv2
import json
import math

def iou(circle1, circle2):
    x1, y1, r1 = circle1['x'], circle1['y'], circle1['radius']
    x2, y2, r2 = circle2['x'], circle2['y'], circle2['radius']
    
    center_distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    radius_sum = r1 + r2

    if center_distance >= radius_sum:
        # The circles do not overlap
        return 0
    elif center_distance <= abs(r1 - r2):
        # One circle is completely within the other
        if r1 < r2:
            # Circle1 is completely inside Circle2
            return math.pi * r1 ** 2 / (math.pi * r2 ** 2)
        else:
            # Circle2 is completely inside Circle1
            return math.pi * r2 ** 2 / (math.pi * r1 ** 2)
    else:
        # Partial overlap
        d = center_distance  # Correct definition of d
        part1 = r1**2 * math.acos((d**2 + r1**2 - r2**2) / (2 * d * r1))
        part2 = r2**2 * math.acos((d**2 + r2**2 - r1**2) / (2 * d * r2))
        part3 = 0.5 * math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))
        
        intersection_area = part1 + part2 - part3
        total_area = math.pi * (r1**2 + r2**2) - intersection_area
        return intersection_area / total_area
    
def evaluate_algorithm(ground_truths, detections, iou_threshold=0.5):
    true_positives = 0
    for detection in detections:
        for truth in ground_truths:
            if iou(detection, truth) > iou_threshold:
                true_positives += 1
                break
    
    total_predictions = len(detections)
    total_actual = len(ground_truths)

    precision = true_positives / total_predictions if total_predictions else 0
    recall = true_positives / total_actual if total_actual else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0

    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }