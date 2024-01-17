from flask import jsonify, request
from flask import current_app as app
from factory import mongo
from bson import json_util, ObjectId
import os
import re
import google.generativeai as genai

def obtener_parametro(param, tipo=int, es_string=False):
    valor = request.args.get(param)
    if es_string:
        return valor
    try:
        return tipo(valor)
    except (TypeError, ValueError):
        return None

def predict_view():

    user = obtener_parametro("user", es_string=True)
    m2 = obtener_parametro('m2')
    antiguedad = obtener_parametro('antiguedad')
    ambientes = obtener_parametro('ambientes')
    banos = obtener_parametro('baños')
    ubicacion = obtener_parametro('ubicacion', es_string=True)
    tipo_propiedad = obtener_parametro('tipo_propiedad', es_string=True)
    condicion_interna = obtener_parametro('condicion_interna')
    condicion_externa = obtener_parametro('condicion_externa')
    estado_conservacion = obtener_parametro('estado_conservacion', es_string=True)
    patio_jardin = obtener_parametro('patio_jardin', es_string=True)
    caracteristicas_adicionales = obtener_parametro('caracteristicas_adicionales', es_string=True)
    terreno_adyacente = obtener_parametro('terreno_adyacente', es_string=True)
    seguridad = obtener_parametro('seguridad', es_string=True)
    piso_nivel = obtener_parametro('piso_nivel')
    caracteristicas_edificio = obtener_parametro('caracteristicas_edificio', es_string=True)
    caracteristicas_casa = obtener_parametro('caracteristicas_casa', es_string=True)
    ascensor = obtener_parametro('ascensor', es_string=True)
    vista = obtener_parametro('view', es_string=True)
    estacionamiento = obtener_parametro('estacionamiento', es_string=True)

    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    genai.configure(api_key=GOOGLE_API_KEY)
    genai_model = genai.GenerativeModel('gemini-pro')
    prompt = ""

    if tipo_propiedad == 'casa':
        prompt = f"""Calcula el precio estimado de una casa en dólares americanos, integrando factores globales y locales, incluyendo análisis del mercado inmobiliario local, ventas comparables recientes, tendencias económicas y demográficas, planes de desarrollo local, ajustes por inflación y condiciones económicas, utilizando métodos estadísticos avanzados y cruzando con índices inmobiliarios oficiales. Realiza integración de datos en tiempo real si es posible. Ubicación: {ubicacion}. Metros Cuadrados (aproximados): {m2}. Antigüedad (años desde la construcción): {antiguedad}. Número de Ambientes: {ambientes}. Baños: {banos}. Condición Interna (1: Malo, 2: Medio, 3: Muy Bueno): {condicion_interna}. Condición Externa (1: Malo, 2: Medio, 3: Muy Bueno): {condicion_externa}. Estado de Conservación: {estado_conservacion}. Patio/Jardín (sí/no): {patio_jardin}. Características adicionales (ej: piscina, garaje, sótano): {caracteristicas_adicionales}, {caracteristicas_casa}. Terreno cercano a centro comercial (sí/no): {terreno_adyacente}. Seguridad (ej: sistema de alarma, vigilancia): {seguridad}. Prioriza las características mencionadas, pero si no existe una coincidencia exacta, proporciona un precio basado en casas similares en la misma zona. Solo el precio, es decir, solo retorna números. EN EL UNICO CASO QUE HAYA ALGUN 'None' EN EL PROMPT RESPONSE VACIO."""
    elif tipo_propiedad == 'departamento':
        prompt = f"""Calcula el precio estimado de un departamento en dólares americanos, considerando factores globales y locales, incluyendo análisis del mercado inmobiliario local específico para departamentos, ventas comparables recientes, tendencias económicas y demográficas, próximos desarrollos y cambios en infraestructura, ajustes por condiciones económicas actuales, utilizando técnicas estadísticas avanzadas y validación con índices inmobiliarios oficiales. Integra datos en tiempo real cuando sea posible. Ubicación: {ubicacion}. Metros Cuadrados (aproximados): {m2}. Antigüedad (años desde la construcción): {antiguedad}. Número de Ambientes: {ambientes}. Baños: {banos}. Piso o nivel del departamento: {piso_nivel}. Condición Interna (1: Malo, 2: Medio, 3: Muy Bueno): {condicion_interna}. Condición Externa (1: Malo, 2: Medio, 3: Muy Bueno): {condicion_externa}. Estado de Conservación: {estado_conservacion}. Características del edificio (ej: gimnasio, seguridad, piscina): {caracteristicas_edificio}. Ascensor (sí/no): {ascensor}. Vista (ej: ciudad, mar, parque): {vista}. Incluye estacionamiento (sí/no): {estacionamiento}. Prioriza las características mencionadas, pero si no hay coincidencia exacta, proporciona un precio basado en departamentos similares en la misma zona. Solo el precio, es decir, solo retorna números. EN EL UNICO CASO QUE HAYA ALGUN 'None' EN EL PROMPT RESPONSE VACIO."""

    else:
        return jsonify({"error": "Tipo de propiedad no válido"}), 400

    response = genai_model.generate_content(prompt)
    response_text = response.text

    precio_numerico = re.findall(r'\d+', response_text)
    precio = ''.join(precio_numerico)


    print(precio_numerico)

    prediction_data = {
        'user': user,
        "tipo": tipo_propiedad,
        'm2': m2,
        'ambientes': ambientes,
        'banos': banos,
        'ubicacion': ubicacion,
        'precio': precio
    }

    mongo.db.swan_app_prediction.insert_one(prediction_data)

    return jsonify({"Precio_Predicho": response_text})



def predictions_by_user():
    with app.app_context():
        user_id = request.args.get('id')
        try:
            predictions = mongo.db.swan_app_prediction.find({"user": user_id})
            # Convertir cada documento a un diccionario con un string de '_id'
            prediction_list = [{
                **prediction,
                '_id': str(prediction['_id'])
            } for prediction in predictions]
            return jsonify({'predictions': prediction_list})
        except Exception as e:
            print(f"Error accessing database: {e}")
            return jsonify({'error': 'Error accessing database'}), 500

def delete_prediction_by_id():
    try:
        # Obtiene el _id desde la solicitud
        prediction_id = request.args.get('_id')

        # Verifica que el _id ha sido proporcionado
        if not prediction_id:
            return jsonify({'error': 'No _id provided'}), 400

        # Convierte el _id en un objeto ObjectId
        obj_id = ObjectId(prediction_id)

        # Realiza la operación de eliminación
        result = mongo.db.swan_app_prediction.delete_one({'_id': obj_id})

        # Verifica si se ha eliminado algún documento
        if result.deleted_count:
            return jsonify({'message': 'Prediction deleted successfully'}), 200
        else:
            return jsonify({'error': 'No prediction found with the provided _id'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_prediction_by_id():
    try:
        prediction_id = request.args.get('_id')
        if not prediction_id:
            return jsonify({'error': 'No _id provided'}), 400

        obj_id = ObjectId(prediction_id)
        prediction = mongo.db.swan_app_prediction.find_one({'_id': obj_id})

        if prediction:
            return jsonify({**prediction, '_id': str(prediction['_id'])})
        else:
            return jsonify({'error': 'No prediction found with the provided _id'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_prediction_price():
    try:
        data = request.json
        prediction_id = data.get('_id')
        new_price = data.get('price')

        if not prediction_id or new_price is None:
            return jsonify({'error': 'Missing _id or price'}), 400

        obj_id = ObjectId(prediction_id)
        result = mongo.db.swan_app_prediction.update_one(
            {'_id': obj_id},
            {'$set': {'price': new_price}}
        )

        if result.matched_count:
            return jsonify({'message': 'Prediction price updated successfully'}), 200
        else:
            return jsonify({'error': 'No prediction found with the provided _id'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
