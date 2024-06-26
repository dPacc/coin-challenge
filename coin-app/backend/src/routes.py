from flask import Blueprint, request, jsonify
from src import db
from .models import Image, ObjectDetection
from .utils import manual_circle_mask, hough_circle_detection, contour_based_segmentation, evaluate_model
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

        json_path = os.path.join('coin-dataset', '_annotations.coco.json')
        with open(json_path, 'r') as file:
            data = json.load(file)
        annotations = [ann for ann in data['annotations'] if data['images'][ann['image_id']]['file_name'] == image.filename]

        # Find the mask based on the specified algorithm
        if algorithm == 'manual':
            if not annotations:
                return jsonify({'message': 'No annotations found for this image'})
            mask = manual_circle_mask(img, annotations)
        elif algorithm == 'hough':
            # Extract the required parameters from the annotations
            radii = [min(ann['bbox'][2], ann['bbox'][3]) // 2 for ann in annotations]
            min_radius = min(radii)
            max_radius = max(radii)
            dp = 1.2
            min_dist = min(img.shape[:2]) // 4
            
            mask = hough_circle_detection(img, min_radius, max_radius, dp, min_dist)
        elif algorithm == 'contour':
            mask = contour_based_segmentation(img)
        else:
            return jsonify({'message': 'Unsupported algorithm specified'})
        
        objects = []
        bbox_image = img.copy()
        if algorithm == 'hough':
            # Draw circles on the bbox_image for Hough Circle Transform
            circles = cv2.HoughCircles(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.HOUGH_GRADIENT,
                                    dp=dp, minDist=min_dist, param1=50, param2=30,
                                    minRadius=min_radius, maxRadius=max_radius)
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                for index, (x, y, r) in enumerate(circles, start=1):
                    object_id = f"{image_id}_{len(objects) + 1}"
                    object_detection = ObjectDetection(
                        image_id=image_id,
                        object_id=object_id,
                        bbox=[int(x - r), int(y - r), int(2 * r), int(2 * r)],
                        centroid=[int(x), int(y)],
                        radius=int(r)
                    )
                    db.session.add(object_detection)
                    objects.append({
                        'id': object_id,
                        'bbox': [int(x - r), int(y - r), int(2 * r), int(2 * r)],
                        'centroid': [int(x), int(y)],
                        'radius': int(r)
                    })
                    cv2.circle(bbox_image, (x, y), r, (0, 255, 0), 2)
                    cv2.putText(bbox_image, str(index), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (23, 247, 23), 5)
        elif algorithm != 'manual':
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for index, cnt in enumerate(contours, start=1):
                if cv2.contourArea(cnt) > 100:
                    (x, y), radius = cv2.minEnclosingCircle(cnt)
                    center = (int(x), int(y))
                    radius = int(radius)
                    object_id = f"{image_id}_{len(objects) + 1}"
                    object_detection = ObjectDetection(
                        image_id=image_id,
                        object_id=object_id,
                        bbox=[int(x) - radius, int(y) - radius, 2 * radius, 2 * radius],
                        centroid=[int(x), int(y)],
                        radius=radius
                    )
                    db.session.add(object_detection)
                    objects.append({
                        'id': object_id,
                        'bbox': [int(x) - radius, int(y) - radius, 2 * radius, 2 * radius],
                        'centroid': [int(x), int(y)],
                        'radius': radius
                    })
                    cv2.circle(bbox_image, center, radius, (0, 255, 0), 2)
                    cv2.putText(bbox_image, str(index), (center[0], center[1]), cv2.FONT_HERSHEY_SIMPLEX, 2, (23, 247, 23), 5)
        else:
            for index, annotation in enumerate(annotations, start=1):
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
                cv2.rectangle(bbox_image, (x, y), (x + width, y + height), (0, 255, 0), 2)
                cv2.putText(bbox_image, str(index), (center[0], center[1]), cv2.FONT_HERSHEY_SIMPLEX, 2, (23, 247, 23), 5)
        
        db.session.commit()
        
        # Encode the original image, image with bounding boxes, and masked image as base64 strings
        original_image = cv2.imencode('.jpg', img)[1].tostring()
        bbox_image_encoded = cv2.imencode('.jpg', bbox_image)[1].tostring()
        masked_image = cv2.imencode('.jpg', mask)[1].tostring()
        
        return jsonify({
            'original_image': base64.b64encode(original_image).decode('utf-8'),
            'bbox_image': base64.b64encode(bbox_image_encoded).decode('utf-8'),
            'masked_image': base64.b64encode(masked_image).decode('utf-8'),
            'objects': objects
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

