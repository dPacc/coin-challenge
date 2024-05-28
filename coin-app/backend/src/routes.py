from flask import Blueprint, request, jsonify
from src import db
from .models import Image, ObjectDetection
from .utils import manual_circle_mask, hough_circle_detection, threshold_segmentation, contour_based_segmentation, evaluate_algorithm
import cv2
import numpy as np
import base64
import os
import json

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Server running successfully'})

@main.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    filename = file.filename
    image_data = file.read()
    
    # Check if an image with the same content already exists in the database
    existing_image = Image.query.filter_by(data=image_data).first()
    if existing_image:
        return jsonify({'message': 'Image already exists', 'id': existing_image.id})
    
    # If the image doesn't exist, save it to the database
    new_image = Image(filename=filename, data=image_data)
    db.session.add(new_image)
    db.session.commit()
    
    return jsonify({'message': 'Image uploaded successfully', 'id': new_image.id})


# API for getting the list of images from the DB
@main.route('/images', methods=['GET'])
def get_images():
    images = Image.query.all()
    image_list = []
    for image in images:
        image_data = base64.b64encode(image.data).decode('utf-8')
        image_list.append({
            'id': image.id,
            'filename': image.filename,
            'data': image_data
        })
    return jsonify(image_list)

# API for getting the image data from the DB
@main.route('/image/<int:image_id>', methods=['GET'])
def get_image(image_id):
    image = Image.query.get(image_id)
    if image:
        image_data = base64.b64encode(image.data).decode('utf-8')
        return jsonify({
            'id': image.id,
            'filename': image.filename,
            'data': image_data
        })
    else:
        return jsonify({'message': 'Image not found'})

# API for processing the image and returning the detected objects
@main.route('/process/<int:image_id>', methods=['POST'])
def process_image(image_id):
    image = Image.query.get(image_id)
    if image:
        nparr = np.frombuffer(image.data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        algorithm = request.json['algorithm']
        mask = None

        # Load the ground truth annotations from the JSON file
        json_path = os.path.join('coin-dataset', '_annotations.coco.json')
        with open(json_path, 'r') as file:
            data = json.load(file)
        annotations = [ann for ann in data['annotations'] if data['images'][ann['image_id']]['file_name'] == image.filename]

        if algorithm == 'manual':
            if not annotations:
                return jsonify({'message': 'No annotations found for this image'})
            mask = manual_circle_mask(img, annotations)

        elif algorithm in ['hough', 'threshold', 'contour']:
            if algorithm == 'hough':
                mask = hough_circle_detection(img)
            elif algorithm == 'threshold':
                mask = threshold_segmentation(img)
            elif algorithm == 'contour':
                mask = contour_based_segmentation(img)

        else:
            return jsonify({'message': 'Unsupported algorithm specified'})

        objects = []
        detections = []
        bbox_image = img.copy()
        if algorithm != 'manual':
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                if cv2.contourArea(cnt) > 100:
                    (x, y), radius = cv2.minEnclosingCircle(cnt)
                    center = (int(x), int(y))
                    radius = int(radius)
                    object_id = f"{image_id}_{len(objects) + 1}"
                    object_detection = ObjectDetection(
                        image_id=image_id,
                        object_id=object_id,
                        bbox=[int(x) - radius, int(y) - radius, 2 * radius, 2 * radius],
                        centroid=[center],
                        radius=radius
                    )
                    db.session.add(object_detection)
                    objects.append({
                        'id': object_id,
                        'bbox': [int(x) - radius, int(y) - radius, 2 * radius, 2 * radius],
                        'centroid': [center],
                        'radius': radius
                    })
                    detections.append({'x': center[0], 'y': center[1], 'radius': radius})
                    cv2.circle(bbox_image, center, radius, (0, 255, 0), 2)
        else:
            for annotation in annotations:
                x, y, width, height = annotation['bbox']
                center = (x + width // 2, y + height // 2)
                radius = min(width, height) // 2
                object_id = f"{image_id}_{annotation['id']}"
                object_detection = ObjectDetection(
                    image_id=image_id,
                    object_id=object_id,
                    bbox=[x, y, width, height],
                    centroid=[center[0], center[1]],
                    radius=radius
                )
                db.session.add(object_detection)
                objects.append({
                    'id': object_id,
                    'bbox': [x, y, width, height],
                    'centroid': [center[0], center[1]],
                    'radius': radius
                })
                detections.append({'x': center[0], 'y': center[1], 'radius': radius})
                cv2.rectangle(bbox_image, (x, y), (x + width, y + height), (0, 255, 0), 2)

        # Prepare ground truths and evaluate if necessary
        ground_truths = [{'x': ann['bbox'][0] + ann['bbox'][2] // 2, 'y': ann['bbox'][1] + ann['bbox'][3] // 2, 'radius': min(ann['bbox'][2], ann['bbox'][3]) // 2} for ann in annotations]
        if algorithm != 'manual':
            evaluation_metrics = evaluate_algorithm(ground_truths, detections)
        
        db.session.commit()
        
        # Encode the original image, image with bounding boxes, and masked image as base64 strings
        original_image = cv2.imencode('.jpg', img)[1].tostring()
        bbox_image_encoded = cv2.imencode('.jpg', bbox_image)[1].tostring()
        masked_image = cv2.imencode('.jpg', mask)[1].tostring()
        
        return jsonify({
            'original_image': base64.b64encode(original_image).decode('utf-8'),
            'bbox_image': base64.b64encode(bbox_image_encoded).decode('utf-8'),
            'masked_image': base64.b64encode(masked_image).decode('utf-8'),
            'objects': objects,
            'evaluation_metrics': evaluation_metrics if algorithm != 'manual' else None
        })
    else:
        return jsonify({'message': 'Image not found'})

@main.route('/delete/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    image = Image.query.get(image_id)
    if image:
        # Delete the associated object detections
        ObjectDetection.query.filter_by(image_id=image_id).delete()
        
        # Delete the image
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'message': 'Image deleted successfully'})
    else:
        return jsonify({'message': 'Image not found'})

@main.route('/objects/<int:image_id>', methods=['GET'])
def get_objects(image_id):
    objects = ObjectDetection.query.filter_by(image_id=image_id).all()
    object_list = []
    for obj in objects:
        object_list.append({
            'id': obj.object_id,
            'bbox': obj.bbox,
            'centroid': obj.centroid,
            'radius': obj.radius
        })
    return jsonify(object_list)

@main.route('/object/<string:object_id>', methods=['GET'])
def get_object_details(object_id):
    object_detection = ObjectDetection.query.filter_by(object_id=object_id).first()
    if object_detection:
        return jsonify({
            'id': object_detection.object_id,
            'bbox': object_detection.bbox,
            'centroid': object_detection.centroid,
            'radius': object_detection.radius
        })
    else:
        return jsonify({'message': 'Object not found'})

