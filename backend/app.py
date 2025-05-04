from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson import ObjectId
import json
from datetime import datetime
import pandas as pd
import numpy as np
from utils.hybrid_recommender import recommend,  add_recommender_interaction, init_app

app = Flask(__name__)
CORS(app)

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/ecommerce_db"
mongo = PyMongo(app)

# Initialize the recommender system with MongoDB
init_app(app)

# Create text index for search
try:
    mongo.db.products.create_index([
        ("product_name", "text"),
        ("description", "text"),
        ("category", "text"),
        ("brand", "text")
    ])
except Exception as e:
    print(f"Index might already exist: {e}")

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
    if not data or not data.get('email') or not data.get('password') or not data.get('location'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if mongo.db.users.find_one({'email': data['email']}):
        return jsonify({'error': 'User already exists'}), 409
    
    user = {
        'email': data['email'],
        'password': data['password'],  # In production, hash the password
        'created_at': datetime.utcnow(),
        'location': data['location'],
        'preferences': data.get('preferences', {}),
        'interactions': []
    }
    
    result = mongo.db.users.insert_one(user)
    return jsonify({
        'message': 'User created successfully', 
        'user_id': str(result.inserted_id),
        'location': data['location']
    }), 201

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

@app.route('/api/cart_interactions/<user_id>', methods=['GET'])
def get_cart_interactions(user_id):
    """Fetch latest 'add_to_cart' interactions for a user, sorted by timestamp desc."""
    try:
        interactions = list(
            mongo.db.interactions.find({
                'user_id': ObjectId(user_id),
                'interaction_type': 'add_to_cart'
            }).sort('timestamp', -1)
        )
        return jsonify({'cart_interactions': interactions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/previous_orders/<user_id>', methods=['GET'])
def get_previous_orders(user_id):
    """Fetch previous 'purchase' interactions for a user, sorted by timestamp desc."""
    try:
        orders = list(
            mongo.db.interactions.find({
                'user_id': ObjectId(user_id),
                'interaction_type': 'purchase'
            }).sort('timestamp', -1)
        )
        return jsonify({'previous_orders': orders})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        recommendations_df = recommend(user_id, k=20)
        recommendations = []
        for idx, row in recommendations_df.iterrows():
            recommendations.append({
                'product_id': str(idx),
                'category': row['category'],
                'brand': row['brand'],
                'price': float(row['price']),
                'product_name': row['product_name'],
                'description': row['description'],
                'score': float(row['score']),
                'recommendation_category': row['recommendation_source']  # Use the source from the recommender
            })
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Profile route
@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user_data = {
            'email': user.get('email'),
            'preferences': user.get('preferences', {})
        }
        interactions = list(
            mongo.db.interactions.find({'user_id': ObjectId(user_id)})
            .sort('timestamp', -1)
        )
        summary = {}
        for inter in interactions:
            t = inter.get('interaction_type')
            summary[t] = summary.get(t, 0) + 1
            
        # Get recent interactions with product details
        recent_interactions = []
        for inter in interactions[:10]:
            product = mongo.db.products.find_one({'_id': inter.get('product_id')})
            if product:
                recent_interactions.append({
                    'product_id': str(inter.get('product_id')),
                    'interaction_type': inter.get('interaction_type'),
                    'timestamp': inter.get('timestamp'),
                    'product_name': product.get('product_name'),
                    'category': product.get('category'),
                    'brand': product.get('brand')
                })
        
        # Calculate recommendation profile
        if interactions:
            # Get product details for interactions
            product_interactions = []
            for inter in interactions:
                product = mongo.db.products.find_one({'_id': inter.get('product_id')})
                if product:
                    product_interactions.append({
                        'category': product.get('category'),
                        'brand': product.get('brand'),
                        'interaction_type': inter.get('interaction_type'),
                        'timestamp': inter.get('timestamp')
                    })

            # Calculate category preferences
            category_counts = {}
            brand_counts = {}
            interaction_weights = {'view': 1, 'add_to_cart': 3, 'purchase': 5}
            
            for inter in product_interactions:
                weight = interaction_weights.get(inter['interaction_type'], 1)
                
                # Category preferences
                cat = inter['category']
                category_counts[cat] = category_counts.get(cat, 0) + weight
                
                # Brand preferences
                brand = inter['brand']
                brand_counts[brand] = brand_counts.get(brand, 0) + weight
            
            # Sort and normalize preferences
            total_category_weight = sum(category_counts.values()) or 1
            total_brand_weight = sum(brand_counts.values()) or 1
            
            recommendation_profile = {
                'category_preferences': {k: v/total_category_weight 
                                      for k, v in sorted(category_counts.items(), 
                                                       key=lambda x: x[1], reverse=True)},
                'brand_preferences': {k: v/total_brand_weight 
                                    for k, v in sorted(brand_counts.items(), 
                                                     key=lambda x: x[1], reverse=True)},
                'interaction_patterns': summary
            }
        else:
            recommendation_profile = {
                'category_preferences': {},
                'brand_preferences': {},
                'interaction_patterns': {}
            }

        return jsonify({
            'user': user_data,
            'summary': summary,
            'recent': recent_interactions,
            'recommendation_profile': recommendation_profile
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Product routes
@app.route('/api/products', methods=['GET'])
def get_products():
    products = list(mongo.db.products.find())
    return jsonify({'products': products})

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    # Try to cast product_id to int, fallback to string if ValueError occurs
    try:
        lookup_id = int(product_id)
    except ValueError:
        lookup_id = product_id
    product = mongo.db.products.find_one({'product_id': lookup_id})
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product)

@app.route('/api/products/search', methods=['GET'])
def search_products():
    query = request.args.get('query', '')
    category = request.args.get('category')
    brand = request.args.get('brand')
    
    # Build the search filter
    search_filter = {}
    
    if query:
        search_filter['$text'] = {'$search': query}
    
    if category:
        search_filter['category'] = category
        
    if brand:
        search_filter['brand'] = brand
    
    # Execute search with filters
    try:
        if query:
            # If there's a text query, use text search with sorting by score
            products = list(mongo.db.products.find(
                search_filter,
                {'score': {'$meta': 'textScore'}}
            ).sort([('score', {'$meta': 'textScore'})]))
        else:
            # If no text query, just filter by category/brand
            products = list(mongo.db.products.find(search_filter))
            
        return jsonify({'products': products})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)