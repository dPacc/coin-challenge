from flask import Blueprint, request, jsonify
from flask_restx import Api, Resource, reqparse
from werkzeug.datastructures import FileStorage
from src import db
from .models import Image, ObjectDetection
from .utils import manual_circle_mask, hough_circle_detection, threshold_segmentation, contour_based_segmentation, evaluate_model
import cv2
import numpy as np
import base64
import os
import json

blueprint = Blueprint('api', __name__)
api = Api(blueprint, version='1.0', title='Coin Challenge API', description='API for coin detection and segmentation')

@api.route('/')
class Home(Resource):
    def get(self):
        """
        Route to confirm that the server is running.
        """
        return {'message': 'Server is running'}

upload_parser = reqparse.RequestParser()
upload_parser.add_argument('image', type=werkzeug.datastructures.FileStorage, location='files', required=True, help='Image file')

@api.route('/upload')
class Upload(Resource):
    @api.expect(upload_parser)
    def post(self):
        """
        API for uploading the coin image.
        """
        file = request.files['image']
        filename = file.filename
        image_data = file.read()
        
        existing_image = Image.query.filter_by(data=image_data).first()
        if existing_image:
            return {'message': 'Image already exists', 'id': existing_image.id}
        
        new_image = Image(filename=filename, data=image_data)
        db.session.add(new_image)
        db.session.commit()
        
        return {'message': 'Image uploaded successfully', 'id': new_image.id}

@api.route('/images')
class ImageList(Resource):
    def get(self):
        """
        API for getting the list of images from the DB.
        """
        images = Image.query.all()
        image_list = []
        for image in images:
            image_data = base64.b64encode(image.data).decode('utf-8')
            image_list.append({
                'id': image.id,
                'filename': image.filename,
                'data': image_data
            })
        return image_list

@api.route('/image/<int:image_id>')
@api.param('image_id', 'The ID of the image')
class ImageDetail(Resource):
    def get(self, image_id):
        """
        API for getting the image data from the DB.
        """
        image = Image.query.get(image_id)
        if image:
            image_data = base64.b64encode(image.data).decode('utf-8')
            return {
                'id': image.id,
                'filename': image.filename,
                'data': image_data
            }
        else:
            return {'message': 'Image not found'}

process_parser = reqparse.RequestParser()
process_parser.add_argument('algorithm', type=str, required=True, help='Algorithm to use for processing')

@api.route('/process/<int:image_id>')
@api.param('image_id', 'The ID of the image')
class Process(Resource):
    @api.expect(process_parser)
    def post(self, image_id):
        """
        API for processing the image and returning the detected objects.
        """
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
                    return {'message': 'No annotations found for this image'}
                mask = manual_circle_mask(img, annotations)
            elif algorithm == 'hough':
                mask = hough_circle_detection(img)
            elif algorithm == 'threshold':
                mask = threshold_segmentation(img)
            elif algorithm == 'contour':
                mask = contour_based_segmentation(img)
            else:
                return {'message': 'Unsupported algorithm specified'}
            
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
            
            original_image = cv2.imencode('.jpg', img)[1].tostring()
            bbox_image_encoded = cv2.imencode('.jpg', bbox_image)[1].tostring()
            masked_image = cv2.imencode('.jpg', mask)[1].tostring()
            
            return {
                'original_image': base64.b64encode(original_image).decode('utf-8'),
                'bbox_image': base64.b64encode(bbox_image_encoded).decode('utf-8'),
                'masked_image': base64.b64encode(masked_image).decode('utf-8'),
                'objects': objects
            }
        else:
            return {'message': 'Image not found'}

@api.route('/delete/<int:image_id>')
@api.param('image_id', 'The ID of the image')
class DeleteImage(Resource):
    def delete(self, image_id):
        """
        API for deleting an image and its associated object detections.
        """
        image = Image.query.get(image_id)
        if image:
            ObjectDetection.query.filter_by(image_id=image_id).delete()
            
            db.session.delete(image)
            db.session.commit()
            
            return {'message': 'Image deleted successfully'}
        else:
            return {'message': 'Image not found'}

@api.route('/objects/<int:image_id>')
@api.param('image_id', 'The ID of the image')
class ObjectList(Resource):
    def get(self, image_id):
        """
        API for getting the list of detected objects for an image.
        """
        objects = ObjectDetection.query.filter_by(image_id=image_id).all()
        object_list = []
        for obj in objects:
            object_list.append({
                'id': obj.object_id,
                'bbox': obj.bbox,
                'centroid': obj.centroid,
                'radius': obj.radius
            })
        return object_list

@api.route('/object/<string:object_id>')
@api.param('object_id', 'The ID of the object')
class ObjectDetail(Resource):
    def get(self, object_id):
        """
        API for getting the details of a specific detected object.
        """
        object_detection = ObjectDetection.query.filter_by(object_id=object_id).first()
        if object_detection:
            return {
                'id': object_detection.object_id,
                'bbox': object_detection.bbox,
                'centroid': object_detection.centroid,
                'radius': object_detection.radius
            }
        else:
            return {'message': 'Object not found'}