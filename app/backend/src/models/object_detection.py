from src import db

class ObjectDetection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
    object_id = db.Column(db.String(100), nullable=False)
    bbox = db.Column(db.JSON, nullable=False)
    centroid = db.Column(db.JSON, nullable=False)
    radius = db.Column(db.Integer, nullable=False)