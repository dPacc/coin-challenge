from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_restx import Api

db = SQLAlchemy()
cors = CORS()
api = Api()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    db.init_app(app)
    cors.init_app(app)
    api.init_app(app)
    
    from .routes import blueprint as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    return app