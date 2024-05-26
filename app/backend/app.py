import os
import cv2
import json
import base64
import numpy as np
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

app = Flask(__name__)

# Configure CORS
CORS(app, origins="*")

# Define the database connection URL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@db:5432/image_db'
db = SQLAlchemy(app)

# Schema for the Image model
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)

    def __repr__(self):
        return f'<Image {self.filename}>'
    
# Schema for the ObjectDetection model
class ObjectDetection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
    object_id = db.Column(db.String(100), nullable=False)
    bbox = db.Column(db.JSON, nullable=False)
    centroid = db.Column(db.JSON, nullable=False)
    radius = db.Column(db.Integer, nullable=False)

# Create the database if it doesn't exist
def create_db():
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    if not database_exists(engine.url):
        create_database(engine.url)
    with app.app_context():
        db.create_all()

# API for uploading and saving the image on the DB
@app.route('/upload', methods=['POST'])
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
@app.route('/images', methods=['GET'])
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
@app.route('/image/<int:image_id>', methods=['GET'])
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
# API for processing the image and returning the detected objects
@app.route('/process/<int:image_id>', methods=['POST'])
def process_image(image_id):
    image = Image.query.get(image_id)
    if image:
        nparr = np.frombuffer(image.data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        algorithm = request.json['algorithm']
        mask = None
        if algorithm == 'manual':
            json_path = os.path.join('coin-dataset', '_annotations.coco.json')
            with open(json_path, 'r') as file:
                data = json.load(file)
            annotations = [ann for ann in data['annotations'] if data['images'][ann['image_id']]['file_name'] == image.filename]
            if not annotations:
                return jsonify({'message': 'No annotations found for this image'})
            mask = manual_circle_mask(img, annotations)
        elif algorithm == 'hough':
            mask = hough_circle_detection(img)
        elif algorithm == 'threshold':
            mask = threshold_segmentation(img)
        elif algorithm == 'contour':
            mask = contour_based_segmentation(img)
        else:
            return jsonify({'message': 'Unsupported algorithm specified'})
        
        objects = []
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
                cv2.rectangle(bbox_image, (x, y), (x + width, y + height), (0, 255, 0), 2)
        
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

@app.route('/delete/<int:image_id>', methods=['DELETE'])
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

@app.route('/objects/<int:image_id>', methods=['GET'])
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

@app.route('/object/<string:object_id>', methods=['GET'])
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

if __name__ == '__main__':
    create_db()

    app.run(host='0.0.0.0', port=8000)