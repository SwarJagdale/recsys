from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson import ObjectId
import json
from datetime import datetime
import pandas as pd
import numpy as np
from utils.HybridRecommender import recommend, add_recommender_interaction, init_app, get_demographic_recommendations, get_recency_scores, get_collaborative_scores, get_context_recommendations
# from utils.HybridRecommender.demographic import get_demographic_recommendations
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

# ==========================================================================
# =============================== Login Routes===============================
# ==========================================================================
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    if not data or not data.get('email') or not data.get('password') or not data.get('location'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    last_user = mongo.db.users.find_one({}, sort=[('user_id', -1)])
    print(last_user, 'last_user')
    
    if mongo.db.users.find_one({'email': data['email']}, {'_id': 0}):
        return jsonify({'error': 'User already exists'}), 409
    
    # Generate a new integer user_id
    last_user = mongo.db.users.find_one(sort=[('user_id', -1)])

    new_user_id = 1 if not last_user else int(last_user['user_id']) + 1
    
    user = {
        'user_id': new_user_id,
        'email': data['email'],
        'password': data['password'],  # In production, hash the password
        'created_at': datetime.utcnow(),
        'location': data['location'],
        'preferences': data.get('preferences', {}),
        'interactions': [],
        'user_id': int(last_user['user_id']) + 1 if last_user else 1,
    }
    
    result = mongo.db.users.insert_one(user)
    return jsonify({
        'message': 'User created successfully', 
        'user_id': str(int(last_user['user_id'])+1) if last_user else 1,
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
    }, {'_id': 0, 'preferences': 1, 'user_id': 1})
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return jsonify({
        'message': 'Login successful',
        'user_id': str(user['user_id']),
        'preferences': user.get('preferences', {})
    })

# ==========================================================================
# =============================== User Routes ===============================
# ==========================================================================

@app.route('/api/cart_interactions/<user_id>', methods=['GET'])
def get_cart_interactions(user_id):
    try:
        pipeline = [
            {
                '$match': {
                    'user_id': int(user_id),
                    'interaction_type': 'add_to_cart'
                }
            },
            {
                '$lookup': {
                    'from': 'products',
                    'localField': 'product_id',
                    'foreignField': 'product_id',
                    'as': 'product'
                }
            },
            {
                '$unwind': '$product'
            },
            {
                '$project': {
                    '_id': 0,
                    'product_id': 1,
                    'timestamp': 1,
                    'product_name': '$product.product_name',
                    'price': '$product.price',
                    'description': '$product.description',
                    'category': '$product.category',
                    'brand': '$product.brand'
                }
            },
            {
                '$sort': {'timestamp': -1}
            }
        ]
        
        interactions = list(mongo.db.interactions.aggregate(pipeline))
        return jsonify({'cart_interactions': interactions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/previous_orders/<user_id>', methods=['GET'])
def get_previous_orders(user_id):
    try:
        pipeline = [
            {
                '$match': {
                    'user_id': int(user_id),
                    'interaction_type': 'purchase'
                }
            },
            {
                '$lookup': {
                    'from': 'products',
                    'localField': 'product_id',
                    'foreignField': 'product_id',
                    'as': 'product'
                }
            },
            {
                '$unwind': '$product'
            },
            {
                '$project': {
                    '_id': 0,
                    'product_id': 1,
                    'timestamp': 1,
                    'product_name': '$product.product_name',
                    'price': '$product.price',
                    'description': '$product.description',
                    'category': '$product.category',
                    'brand': '$product.brand'
                }
            },
            {
                '$sort': {'timestamp': -1}
            }
        ]
        
        orders = list(mongo.db.interactions.aggregate(pipeline))
        return jsonify({'previous_orders': orders})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        user = mongo.db.users.find_one({'user_id': int(user_id)}, {'_id': 0, 'email': 1, 'preferences': 1})
        if not user:
            return jsonify({'error': 'User not found'}), 404

        interactions = list(
            mongo.db.interactions.find(
                {'user_id': int(user_id)},
                {'_id': 0, 'interaction_type': 1, 'timestamp': 1, 'product_id': 1}
            ).sort('timestamp', -1)
        )
        
        summary = {}
        for inter in interactions:
            t = inter.get('interaction_type')
            summary[t] = summary.get(t, 0) + 1
            
        # Get recent interactions with product details
        recent_interactions = []
        for inter in interactions[:10]:
            product = mongo.db.products.find_one(
                {'product_id': inter.get('product_id')},
                {'_id': 0, 'product_name': 1, 'category': 1, 'brand': 1}
            )
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
                product = mongo.db.products.find_one(
                    {'product_id': inter.get('product_id')},
                    {'_id': 0, 'category': 1, 'brand': 1}
                )
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
                if cat:  # Only add if category exists
                    category_counts[cat] = category_counts.get(cat, 0) + weight
                
                # Brand preferences
                brand = inter['brand']
                if brand:  # Only add if brand exists
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
            'user': user,
            'summary': summary,
            'recent': recent_interactions,
            'recommendation_profile': recommendation_profile
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/interactions', methods=['POST'])
def add_interaction():
    data = request.json
    if not data or not data.get('user_id') or not data.get('product_id') or not data.get('interaction_type'):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate interaction type
    valid_interaction_types = ['view', 'add_to_cart', 'purchase']
    if data['interaction_type'] not in valid_interaction_types:
        return jsonify({'error': f'Invalid interaction type. Must be one of: {", ".join(valid_interaction_types)}'}), 400

    try:
        # Convert IDs to integers
        user_id = int(data['user_id'])
        product_id = int(data['product_id'])
    except (ValueError, TypeError):
        return jsonify({'error': 'user_id and product_id must be valid integers'}), 400

    # Verify user exists
    if not mongo.db.users.find_one({'user_id': user_id}):
        return jsonify({'error': 'User not found'}), 404

    # Verify product exists
    if not mongo.db.products.find_one({'product_id': product_id}):
        return jsonify({'error': 'Product not found'}), 404

    interaction = {
        'user_id': user_id,
        'product_id': product_id,
        'interaction_type': data['interaction_type'],
        'timestamp': datetime.utcnow()
    }
    
    result = mongo.db.interactions.insert_one(interaction)
    
    return jsonify({
        'message': 'Interaction recorded successfully',
        'interaction_id': str(result.inserted_id)
    }), 201


# ==========================================================================
# =============================== Product Routes ===========================
# ==========================================================================

@app.route('/api/products', methods=['GET'])
def get_products():
    products = list(mongo.db.products.find({}, {'_id': 0}))
    return jsonify({'products': products})

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    try:
        lookup_id = int(product_id)
    except ValueError:
        lookup_id = product_id
        
    product = mongo.db.products.find_one({'product_id': lookup_id}, {'_id': 0})
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product)

@app.route('/api/products/search', methods=['GET'])
def search_products():
    query = request.args.get('query', '')
    category = request.args.get('category')
    brand = request.args.get('brand')
    
    search_filter = {}
    
    if query:
        search_filter['$text'] = {'$search': query}
    
    if category:
        search_filter['category'] = {'$regex': f'^{category}$', '$options': 'i'}
        
    if brand:
        search_filter['brand'] = {'$regex': f'^{brand}$', '$options': 'i'}
    
    try:
        if query:
            products = list(mongo.db.products.find(
                search_filter,
                {'_id': 0, 'score': {'$meta': 'textScore'}}
            ).sort([('score', {'$meta': 'textScore'})]))
        else:
            products = list(mongo.db.products.find(search_filter, {'_id': 0}))
            
        return jsonify({'products': products})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==========================================================================
# =============================== Recommendation Routes ===================
# ==========================================================================

@app.route('/api/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    try:
        recommendations_df = recommend(user_id, k=20)
        print(recommendations_df)
        recommendations = []
        for idx, row in recommendations_df.iterrows():
            recommendations.append({
                'product_id': str(idx),
                'category': row['category'],
                'brand': row['brand'],
                'price': float(row['price']),
                'product_name': row['product_name'],
                'description': row['description'],
                # 'score': float(row['score']),
                'recommendation_category': row['recommendation_source']
            })
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==========================================================================
# =============================== Dev Routes =============================
# ==========================================================================

@app.route('/api/dev/demographics', methods=['GET'])
def get_demographics():
    location = request.args.get('location')
    if not location:
        return jsonify({'error': 'Missing location parameter'}), 400
    recommendations = get_demographic_recommendations(location=location, n_items=20)
    return jsonify({'recommendations': recommendations})




if __name__ == '__main__':
    app.run(debug=True)
