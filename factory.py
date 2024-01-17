# factory.py

from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os

load_dotenv()

mongo = PyMongo()  # Crea una instancia de PyMongo

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")

    mongo.init_app(app)  # Inicializa la instancia de PyMongo con la app

    from prediction_views import predict_view, predictions_by_user, delete_prediction_by_id, update_prediction_price, get_prediction_by_id
    app.add_url_rule('/predict', view_func=predict_view, methods=['GET'])
    app.add_url_rule('/predictions', view_func=predictions_by_user, methods=['GET'])
    app.add_url_rule('/delete_prediction', view_func=delete_prediction_by_id, methods=['DELETE'])
    app.add_url_rule('/get_prediction', view_func=get_prediction_by_id, methods=['GET'])
    app.add_url_rule('/update_prediction_price', view_func=update_prediction_price, methods=['POST'])


    return app
