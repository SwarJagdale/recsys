from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson import ObjectId
import json
from datetime import datetime
import pandas as pd
import numpy as np
from utils.hybrid_recommender import recommend, add_interaction as add_recommender_interaction, init_app

app = Flask(__name__)
CORS(app)

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/ecommerce_db"
mongo = PyMongo(app)

# Initialize the recommender system with MongoDB
init_app(app)

# JSON encoder for ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

app.json_encoder = JSONEncoder

# User routes
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if mongo.db.users.find_one({'email': data['email']}):
        return jsonify({'error': 'User already exists'}), 409
    
    user = {
        'email': data['email'],
        'password': data['password'],  # In production, hash the password
        'created_at': datetime.utcnow(),
        'preferences': data.get('preferences', {}),
        'interactions': []
    }
    
    result = mongo.db.users.insert_one(user)
    return jsonify({'message': 'User created successfully', 'user_id': str(result.inserted_id)}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    user = mongo.db.users.find_one({
        'email': data['email'],
        'password': data['password']  # In production, verify hashed password
    })
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return jsonify({
        'message': 'Login successful',
        'user_id': str(user['_id']),
        'preferences': user.get('preferences', {})
    })

# Interaction routes
@app.route('/api/interactions', methods=['POST'])
def add_interaction():
    data = request.json
    if not data or not data.get('user_id') or not data.get('product_id') or not data.get('interaction_type'):
        return jsonify({'error': 'Missing required fields'}), 400

    interaction_type = data['interaction_type']
    user_id = data['user_id']
    product_id = data['product_id']

    # Store interaction in MongoDB using ObjectId
    interaction = {
        'user_id': ObjectId(user_id),
        'product_id': int(product_id),
        'interaction_type': interaction_type,
        'timestamp': datetime.utcnow()
    }
    mongo.db.interactions.insert_one(interaction)

    # Pass IDs to recommender system
    add_recommender_interaction(user_id, product_id, interaction_type)
    
    return jsonify({'message': 'Interaction recorded successfully'}), 201

# Recommendation routes
@app.route('/api/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    try:
        # Use user_id as a string (MongoDB ObjectId)
        recommendations_df = recommend(user_id, k=10)
        # Convert recommendations to list of dictionaries
        recommendations = []
        for idx, row in recommendations_df.iterrows():
            recommendations.append({
                'product_id': str(idx),
                'category': row['category'],
                'brand': row['brand'],
                'price': float(row['price'])
            })
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Product routes
@app.route('/api/products', methods=['GET'])
def get_products():
    products = list(mongo.db.products.find())
    return jsonify({'products': products})

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product)

if __name__ == '__main__':
    app.run(debug=True) 