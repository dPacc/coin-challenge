import os
import cv2
import json

def evaluate_model(dataset_folder):
    json_path = os.path.join(dataset_folder, '_annotations.coco.json')
    with open(json_path, 'r') as file:
        data = json.load(file)
    
    image_id_to_file = {image['id']: image['file_name'] for image in data['images']}
    annotations_by_image = {ann['image_id']: [] for ann in data['annotations']}
    for annotation in data['annotations']:
        annotations_by_image[annotation['image_id']].append(annotation)
    
    total_objects = len(data['annotations'])
    detected_objects = 0
    
    for image_id, annotations in annotations_by_image.items():
        image_path = os.path.join(dataset_folder, image_id_to_file[image_id])
        image = cv2.imread(image_path)
        if image is None:
            continue
        
        # Perform circular object detection and segmentation
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 100)
        
        if circles is not None:
            detected_objects += len(circles[0])
    
    precision = detected_objects / total_objects
    recall = detected_objects / total_objects
    f1_score = 2 * (precision * recall) / (precision + recall)
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }